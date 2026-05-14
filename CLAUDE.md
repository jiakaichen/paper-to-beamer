# CLAUDE.md

## Project Overview

This project uses Claude to convert academic papers (PDFs) into LaTeX Beamer slide decks. The workflow extracts tables and figures as images, generates structured presentation slides, and outputs a compilable Beamer project.

## Directory Layout

```
your-project/
├── CLAUDE.md                ← You are here
├── paper/                   ← Source PDFs go here
│   └── *.pdf
├── beamer/                  ← Generated .tex files go here
│   ├── main.tex
│   └── figure/              ← Extracted table/figure images go here
│       ├── table_II.png
│       └── ...
└── .claude/
    └── skills/
        └── paper-to-beamer/
```

**Input:**  `paper/`  — Drop academic PDFs here.
**Output:** `beamer/main.tex` + `beamer/figure/*.png` — Compilable from `beamer/`.

## Available Skills

- **paper-to-beamer**: Summarize academic papers into Beamer slides with extracted tables/figures.
  Location: `.claude/skills/paper-to-beamer/SKILL.md`
  Trigger: Any request involving academic PDFs and slides, presentations, Beamer, or lecture notes.

## Workflow

When the user asks for slides from a paper:

1. Read `.claude/skills/paper-to-beamer/SKILL.md` first — always follow its step-by-step instructions
2. Run `scripts/inspect_pdf.py` on the PDF in `paper/` to get page count and table/figure locations
3. Rasterize pages containing tables/figures with `pdftoppm -jpeg -r 300` to `/tmp/`
4. Visually inspect rasterized pages, then crop with `scripts/crop_tables.py` — save output to `beamer/figure/`
5. Read the paper text and fill in the Beamer template from `references/beamer_template.tex`
6. Write the completed `.tex` to `beamer/main.tex`
7. Optionally zip `beamer/` for portability

The user compiles with: `cd beamer && pdflatex main.tex && pdflatex main.tex`

## Naming Conventions

| Item | Pattern | Location | Example |
|------|---------|----------|---------|
| Source PDF | `<descriptive_name>.pdf` | `paper/` | `paper/dennis_mullineaux_2000.pdf` |
| Main slides | `main.tex` | `beamer/` | `beamer/main.tex` |
| Table image | `table_<LABEL>.png` | `beamer/figure/` | `beamer/figure/table_II.png` |
| Figure image | `figure_<LABEL>.png` | `beamer/figure/` | `beamer/figure/figure_1.png` |
| Output zip | `beamer_slides.zip` | project root | `beamer_slides.zip` |

Inside `main.tex`, images are referenced with the relative path `figure/<name>.png`
(e.g., `\includegraphics[height=0.82\textheight]{figure/table_II.png}`). A
`\graphicspath{{figure/}}` declaration is included so `\includegraphics{table_II.png}`
also works.

## Environment

- Python 3.8+ with `Pillow` (install via `pip install Pillow --break-system-packages` if needed)
- `poppler-utils` must be available (`pdftoppm`, `pdftotext`, `pdfinfo`, `pdfimages`)
- Rasterize at 300 DPI by default; use 150 DPI only if the user requests smaller files
- A LaTeX distribution (TeX Live / MiKTeX) is needed on the user's machine to compile

## Coding Style

- Use Python for all helper scripts; no Node.js dependencies
- Prefer CLI tools from `poppler-utils` over Python PDF libraries for rasterization
- Use `Pillow` for image manipulation (cropping, resizing)
- Keep scripts self-contained with clear `--help` output

## Common Pitfalls to Avoid

- `pdftoppm` zero-pads output filenames based on total page count — always use `ls` to find the actual filename instead of guessing
- LaTeX special characters (`%`, `$`, `&`, `#`, `_`) in paper text must be escaped in the `.tex` output
- Some PDFs have vector-drawn tables that won't appear via `pdfimages` — always rasterize the page with `pdftoppm` instead
- When cropping, include the table title and footnotes but exclude running headers and page numbers
- Always `mkdir -p beamer/figure` before writing cropped images — don't assume the directory exists
