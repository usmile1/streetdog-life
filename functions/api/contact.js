/**
 * POST /api/contact — the general contact form on /contact/.
 *
 * The open door: anything at all. The form on /games/ stays about the game (offers of help), and
 * /support/ stays about problems with a build and information-removal requests. Three narrow forms
 * beat one broad one, because the question you are asked shapes the answer you get.
 *
 * Every defence and the environment variables it needs live in ./_lib.js, shared with the others.
 */
import { json, submitForm } from "./_lib.js";

const SPEC = {
  name: "contact",
  fields: [
    { key: "name", label: "Name", max: 120, required: true },
    { key: "email", label: "Email", max: 200, required: true, email: true },
    { key: "message", label: "What’s on their mind", max: 4000, required: true },
  ],
  replyTo: "email",
  source: "https://streetdog.life/contact/",
  subject: (v) => `streetdog.life — message from ${v.name}`,
};

export const onRequestPost = ({ request, env }) => submitForm({ request, env, spec: SPEC });

// See the note in interest.js: method-specific, never a catch-all `onRequest`.
export const onRequestGet = () => json({ error: "POST only." }, 405);
