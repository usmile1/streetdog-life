/**
 * Shared form handling for the Pages Functions in this directory.
 *
 * ⚠ The leading underscore is deliberate: Cloudflare Pages does not route files whose name begins
 * with "_", so this is a module rather than an endpoint. Rename it and it becomes a public URL.
 *
 * Both public forms on the site (tester interest, support) need exactly the same defences, and
 * duplicating them is how one copy quietly falls behind the other. Adding a third form should mean
 * writing a spec, not writing another honeypot.
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
 * If any are missing every form fails LOUDLY with a 500 and logs which one, rather than silently
 * accepting submissions and dropping them on the floor. A form that says "thank you" and throws the
 * message away is worse than a form that is visibly broken.
 */

export const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });

const REQUIRED_ENV = ["TURNSTILE_SECRET", "RESEND_API_KEY", "NOTIFY_TO", "NOTIFY_FROM"];

/**
 * Run one form submission end to end.
 *
 * spec = {
 *   name:      short label used in the log line and the mail subject
 *   fields:    [{ key, label, max, required, email }]
 *   replyTo:   optional field key whose value becomes the mail's Reply-To
 *   source:    the page the form lives on, quoted in the mail body
 * }
 */
export async function submitForm({ request, env, spec }) {
  // --- config ---------------------------------------------------------------------------------
  const missing = REQUIRED_ENV.filter((k) => !env[k]);
  if (missing.length) {
    console.error(`${spec.name}: missing env vars:`, missing.join(", "));
    return json({ error: "The form is not working just now. Please try again later." }, 500);
  }

  // --- parse ----------------------------------------------------------------------------------
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Malformed request." }, 400);
  }

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
    console.warn(`${spec.name}: honeypot tripped`, {
      ip: request.headers.get("CF-Connecting-IP"),
      ua: request.headers.get("User-Agent"),
    });
    return json({ ok: true });
  }

  // --- how fast was it submitted ----------------------------------------------------------------
  // Bots post the moment they parse the page. Nobody types a form in under two seconds.
  // Client-supplied and therefore forgeable, which is exactly why it only ever REJECTS and is
  // stacked behind Turnstile rather than trusted on its own. Missing is treated as fine — an older
  // browser or a blocked script should not lock someone out of the form.
  const elapsed = Number(body.elapsed_ms);
  if (Number.isFinite(elapsed) && elapsed >= 0 && elapsed < 2000) {
    console.warn(`${spec.name}: submitted in`, elapsed, "ms — too fast");
    return json({ error: "That was quick — please try once more." }, 400);
  }

  // --- validate. The client checks too, for a kinder message; this is the check that counts ------
  const values = {};
  for (const f of spec.fields) {
    const v = String(body[f.key] ?? "").trim();
    if (f.required && !v) return json({ error: "Please fill in every required field." }, 400);
    if (v.length > f.max) return json({ error: "That is longer than the form allows." }, 400);
    // Deliberately loose. Email addresses are far stranger than any regex people write, and the real
    // proof of an address is that a message to it arrives.
    if (f.email && v && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v))
      return json({ error: "That email address does not look right." }, 400);
    values[f.key] = v;
  }

  // --- Turnstile ------------------------------------------------------------------------------
  const token = String(body["cf-turnstile-response"] ?? "");
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
    console.warn(`${spec.name}: turnstile rejected`, outcome["error-codes"]);
    return json({ error: "The anti-spam check did not pass. Please try again." }, 403);
  }

  // --- send -----------------------------------------------------------------------------------
  const lines = spec.fields
    .map((f) => `${f.label}:\n${values[f.key] || "(not given)"}\n`)
    .join("\n");
  const replyTo = spec.replyTo ? values[spec.replyTo] : "";

  const sent = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: env.NOTIFY_FROM,
      to: [env.NOTIFY_TO],
      // Reply-To only when the form actually collected an address, so hitting Reply answers the
      // person rather than the form. Omitted entirely otherwise — a blank Reply-To is worse than none.
      ...(replyTo ? { reply_to: replyTo } : {}),
      subject: spec.subject(values),
      text:
        `${lines}\n---\nSent from ${spec.source}\n` +
        `Country: ${request.headers.get("CF-IPCountry") ?? "unknown"}\n`,
    }),
  });

  if (!sent.ok) {
    // Log the reason but never return it: provider errors can carry account details.
    console.error(`${spec.name}: resend failed`, sent.status, await sent.text().catch(() => ""));
    return json({ error: "Could not send just now. Please try again in a moment." }, 502);
  }

  return json({ ok: true });
}
