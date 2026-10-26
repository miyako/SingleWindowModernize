#!/usr/bin/env python3
"""Disassemble the source PDF into editable parts.

Outputs (never overwrites existing files unless --force):
  src/<src>.md                source body text as Markdown
  figures/fig-NN.png          original figure images
  figures/fig-NN.<src>.txt    OCR'd figure text, one element per line
  figures/layout/fig-NN.json  bounding box of each figure text line

All document-specific thresholds come from technote.json (see tools/config.py
and `make inspect`).
"""
import argparse
import io
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps

import config

ROOT = config.ROOT
CFG = config.load()
CODE_COLORS = {int(c.lstrip("#"), 16) for c in CFG["code"]["colors"]}
CODE_FONTS = CFG["code"]["fonts"]
MARKERS = set(CFG["bullets"]["fonts"])
STRIP_FONTS = set(CFG["bullets"]["strip_fonts"])
GLYPHS = set(CFG["bullets"]["glyphs"])
HEADING_LEVEL_BY_X = {int(k): v for k, v in CFG["heading"]["levels_by_x"].items()}
SRC = CFG["source_lang"]


def write(path: Path, text: str, force: bool):
    if path.exists() and not force:
        print(f"skip (exists): {path.relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote: {path.relative_to(ROOT)}")


def esc(text):
    """Escape what Markdown would read as markup in body text (<tag, *)."""
    return re.sub(r"<(?=[A-Za-z/!])", "&lt;", text).replace("*", r"\*")


def md_table(header, rows):
    cell = lambda t: esc(t).replace("|", r"\|")
    md = ["| " + " | ".join(map(cell, header)) + " |", "|" + "---|" * len(header)]
    md += ["| " + " | ".join(map(cell, r)) + " |" for r in rows]
    return "\n".join(md) + "\n"


def merge_row(dst, src):
    for i, t in enumerate(src):
        if t:
            dst[i] = join_lines([dst[i], t]) if dst[i] else t


def cell_text(page, rect):
    """(text, all_bold, x) of a ruled table cell. A wrapped token such as a regex or a path
    (no spaces, contains ^$|\\/) is joined without a space."""
    lines, bold, x = [], True, None
    for b in page.get_text("dict", clip=rect)["blocks"]:
        for l in b.get("lines", []):
            spans = [s for s in l["spans"] if s["text"].strip()]
            if not spans:
                continue
            bold = bold and all("Bold" in font_of(s) for s in spans)
            x = l["bbox"][0] if x is None else min(x, l["bbox"][0])
            lines.append("".join(s["text"] for s in l["spans"]).strip())
    if len(lines) > 1 and all(" " not in l for l in lines) and re.search(r"[\^$|\\/]", "".join(lines)):
        return "".join(lines), bold, x
    return join_lines(lines), bool(lines) and bold, x


def table_rows(page, table):
    """[[cells], is_bold] per row of a ruled table. The columns are the text x positions of the
    first row; every other cell goes to the nearest one (grids often have padding columns)."""
    rows = [[c for c in (cell_text(page, pymupdf.Rect(c)) for c in r.cells if c) if c[0]] for r in table.rows]
    rows = [r for r in rows if r]
    if not rows:
        return []
    cols = sorted(c[2] for c in rows[0])
    out = []
    for cells in rows:
        texts = [""] * len(cols)
        for t, _, x in cells:
            i = min(range(len(cols)), key=lambda k: abs(cols[k] - x))
            texts[i] = join_lines([texts[i], t]) if texts[i] else t
        out.append([texts, all(b for _, b, _ in cells)])
    return out


