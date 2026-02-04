"""Main cleaning script for the Oscars speeches dataset.

Loads raw data from two sources (Kaggle CSV + scraped Academy CSV),
normalizes both, merges them (preferring the Academy version on
duplicates), and outputs cleaned_speeches.csv.

Usage:
    python scripts/clean_speeches.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config import MIN_YEAR, TARGET_CATEGORIES, OUTPUT_COLUMNS

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
KAGGLE_PATH = RAW_DIR / "kaggle_speeches.csv"
ACADEMY_PATH = RAW_DIR / "academy_scraped.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "cleaned_speeches.csv"

# Regex for the Year column in Kaggle data, e.g. "2016 (89th) Academy Awards"
_YEAR_RE = re.compile(r"^(\d{4})\s+\((\d+)(?:st|nd|rd|th)\)")

# Regex for parenthetical notes in the Winner field
_PAREN_NOTE_RE = re.compile(r"\s*\(.*?\)\s*$")

# Regex for the "WINNER NAME:\n" header that starts many speeches
_SPEECH_HEADER_RE = re.compile(r"^\s*[A-Z][A-Z\s.''\-]+:\s*\n?")


# ---------------------------------------------------------------------------
# Kaggle source
# ---------------------------------------------------------------------------

def load_kaggle(path: Path = KAGGLE_PATH) -> pd.DataFrame:
    """Load and clean the Kaggle CSV into the standard schema."""
    if not path.exists():
        return pd.DataFrame(columns=OUTPUT_COLUMNS + ["_source"])

    df = pd.read_csv(path)
    df = df.dropna(how="all")

    # Parse year/ceremony from formatted string
    years, ceremonies = [], []
    for val in df["Year"]:
        m = _YEAR_RE.match(str(val))
        if m:
            years.append(int(m.group(1)))
            ceremonies.append(int(m.group(2)))
        else:
            years.append(None)
            ceremonies.append(None)
    df["year"] = pd.array(years, dtype=pd.Int64Dtype())
    df["ceremony"] = pd.array(ceremonies, dtype=pd.Int64Dtype())

    # Normalize categories
    df["category"] = df["Category"].map(TARGET_CATEGORIES)
    df = df.dropna(subset=["category"])

    # Filter by year
    df = df[df["year"] >= MIN_YEAR]

    # Clean winner names
    df["winner_raw"] = df["Winner"].astype(str).str.strip()
    df["winner_clean"] = df["winner_raw"].apply(
        lambda s: _PAREN_NOTE_RE.sub("", s).strip()
    )

    # Clean speeches
    df["speech_clean"] = (
        df["Speech"].astype(str).str.strip()
        .apply(lambda s: _SPEECH_HEADER_RE.sub("", s).strip())
    )

    # Film title
    df["film_title"] = df["Film Title"]

    df["_source"] = "kaggle"
    return df[OUTPUT_COLUMNS + ["_source"]]


# ---------------------------------------------------------------------------
# Academy (scraped) source
# ---------------------------------------------------------------------------

def load_academy(path: Path = ACADEMY_PATH) -> pd.DataFrame:
    """Load and clean the scraped Academy CSV into the standard schema."""
    if not path.exists():
        return pd.DataFrame(columns=OUTPUT_COLUMNS + ["_source"])

    df = pd.read_csv(path)
    df = df.dropna(how="all")

    # year and ceremony are already numeric from the scraper
    df["year"] = pd.array(df["year"], dtype=pd.Int64Dtype())
    df["ceremony"] = pd.array(df["ceremony"], dtype=pd.Int64Dtype())

    # Normalize categories (scraper stores raw category strings)
    df["category"] = df["category"].map(TARGET_CATEGORIES)
    df = df.dropna(subset=["category"])

    # Filter by year
    df = df[df["year"] >= MIN_YEAR]

    # Clean winner names
    df["winner_raw"] = df["winner"].astype(str).str.strip()
    df["winner_clean"] = df["winner_raw"].apply(
        lambda s: _PAREN_NOTE_RE.sub("", s).strip()
    )

    # Clean speeches — remove the "WINNER NAME:\n" header
    df["speech_clean"] = (
        df["speech"].astype(str).str.strip()
        .apply(lambda s: _SPEECH_HEADER_RE.sub("", s).strip())
    )

    # Film title
    df["film_title"] = df["film_title"].astype(str).str.strip()

    df["_source"] = "academy"
    return df[OUTPUT_COLUMNS + ["_source"]]


# ---------------------------------------------------------------------------
# Merge & deduplicate
# ---------------------------------------------------------------------------

def merge_sources(kaggle: pd.DataFrame, academy: pd.DataFrame) -> pd.DataFrame:
    """Merge both sources, preferring academy on (year, category) duplicates."""
    combined = pd.concat([academy, kaggle], ignore_index=True)

    # Drop duplicates on (year, category), keeping first = academy (concat order)
    before = len(combined)
    combined = combined.drop_duplicates(subset=["year", "category"], keep="first")
    dupes = before - len(combined)
    if dupes:
        print(f"Deduplication: removed {dupes} Kaggle rows that overlap with Academy data")

    # Drop the source column, sort, and reset index
    combined = combined.drop(columns=["_source"])
    combined = combined.sort_values(["year", "category"]).reset_index(drop=True)
    return combined


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(out_path: Path = OUT_PATH) -> pd.DataFrame:
    """Run the full cleaning pipeline and write to CSV."""
    print("Loading Kaggle data...")
    kaggle = load_kaggle()
    print(f"  {len(kaggle)} rows from Kaggle")

    print("Loading Academy data...")
    academy = load_academy()
    print(f"  {len(academy)} rows from Academy")

    df = merge_sources(kaggle, academy)

    # Write output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\nWrote {len(df)} rows to {out_path}")

    # Verification
    print("\n--- Verification ---")
    print(f"Unique categories ({len(df['category'].unique())}): {sorted(df['category'].unique())}")
    print(f"Year range: {df['year'].min()} – {df['year'].max()}")
    nulls = df[["year", "category", "winner_clean", "speech_clean"]].isnull().sum()
    print(f"Null counts in key columns:\n{nulls}")
    dupes = df.duplicated(subset=["year", "category"], keep=False)
    print(f"Duplicate (year, category) pairs: {dupes.sum()}")
    print(f"\nSample rows:\n{df.head(3).to_string()}")

    return df


if __name__ == "__main__":
    run_pipeline()
