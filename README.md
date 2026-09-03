# streetdog.life

Greg Warden's site. Short stories, a game, and whatever else earns a section.

**Sandy and ARC9** — the game — is *one section of this*, not the other way round. Its source lives in
a separate private repo; only its public page is here.

Static HTML, one stylesheet, no build step, no `package.json`. A handful of hand-written pages does
not need a toolchain, and a toolchain is the part that rots between the times anyone looks at it.

```
index.html              the front door — lists the sections that exist
sandy-and-arc9/         the game
assets/site.css         one stylesheet, shared by every page
assets/*.png            images
```

## ⚠ This repo is PUBLIC

Everything committed is visible immediately — **when it is committed, not when it is linked.** An
unpublished draft in the working tree is private; the moment it is committed it is not. Write drafts
on a branch, or keep them out of the repo until they are ready.

No secrets, ever. `.gitignore` blocks `.env*`, `.dev.vars*` and `.wrangler/`, but that is the backstop,
not the plan. A Cloudflare API token, if one is ever needed, goes in the macOS Keychain:

```sh
security add-generic-password -a "$USER" -s streetdog-cf-token -w      # prompts, hidden
export CLOUDFLARE_API_TOKEN=$(security find-generic-password -a "$USER" -s streetdog-cf-token -w)
```

## Deploying — Cloudflare Pages

Connect this repo through the **Cloudflare dashboard**, which uses a GitHub App and needs **no API
token**. A token is only required for `wrangler` CLI or GitHub Actions deploys.

| Setting | Value |
|---|---|
| Production branch | `main` |
| Build command | *(empty)* |
| Build output directory | `/` (repo root) |

Because this repo holds only the site, every push is meant to deploy — no build-watch-path filtering
needed, which was the reason the site left the game's repo.

### DNS — registrar stays GoDaddy, DNS moves to Cloudflare

Cloudflare must be **authoritative for DNS**; it does not need to be the registrar.

The dashboard calls this **"Onboard a domain"**, under **Domains**. It used to be "Add a site" and
that label is gone — if you go looking for it you will not find it.

1. Dashboard → **Domains** → **Onboard a domain**.
2. Enter the apex domain `streetdog.life`, choose how to add DNS records → **Continue**.
3. Choose a plan — **Free**.
4. **Review the scanned DNS records.** See the warning below; this is the step that matters.
5. Cloudflare gives you **two nameservers**. GoDaddy → domain → **Nameservers → Change → Custom** →
   enter both. Registration, renewal and billing stay at GoDaddy.
6. Wait for propagation — usually under an hour, occasionally 24–48.
7. Pages project → **Custom domains** → add `streetdog.life` and `www.streetdog.life`.

⚠ **Check what GoDaddy is serving before you switch.** Cloudflare's own docs say to verify the scan by
hand, specifically for apex records, subdomains, and **email: MX, TXT, SPF, DKIM, DMARC**. Any of those
that exist and do not get recreated in Cloudflare go down the moment the nameservers move. Keep
GoDaddy's DNS page open alongside and compare line by line — the scan is a scan, not a guarantee.

Each record has a **Proxied** (orange cloud) / **DNS only** (grey cloud) toggle. Proxied is right for
the site. **Any MX record must be DNS only** — mail cannot be proxied.

## Adding a section

1. New folder with an `index.html`.
2. Link `/assets/site.css`; the masthead and layout come free.
3. Add a row to the list in `index.html`.

**A section is listed on the front page only once it exists.** No greyed-out "coming soon" rows — that
is a promise, and the point of these pages is not to make any.

## The game's changelog

Planned but not written. When it happens: **hand-written, one entry per release, never generated from
commits.** The game repo's commit messages name licensed asset packs and their terms, internal file
paths, unreleased plans and debugging notes. A release is not a commit.

## The tester form

Also planned. It needs a Cloudflare Pages Function plus an email API (Resend or MailChannels), since a
static page cannot send mail, and Cloudflare Turnstile, because any public form collects bots within
days. It handles **personal data** — name, email, and why someone wants to help — so it needs a line
saying what that is used for and that it is not passed on, and that line has to agree with the game's
App Store privacy answers.
