/**
 * POST /api/support — the support form on /support/.
 *
 * Two jobs: reporting a problem with a build, and requesting removal of personal information (the
 * privacy note on /games/ points here for that).
 *
 * ⚠ THIS FORM COLLECTS NO EMAIL ADDRESS, which has a consequence worth knowing before relying on it:
 * a removal request arrives with a name and nothing to match against, and there is no way to reply
 * and confirm. If removal requests are meant to be actioned reliably, this form needs an email field
 * — see the note in /support/index.html. Left as specified for now, deliberately.
 *
 * Every defence and the environment variables it needs live in ./_lib.js, shared with /api/interest.
 */
import { json, submitForm } from "./_lib.js";

const SPEC = {
  name: "support",
  fields: [
    { key: "name", label: "Name", max: 120, required: true },
    { key: "build", label: "Build number", max: 60, required: false },
    { key: "issue", label: "Issue", max: 4000, required: true },
  ],
  source: "https://streetdog.life/support/",
  subject: (v) => `streetdog.life support — ${v.name}${v.build ? ` (build ${v.build})` : ""}`,
};

export const onRequestPost = ({ request, env }) => submitForm({ request, env, spec: SPEC });

// See the note in interest.js: method-specific, never a catch-all `onRequest`.
export const onRequestGet = () => json({ error: "POST only." }, 405);
