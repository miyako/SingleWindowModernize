---
description: "Reference for the technical-note localisation pipeline: technote.json keys, extraction heuristics, figure localisation, PDF reassembly and known pitfalls"
applyTo: "document/**,src/**,figures/**,tools/**,style/**,data/**,glossary.md,technote.json,Makefile"
---

# Technical note localisation pipeline: reference

The workflow, rules and checkpoints are in `AGENTS.md`. This file is a technical reference for `tools/` (the Python
pipeline, committed in the repository). `<src>` is `source_lang` (normally `en`) and `<tgt>` is `target_lang`
(e.g. `ja`). Skills (`technote-*` and the generic 4D skills) are in `.agents/skills/`; see `.agents/AGENTS.md`.

## Pipeline

| Step | Tool | Input → output |
|---|---|---|
| inspect | `tools/inspect_pdf.py [--write]` | PDF → style report + suggested `technote.json` |
| extract | `tools/extract.py [--force] [--dry-run]` | PDF → `src/<src>.md`, `figures/fig-NN.png`, `fig-NN.<src>.txt`, `layout/fig-NN.json` |
| check | `tools/build.py --check` | `src/<src>.md` vs `src/<tgt>.md`: code blocks identical, figure refs equal |
| figures | `tools/render_figures.py` | `figures/` → `build/figures/fig-NN.png` |
| review | `tools/contact_sheet.py [--compare] [NN ...]` | → `build/contact-N.png` |
| pdf | `tools/build.py [--lang xx]` | check → figures → Markdown → HTML → Chrome PDF (2 passes for TOC page numbers) |
| 4D syntax | skill `4dlsp` (`tool4d-lsp-stdio`, provisioned into `tools/4dlsp/`) | `.4dm` files → diagnostics |
| 4D run | `tools/tool4d.py demo/<Name> [test.4dm] [--compile] [--data \| --new-data] [--component DIR]` | runs a test method (or a whole-project compile) headlessly in a temp copy |
| data | `tools/wikidata.py query FILE.rq` / `entities Q.. --langs` | Wikidata with a QLever fallback |

`tools/config.py` loads `technote.json` merged over `DEFAULTS` (keys starting with `$` are ignored).

## technote.json keys

| Key | Meaning |
|---|---|
| `source_pdf` | Path; default is the only PDF in `document/` |
| `source_lang`, `target_lang` | Language codes; select file names and figure fonts |
| `output_pdf` | `"{stem}_{lang}.pdf"` |
| `toc_title` | `{lang: title}` for the generated table of contents |
| `accent_color` | Heading colour (CSS `--accent`) |
| `page_size` | `letter` or `a4` |
| `cover` | `{page, lines}`: the title block is the first `lines` text lines of `page` |
| `skip_pages` | 1-based pages not extracted (cover, original TOC); both are regenerated |
| `header_y`, `footer_y` | Lines with top above `header_y` or below `footer_y` (pt) are dropped |
| `heading.fonts` | Substrings of font names that mark headings; with `heading.min_size` |
| `heading.levels_by_x` | `{"x": level}`: heading level by left x (nearest within 6 pt); otherwise `default_level` |
| `code.colors` | Hex colours of syntax-highlighted code spans (Word exports code as coloured text) |
| `code.fonts` | Monospace font substrings |
| `code.indent` | x offset (pt) from the body margin at which an unstyled line *continues* a code block (default 5); `null`: only colour/font mark code |
| `code.indent_starts` | `true`: an indented line can also *start* a code block (old rule; for PDFs whose code is only indented, with no colour or monospace font). Default `false`: indented tables and notes stay text |
| `code.blank_lines_inside` | `true`: blank lines (and page breaks) never end a code block |
| `bullets.fonts` / `strip_fonts` / `glyphs` | Glyph fonts that mark list items / fonts of separator spans to drop / marker characters set in the body font (default `•`, `◦`, `▪`) |
| `caption.italic`, `caption.min_x` | Captions are italic lines starting right of `min_x` |
| `caption.pattern` | Regex searched in the line. With `italic: true` a matching line is a caption even if not italic; with `italic: false` only matching lines are captions (e.g. `"^Figure \\d"`) |
| `caption.max_size` | Lines with text larger than this (pt) are never captions (null: any size) |
| `quote.italic` | `true`: fully italic lines that are not captions become `>` blockquotes (notes, quoted user input). `callout.italic` is an alias |
| `figure.min_width_pt` | Images narrower than this (inline icons) are not extracted as figures |
| `vector_figures` | `[{page, clip: [x0,y0,x1,y1], dpi}]`: rasterise a vector diagram as one figure (default 300 dpi); text and images inside `clip` are dropped from the body, and the figure is OCR'd like the others |
| `table.size` | Font size used only by table cells (or null) |
| `table.ruled` | `true`: detect ruled (drawn) tables with pymupdf `find_tables` and emit Markdown tables |
| `paragraph.gap`, `short_line_x1` | Start a new paragraph after a vertical gap > `gap`, or after a short line ending in `.` or `:` |
| `ocr.engine` | `tesseract` (default), `vision` (macOS Apple Vision via `tools/ocr_vision.swift`; far better on small text in coloured boxes) or `auto` (vision when `swift` is available) |
| `ocr.psm`, `min_conf`, `noise` | Tesseract page-segmentation mode, word confidence threshold, regex of junk lines |
| `ocr.scale` | Upscale factor before Tesseract (2–3 helps small diagram text); boxes stay in image pixels |
| `ocr.second_pass_scale` | e.g. `3`: add a pass on an upscaled, contrast-stretched greyscale copy, which finds light text on tinted shapes; its lines are added where nothing was found, or replace a line they extend |
| `figure_fonts` | `{light, regular, bold: ["path#index", ...]}`: overrides the per-platform defaults |

