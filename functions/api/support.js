/**
 * POST /api/support — the support form on /support/.
 *
 * Two jobs: reporting a problem with a build, and requesting removal of personal information (the
 * privacy note on /games/ points here for that).
 *
 * Email is REQUIRED, and that is load-bearing for the second job: a removal request needs an address
 * both to match the stored record against and to confirm the deletion back to. Without one the
 * request arrives as a name and nothing else, and cannot be actioned or answered.
 *
 * Every defence and the environment variables it needs live in ./_lib.js, shared with the others.
 */
import { json, submitForm } from "./_lib.js";

const SPEC = {
  name: "support",
  fields: [
    { key: "name", label: "Name", max: 120, required: true },
    { key: "email", label: "Email", max: 200, required: true, email: true },
    { key: "build", label: "Build number", max: 60, required: false },
    { key: "issue", label: "Issue", max: 4000, required: true },
  ],
  replyTo: "email",
  source: "https://streetdog.life/support/",
  subject: (v) => `streetdog.life support — ${v.name}${v.build ? ` (build ${v.build})` : ""}`,
};

export const onRequestPost = ({ request, env }) => submitForm({ request, env, spec: SPEC });

// See the note in interest.js: method-specific, never a catch-all `onRequest`.
export const onRequestGet = () => json({ error: "POST only." }, 405);
