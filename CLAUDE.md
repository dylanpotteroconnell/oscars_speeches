# Oscars Speeches Trivia Game

## Project Goal
Build a trivia game where players see an Academy Award acceptance speech snippet and guess the winner. Starting as a local proof-of-concept app, eventually a website.

## Current State

### Completed: Data Cleaning Pipeline (Phase 1)
- **`scripts/config.py`** - Shared constants:
  - `MIN_YEAR = 1993` (filter threshold)
  - `TARGET_CATEGORIES` - Maps raw category strings to 8 canonical names (Best Picture, Directing, 4 acting categories, 2 screenplay categories)
  - `OUTPUT_COLUMNS` - Defines the 7 output columns
- **`scripts/clean_speeches.py`** - Pipeline that:
  - Loads both raw CSVs from `data/raw/` (Kaggle + Academy scraped)
  - Kaggle: parses year/ceremony from formatted strings (e.g., "2016 (89th) Academy Awards")
  - Academy: year/ceremony already numeric from scraper
  - Normalizes categories via lookup map; drops unmatched
  - Cleans winner names (strips parenthetical notes)
  - Cleans speeches (removes "WINNER NAME:" headers)
  - Either source can be absent (returns empty DataFrame) — modular by design
  - Merges both sources, deduplicates on (year, category) preferring Academy data
  - Outputs to `data/cleaned_speeches.csv`
- **`scripts/scrape_academy.py`** - Playwright-based scraper for aaspeechesdb.oscars.org:
  - Scrapes speeches by year (default 2017-2024) using headless Chromium
  - Navigates results list, expands each record via `ExpandRecord()` JS call
  - Extracts category, film title, winner, and speech text
  - Outputs to `data/raw/academy_scraped.csv`
  - Supports `--start-year` and `--end-year` flags
  - Requires: `pip install playwright && playwright install chromium`
- **`data/raw/kaggle_speeches.csv`** - 1,669 rows, 1939-2016, 7 columns (original Kaggle dataset)
- **`data/raw/academy_scraped.csv`** - Scraped from oscars.org, 2017-2024, all categories
- **`data/cleaned_speeches.csv`** - 253 rows, 1993-2024, 7 columns, 8 target categories, no nulls

### Completed: LLM Labeling Pipeline (Phase 2)
- **`scripts/label_speeches.py`** - Generic incremental labeling pipeline that:
  - Reads `data/cleaned_speeches.csv` as input
  - Stores labels separately in `data/labels.csv` (keyed by year+category)
  - On each run, only calls the LLM for rows missing labels (incremental)
  - Produces `data/speeches_with_labels.csv` (merged output) for downstream use
  - Adding new speeches to the input CSV preserves all existing labels
  - `save_labels()` uses `combine_first` to update only new cells without clobbering existing labels
  - Loops over `TASKS` list from config; each task uses a prompt file + parser
- **`prompts/`** directory — one `.md` file per labeling task:
  - Each file is a self-contained prompt template (instructions, rubric, few-shot examples, prompt with `{placeholders}`)
  - Loaded at runtime via `load_prompt()` and formatted with CSV row columns
  - Files: `distinctiveness.md`, `redaction.md`, `snippet_selection.md`, `snippet_grading.md`, `plot_hint.md`
- **`scripts/config.py`** — shared constants including `TASKS` list, `TASK_DEPENDENCIES`, and `LABELS_KEY_COLUMNS`
- **`.env`** - Gemini API key (gitignored)

**LLM choice**: Gemini 2.0 Flash via Google AI Studio API. Local models (Ollama) were considered but the dev machine has an AMD GPU (RX 6750 XT) — poor ROCm/Windows support makes local inference unreliable. Gemini Flash is ~$0.20 per 1K calls, so even heavy iteration stays under a few dollars.

**Adding a new labeling task**:
1. Create `prompts/{task_name}.md` with instructions, rubric, examples, and `## Prompt` section with `{placeholders}`
2. Add a parser to `PARSERS` dict in `label_speeches.py` (e.g. `parse_int_score` for 1-5 scores, `parse_text` for free text)
3. Add the task name to `TASKS` in `config.py`
4. If the task depends on a prior task's output, add it to `TASK_DEPENDENCIES` in `config.py`

**Current tasks** (active in `TASKS`):
- `distinctiveness` (1-5) — how unique/memorable the speech is
- `redaction` → `redacted_speech` column — LLM-guided redaction using `[REDACT: ...]` inline markup to hide winner/film identity while keeping non-obvious names. 5 few-shot examples covering surname sharing, speaker annotations, contextual first names, character/film titles, and studio names.
- `plot_hint` — cryptic, funny one-sentence hint about the movie/character. 4 few-shot examples.

