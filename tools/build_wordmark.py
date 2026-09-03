#!/usr/bin/env python3
"""
build_wordmark.py — cut "streetdog.life" into a kerb stone.

    tools/build_wordmark.py        ->  assets/wordmark.png, assets/wordmark@2x.png

WHY A STONE. The game carves its street names into the kerb — inlaid concrete plaques set in Optima,
lettered by the light rather than by a font weight. Making the site's masthead the same object ties
the two halves of streetdog.life together with the game's most characteristic detail, instead of
setting the name in a typeface and calling that an identity.

HOW A CUT LETTER ACTUALLY READS. Light falls from the upper left. A groove cut into a flat surface has
two visible interior walls: the one on the groove's upper-left side faces AWAY from the light and goes
dark; the one on its lower-right side faces INTO it and catches. Between them is the floor, which is
just stone with less light reaching it. So all three tones live INSIDE the glyph — nothing spills
outside it, which is what separates a cut letter from a letter with a drop shadow.

The usual shortcut is to draw the text three times at small offsets. That is what the game does and it
is fine at 34 px on a kerb seen from above, but at masthead size the offset copies read as three
overlapping letters. Here the walls are derived instead: rim = glyph MINUS glyph-shifted, so each band
is exactly the sliver of the stroke facing that way, and thin strokes never grow a halo.

Needs Pillow. ~/Sites has no .python-version, so plain `python3` here is the SYSTEM python, which has
no Pillow. Use a pyenv interpreter:

    ~/.pyenv/versions/3.12.7/bin/python3 tools/build_wordmark.py

The other two tools in this directory are stdlib-only on purpose and do not have that problem.
"""
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "wordmark.png")

TEXT = "streetdog.life"

# Optima — the same face the game cuts its street name-stones in. Flared stems and no hairlines; it was
# drawn from Renaissance stone inscription, which is exactly this job.
#
# ⚠ Note the FIRST path does not exist on macOS 15+ and PIL loads it anyway: when truetype() cannot open
# a path it falls back to searching the system font directories by BASENAME. That fallback is why the
# game's emit_intersections.py has rendered correctly for months from a path that is simply wrong. It is
# a coin-flip we should not take here, so the real location is listed and verified.
FONT_CANDIDATES = [
    "/System/Library/Fonts/Optima.ttc",
    "/System/Library/Fonts/Supplemental/Optima.ttc",
    "/Library/Fonts/Optima.ttc",
]

# Concrete. The game shades its kerb with _CurbColor (150,148,140); this is that value, so the stone on
# the website is the same stone as the one in the town.
STONE = (150, 148, 140)
FLOOR = (99, 97, 92)       # the groove floor — stone, just less lit
DARK = (52, 50, 47)        # the wall facing away from the light
LIT = (216, 213, 204)      # the wall facing into it

SCALE = 3                  # cut at 3x, ship 1x and 2x — a hairline wall must survive the downsample
SIZE = 64                  # cap-ish size at 1x
PAD_X, PAD_Y = 30, 19


def load_font(px):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, px), path
    raise SystemExit(
        "Optima not found. It is a macOS system font, so this generator only runs on a Mac.\n"
        "Tried:\n  " + "\n  ".join(FONT_CANDIDATES)
    )


