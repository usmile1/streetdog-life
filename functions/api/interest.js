/**
 * POST /api/interest — the "want to help test it?" form on /games/.
 *
 * A Cloudflare Pages Function. It runs at the edge; there is no server to keep alive.
 *
 * WHAT IT NEEDS, set as Pages environment variables in the dashboard — NEVER in this repo, which is
 * public. Workers & Pages → streetdog-life → Settings → Variables and Secrets:
 *
 *   TURNSTILE_SECRET   secret key from the Turnstile widget (the SITE key is public and lives in the
 *                      HTML; this is its private half)
 *   RESEND_API_KEY     from resend.com — the thing that actually sends the mail
 *   NOTIFY_TO          where submissions go, e.g. wardeng@gmail.com
 *   NOTIFY_FROM        a verified sender on your Resend domain, e.g. forms@streetdog.life
 *
 * Mark TURNSTILE_SECRET and RESEND_API_KEY as ENCRYPTED. Once encrypted they cannot be read back out
 * of the dashboard, which is the point.
 *
 * If any are missing the endpoint fails LOUDLY with a 500 and logs which one, rather than silently
 * accepting submissions and dropping them on the floor. A form that says "thank you" and throws the
 * message away is worse than a form that is visibly broken.
 */

const MAX = { name: 120, email: 200, why: 2000 };

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });

export async function onRequestPost({ request, env }) {
  // --- config ---------------------------------------------------------------------------------
  const missing = ["TURNSTILE_SECRET", "RESEND_API_KEY", "NOTIFY_TO", "NOTIFY_FROM"]
    .filter((k) => !env[k]);
  if (missing.length) {
    console.error("interest: missing env vars:", missing.join(", "));
    return json({ error: "The form is not working just now. Please try again later." }, 500);
  }

  // --- parse ----------------------------------------------------------------------------------
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Malformed request." }, 400);
  }

  const name = String(body.name ?? "").trim();
  const email = String(body.email ?? "").trim();
  const why = String(body.why ?? "").trim();
  const token = String(body["cf-turnstile-response"] ?? "");

  // --- honeypot ---------------------------------------------------------------------------------
  // An off-screen input no person can see or tab to. If it has anything in it, whatever filled it
  // walked the DOM rather than read the page.
  //
  // ⚠ THIS IS THE ONE PLACE THAT DELIBERATELY LIES: it returns success without sending anything, so
  // a bot cannot tell it was caught and cannot adapt. Everywhere else in this file, saying "sent"
  // when nothing was sent would be the worst possible behaviour.
  //
  // Safe here only because the field name is non-semantic (`hp_field`), so no password manager will
  // autofill it. Rename it to anything resembling "website", "company" or "url" and this stops being
  // a bot trap and starts silently eating real messages from people with autofill.
  if (String(body.hp_field ?? "").trim() !== "") {
    console.warn("interest: honeypot tripped", {
      ip: request.headers.get("CF-Connecting-IP"),
      ua: request.headers.get("User-Agent"),
    });
    return json({ ok: true });
  }

  // --- how fast was it submitted ----------------------------------------------------------------
  // Bots post the moment they parse the page. Nobody types three fields in under two seconds.
  // Client-supplied and therefore forgeable, which is exactly why it only ever REJECTS and is
  // stacked behind Turnstile rather than trusted on its own. Missing is treated as fine — an older
  // browser or a blocked script should not lock someone out of the form.
  const elapsed = Number(body.elapsed_ms);
  if (Number.isFinite(elapsed) && elapsed >= 0 && elapsed < 2000) {
    console.warn("interest: submitted in", elapsed, "ms — too fast");
    return json({ error: "That was quick — please try once more." }, 400);
  }

  // --- validate. The client checks too, for a kinder message; this is the check that counts ------
  if (!name || !email || !why) return json({ error: "Please fill in all three fields." }, 400);
  if (name.length > MAX.name || email.length > MAX.email || why.length > MAX.why)
    return json({ error: "That is longer than the form allows." }, 400);
  // Deliberately loose. Email addresses are far stranger than any regex people write, and the real
  // proof of an address is that a message to it arrives.
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email))
    return json({ error: "That email address does not look right." }, 400);

  // --- Turnstile ------------------------------------------------------------------------------
  if (!token) return json({ error: "Please complete the anti-spam check." }, 400);
  const verify = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      secret: env.TURNSTILE_SECRET,
      response: token,
      remoteip: request.headers.get("CF-Connecting-IP") ?? undefined,
    }),
  });
  const outcome = await verify.json().catch(() => ({ success: false }));
  if (!outcome.success) {
    console.warn("interest: turnstile rejected", outcome["error-codes"]);
    return json({ error: "The anti-spam check did not pass. Please try again." }, 403);
  }

  // --- send -----------------------------------------------------------------------------------
  // reply_to is set to the sender so hitting Reply in the inbox answers the person, not the form.
  const sent = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: env.NOTIFY_FROM,
      to: [env.NOTIFY_TO],
      reply_to: email,
      subject: `streetdog.life — tester interest from ${name}`,
      text:
        `Name:  ${name}\n` +
        `Email: ${email}\n\n` +
        `Why they want to help:\n${why}\n\n` +
        `---\nSent from the form at https://streetdog.life/games/#interest\n` +
        `Country: ${request.headers.get("CF-IPCountry") ?? "unknown"}\n`,
    }),
  });

  if (!sent.ok) {
    // Log the reason but never return it: provider errors can carry account details.
    console.error("interest: resend failed", sent.status, await sent.text().catch(() => ""));
    return json({ error: "Could not send just now. Please try again in a moment." }, 502);
  }

  return json({ ok: true });
}

// A stray GET otherwise returns the Pages 404, which reads as "the endpoint does not exist" while
// debugging and sends you looking in the wrong place.
//
// ⚠ Method-specific export, NOT a catch-all `onRequest`. In Pages Functions an exported `onRequest`
// takes precedence over every onRequestPost/Get/…, so adding one here would have silently disabled
// the POST handler above and broken the form.
export const onRequestGet = () => json({ error: "POST only." }, 405);
