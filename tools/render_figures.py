#!/usr/bin/env python3
"""Render localised figures.

For every figures/layout/fig-NN.json with "localize": true, read
figures/fig-NN.<src>.txt and figures/fig-NN.<tgt>.txt (line N of each file
corresponds to item N in the layout) and write build/figures/fig-NN.png.
Languages and fonts come from technote.json.

Rules for a line in fig-NN.<tgt>.txt:
  * identical to the source line -> left untouched (code, numbers, names)
  * empty                        -> source text is erased, nothing drawn
                                    (use this to merge two source lines
                                    into one translated line)
  * anything else                -> source erased, translation drawn in place
Figures with "replace": "<file>" use that file from figures/ instead (e.g. a localised screenshot).
Figures with "localize": false (or without a .<tgt>.txt) are copied unchanged.

Rotated labels: an item with "angle" (degrees, counter-clockwise), "center" [x, y],
"length" and "thickness" (the inked text extent along and across the baseline, px) is
erased as a rotated rectangle and redrawn rotated; its "box" only samples the colours.
"rotate": 90 (reads bottom to top) or 270 (top to bottom) is a shorthand for a vertical
label that fills its "box" (no angle/center/length/thickness needed).
"""
import json
import math
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config

ROOT = config.ROOT
CFG = config.load()
SRC, TGT = CFG["source_lang"], CFG["target_lang"]
FIG = ROOT / "figures"
OUT = ROOT / "build" / "figures"
FONTS = config.figure_fonts(CFG)


def font(weight, size):
    path, index = FONTS[weight]
    return ImageFont.truetype(path, max(6, int(round(size))), index=index)


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a[:3], b[:3])) ** 0.5


