#!/usr/bin/env python3
"""Draws the Switch build's fallback icon: app/switch/icon.jpg (256x256 JPEG, as elf2nro wants), used when the disc
has no dashboard art for tools/disc_icon.py.

    python3 tools/make_icon.py [out.jpg]

Original artwork, drawn here from shapes: no Monster High logo, character or official art (those are Mattel's). The
committed icon.jpg is what the build uses; this script only remakes it (needs Pillow and the Noto fonts).
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, 'app', 'switch', 'icon.jpg')
S = 1024  # drawn at 4x, scaled down at the end
FONT_TITLE = '/usr/share/fonts/noto/NotoSerifDisplay-Black.ttf'
FONT_SMALL = '/usr/share/fonts/noto/NotoSans-Black.ttf'

PINK = (255, 62, 165)
TEAL = (64, 224, 208)
MOON = (246, 232, 255)
INK = (16, 6, 26)

# Night sky: deep purple to black, lighter behind the moon.
img = Image.new('RGB', (S, S), INK)
px = img.load()
cx, cy = S * 0.5, S * 0.36
for y in range(S):
    for x in range(S):
        d = math.hypot(x - cx, y - cy) / S
        t = max(0.0, 1.0 - d * 1.6)
        px[x, y] = (int(22 + 70 * t), int(8 + 18 * t), int(38 + 96 * t))
draw = ImageDraw.Draw(img)

# Stars.
for i in range(46):
    x = (i * 7919) % S
    y = (i * 104729) % int(S * 0.62)
    r = 2 + (i % 3) * 2
    draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 235, 255))

# Moon glow, then a crescent moon (a full disc with a disc of the sky cut out of it).
glow = Image.new('L', (S, S), 0)
ImageDraw.Draw(glow).ellipse((cx - 300, cy - 300, cx + 300, cy + 300), fill=120)
glow = glow.filter(ImageFilter.GaussianBlur(70))
img.paste(Image.new('RGB', (S, S), (200, 120, 255)), (0, 0), glow)
draw = ImageDraw.Draw(img)
R = 230
moon = Image.new('L', (S, S), 0)
md = ImageDraw.Draw(moon)
md.ellipse((cx - R, cy - R, cx + R, cy + R), fill=255)
md.ellipse((cx - R + 120, cy - R - 60, cx + R + 120, cy + R - 60), fill=0)
img.paste(Image.new('RGB', (S, S), MOON), (0, 0), moon)
draw = ImageDraw.Draw(img)


def bat(cx, cy, w, color):
    """A bat in flight: body plus two scalloped wings."""
    h = w * 0.42
    wing = [(cx, cy - h * 0.15),
            (cx + w * 0.18, cy - h * 0.55), (cx + w * 0.5, cy - h * 0.75),
            (cx + w * 0.42, cy - h * 0.1), (cx + w * 0.34, cy + h * 0.05),
            (cx + w * 0.26, cy - h * 0.05), (cx + w * 0.17, cy + h * 0.15),
            (cx + w * 0.08, cy + h * 0.02), (cx, cy + h * 0.35)]
    mirror = [(2 * cx - x, y) for x, y in reversed(wing)]
    draw.polygon(wing + mirror, fill=color)
    draw.ellipse((cx - w * 0.06, cy - h * 0.45, cx + w * 0.06, cy + h * 0.2), fill=color)
    draw.polygon([(cx - w * 0.055, cy - h * 0.35), (cx - w * 0.03, cy - h * 0.6), (cx - w * 0.005, cy - h * 0.38)],
                 fill=color)
    draw.polygon([(cx + w * 0.055, cy - h * 0.35), (cx + w * 0.03, cy - h * 0.6), (cx + w * 0.005, cy - h * 0.38)],
                 fill=color)


bat(S * 0.30, S * 0.42, 300, INK)
bat(S * 0.80, S * 0.20, 170, INK)

# A stitched heart, pink with teal stitches, low on the moon.
hx, hy, hr = S * 0.64, S * 0.47, 78
heart = [(hx + hr * 16 * math.sin(t) ** 3 / 16 * 1.25,
          hy - hr * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16 * 1.25)
         for t in [i * 2 * math.pi / 120 for i in range(120)]]
draw.polygon(heart, fill=PINK, outline=INK, width=8)
draw.line((hx - 14, hy - 70, hx + 10, hy + 80), fill=TEAL, width=10)
for k in range(-2, 3):
    yy = hy + k * 28
    xx = hx - 2 + k * 4.8
    draw.line((xx - 26, yy - 6, xx + 26, yy + 6), fill=TEAL, width=9)

# Title band.
band_top = int(S * 0.66)
draw.rectangle((0, band_top, S, S), fill=INK)
draw.rectangle((0, band_top, S, band_top + 12), fill=PINK)
for x in range(0, S, 64):  # stitches along the band
    draw.line((x + 14, band_top + 30, x + 46, band_top + 30), fill=TEAL, width=8)


def centered(text, font, y, color, stroke=0, stroke_color=None):
    w = draw.textlength(text, font=font)
    draw.text(((S - w) / 2, y), text, font=font, fill=color, stroke_width=stroke, stroke_fill=stroke_color)


centered('NEW GHOUL', ImageFont.truetype(FONT_TITLE, 136), band_top + 42, PINK, 6, (90, 0, 60))
centered('IN SCHOOL', ImageFont.truetype(FONT_TITLE, 104), band_top + 190, (255, 255, 255), 5, (60, 20, 90))

os.makedirs(os.path.dirname(out), exist_ok=True)
img.resize((256, 256), Image.LANCZOS).save(out, 'JPEG', quality=95)
print(out)