def line_items(page):
    items, tables = [], []
    if CFG["table"]["ruled"]:
        for t in page.find_tables().tables:
            rect = pymupdf.Rect(t.bbox)
            tables.append(rect)
            items.append({"kind": "table", "y0": rect.y0, "y1": rect.y1, "x": round(rect.x0),
                          "rows": table_rows(page, t)})
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            spans = list(l["spans"])
            x0, y0, x1, y1 = l["bbox"]
            if y0 > CFG["footer_y"] or y0 < CFG["header_y"]:  # running header/footer
                continue
            if any(pymupdf.Point((x0 + x1) / 2, (y0 + y1) / 2) in r for r in tables):
                continue
            items.append({"kind": "line", "x": round(x0), "y0": y0, "y1": y1, "x1": x1,
                          "spans": spans, "text": "".join(s["text"] for s in spans)})
    for info in page.get_image_info(xrefs=True):
        x0, y0, x1, y1 = info["bbox"]
        if x1 - x0 < CFG["figure"]["min_width_pt"]:  # inline icon, not a figure
            continue
        items.append({"kind": "image", "y0": y0, "y1": y1, "xref": info["xref"],
                      "width_pt": x1 - x0, "bbox": (x0, y0, x1, y1)})
    for vf in CFG["vector_figures"]:  # vector diagram: rasterise the clip as one figure
        if vf["page"] != page.number + 1:
            continue
        clip = pymupdf.Rect(vf["clip"])
        items = [it for it in items if not clip.contains(
            pymupdf.Rect(it.get("bbox") or (it["x"], it["y0"], it.get("x1", it["x"]), it["y1"])))]
        items.append({"kind": "image", "y0": clip.y0, "y1": clip.y1, "clip": tuple(clip),
                      "dpi": vf.get("dpi", 300), "width_pt": clip.width})
    items.sort(key=lambda it: (it["y0"], it.get("x", 0)))
    # lines of one row (e.g. a bullet glyph and its text) can differ slightly in y0: order them by x
    rows = []
    for it in items:
        if rows and it["kind"] == "line" and rows[-1][0]["kind"] == "line" and it["y0"] - rows[-1][0]["y0"] < 2:
            rows[-1].append(it)
        else:
            rows.append([it])
    return [it for row in rows for it in sorted(row, key=lambda it: it.get("x", 0))]


def font_of(span):
    return span["font"].split("+")[-1]


def is_code_font(span):
    return any(f in font_of(span) for f in CODE_FONTS)


def is_code_line(item, body_x, in_code=False):
    """Code-styled spans mark code: all of them (even at the body x), or some of them on an
    indented line. Indentation alone only continues a code block, unless code.indent_starts."""
    styled = [s["color"] in CODE_COLORS or is_code_font(s) for s in item["spans"] if s["text"].strip()]
    if styled and all(styled):
        return True
    if any(styled) and item["x"] != body_x:
        return True
    indent = CFG["code"]["indent"]
    return (in_code or CFG["code"]["indent_starts"]) and indent is not None and item["x"] >= body_x + indent


def is_italic(item):
    # font names can be truncated ("HelveticaNeue-MediumItal"): also trust the span's italic flag
    spans = [s for s in item["spans"] if s["text"].strip()]
    return bool(spans) and all("Ital" in font_of(s) or "Oblique" in font_of(s) or s["flags"] & 2 for s in spans)


def is_heading(fonts, size):
    h = CFG["heading"]
    return size >= h["min_size"] and any(any(f in font for f in h["fonts"]) for font in fonts)


def is_caption(item):
    """caption.italic: italic lines or lines matching caption.pattern; otherwise lines matching the
    pattern (or any line when there is no pattern). Always right of min_x and at most max_size.
    With quote.italic, italic alone is not enough: the pattern or max_size must tell captions apart."""
    spans = [s for s in item["spans"] if s["text"].strip()]
    cap = CFG["caption"]
    if not spans or item["x"] <= cap["min_x"] or (cap["max_size"] and max(s["size"] for s in spans) > cap["max_size"]):
        return False
    match = bool(cap["pattern"]) and bool(re.search(cap["pattern"], item["text"].strip()))
    if cap["italic"]:
        return match or (is_italic(item) and (not CFG["quote"]["italic"] or bool(cap["max_size"])))
    return match or not cap["pattern"]