`make inspect` derives most of these from a style histogram of the body pages:
- headings: larger than the body text, not black or bold/medium
- code: non-black colours at body size
- captions: black italic text

**Verify the result against the report;** heuristics can be wrong for unusual documents. If the PDF uses a
monospace font for code instead of colours, `code.colors` can stay empty.

## Extraction details (`tools/extract.py`)

- Lines are classified in reading order. Lines on the same row (tops within 2 pt) are ordered by x, so a bullet
  glyph comes before its text.
  - **heading:** font and size, not code
  - **code:** every span in a code colour or code font (even at the body margin); some styled spans on an indented
    line; or an indented line inside a code block that has already started (see `code.indent_starts`)
  - **caption:** italic (or `caption.pattern`) and x > `min_x`
  - **quote** (`quote.italic`): all-italic lines, grouped by vertical gap
  - **bullet:** a marker font or glyph; following lines indented past the marker continue the item
  - **table row:** `table.size`, or inside a ruled table (`table.ruled`). Columns come from the first (header) row;
    a row without a first cell continues the previous row (wrapped cell text); a header repeated after a page break
    is dropped; a different all-bold row starts a new table.
  - **body**
- Code blocks:
  - consecutive code lines become one fence
  - the language is guessed: `json`, `html`, `js`, `text`, otherwise `4d`
  - indentation: spaces kept in the PDF are kept as is; otherwise one level when x is right of the block's left edge
- Inline: bold spans → `**…**` (adjacent bold runs are merged); inline code-coloured or monospace spans →
  `` `…` ``. `<tag` and `*` in text are escaped (`&lt;`, `\*`) so Markdown does not read them as markup.
- The cover title may wrap over several lines in the same font and size; they become one `#` title.
- `--dry-run` prints the Markdown without writing anything: use it to tune `technote.json` before extracting.
- Figures: raster images become `figures/fig-NN.png` (RGBA composited onto white) in document order, with
  `![caption](fig-NN)` placed where the image sits.
  - `layout/fig-NN.json` stores `source`, `page`, `width_pt` (the placed width, reused in the rebuild) and
    `localize`, plus one `items[]` entry per OCR line with its `box`.
- Vector diagrams (drawn with PDF paths, not images) are **not** extracted by default. `inspect` lists pages with
  many drawings. If they contain text, ask the user: either add the region to `vector_figures` (rasterised into a
  figure, numbered in document order), or leave it.
- Re-extraction never overwrites. `--force` overwrites `<src>` files and layouts, so warn the user first:
  it discards OCR corrections and layout tweaks.
- **Validate:** compare the numbers of headings, code blocks and figures in `src/<src>.md` with your own count from
  the PDF, then read it once end to end for broken joins and merged code lines.
- **OCR:** check every `fig-NN.<src>.txt` by eye and correct it; it is the reference that line N maps to. Typical
  errors: `4D` read as `AD`, `×`, `θ`, `=`, units, stray `E`/`eee` lines from borders and arrows.

## Translation conventions

