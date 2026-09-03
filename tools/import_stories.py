#!/usr/bin/env python3
"""
import_stories.py — pull the Sandy & ARC9 series out of the vss365 archive into data/stories.json.

    tools/import_stories.py [path/to/archive/stories.json]

The archive lives OUTSIDE this repo (~/vss365-archive by default) because it holds all 348 stories
across every series, and only the 254 Sandy & ARC9 ones belong on the site. Run this when the archive
changes; commit the result. build_stories.py then turns data/stories.json into the page.

WHICH TEXT FIELD, AND WHY IT MATTERS. Each archive record carries three versions:

    text            what was actually posted   — "the mad dash to the #vanity?"
    text_tagged     the same, markdown breaks  — "the mad dash to the #vanity?"
    text_untagged   the prompt word un-hashed  — "the mad dash to the vanity?"

We take **text_untagged**. On the site the prompt is the HEADWORD of the entry, so repeating it as a
hashtag inside the prose says the same thing twice and leaves a "#" mid-sentence that only makes sense
if you know the form. Twitter needed the hashtag; a page with the prompt in the margin does not.

For 15 records across the archive the untagged version is more than the hashtag minus its "#" — the
line was reworded so it reads as prose. That is exactly why this is a curated field in the archive and
not something to strip with a regex here.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "stories.json")
DEFAULT_SRC = os.path.expanduser("~/vss365-archive/clean/stories.json")

SERIES = "arc9-and-sandy"


def clean(text):
    """Drop markdown hard-breaks ('  \\n'), keep the line breaks themselves — they are the form."""
    return "\n".join(line.rstrip() for line in text.strip().split("\n"))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    if not os.path.exists(src):
        raise SystemExit(
            f"archive not found: {src}\n"
            "It is not part of this repo. Pass its path as an argument."
        )

    all_rows = json.load(open(src, encoding="utf-8"))
    rows = [r for r in all_rows if r.get("series") == SERIES]
    rows.sort(key=lambda r: (r["date"], r.get("prompt") or ""))

    out = [{
        "id": r["id"],
        "date": r["date"],
        "prompt": r.get("prompt") or "",
        "tags": r.get("tags") or [],
        "text": clean(r["text_untagged"]),
    } for r in rows]

    # Loud, not silent: a '#' surviving into the clean text means the archive's untagged field did not
    # do its job for that record, and the page would show a stray hashtag next to its own headword.
    strays = [r["id"] for r in out if "#" in r["text"]]
    if strays:
        print(f"⚠ {len(strays)} record(s) still contain a '#': {', '.join(strays[:5])}")
    missing = [r["id"] for r in out if not r["prompt"]]
    if missing:
        print(f"⚠ {len(missing)} record(s) have no prompt: {', '.join(missing[:5])}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print(f"wrote {os.path.relpath(OUT, ROOT)}  "
          f"({len(out)} of {len(all_rows)} archive rows, series={SERIES!r})")
    print(f"  {out[0]['date']} – {out[-1]['date']}")


if __name__ == "__main__":
    main()
