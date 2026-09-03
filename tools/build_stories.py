#!/usr/bin/env python3
"""
build_stories.py — generate stories/index.html from data/stories.json.

Run by hand when the archive changes; the OUTPUT is committed. That keeps the deployed site static
with no build step at Cloudflare, which is the whole point of this repo — the same trade the game
makes when it solves things offline and commits the artifact.

    tools/build_stories.py

Source of truth is data/stories.json: the Sandy & ARC9 series harvested from the #vss365 archive,
already filtered to that series and sorted by date. 254 stories, 2021-06-06 to 2024-08-04.
"""
import json
import os
import re
from collections import OrderedDict
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "stories.json")
OUT = os.path.join(ROOT, "stories", "index.html")

MONTHS = ("January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")


def pretty_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def render_text(text):
    """Escape, then mark up the #prompt hashtags and keep the line breaks.

    The hashtag is not decoration: #vss365 gives you one word a day and the story has to contain it,
    so the tag IS the constraint the piece was written against. Highlighting it shows the shape of
    the form rather than hiding a stray character.
    """
    safe = escape(text).strip()
    safe = re.sub(r"(?<!\w)#(\w+)", r'<span class="tag">#\1</span>', safe)
    return "<br>".join(line.strip() for line in safe.split("\n") if line.strip())


def main():
    stories = json.load(open(DATA, encoding="utf-8"))
    by_year = OrderedDict()
    for s in stories:
        by_year.setdefault(s["date"][:4], []).append(s)

    years = list(by_year)
    nav = " ".join(f'<a href="#y{y}">{y}</a>' for y in years)

    parts = []
    for y in years:
        parts.append(f'\n<h2 id="y{y}">{y} <span class="count">{len(by_year[y])} stories</span></h2>\n')
        for s in by_year[y]:
            prompt = (f'<span class="tag">#{escape(s["prompt"])}</span>'
                      if s.get("prompt") else '<span class="noprompt">no prompt recorded</span>')
            parts.append(
                '<article class="vss">\n'
                f'  <header><time datetime="{s["date"]}">{pretty_date(s["date"])}</time> {prompt}</header>\n'
                f'  <p>{render_text(s["text"])}</p>\n'
                '</article>\n'
            )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Street Dog Stories — streetdog.life</title>
<meta name="description" content="Sandy the street dog and ARC9 his robot companion: {len(stories)} very short stories written to the #vss365 daily prompt, 2021–2024.">
<meta property="og:type" content="website">
<meta property="og:title" content="Street Dog Stories">
<meta property="og:description" content="Sandy and ARC9 — {len(stories)} very short stories written to a daily one-word prompt.">
<meta property="og:url" content="https://streetdog.life/stories/">
<link rel="icon" href="/assets/sandy-arc9-180.png">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
<div class="wrap wide">

  <div class="masthead"><a class="home" href="/">← streetdog.life</a></div>

  <h1>Street Dog Stories</h1>
  <p class="tagline">Sandy, and ARC9 his robot companion.</p>

  <p>
    In 2021 — pre-Elon, and before my subsequent departure from Twitter — I kept noticing tweets from
    one of my favourite musicians, <a href="https://jiminfantino.com/" rel="noopener">Jim Infantino</a>,
    tagged <span class="tag">#vss365</span>. I had no idea what it was about, but they were interesting
    little bits of fiction. After a few had crossed my feed I learned that #vss365 is a daily prompt,
    and that a whole community writes a story of 160 characters or fewer to it every day.
  </p>

  <p>
    Believing I had stories of my own trapped in my head, I started joining in. A few days later two
    recurring characters had emerged: <strong>Sandy</strong> the street dog, and <strong>ARC9</strong>,
    his robot companion.
  </p>

  <p>
    I am no longer on Twitter, so I have harvested the stories here. Each one was written to the day's
    one-word prompt, which appears in the story itself. Enjoy.
  </p>

  <p class="quiet">
    {len(stories)} stories · {pretty_date(stories[0]['date'])} – {pretty_date(stories[-1]['date'])}
  </p>

  <nav class="years">{nav}</nav>

  {''.join(parts)}

  <footer>
    <a href="/">streetdog.life</a> · <a href="/games/">Street Dog Games</a>
  </footer>

</div>
</body>
</html>
"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    noprompt = sum(1 for s in stories if not s.get("prompt"))
    print(f"wrote {os.path.relpath(OUT, ROOT)}  ({len(stories)} stories, {len(years)} years, "
          f"{len(html) // 1024} KB)")
    for y in years:
        print(f"    {y}  {len(by_year[y]):>3}")
    if noprompt:
        print(f"  {noprompt} story/stories have no prompt recorded — shown with the date alone")


if __name__ == "__main__":
    main()