def inline_md(spans):
    out = []
    for s in spans:
        t = esc(s["text"])
        if t.strip() and s["color"] not in CODE_COLORS and "Bold" in font_of(s):
            lead = t[: len(t) - len(t.lstrip())]
            trail = t[len(t.rstrip()):]
            t = f"{lead}**{t.strip()}**{trail}"
        out.append(t)
    return re.sub(r"\*\*(\s+)\*\*", r"\1", "".join(out))  # **a** **b** -> **a b**


def join_lines(lines):
    text = ""
    for l in lines:
        l = l.strip()
        if not text:
            text = l
        elif text.endswith("-") and not text.endswith(" -"):
            text += l
        else:
            text += " " + l
    return re.sub(r"\s{2,}", " ", text).strip()


def code_lang(lines):
    """Best guess; the agent should review fences after extraction.
    ```text marks sample values (numbers, output) that may be localised."""
    src = "\n".join(lines)
    if re.match(r"\s*[\[{]", src) and re.search(r'"\s*:', src) and not re.search(r":=", src):
        return "json"
    if re.search(r"^\s*<(!doctype|html|div|script)", src, re.M | re.I):
        return "html"
    if re.search(r"^\s*(var|let|const|function) |=>|\bdocument\.|\bwindow\.", src, re.M) and ":=" not in src:
        return "js"
    if re.fullmatch(r"[\s\d\.\-+\[\],°'\"NSEW:/=×θ]+", src):
        return "text"
    return "4d"


def code_line_text(item, min_x):
    raw = "".join(s["text"] for s in item["spans"]).rstrip()
    stripped = raw.lstrip(" ")
    spaces = len(raw) - len(stripped)
    if spaces:  # the PDF kept the indentation as spaces: keep it as is
        return raw
    return ("    " if item["x"] > min_x + 10 else "") + stripped