- Translate paragraph by paragraph, keeping Markdown structure and order.
- Translate captions but keep `fig-NN`. Keep the fences of code blocks exactly as they are, language tag included.
- Japanese:
  - です・ます調.
  - Half-width alphanumerics, no spaces between Japanese and Latin text (`4D.Vector型`).
  - Full-width `（）` and `：` in prose.
  - Use the official 4D Japanese documentation terms (e.g. Webエリア, エンティティセレクション, データストア, 引数,
    メソッド, フォーム, コレクション) and record them in `glossary.md` (`| English | 日本語 | Notes |`).
  - First occurrence of a technical term: 日本語（English）.
- Other languages: agree on the style with the user, and set the fonts (`figure_fonts`) and the font stack in
  `style/style.css`.
- Inline code (`` `name` ``) stays as is. Identifiers in prose that refer to code stay in their original form.
- Keep figure labels short: the boxes are fixed.
- Translator's notes (e.g. where the localised demo differs from the original): only with the user's agreement, as a
  `> **訳注**：…` blockquote right after the paragraph concerned. It is the only extra block allowed in `src/<tgt>.md`;
  it is styled by `blockquote` in `style/style.css`.

## Figure localisation (`tools/render_figures.py`)

Line N of `fig-NN.<tgt>.txt` maps to line N of `fig-NN.<src>.txt` and to `items[N]` in the layout:
- **identical:** keep the original pixels
- **empty:** erase, draw nothing
- **otherwise:** erase and draw the translation

For each changed item:
1. The background colour is sampled from a ring around the box; the box is erased with padding (`erase_pad`).
2. The foreground colour is sampled from the darkest differing pixels.
3. The size comes from the original text height and width, then is clamped to the box.
4. Similar sizes are snapped together, so labels of the same rank match (groups within 8 %; single labels within
   30 % join the nearest group).
5. The text is drawn with the weight (`light`, `regular` or `bold`) and alignment (`center` or `left`).

Overrides per item: `scale`, `size`, `weight`, `align`, `dx`, `dy`, `box`, `bg`, `fg`, `erase_pad`.

Rotated labels (OCR usually misses them; add the item and its line by hand):
- `rotate: 90` (reads bottom to top) or `270` (top to bottom): a vertical label filling its `box`.
- Any angle: `angle` (degrees, counter-clockwise), `center: [x, y]`, `length` and `thickness` (inked extent along
  and across the baseline, px); `box` is then only used to sample colours.
- For rotated labels, `dx`/`dy` move the centre in image pixels.
Per figure:
- `"localize": false` copies the image unchanged unless `"replace"` is set (use it to bypass diagram overlays on screenshots)
- `"replace": "fig-NN-<tgt>.png"` takes precedence over `localize` and uses a ready-made image from `figures/`, keeping `width_pt` (a different aspect
  ratio only changes the height)

Typical fixes:
- OCR merged two labels: split the text and give explicit `box` values.
- The erase removes legend dots or arrows next to text: shift the box (`dx`, or a narrower `box`) and use `align: left`.
- A title came out too small: `scale: 1.3`.
- Text runs outside its shape: shorten the translation (preferred), or use `size`.
- Figures that show sample data (field names, values) may need edits that match the demo, e.g. new
  `name<TGT>` fields.

Always check with `make review` (original above, localised below).

### Screenshots

Use `technote-localise-screenshots` for mechanical screenshot text replacement. If the pinned `.agents` does not
contain the skill, report the missing dependency and leave screenshots unchanged until it is published and the
submodule is updated. Reusable procedures belong in that skill, not in this reference.

- Keep the original `figures/fig-NN.png` untouched. Save the result as `figures/fig-NN-<tgt>.png` and use `"replace"`
  in the layout; keep `"localize": false` so the diagram renderer cannot accidentally repaint the screenshot.
- Resolve 4D-owned UI text from target-language `.xlf` resources in a local full 4D or 4D Server installation
  (not English-only tool4d). Resolve demo-owned text from the demo's translated resources. Preserve code,
  identifiers and values unless an approved demo-data change requires otherwise.
- Match each region's actual fonts and rendering context: 4D form, browser content (CSS/webfonts), browser chrome
  or OS dialog; platform/version, locale, theme and display scale affect the result. The diagram renderer's global
  `figure_fonts` is not a per-region screenshot font selector; do not invent unsupported item font overrides.
