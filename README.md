# Oscar Speech Trivia

A trivia game where you read an Academy Award acceptance speech snippet and guess the movie and category.

## Setup

```bash
pip install pandas google-generativeai python-dotenv
# Only needed if scraping new speeches:
pip install playwright && playwright install chromium
```

Create a `.env` file in the project root with your Gemini API key:
```
GEMINI_API_KEY=your_key_here
```

## Data Pipeline

The data CSVs are not checked into the repo. Run all commands from the project root.

### 1. Scrape speeches from oscars.org (optional)

Only needed to refresh scraped data. The Kaggle CSV (`data/raw/kaggle_speeches.csv`) must be provided separately.

```bash
python scripts/scrape_academy.py                                    # scrapes 2017-2024
python scripts/scrape_academy.py --start-year 2023 --end-year 2024  # specific range
```

### 2. Clean and merge raw data

```bash
python scripts/clean_speeches.py
```

Loads both sources from `data/raw/`, normalizes categories, deduplicates, and outputs `data/cleaned_speeches.csv`.

### 3. Label speeches with Gemini

```bash
python scripts/label_speeches.py          # full dataset
python scripts/label_speeches.py --test   # 20-speech test subset
```

Incremental -- only calls the LLM for unlabeled rows. Safe to re-run.

### 4. Export game data

```bash
python scripts/export_game_data.py
```

### 5. Play the game

```bash
# Quick start (exports + serves):
run_game.bat

# Or manually:
python scripts/export_game_data.py && python -m http.server 8000 -d game -b localhost
# Then open http://localhost:8000/
```

## Re-labeling a single speech

```bash
python scripts/relabel.py --film "gravity" --category "directing" --task redaction --note "Redact the film title"
python scripts/relabel.py --film "gravity" --category "directing" --task snippet_selection
python scripts/relabel.py --film "gravity" --category "directing" --task snippet_grading
```
