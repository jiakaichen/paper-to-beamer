# Paper-to-Beamer Skill

Convert academic papers (PDF) into professional LaTeX Beamer slide decks with
extracted tables and figures.

## What It Does

Given an academic paper in PDF format, this skill:

1. **Inspects** the PDF to identify tables, figures, and page structure
2. **Extracts** tables and figures as high-resolution cropped images
3. **Generates** a structured Beamer `.tex` file with research questions,
   literature review, data, empirical results, and conclusions
4. **Packages** everything into a compilable `.zip` (`.tex` + images)

## Project Directory Structure

The skill expects the following layout in your project:

```
your-project/
├── README.md                         # This file
├── CLAUDE.md
├── paper/                            # Source PDFs go here
│   └── some_paper.pdf
├── beamer/                           # Generated slides go here
│   ├── main.tex
│   └── figure/                       # Extracted tables/figures
│       ├── table_II.png
│       ├── table_III.png
│       └── ...
└── .claude/
    └── skills/
        └── paper-to-beamer/
            ├── SKILL.md
            ├── scripts/
            │   ├── inspect_pdf.py
            │   └── crop_tables.py
            └── references/
                └── beamer_template.tex
```

## Skill Directory Structure

```
paper-to-beamer/
├── SKILL.md                          # Main skill instructions
├── scripts/
│   ├── __init__.py
│   ├── inspect_pdf.py                # PDF content inventory
│   └── crop_tables.py                # Crop tables/figures from pages
├── references/
│   └── beamer_template.tex           # Starter Beamer template
└── assets/                           # (empty — for future custom themes)
```

## Installation

### Claude Code (CLI)

Place the skill folder in your project's skill directory:

```bash
# Option A: project-level skill
mkdir -p .claude/skills
cp -r paper-to-beamer .claude/skills/

# Option B: user-level skill (available across all projects)
mkdir -p ~/.claude/skills
cp -r paper-to-beamer ~/.claude/skills/
```

Then in your `CLAUDE.md` or project instructions, add:

```markdown
## Available Skills
- paper-to-beamer: Summarize academic papers into Beamer slides.
  Location: .claude/skills/paper-to-beamer/SKILL.md
```

### VS Code with Claude Extension

1. Copy `paper-to-beamer/` into your workspace under `.claude/skills/`
2. The extension will auto-detect the skill from `SKILL.md`

### Manual Usage (without skill auto-detection)

You can also reference the skill directly in your prompt:

```
Please read .claude/skills/paper-to-beamer/SKILL.md and follow its
instructions to create Beamer slides from the attached paper.
```

## Usage Examples

```
Generate a LaTeX Beamer slide deck to summarize the paper in the `paper` 
folder. Discuss the paper's research question, the five most related 
papers in the literature, the research data, the key empirical measure 
and its construction, the key empirical identification strategy, and the 
empirical results. Generate the Beamer TeX code for Beamer slides under 
the `beamer` folder. In addition, obtain the Tables and Figures from 
the paper, save them as image files in the `figure` folder under 
`beamer`, and include them in the Beamer TeX code. 
```

## Dependencies

**On the server / CLI environment:**
- `poppler-utils` (provides `pdftoppm`, `pdftotext`, `pdfinfo`, `pdfimages`)
- Python 3.8+
- `Pillow` (`pip install Pillow`)

**For the user to compile the output:**
- A LaTeX distribution with Beamer (TeX Live, MiKTeX, etc.)
- Run `pdflatex main.tex` twice in the extracted zip directory