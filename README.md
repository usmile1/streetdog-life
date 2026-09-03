# streetdog.life

Greg Warden's site. Short stories, a game, and whatever else earns a section.

**Sandy and ARC9** — the game — is *one section of this*, not the other way round. Its source lives in
a separate private repo; only its public page is here.

Static HTML, one stylesheet, no build step, no `package.json`. A handful of hand-written pages does
not need a toolchain, and a toolchain is the part that rots between the times anyone looks at it.

```
index.html              the front door — Dan, the wordmark, two doors
stories/index.html      254 #vss365 stories        ← GENERATED, do not hand-edit
games/index.html        the game, the offer-of-help form, the CREDITS
support/index.html      report a build problem / ask for your info to be removed
news/index.html         release notes and posts    ← GENERATED, do not hand-edit
news/posts/*.md         write posts here
data/stories.json       the Sandy & ARC9 archive   ← GENERATED from the vss365 archive
tools/import_stories.py  ~/vss365-archive   -> data/stories.json
tools/build_stories.py   data/stories.json  -> stories/index.html
tools/build_news.py      news/posts/*.md    -> news/index.html
tools/build_wordmark.py  Optima             -> assets/wordmark.png (the kerb stone)
tools/stamp_css.py       hashes site.css into every page's <link>  ← RUN LAST
functions/api/_lib.js       shared form handling — honeypot, timing, Turnstile, Resend
functions/api/interest.js   the offer-of-help form endpoint  (Pages Function)
functions/api/support.js    the support form endpoint        (Pages Function)
assets/site.css         one stylesheet, shared by every page
_redirects              /sandy-and-arc9/ -> /games/
```

**Everything generated is committed.** Edit the source, re-run the tool, commit the output:

```sh
tools/import_stories.py   # after the vss365 archive changes  (then build_stories)
tools/build_stories.py    # after changing data/stories.json
tools/build_news.py       # after adding a post to news/posts/
tools/build_wordmark.py   # only if the wordmark itself changes — needs Pillow, see the file
tools/stamp_css.py        # ALWAYS LAST — after any CSS edit, and after the two generators
```

## ⚠ The stylesheet must be cache-busted, and `_headers` cannot do it

Pages serves `/assets/*` with `Cache-Control: max-age=14400` (four hours) while HTML revalidates every
request. So a deploy that **renames a CSS class** hands new HTML to browsers still holding the old
stylesheet: the element gets a class nothing styles and renders as an empty div. This already
happened — renaming `.hero` to `.portrait` made the masthead photo vanish for anyone who had visited
earlier that day, while a fresh browser looked perfect. It is invisible to whoever deploys it.

**`_headers` does not fix this, and it was measured, not assumed.** Pages *does* read the file — a
probe header added next to the rule came back on the response — but it overrides `Cache-Control` on
static assets anyway:

```
x-sdl-headers-applied: yes                              ← our header, applied
cache-control: public, max-age=14400, must-revalidate   ← our Cache-Control, ignored
```

So the URL is the only lever. `tools/stamp_css.py` writes a hash of `site.css` into every page's
`<link>`, which changes exactly when the file does. **Run it last, always.** It is idempotent.

⚠ `build_wordmark.py` needs Pillow, and `~/Sites` has no `.python-version`, so plain `python3` here is
the system one and has none. Run it with a pyenv interpreter. The other three are stdlib-only.

**The stories carry the archive's *untagged* text.** The prompt is the headword in the margin of each
entry, so the story itself does not repeat it as `#word` — `import_stories.py` explains why that is a
curated field rather than a regex.

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

## Credits are a licence term, not a courtesy

The credits block on `/games/` exists because two of its entries are **obligations**:

| | requires |
|---|---|
| **LimeZu — Modern Exteriors** | a credit **with a working link**. The game may not be distributed without it. |
| **OpenStreetMap** | the street layout is OSM data under **ODbL 1.0** — "© OpenStreetMap contributors" plus a link to the licence. |
| Synty — Simple Dogs | no credit required; the terms care that the work is never passed off as ours. Credited anyway. |
| USGS | public domain. Credited anyway. |
| Epidemic Sound | credit expected. |

Do not trim that block or let the links stop being links. The game screenshot is fine to publish here —
a screenshot is a derivative work showing the game, which is what both art licences are for — but the
**source art must never be committed to any repo**, public or private.

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

## The two forms — BUILT, but need configuring before they work

- `/games/#interest` → `functions/api/interest.js` — offers of help
- `/support/` → `functions/api/support.js` — build problems, and information-removal requests

Both share `functions/api/_lib.js`, which holds every defence (honeypot, timing floor, Turnstile,
validation, sending) so the two cannot drift apart. **The leading underscore matters** — Pages does
not route files starting with `_`, so it stays a module rather than becoming a public URL.

One Turnstile widget and one set of environment variables covers both. Until the steps below are done
they **fail visibly** rather than silently accepting and discarding submissions — which is the right
way round, but it does mean both forms are broken until you finish.

⚠ **The support form collects no email address**, as specified. A removal request therefore arrives
with a name and nothing to match it against, and there is no way to reply and confirm it was done. If
those requests need to be actioned reliably, add an email field to `support/index.html` and to the
`SPEC` in `functions/api/support.js`.

**1. Turnstile** (dashboard → Turnstile → Add widget, hostname `streetdog.life`). It gives a **site
key** and a **secret key**. Put the *site* key into **both** `games/index.html` and
`support/index.html`, replacing `TURNSTILE_SITE_KEY` — it is public by design and belongs in the
repo. The *secret* does not.

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