def concrete(w, h, seed_scale):
    """A stone surface: fine aggregate grain plus slow blotching, both very quiet.

    Flat fill is the tell — real concrete is never one value, and an evenly coloured slab reads as a
    grey rectangle with letters on it no matter how good the engraving is."""
    grain = Image.effect_noise((w, h), 10).filter(ImageFilter.GaussianBlur(0.5 * seed_scale))

    # Blotches: noise generated small and scaled up, so the variation has a much longer wavelength than
    # the grain. One noise field at one frequency looks like television static.
    #
    # Kept FAINT and short — the first cut used a long wavelength at full amplitude and the slab read as
    # camouflage. Surface texture here is meant to be felt rather than seen; anything you can actually
    # make out competes with the letters, which are the only thing on this image with a job.
    small = Image.effect_noise((max(2, w // 14), max(2, h // 14)), 11)
    blotch = small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2 * seed_scale))

    mix = ImageChops.blend(grain, blotch, 0.5)
    base = Image.new("L", (w, h), 128)
    # effect_noise centres on 128, so blending against a flat 128 keeps the mean where STONE put it and
    # only the deviation survives.
    tex = ImageChops.blend(base, mix, 0.42)

    surf = Image.new("RGB", (w, h), STONE)
    return Image.merge("RGB", [
        ImageChops.add(ch, tex, scale=1, offset=-128) for ch in surf.split()
    ])


def rim(mask, dx, dy):
    """The sliver of a glyph facing direction (dx,dy): the mask minus itself shifted that way."""
    shifted = ImageChops.offset(mask, dx, dy)
    return ImageChops.subtract(mask, shifted)


def render(scale):
    font, path = load_font(SIZE * scale)
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    bb = probe.textbbox((0, 0), TEXT, font=font)
    px, py = PAD_X * scale, PAD_Y * scale
    w = (bb[2] - bb[0]) + px * 2
    h = (bb[3] - bb[1]) + py * 2

    stone = concrete(w, h, scale / 3)

    # The glyph mask, drawn once. Everything below is derived from it.
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((px - bb[0], py - bb[1]), TEXT, font=font, fill=255)

    o = max(1, round(1.7 * scale))
    # Just enough blur to take the stair-stepping off a diagonal wall. The first cut used 0.5*scale and
    # the walls smeared into each other, which turns a groove back into a soft emboss.
    soften = ImageFilter.GaussianBlur(0.28 * scale)
    dark = rim(mask, o, o).filter(soften)        # upper-left wall — away from the light
    lit = rim(mask, -o, -o).filter(soften)       # lower-right wall — into it

    # Crisp mask, NOT a blurred one: blurring the floor spreads it past the glyph edge and rings every
    # letter in a grey halo, which is the single clearest tell that the letters sit on top of the stone.
    stone.paste(FLOOR, (0, 0), mask)
    stone.paste(LIT, (0, 0), lit)
    stone.paste(DARK, (0, 0), dark)

    # Seat the slab: a lit top edge and a shadowed bottom one, so it sits ON the page rather than
    # floating in it. Two one-pixel-ish bands, nothing more.
    edge = ImageDraw.Draw(stone, "RGBA")
    t = max(1, scale // 2)
    edge.rectangle([0, 0, w, t], fill=LIT + (90,))
    edge.rectangle([0, h - t - 1, w, h], fill=DARK + (70,))

    # Rounded alpha. Barely rounded — a kerb stone is sawn, not moulded.
    alpha = Image.new("L", (w, h), 0)
    ImageDraw.Draw(alpha).rounded_rectangle([0, 0, w - 1, h - 1], radius=3 * scale, fill=255)
    out = stone.convert("RGBA")
    out.putalpha(alpha)
    return out, path


def main():
    big, path = render(SCALE)
    two = big.resize((round(big.width * 2 / SCALE), round(big.height * 2 / SCALE)), Image.LANCZOS)
    one = big.resize((big.width // SCALE, big.height // SCALE), Image.LANCZOS)

    two.save(OUT.replace(".png", "@2x.png"), optimize=True)
    one.save(OUT, optimize=True)

    print(f"  cut in {path}")
    for p in (OUT, OUT.replace(".png", "@2x.png")):
        im = Image.open(p)
        print(f"  wrote {os.path.relpath(p, ROOT):<24} {im.width}x{im.height}  "
              f"{os.path.getsize(p) / 1024:.0f} KB")
    print("  the font FILE never ships — only these rasters, same rule as the game's name-stones")


if __name__ == "__main__":
    main()
