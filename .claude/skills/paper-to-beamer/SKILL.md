---
name: paper-to-beamer
description: >
  Summarize academic papers (PDF) into LaTeX Beamer slide decks. Use this skill
  whenever a user uploads an academic paper or research article and asks for a
  presentation, slides, summary deck, Beamer output, or lecture notes. Also
  trigger when the user says "summarize this paper as slides", "create a
  presentation from this PDF", "make beamer slides", "turn this paper into a
  talk", or similar. Covers: PDF table/figure extraction as images, structured
  slide generation with research question / literature / data / results /
  conclusion sections, and packaging into a compilable .zip. Even if the user
  doesn't explicitly say "Beamer", trigger this skill when they want slides
  from an academic PDF—Beamer is the default academic format.
---

# Paper-to-Beamer Skill

Convert academic papers (PDF) into professional LaTeX Beamer slide decks with
extracted tables and figures.

## Overview

This skill automates a multi-step workflow:

1. **Read the paper** — extract text and identify key tables/figures
2. **Extract visuals** — rasterize table/figure pages from the PDF as images
3. **Generate slides** — produce a Beamer `.tex` file following a structured
   academic template
4. **Package output** — bundle `.tex` + images into a compilable `.zip`

## Step-by-step Workflow

### Step 1: Inspect the PDF

The user stores PDFs in the `paper/` folder at the project root. Run the
helper script to get a content inventory:

```bash
python <SKILL_DIR>/scripts/inspect_pdf.py "paper/<filename>.pdf"
```

This prints page count, text-extractability check, and embedded image list.
Review the output to understand the paper's structure.

If text is already available in context (e.g., user uploaded and the content
appears inline), skip heavy text extraction — use the in-context text directly.

### Step 2: Identify tables and figures

Scan the paper for tables and figures to extract. Common patterns:
- Tables are labeled "TABLE I", "Table 1", "Tab. 1", etc.
- Figures are labeled "FIGURE 1", "Figure 1", "Fig. 1", etc.

If the user specifies which tables/figures to extract, use their list.
Otherwise, extract all numbered tables and key result figures.

Rasterize candidate pages at 300 DPI into the figure output directory:

```bash
mkdir -p beamer/figure
pdftoppm -jpeg -r 300 -f <start> -l <end> "paper/<filename>.pdf" /tmp/pages
```

Then visually inspect (view) each page image to locate exact table/figure
boundaries.

### Step 3: Crop tables and figures

Use the helper script to crop specific regions into `beamer/figure/`:

```bash
python <SKILL_DIR>/scripts/crop_tables.py \
  --input /tmp/pages-05.jpg \
  --output beamer/figure/table_I.png \
  --crop "5%,8%,95%,70%"
```

The `--crop` argument is `left%, top%, right%, bottom%` as percentages of the
full image dimensions. Adjust percentages after visual inspection to capture
just the table with its title and notes, excluding page headers/footers.

**Cropping guidelines:**
- Include the table/figure title (e.g., "TABLE II") in the crop
- Include footnotes and significance indicators (*, **, ***)
- Exclude page numbers and running headers
- Leave ~2% padding around the content
- For tables that span the full page width, use left=3%, right=97%

If manual percentage tuning is tedious, crop generously first (include some
whitespace) — Beamer's `\includegraphics` with `height=0.82\textheight` will
scale it down cleanly.

### Step 4: Read the paper and identify content

Extract the following from the paper text (in-context or via pdftotext):

| Section | What to extract |
|---------|----------------|
| **Research question** | The 1–2 central questions or hypotheses |
| **Literature** | The 3 most directly related prior papers (author, year, key finding) |
| **Data** | Source, sample size, time period, key variables |
| **Model / method** | Econometric or statistical approach |
| **Results** | Main findings from each key table/figure |
| **Conclusion** | Summary of contributions and implications |

### Step 5: Generate the Beamer .tex file

Use the reference template at:

```
<SKILL_DIR>/references/beamer_template.tex
```

Read that template, then customize it for the specific paper. The template
has placeholder slides for each section — fill them in with the extracted
content.

**Slide design principles:**
- 12–20 slides total (excluding title and thank-you)
- One table/figure per slide — never cram two onto one slide
- Each table/figure slide should be followed by an interpretation slide
- Use `\includegraphics[height=0.82\textheight]{figure/<filename>}` for images
- Bullet items should be 1–2 sentences, not single words
- Prefer `enumerate` for sequenced findings, `itemize` for parallel points
- Use `\bigskip` between logical groups instead of excessive nesting
- Bold key terms with `\textbf{}` sparingly — only for variable names or
  critical findings

**Slide structure (order may vary):**

```
1. Title slide
2. Outline
3. Research questions (1 slide)
4. Related literature (1–2 slides)
5. Model / empirical specification (1–2 slides)
6. Key variables (1 slide)
7. Data description (1 slide)
8–N. Results: [table image] + [interpretation] pairs
N+1. Conclusions / key findings (1 slide)
N+2. Thank you
```

### Step 6: Package and deliver

The `.tex` file goes in `beamer/` and images are already in `beamer/figure/`.

```bash
# Ensure directories exist
mkdir -p beamer/figure

# Write main.tex into beamer/
# (already done in Step 5)

# Verify all referenced images exist
ls beamer/figure/table_*.png beamer/figure/figure_*.png 2>/dev/null

# Optional: create a zip for portability
cd beamer && zip -r ../beamer_slides.zip . && cd ..
```

The user compiles directly from the `beamer/` directory:
`cd beamer && pdflatex main.tex && pdflatex main.tex`

Since `main.tex` references images via `figure/<name>.png`, the relative path
resolves correctly when `pdflatex` runs from `beamer/`.

## Common Pitfalls

- **pdftoppm page numbering**: Output filenames are zero-padded based on total
  page count (e.g., `page-03.jpg` for a 50-page PDF). Use `ls` to find the
  actual filename rather than guessing.
- **Pillow import**: Use `from PIL import Image` after `pip install Pillow`.
- **Table crops cut off**: Always visually verify crops before packaging. If
  in doubt, crop more generously — extra whitespace is preferable to missing
  content.
- **LaTeX special characters**: Escape `%`, `$`, `&`, `#`, `_` in text
  extracted from PDFs. The helper script handles common cases but always
  double-check author names and titles.
- **Large images**: 300 DPI produces large files. For a leaner zip, re-save
  cropped images at 150 DPI or convert to PNG with compression.

## Dependencies

- `poppler-utils` (pdftoppm, pdftotext, pdfinfo) — usually pre-installed
- `Pillow` Python package — install with `pip install Pillow`
- A LaTeX distribution (for the user to compile) — not needed on the server

## File Reference

| File | Purpose |
|------|---------|
| `scripts/inspect_pdf.py` | Quick PDF content inventory |
| `scripts/crop_tables.py` | Crop regions from rasterized page images |
| `references/beamer_template.tex` | Starter Beamer template with all sections |
