/**
 * POST /api/interest — the "want to help?" form on /games/.
 *
 * A Cloudflare Pages Function running at the edge; there is no server to keep alive. Every defence
 * (honeypot, timing floor, Turnstile, validation) and the environment variables it needs live in
 * ./_lib.js, shared with /api/support.
 */
import { json, submitForm } from "./_lib.js";

const SPEC = {
  name: "interest",
  fields: [
    { key: "name", label: "Name", max: 120, required: true },
    { key: "email", label: "Email", max: 200, required: true, email: true },
    { key: "why", label: "How they would like to help", max: 2000, required: true },
  ],
  replyTo: "email",
  source: "https://streetdog.life/games/#interest",
  subject: (v) => `streetdog.life — offer of help from ${v.name}`,
};

export const onRequestPost = ({ request, env }) => submitForm({ request, env, spec: SPEC });

// A stray GET otherwise returns the Pages 404, which reads as "the endpoint does not exist" while
// debugging and sends you looking in the wrong place.
//
// ⚠ Method-specific export, NOT a catch-all `onRequest`. In Pages Functions an exported `onRequest`
// takes precedence over every onRequestPost/Get/…, so adding one here would silently disable the
// POST handler above and break the form.
export const onRequestGet = () => json({ error: "POST only." }, 405);