- `snippet_selection` → `golden_snippet` column — pick the most interesting/distinctive excerpt from the redacted speech. Depends on `redacted_speech`. 4 few-shot examples.
- `snippet_grading` (1-5) — rate how interesting the selected snippet is. Depends on `golden_snippet`. 3 few-shot examples.

**Redaction format**: The LLM returns the full speech with `[REDACT: original text]` tags. Utility functions in `label_speeches.py`:
- `render_redacted()` — strips tags to produce display text with `______` blanks
- `extract_redactions()` — pulls out the list of redacted strings

**Task dependencies**: Some tasks need output from earlier tasks as prompt input. `TASK_DEPENDENCIES` in `config.py` maps task → required label columns. The pipeline merges prior labels into the row before prompting, so templates can use placeholders like `{redacted_speech}`. `TASK_LABEL_COLUMNS` in `label_speeches.py` maps task names to their output column when it differs from the task name.

**Re-labeling a single speech**: `scripts/relabel.py` re-runs one task for one speech without affecting other labels. Supports `--note` to append correction instructions to the prompt, and `--override` to set a value directly without calling the LLM. If the task has downstream dependents (e.g. redaction → snippet_selection → snippet_grading), re-run those separately after.
```bash
python scripts/relabel.py --film "gravity" --category "directing" --task redaction --note "Redact the film title"
python scripts/relabel.py --film "gravity" --category "directing" --task snippet_selection
python scripts/relabel.py --film "gravity" --category "directing" --task snippet_grading
```

### Completed: Game Prototype (Phase 3)
- **`scripts/export_game_data.py`** - Exports labeled data as JSON for the game:
  - Reads merged CSV, filters to `snippet_grading >= 3`
  - Loads full `cleaned_speeches.csv` as decoy pool for film options
  - `pick_film_options()` generates 6 shuffled film titles per speech: 3 same-category (correct + 2 peers within ±5 years) + 3 decoy-cluster (1 seed from different category + 2 from seed's category)
  - Outputs `game/data.json` with speech objects (snippet, redactions, hints, answers, film_options)
  - Strips LLM triple-quote artifacts from snippets
  - Converts NaN values to null for valid JSON (`_safe()` helper)
  - Supports `--test` flag
- **`game/index.html`** - Single-file trivia game UI:
  - Start screen with rules explanation (includes year range 1993-2024) and link to sources page
  - Each game = 5 random speeches; shows redacted golden snippet, player guesses movie + category
  - Two-tier hint system: hint 1 = narrow to 6 film options, hint 2 = plot hint. If either is missing, skips to the other.
  - Scoring: 10 points base, -2 per hint, -2 per wrong guess (min 1 if correct), 0 if wrong after 3 guesses
  - "Give up" button to skip a speech (0 points)
  - Feedback stacks (hints, wrong guesses all visible); validation messages auto-clear on next action
  - Reveals unredacted snippet (in matching card style) with highlighted redactions + full speech
  - "Report an issue" link after each round → pre-fills Google Form with speech identifier
  - End-of-game summary with per-speech breakdown and acceptance-speech-themed grade
  - Visual: dark theme with gold accents, subtle card glow, gold divider between snippet and guess form
- **`game/sources.html`** - Data sources page explaining where speeches come from (Kaggle 1939-2016, Academy scraper 2017-2024)
- **`run_game.bat`** - Quick-start script: exports game data + starts local server at localhost:8000
- **`notebooks/explore_data.ipynb`** - Data exploration notebook with `show_speech()` for browsing speeches and `show_labels()` for inspecting all labels on a speech (search by winner, film, category, year substring)

### Not Yet Started

#### Game Enhancements
- Deploy as a website
- More hint types (beyond plot hint)
- Difficulty levels / speech filtering

## Design Decisions
- **CSV as intermediate format** between pipeline stages (even if app uses something else)
- **Year cutoff (1993+)** to keep speeches reasonably recognizable
- **8 major categories only** for now: Best Picture, Directing, 4 acting, 2 screenplay
- **Pipeline is modular** - each step is a separate function, easy to extend

## Running

All commands run from project root.

```bash
# Phase 0: Scrape new speeches from oscars.org (only needed once or to refresh)
python scripts/scrape_academy.py                        # scrapes 2017-2024
python scripts/scrape_academy.py --start-year 2023 --end-year 2024  # specific range

# Phase 1: Clean raw data (merges Kaggle + Academy sources)
python scripts/clean_speeches.py

# Phase 2: Label speeches (incremental — safe to re-run)
python scripts/label_speeches.py          # full dataset
python scripts/label_speeches.py --test   # 20-speech test subset

# Phase 3: Export game data
python scripts/export_game_data.py

# Phase 4: Play the game
run_game.bat
# Or manually:
python scripts/export_game_data.py
python -m http.server 8000 -d game -b localhost
# Then open http://localhost:8000/
```
Requires: pandas, google-generativeai, python-dotenv, playwright (for scraper only)
