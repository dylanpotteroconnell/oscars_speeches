"""Export labeled speeches as JSON for the game UI.

Reads the merged speeches-with-labels CSV, filters to speeches with
snippet_grading >= 3, and writes game/data.json.

Usage:
    python scripts/export_game_data.py          # full dataset
    python scripts/export_game_data.py --test   # test subset
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MERGED_PATH = PROJECT_ROOT / "data" / "speeches_with_labels.csv"
TEST_MERGED_PATH = PROJECT_ROOT / "data" / "test_speeches_with_labels.csv"
CLEANED_PATH = PROJECT_ROOT / "data" / "cleaned_speeches.csv"
OUTPUT_PATH = PROJECT_ROOT / "game" / "data.json"

REDACT_PATTERN = re.compile(r"\[REDACT:\s*(.*?)\]")

MIN_SNIPPET_GRADE = 3


def render_redacted(marked_up: str) -> str:
    """Replace [REDACT: ...] with blanks for display."""
    return REDACT_PATTERN.sub("______", marked_up)


def extract_redactions(marked_up: str) -> list[str]:
    """Pull out the list of redacted strings in order."""
    return REDACT_PATTERN.findall(marked_up)


def _safe(value):
    """Convert pandas NaN/NaT to None for JSON serialisation."""
    if isinstance(value, float) and pd.isna(value):
        return None
    if pd.isna(value):
        return None
    return value


def strip_outer_quotes(text: str) -> str:
    """Remove wrapping triple-quotes or single-quotes left by the LLM."""
    text = text.strip()
    for q in ['"""', "'''", '"', "'"]:
        if text.startswith(q) and text.endswith(q) and len(text) > len(q) * 2:
            text = text[len(q):-len(q)].strip()
    return text


def _sample_titles(pool: pd.DataFrame, n: int, exclude: set[str],
                    year: int | None = None, year_range: int = 5) -> list[str]:
    """Sample up to *n* unique film titles from *pool*, excluding *exclude*.

    If *year* is given, prefer films within ±year_range first; if not enough,
    widen to the full pool.
    """
    candidates = pool[~pool["film_title"].isin(exclude)]
    if year is not None:
        nearby = candidates[(candidates["year"] >= year - year_range) &
                            (candidates["year"] <= year + year_range)]
        nearby_titles = nearby["film_title"].unique().tolist()
        if len(nearby_titles) >= n:
            return random.sample(nearby_titles, n)
        # Not enough nearby — take what we can, fill from the rest
        remaining = n - len(nearby_titles)
        far = candidates[~candidates["film_title"].isin(set(nearby_titles))]
        far_titles = far["film_title"].unique().tolist()
        return nearby_titles + random.sample(far_titles, min(remaining, len(far_titles)))
    titles = candidates["film_title"].unique().tolist()
    return random.sample(titles, min(n, len(titles)))


def pick_film_options(pool: pd.DataFrame, row: pd.Series) -> list[str]:
    """Return 6 shuffled film titles: 3 same-category cluster + 3 decoy cluster.

    *pool* is the full cleaned_speeches DataFrame (all 134 rows).
    """
    correct_film = row["film_title"]
    category = row["category"]
    year = int(row["year"])

    used: set[str] = {correct_film}

    # --- Same-category cluster: correct film + 2 others from same category ---
    same_cat = pool[pool["category"] == category]
    same_picks = _sample_titles(same_cat, 2, exclude=used, year=year)
    used.update(same_picks)
    same_cluster = [correct_film] + same_picks

    # --- Decoy cluster: 1 film from different category, then 2 from *that* film's category ---
    diff_cat = pool[pool["category"] != category]
    seed_picks = _sample_titles(diff_cat, 1, exclude=used, year=year)
    if not seed_picks:
        # Extreme fallback: just grab anything not used
        seed_picks = _sample_titles(pool, 1, exclude=used)
    if seed_picks:
        seed_film = seed_picks[0]
        used.add(seed_film)
        seed_row = pool[pool["film_title"] == seed_film].iloc[0]
        seed_cat = pool[pool["category"] == seed_row["category"]]
        decoy_peers = _sample_titles(seed_cat, 2, exclude=used,
                                     year=int(seed_row["year"]))
        used.update(decoy_peers)
        decoy_cluster = [seed_film] + decoy_peers
    else:
        decoy_cluster = []

    # --- Combine and pad if needed ---
    options = same_cluster + decoy_cluster
    if len(options) < 6:
        extra = _sample_titles(pool, 6 - len(options), exclude=set(options))
        options.extend(extra)

    random.shuffle(options)
    return options


def build_game_data(df: pd.DataFrame, pool: pd.DataFrame) -> dict:
    """Build the JSON structure for the game."""
    # Filter to rows with good snippets
    df = df[df["snippet_grading"] >= MIN_SNIPPET_GRADE].copy()
    df = df.reset_index(drop=True)
    print(f"Filtered to {len(df)} speeches with snippet_grading >= {MIN_SNIPPET_GRADE}")

    speeches = []
    for i, row in df.iterrows():
        golden_snippet = strip_outer_quotes(str(row["golden_snippet"]))
        redacted_speech = strip_outer_quotes(str(row["redacted_speech"]))
        speech_clean = str(row["speech_clean"])

        speeches.append({
            "id": int(i),
            "year": int(row["year"]),
            "category": row["category"],
            "film_title": row["film_title"],
            "winner_clean": row["winner_clean"],
            "golden_snippet": golden_snippet,
            "snippet_display": render_redacted(golden_snippet),
            "redactions": extract_redactions(golden_snippet),
            "full_speech_display": render_redacted(redacted_speech),
            "full_speech_raw": speech_clean,
            "plot_hint": _safe(row["plot_hint"]),
            "snippet_grading": int(row["snippet_grading"]),
            "film_options": pick_film_options(pool, row),
        })

    categories = sorted(df["category"].unique().tolist())

    return {
        "speeches": speeches,
        "categories": categories,
    }


def main():
    parser = argparse.ArgumentParser(description="Export game data as JSON")
    parser.add_argument("--test", action="store_true",
                        help="Use test subset instead of full dataset")
    args = parser.parse_args()

    input_path = TEST_MERGED_PATH if args.test else MERGED_PATH
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows from {input_path.name}")

    pool = pd.read_csv(CLEANED_PATH)
    print(f"Loaded {len(pool)} rows from {CLEANED_PATH.name} as decoy pool")

    game_data = build_game_data(df, pool)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(game_data, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(game_data['speeches'])} speeches to {OUTPUT_PATH}")
    print(f"Categories: {game_data['categories']}")


if __name__ == "__main__":
    main()
