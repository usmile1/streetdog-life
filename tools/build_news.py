#!/usr/bin/env python3
"""
build_news.py — generate news/index.html from the posts in news/posts/*.md.

Run by hand; the OUTPUT is committed. Same trade as the stories page: the deployed site stays static
with no build step at Cloudflare.

    tools/build_news.py

ONE SECTION, NOT TWO. Release notes and short essays are the same shape — a dated post — so they live
together rather than in a "changelog" and a "blog" that would each hold two entries. Split later if one
of them ever gets long enough to deserve its own page.

⚠ POSTS ARE WRITTEN BY HAND, NEVER GENERATED FROM COMMITS. The game's repo names licensed asset packs
and their terms, internal file paths, unreleased plans and debugging notes. A release is not a commit.

POST FORMAT — front matter, then a deliberately small subset of markdown:

    title: Build 2 is on TestFlight
    date: 2026-09-03
    ---
    Paragraphs separated by blank lines.

    ## A heading

    **bold**, *italic*, [links](https://example.com), and - bullet lists.

The subset is small on purpose. A full markdown library would be a dependency that rots between the
times anyone looks at this, and none of these posts need more than this.
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POSTS = os.path.join(ROOT, "news", "posts")
OUT = os.path.join(ROOT, "news", "index.html")

MONTHS = ("January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")


def pretty_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def inline(s):
    """Escape first, then the inline subset. Order matters: escaping after would eat the tags."""
    s = html.escape(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def body_to_html(body):
    out, bullets = [], []

    def flush():
        if bullets:
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for block in re.split(r"\n\s*\n", body.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            flush()
            out.append(f"<h3>{inline(block[3:].strip())}</h3>")
        elif all(line.strip().startswith("- ") for line in block.splitlines()):
            for line in block.splitlines():
                bullets.append(line.strip()[2:])
            flush()
        else:
            flush()
            out.append("<p>" + inline(block).replace("\n", " ") + "</p>")
    flush()
    return "\n  ".join(out)


def read_post(path):
    raw = open(path, encoding="utf-8").read()
    if "---" not in raw:
        raise SystemExit(f"{path}: missing the '---' separating front matter from the body")
    head, body = raw.split("---", 1)
    meta = {}
    for line in head.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    for required in ("title", "date"):
        if required not in meta:
            raise SystemExit(f"{path}: front matter needs a '{required}:' line")
    return meta, body


def main():
    os.makedirs(POSTS, exist_ok=True)
    files = sorted(f for f in os.listdir(POSTS) if f.endswith(".md"))
    posts = []
    for f in files:
        meta, body = read_post(os.path.join(POSTS, f))
        posts.append((meta["date"], meta["title"], body_to_html(body), f))
    posts.sort(reverse=True)   # newest first

    if not posts:
        articles = '<p class="quiet">Nothing yet.</p>'
    else:
        articles = "\n".join(
            f'<article class="post">\n'
            f'  <header><time datetime="{d}">{pretty_date(d)}</time></header>\n'
            f'  <h2>{html.escape(t)}</h2>\n'
            f'  {b}\n'
            f'</article>' for d, t, b, _ in posts)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>News — streetdog.life</title>
<meta name="description" content="Updates on Sandy and ARC9, and whatever else is happening at streetdog.life.">
<meta property="og:type" content="website">
<meta property="og:title" content="News — streetdog.life">
<meta property="og:url" content="https://streetdog.life/news/">
<link rel="icon" href="/assets/sandy-arc9-180.png">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
<div class="wrap">

  <div class="masthead"><a class="home" href="/">← streetdog.life</a></div>

  <h1>News</h1>
  <p class="tagline">What has changed, and what I have been thinking about.</p>

  {articles}

  <footer>
    <a href="/">streetdog.life</a>
    <a href="/stories/">Stories</a>
    <a href="/games/">Games</a>
    <a href="/news/">News</a>
    <a href="/contact/">Contact</a>
    <a href="/support/">Support</a>
  </footer>

</div>
</body>
</html>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {os.path.relpath(OUT, ROOT)}  ({len(posts)} post(s))")
    for d, t, _, f in posts:
        print(f"    {d}  {t}")


if __name__ == "__main__":
    main()