def extract_body(doc):
    out = []
    cover = CFG["cover"]
    p1 = [it for it in line_items(doc[cover["page"] - 1]) if it["kind"] == "line" and it["text"].strip()]
    p1 = p1[:cover["lines"]]

    def style(it):
        s = next(s for s in it["spans"] if s["text"].strip())
        return font_of(s), round(s["size"], 1)

    n = 1  # a title that wraps onto several lines in the same style is one title
    while n < len(p1) and style(p1[n]) == style(p1[0]):
        n += 1
    title = join_lines(it["text"] for it in p1[:n])
    rest = [it["text"].strip() for it in p1[n:]]
    out.append(f"# {title}\n\n" + "".join(f"{r}\n\n" for r in rest).rstrip("\n") + "\n")

    figures = []
    state = {"para": [], "code": [], "bullets": [], "in_bullet": False, "table": [], "quote": [], "ruled": None}
    body_x = 72
    prev = None

    def flush_para():
        if state["para"]:
            out.append(join_lines(state["para"]) + "\n")
            state["para"] = []

    def flush_bullets():
        if state["bullets"]:
            out.append("\n".join(f"- {join_lines(b)}" for b in state["bullets"]) + "\n")
            state["bullets"] = []
        state["in_bullet"] = False

    def flush_code():
        items = state["code"]
        if items:
            min_x = min(it["x"] for it in items if it["text"].strip())
            lines = [code_line_text(it, min_x) if it["text"].strip() else "" for it in items]
            while lines and not lines[-1]:
                lines.pop()
            out.append(f"```{code_lang(lines)}\n" + "\n".join(lines) + "\n```\n")
            state["code"] = []

    def flush_table():
        """Cells go to the column of the nearest first-row cell; a row with an empty first cell
        continues the previous row (wrapped text); a repeated header (page break) is dropped."""
        if state["table"]:
            first = sorted(state["table"][0][1], key=lambda c: c["x"])
            cols, header = [c["x"] for c in first], [c["text"].strip() for c in first]
            rows = []
            for _, cells in state["table"]:
                row = [""] * len(cols)
                for c in sorted(cells, key=lambda c: c["x"]):
                    i = min(range(len(cols)), key=lambda i: abs(cols[i] - c["x"]))
                    row[i] = join_lines([row[i], c["text"]]) if row[i] else c["text"].strip()
                if rows and row == header:
                    continue
                if rows and not row[0]:
                    merge_row(rows[-1], row)
                else:
                    rows.append(row)
            out.append(md_table(rows[0], rows[1:]))
            state["table"] = []

    def flush_quote():
        if state["quote"]:
            out.append("> " + join_lines(state["quote"]) + "\n")
            state["quote"] = []

    def flush_all():
        flush_para(); flush_bullets(); flush_code(); flush_table(); flush_quote()

    def add_ruled_table(rows):
        """Leading all-bold rows are the header; a table that repeats the header of the table
        just before it continues that table (page break)."""
        nhead = next((i for i, (_, bold) in enumerate(rows) if not bold), len(rows))
        header = [""] * len(rows[0][0])
        for texts, _ in rows[:nhead]:
            merge_row(header, texts)
        body = [texts for texts, _ in rows[nhead:]]
        last = state["ruled"]
        if not (last and last["at"] == len(out) - 1 and nhead and last["header"] == header):
            last = state["ruled"] = {"header": header if nhead else body.pop(0), "rows": [], "at": len(out)}
            out.append("")
        for texts in body:
            if last["rows"] and not texts[0]:
                merge_row(last["rows"][-1], texts)
            else:
                last["rows"].append(texts)
        out[last["at"]] = md_table(last["header"], last["rows"])

    skip = {p - 1 for p in CFG["skip_pages"]}
    for pno in (p for p in range(len(doc)) if p not in skip):
        for it in line_items(doc[pno]):
            if it["kind"] == "table":
                flush_all()
                if it["rows"]:
                    add_ruled_table(it["rows"])
                prev = None
                continue
            if it["kind"] == "image":
                flush_all()
                figures.append({"page": pno + 1, "width_pt": it["width_pt"],
                                **{k: it[k] for k in ("xref", "clip", "dpi") if k in it}})
                out.append(f"![](fig-{len(figures):02d})\n")
                prev = None
                continue
            text = it["text"]
            fonts = {font_of(s) for s in it["spans"] if s["text"].strip()}
            size = round(max(s["size"] for s in ([s for s in it["spans"] if s["text"].strip()] or it["spans"])))

            if not text.strip():
                code = CFG["code"]
                if state["code"] and (code["blank_lines_inside"] or code["indent"] is None
                                      or it["x"] >= body_x + code["indent"]):
                    state["code"].append(it)
                else:
                    flush_code()
                prev = None
                continue

            if is_heading(fonts, size) and not is_code_line(it, it["x"] + 1000):
                flush_all()
                near = [x for x in HEADING_LEVEL_BY_X if abs(x - it["x"]) <= 6]
                level = (HEADING_LEVEL_BY_X[min(near, key=lambda x: abs(x - it["x"]))] if near
                         else CFG["heading"]["default_level"])
                out.append(f"{'#' * level} {text.strip()}\n")
                body_x = it["x"]
                prev = None
                continue

            if is_caption(it):
                flush_all()
                caption = text.strip()
                last_fig = max((i for i, o in enumerate(out) if o.startswith("![](fig-")), default=None)
                if last_fig is not None:
                    out[last_fig] = out[last_fig].replace("![]", f"![{caption}]")
                else:
                    out.append(f"*{caption}*\n")
                prev = None
                continue

            if CFG["quote"]["italic"] and is_italic(it):  # notes, warnings, quoted input
                flush_para(); flush_bullets(); flush_code(); flush_table()
                if state["quote"] and abs(it["y0"] - state["quote_y1"]) > CFG["paragraph"]["gap"]:
                    flush_quote()
                state["quote"].append(inline_md(it["spans"]))
                state["quote_y1"] = it["y1"]
                prev = it
                continue
            flush_quote()

            if CFG["table"]["size"] and size == CFG["table"]["size"]:  # table cells
                flush_para(); flush_bullets(); flush_code()
                if state["table"] and abs(state["table"][-1][0] - it["y0"]) < 3:
                    state["table"][-1][1].append(it)
                    if all("Bold" in f for f in fonts) and len(state["table"]) > 1:
                        row = state["table"].pop()
                        if not {c["text"].strip() for c in row[1]} <= {
                                c["text"].strip() for c in state["table"][0][1]}:
                            flush_table()  # a new header row starts another table
                        state["table"].append(row)
                else:
                    state["table"].append((it["y0"], [it]))
                continue
            flush_table()

            if fonts & MARKERS or text.strip() in GLYPHS:
                flush_para(); flush_code()
                state["in_bullet"], state["bullet_x"] = True, it["x"]
                rest = inline_md([s for s in it["spans"] if font_of(s) not in MARKERS | STRIP_FONTS
                                  and s["text"].strip() not in GLYPHS])
                state["bullets"].append([rest] if rest.strip() else [])
                prev = it
                continue

            if state["in_bullet"] and it["x"] > state["bullet_x"] + 2 and not any(
                    s["color"] in CODE_COLORS for s in it["spans"]):
                state["bullets"][-1].append(inline_md(it["spans"]))
                prev = it
                continue

            if is_code_line(it, body_x, bool(state["code"])):
                flush_para(); flush_bullets()
                state["code"].append(it)
                prev = it
                continue

            flush_bullets(); flush_code()
            para = CFG["paragraph"]
            if prev is not None and state["para"] and (
                    abs(it["y0"] - prev["y1"]) > para["gap"]
                    or (prev["x1"] < para["short_line_x1"] and prev["text"].rstrip().endswith((".", ":")))):
                flush_para()
            body_x = it["x"]
            state["para"].append(inline_md(it["spans"]))
            prev = it
    flush_all()
    return "\n".join(out), figures


