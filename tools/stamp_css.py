#!/usr/bin/env python3
"""
stamp_css.py — put a content hash on the stylesheet link in every page.

    tools/stamp_css.py

WHY THIS EXISTS. Cloudflare Pages serves /assets/* with `Cache-Control: max-age=14400` — four hours —
while HTML revalidates on every request. So a deploy that renames a CSS class ships new HTML to
browsers still holding the OLD stylesheet, the element lands on a class nothing styles, and it
renders as an empty div. That is not hypothetical: renaming `.hero` to `.portrait` made the
photograph in the masthead vanish for anyone who had loaded the site earlier that day, while a fresh
browser rendered it perfectly — which is the worst kind of bug, because it looks fine to whoever
deployed it, and headless screenshots start with an empty cache every time.

⚠ AND `_headers` CANNOT FIX IT. That was tried and MEASURED. Pages does read the file — a probe header
added alongside the Cache-Control rule came back on the response — but Pages **overrides
Cache-Control on static assets regardless**:

    x-sdl-headers-applied: yes                              ← our header, applied
    cache-control: public, max-age=14400, must-revalidate   ← ours ignored

So the only lever left is the URL. `site.css?v=<hash of site.css>` changes exactly when the file
changes, which makes the stylesheet uncacheable across a real edit and fully cacheable otherwise.

RUN THIS AFTER ANY CSS CHANGE, and after build_stories/build_news, since those regenerate their pages
with a bare link. It is idempotent — running it twice is a no-op — so when in doubt, run it.
"""
import hashlib
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSS = os.path.join(ROOT, "assets", "site.css")

# href="/assets/site.css" with or without an existing ?v=... — so re-stamping replaces, never appends.
LINK = re.compile(r'href="/assets/site\.css(?:\?v=[0-9a-f]+)?"')


def main():
    digest = hashlib.sha256(open(CSS, "rb").read()).hexdigest()[:8]
    want = f'href="/assets/site.css?v={digest}"'

    pages = sorted(glob.glob(os.path.join(ROOT, "*.html"))
                   + glob.glob(os.path.join(ROOT, "*", "index.html")))
    changed, already, missing = [], [], []

    for p in pages:
        src = open(p, encoding="utf-8").read()
        if not LINK.search(src):
            missing.append(os.path.relpath(p, ROOT))
            continue
        out = LINK.sub(want, src)
        if out == src:
            already.append(os.path.relpath(p, ROOT))
        else:
            open(p, "w", encoding="utf-8").write(out)
            changed.append(os.path.relpath(p, ROOT))

    print(f"site.css -> v={digest}")
    for p in changed: print(f"  stamped   {p}")
    for p in already: print(f"  unchanged {p}")
    # A page with no stylesheet link at all is almost certainly a mistake, so say so rather than
    # skipping it quietly.
    for p in missing: print(f"  ⚠ NO STYLESHEET LINK: {p}")


if __name__ == "__main__":
    main()