- When in doubt, follow `4dcli` to launch full GUI 4D and capture the relevant runtime UI. Headless tool4d or a
  Form Editor image cannot establish native-dialog fidelity. Do not modify the demo for capture without the
  project-editing checkpoint. If still uncertain or the matching environment is unavailable, request manual
  confirmation or a localised screenshot, and leave the result explicitly unverified.
- Review replacements on contact sheets and at native resolution, then spot-check the rebuilt PDF. Keep
  checkpoint 4: mechanical translation does not remove editorial approval.

## Reassembly (`tools/build.py`)

1. Check: code blocks are compared by position, ```` ```text ```` blocks are skipped, and the sets of figure
   references must match. Any mismatch aborts with a diff.
2. Render the figures.
3. Markdown → HTML (`fenced_code`, `tables`, `attr_list`).
   - The cover comes from the first lines of `<tgt>.md`, and the TOC is generated from the headings.
   - Figures become `<figure>` with `width:{width_pt}pt`.
4. The CSS is `style/style.css` plus injected `:root{--accent}` and `@page{size}`. Chrome is run headless
   (`--headless=new --no-pdf-header-footer --print-to-pdf`) twice; the second pass fills in the TOC page numbers,
   found by searching each heading in the first-pass PDF with pymupdf. Page numbers use `@page` margin boxes
   (Chrome 131+); `pre` uses `overflow-wrap: anywhere` so long code lines wrap.
5. The output is `build/<output_pdf>`. Compare its page count with the original: ±2 pages is normal.

To prove the check works, change one character inside a code block of `<tgt>.md`, run `make check`, confirm it
fails, then revert.

## 4D demo checks

The workflow is in the skill `technote-localise-4d-project`; the 4D rules are in the generic skills it lists.

- **Syntax:** skill `4dlsp` (`validate` for the files you changed, `check-syntax` for the whole project). Don't write
  a startup method or launch 4D just to check syntax.
- **Running code:** `tools/tool4d.py` copies `Project/` and `Resources/` (and `Data/` with `--data`) to a temporary
  folder, adds the test method as `agentTest`, and runs tool4d with `--skip-onstartup`. The test method writes its
  results to `File("/PACKAGE/agent-test.txt")` and ends with `QUIT 4D`; the script prints that file. `--compile`
  runs `Compile project` on the whole project (expect `success: true` and no errors). `--new-data` starts with an
  empty data file; `--component DIR` copies a component bundle (e.g. from the 4D dependency cache: tool4d does not
  download GitHub dependencies) into `Components/`. The repository is never modified. tool4d is looked up in `$TOOL4D`, `tools/4dcli/` (provisioned by the `4dcli` skill), then the standard
  install locations.
- Forms can't be displayed headlessly: ask the user to check window flow and label fit in 4D.

## Verification checklist (before release)

- [ ] `make check` passes, and a deliberate code edit makes it fail. `make` builds; TOC page numbers are right; the
  page count is plausible.
- [ ] Every localised figure has been seen on a contact sheet. Screenshot replacements have authoritative wording
  and context-matched fonts; uncertain rendering is manually confirmed, or the original is explicitly approved as is.
- [ ] No source-language leftovers: grep `<tgt>.md` and `*.<tgt>.txt` for long ASCII sentences and old example
  names.
- [ ] The glossary is consistent: grep for alternative spellings of key terms.
- [ ] Numbers in examples were recomputed from the committed data.
- [ ] 4D: changed `.4dm` files pass the `4dlsp` syntax check; `tools/tool4d.py --compile` and the test methods pass
  (or it is stated that tool4d was unavailable); XLIFF resolves in each language; no unverified token suffixes
  (`:Cnnn`, `:Knn:nn`; see the `4dproject` skill).
- [ ] `git status` is clean; temporary files (`/tmp/...`, tool4d test copies) are removed. Nothing under `.agents/`
  or the provisioned `tools/4d*/` folders is modified or committed.

## Pitfalls

- A caption just above `footer_y` can be dropped. Check that every figure has a caption.
- OCR boxes that merge two labels, or include legend dots: fix them with `box` / `dx`.
- Files the user drops into `build/` are lost on rebuild: move them to `figures/`.
- Re-saving 4D methods in the 4D editor can change line endings (CRLF vs LF). Mention it; don't "fix" it silently.
- The Wikidata SPARQL service can be down or rate-limited for long periods. `tools/wikidata.py` falls back to QLever.
- Linux and macOS builds use different CJK fonts, so release assets should come from the platform the user reviewed.