def vision_lines(png: Path):
    """Apple Vision OCR (macOS): much better than Tesseract on small text in coloured diagram boxes."""
    res = subprocess.run(["swift", str(ROOT / "tools" / "ocr_vision.swift"), str(png)],
                         capture_output=True, text=True, check=True).stdout
    lines = []
    for r in json.loads(res):
        text = r["text"].strip(" |—-~_")
        if r["conf"] * 100 < CFG["ocr"]["min_conf"] or not re.search(r"[A-Za-z]{2}|\d", text) \
                or re.search(CFG["ocr"]["noise"], text):
            continue
        lines.append({"box": r["box"], "text": text})
    return lines


def tesseract_lines(png: Path, scale=1, enhance=False):
    """One Tesseract pass on a copy upscaled by `scale` (greyscale and contrast-stretched if
    `enhance`). Boxes are in original pixels."""
    ocr = CFG["ocr"]
    data = png.read_bytes()
    if scale != 1 or enhance:
        im = Image.open(png).convert("L" if enhance else "RGB")
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        (ImageOps.autocontrast(im) if enhance else im).save(buf, format="PNG")
        data = buf.getvalue()
    tsv = subprocess.run(["tesseract", "stdin", "-", "--psm", str(ocr["psm"]), "tsv"],
                         input=data, capture_output=True, check=True).stdout.decode("utf-8", "replace")
    groups = {}
    for row in tsv.splitlines()[1:]:
        f = row.split("\t")
        if len(f) < 12 or not f[11].strip() or float(f[10]) < ocr["min_conf"]:
            continue
        key = (int(f[2]), int(f[3]), int(f[4]))
        groups.setdefault(key, []).append(
            {"x": math.floor(int(f[6]) / scale), "y": math.floor(int(f[7]) / scale),
             "w": math.ceil(int(f[8]) / scale), "h": math.ceil(int(f[9]) / scale), "text": f[11]})
    lines = []
    for ws in groups.values():
        ws.sort(key=lambda w: w["x"])
        x0 = min(w["x"] for w in ws); y0 = min(w["y"] for w in ws)
        x1 = max(w["x"] + w["w"] for w in ws); y1 = max(w["y"] + w["h"] for w in ws)
        text = " ".join(w["text"] for w in ws).strip(" |—-~_")
        if not re.search(r"[A-Za-z]{3}|\d", text) or re.search(ocr["noise"], text):
            continue  # arrows, borders and other OCR noise
        lines.append({"box": [x0, y0, x1 - x0, y1 - y0], "text": text})
    return lines