def mode_color(pixels):
    counts = {}
    for p in pixels:
        key = tuple(c // 8 * 8 for c in p[:3])
        counts[key] = counts.get(key, 0) + 1
    key = max(counts, key=counts.get)
    sel = [tuple(p) for p in pixels if tuple(c // 8 * 8 for c in p[:3]) == key]
    # the commonest exact colour of the winning bucket, not its mean: averaging pure white
    # with anti-aliasing noise gives an off-white that shows as a visible patch
    return max(set(sel), key=sel.count)


def background(img, box, pad=4):
    x, y, w, h = box
    W, H = img.size
    px = img.load()
    ring = []
    for xx in range(max(0, x - pad), min(W, x + w + pad)):
        for yy in (max(0, y - pad), min(H - 1, y + h + pad)):
            ring.append(px[xx, yy])
    for yy in range(max(0, y - pad), min(H, y + h + pad)):
        for xx in (max(0, x - pad), min(W - 1, x + w + pad)):
            ring.append(px[xx, yy])
    return mode_color(ring)


def foreground(img, box, bg):
    x, y, w, h = box
    px = img.load()
    inside = [px[xx, yy] for xx in range(x, x + w) for yy in range(y, y + h)]
    far = sorted(inside, key=lambda p: dist(p, bg), reverse=True)
    core = far[: max(1, len(far) // 10)]
    ink = sum(1 for p in inside if dist(p, bg) > 60) / max(1, len(inside))
    return tuple(sum(p[i] for p in core) // len(core) for i in range(4)), ink


def free_span(img, box, bg, tol=40):
    """Horizontal extent around the text that has the same background colour."""
    x, y, w, h = box
    W, _ = img.size
    px = img.load()
    rows = [y + h // 4, y + h // 2, y + 3 * h // 4]

    def clear(xx):
        return all(dist(px[xx, r], bg) < tol for r in rows)

    left = x
    while left > 0 and clear(left - 1):
        left -= 1
    right = x + w
    while right < W - 1 and clear(right + 1):
        right += 1
    return left, right


def text_size(draw, text, f):
    l, t, r, b = draw.textbbox((0, 0), text, font=f, anchor="ls")
    return r - l, b - t


def estimate_size(draw, text, box):
    """Font size at which the English text fills its OCR box."""
    _, _, w, h = box
    ref = 100
    tw, _ = text_size(draw, text, font("regular", ref))
    _, ref_h = text_size(draw, "Hg", font("regular", ref))
    by_width = ref * w / max(1, tw)
    by_height = ref * h / ref_h
    return min(max(by_width, by_height * 0.75), by_height * 1.15)


def snap_sizes(sizes, tol=0.08, absorb=0.30):
    """Group near-equal size estimates so labels of the same rank match."""
    if not sizes:
        return []
    order = sorted(range(len(sizes)), key=lambda i: sizes[i])
    groups = [[order[0]]]
    for i in order[1:]:
        if sizes[i] <= sizes[groups[-1][-1]] * (1 + tol):
            groups[-1].append(i)
        else:
            groups.append([i])
    medians = [sorted(sizes[i] for i in g)[len(g) // 2] for g in groups]
    big = [m for g, m in zip(groups, medians) if len(g) > 1] or medians
    out = list(sizes)
    for g, m in zip(groups, medians):
        if len(g) == 1:
            near = min(big, key=lambda b: abs(b - m))
            m = near if abs(near - m) / m <= absorb else m
        for i in g:
            out[i] = m
    return out


def rotation(item):
    """{angle, center, length, thickness, fit} of a rotated label, or None."""
    if "angle" in item:
        return {"angle": item["angle"], "center": item["center"], "length": item["length"],
                "thickness": item["thickness"], "fit": item["length"] * 1.3}
    if item.get("rotate") in (90, 270):
        x, y, w, h = item["box"]
        return {"angle": item["rotate"], "center": (x + w / 2, y + h / 2), "length": h, "thickness": w,
                "fit": h - 4}
    return None


def rotated_rect(cx, cy, length, thick, angle):
    a = math.radians(-angle)  # image y points down
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    return [(cx + sx * length / 2 * ux + sy * thick / 2 * vx, cy + sx * length / 2 * uy + sy * thick / 2 * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def draw_rotated(img, text, f, fill, center, angle):
    l, t, r, b = f.getbbox(text)
    layer = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((2 - l, 2 - t), text, font=f, fill=fill)
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(layer, (int(round(center[0] - layer.width / 2)),
                                int(round(center[1] - layer.height / 2))))


def render(name, layout, en, ja):
    src_img = Image.open(FIG / layout["source"]).convert("RGBA")
    img = Image.new("RGBA", src_img.size, (255, 255, 255, 255))
    img.alpha_composite(src_img)
    draw = ImageDraw.Draw(img)
    jobs = []
    for item, src, dst in zip(layout["items"], en, ja):
        if dst == src:
            continue
        box = item["box"]
        bg = tuple(item["bg"]) if "bg" in item else background(img, box)
        fg, ink = foreground(img, box, bg)
        if "fg" in item:
            fg = tuple(item["fg"])
        rot = rotation(item)
        if rot and "angle" in item:  # fit the source text to its measured length instead of the box
            tw, _ = text_size(draw, src, font("regular", 100))
            size_en = 100 * rot["length"] / max(1, tw)
        elif rot:
            size_en = estimate_size(draw, src, [box[0], box[1], rot["length"], rot["thickness"]])
        else:
            size_en = estimate_size(draw, src, box)
        weight = item.get("weight", "regular")
        left, right = free_span(img, box, bg)
        jobs.append((item, src, dst, box, bg, fg, weight, left, right, size_en))
    snapped = snap_sizes([j[-1] for j in jobs])
    jobs = [j[:-1] + (sz,) for j, sz in zip(jobs, snapped)]
    for item, src, dst, box, bg, fg, weight, left, right, size_en in jobs:
        x, y, w, h = box
        p = item.get("erase_pad", 3)
        rot = rotation(item)
        if rot:
            draw.polygon(rotated_rect(*rot["center"], rot["length"] + 2 * p, rot["thickness"] + 2 * p,
                                      rot["angle"]), fill=bg)
            continue
        draw.rectangle([x - p, y - p, x + w + p, y + h + p], fill=bg)
    W = img.size[0]
    for item, src, dst, box, bg, fg, weight, left, right, size_en in jobs:
        if not dst:
            continue
        x, y, w, h = box
        size = (item.get("size") or size_en) * item.get("scale", 1.0)
        rot = rotation(item)
        if rot:
            f = font(weight, size)
            tw, _ = text_size(draw, dst, f)
            if tw > rot["fit"]:
                f = font(weight, size * rot["fit"] / tw)
            cx, cy = rot["center"]
            draw_rotated(img, dst, f, fg, (cx + item.get("dx", 0), cy + item.get("dy", 0)), rot["angle"])
            continue
        margin = max(6, h // 3)
        if item.get("align") == "left":
            avail = right - x - margin
        else:
            cx = x + w / 2
            avail = 2 * min(cx - left, right - cx) - 2 * margin
        avail = max(avail, w)
        f = font(weight, size)
        tw, _ = text_size(draw, dst, f)
        if tw > avail:
            size *= avail / tw
            f = font(weight, size)
            tw, _ = text_size(draw, dst, f)
        cy = y + h / 2 + item.get("dy", 0)
        tx = x if item.get("align") == "left" else x + w / 2 - tw / 2
        tx = max(4, min(tx + item.get("dx", 0), W - tw - 4))
        draw.text((tx, cy), dst, font=f, fill=fg, anchor="lm")
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / f"{name}.png")


def main():
    errors = 0
    print("figure fonts: " + ", ".join(f"{w}={Path(p).name}" for w, (p, _) in FONTS.items()))
    OUT.mkdir(parents=True, exist_ok=True)
    for lay_path in sorted((FIG / "layout").glob("fig-*.json")):
        name = lay_path.stem
        layout = json.loads(lay_path.read_text())
        ja_path = FIG / f"{name}.{TGT}.txt"
        if layout.get("replace"):
            shutil.copy(FIG / layout["replace"], OUT / f"{name}.png")
            print(f"{name}: replaced with {layout['replace']}")
            continue
        if not layout.get("localize", True) or not ja_path.exists():
            shutil.copy(FIG / layout["source"], OUT / f"{name}.png")
            print(f"{name}: copied unchanged")
            continue
        en = (FIG / f"{name}.{SRC}.txt").read_text(encoding="utf-8").splitlines()
        ja = ja_path.read_text(encoding="utf-8").splitlines()
        n = len(layout["items"])
        if len(en) != n or len(ja) != n:
            print(f"ERROR {name}: layout has {n} items, {SRC}.txt {len(en)} lines, "
                  f"{TGT}.txt {len(ja)} lines - they must match", file=sys.stderr)
            errors += 1
            continue
        render(name, layout, [s.strip() for s in en], [s.strip() for s in ja])
        print(f"{name}: localised")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
