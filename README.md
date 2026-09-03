# streetdog.life

Greg Warden's site. Short stories, a game, and whatever else earns a section.

**Sandy and ARC9** — the game — is *one section of this*, not the other way round. Its source lives in
a separate private repo; only its public page is here.

Static HTML, one stylesheet, no build step, no `package.json`. A handful of hand-written pages does
not need a toolchain, and a toolchain is the part that rots between the times anyone looks at it.

```
index.html              the front door — Dan, the poem, the sections
stories/index.html      254 #vss365 stories        ← GENERATED, do not hand-edit
games/index.html        the game + the tester form
news/index.html         release notes and posts    ← GENERATED, do not hand-edit
news/posts/*.md         write posts here
data/stories.json       the Sandy & ARC9 archive
tools/build_stories.py  data/stories.json  -> stories/index.html
tools/build_news.py     news/posts/*.md    -> news/index.html
functions/api/interest.js   the tester form endpoint (Pages Function)
assets/site.css         one stylesheet, shared by every page
_redirects              /sandy-and-arc9/ -> /games/
```

**Two pages are generated and committed.** Edit the source, re-run the tool, commit the output:

```sh
tools/build_stories.py    # after changing data/stories.json
tools/build_news.py       # after adding a post to news/posts/
```

The site itself still has **no build step** — Cloudflare serves the committed HTML. Generating locally
and committing the artifact is the same trade the game makes with its offline emitters.

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

## The tester form — BUILT, but needs configuring before it works

`/games/#interest` posts to `functions/api/interest.js`, a Pages Function. Until the steps below are
done it **fails visibly** rather than silently accepting and discarding submissions — which is the
right way round, but it does mean the form is broken until you finish.

**1. Turnstile** (dashboard → Turnstile → Add widget, hostname `streetdog.life`). It gives a **site
key** and a **secret key**. Put the *site* key into `games/index.html`, replacing
`TURNSTILE_SITE_KEY` — it is public by design and belongs in the repo. The *secret* does not.

**2. Resend** (resend.com) — verify `streetdog.life` as a sending domain, which means adding the DKIM
and SPF records it gives you to Cloudflare DNS. Then create an API key.

**3. Pages environment variables** — Workers & Pages → streetdog-life → Settings → Variables and
Secrets. Mark the first two **encrypted**; once encrypted they cannot be read back out, which is the
point.

| Variable | Value |
|---|---|
| `TURNSTILE_SECRET` | the secret half of the Turnstile widget — **encrypt** |
| `RESEND_API_KEY` | from Resend — **encrypt** |
| `NOTIFY_TO` | `wardeng@gmail.com` |
| `NOTIFY_FROM` | a verified sender, e.g. `forms@streetdog.life` |

⚠ **MailChannels is not an option** — it ended free Workers sending in 2024. Resend's free tier is
ample for a form nobody has found yet.

**Personal data.** The form collects a name, an email and a reason. The page says outright what that
is used for, that it goes nowhere else, and that it will be deleted on request. That statement has to
stay true — and has to agree with the game's App Store privacy answers.