def _overlap(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    w = min(ax + aw, bx + bw) - max(ax, bx); h = min(ay + ah, by + bh) - max(ay, by)
    return 0 if w <= 0 or h <= 0 else w * h / min(aw * ah, bw * bh)


def _alnum(t):
    return re.sub(r"[^0-9A-Za-z]", "", t)


def ocr_lines(png: Path):
    ocr = CFG["ocr"]
    engine = ocr["engine"]
    if engine == "auto":
        engine = "vision" if sys.platform == "darwin" and shutil.which("swift") else "tesseract"
    if engine == "vision":
        lines = vision_lines(png)
    else:
        lines = tesseract_lines(png, ocr["scale"])
        for extra in tesseract_lines(png, ocr["second_pass_scale"], True) if ocr["second_pass_scale"] else []:
            hits = [l for l in lines if _overlap(l["box"], extra["box"]) > 0.3]
            if not hits:
                lines.append(extra)
            elif (len(hits) == 1 and len(_alnum(extra["text"])) > len(_alnum(hits[0]["text"]))
                  and _alnum(hits[0]["text"]) in _alnum(extra["text"])):
                lines[lines.index(hits[0])] = extra  # e.g. "88%" -> "88% Similar"
    lines.sort(key=lambda l: (l["box"][1] // 10, l["box"][0]))
    return lines


def extract_figures(doc, figures, force):
    figdir = ROOT / "figures"
    (figdir / "layout").mkdir(parents=True, exist_ok=True)
    for n, fig in enumerate(figures, 1):
        name = f"fig-{n:02d}"
        png = figdir / f"{name}.png"
        if force or not png.exists():
            if "clip" in fig:
                pix = doc[fig["page"] - 1].get_pixmap(clip=pymupdf.Rect(fig["clip"]), dpi=fig["dpi"])
            else:
                pix = pymupdf.Pixmap(doc, fig["xref"])
                smask = doc.xref_get_key(fig["xref"], "SMask")
                if smask[0] == "xref":
                    pix = pymupdf.Pixmap(pix, pymupdf.Pixmap(doc, int(smask[1].split()[0])))
            if pix.alpha:  # composite onto white: tesseract reads transparent pixels as black
                img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")
                flat = Image.new("RGB", img.size, "white")
                flat.paste(img, mask=img.getchannel("A"))
                flat.save(png)
            else:
                pix.save(png)
            print(f"wrote: {png.relative_to(ROOT)}")
        layout_path = figdir / "layout" / f"{name}.json"
        if force or not layout_path.exists():
            lines = ocr_lines(png)
            layout = {"source": f"{name}.png", "page": fig["page"],
                      "width_pt": round(fig["width_pt"], 1), "localize": True,
                      "items": [{"box": l["box"], "align": "center"} for l in lines]}
            write(layout_path, json.dumps(layout, indent=1) + "\n", True)
            write(figdir / f"{name}.{SRC}.txt", "\n".join(l["text"] for l in lines) + "\n", True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="overwrite existing extracted files")
    ap.add_argument("--dry-run", action="store_true", help="print the Markdown body and write nothing")
    args = ap.parse_args()
    doc = pymupdf.open(CFG["source_path"])
    body, figures = extract_body(doc)
    if args.dry_run:
        print(body)
        print(f"<!-- {len(figures)} figures -->")
        return
    write(ROOT / "src" / f"{SRC}.md", body, args.force)
    extract_figures(doc, figures, args.force)


if __name__ == "__main__":
    sys.exit(main())
