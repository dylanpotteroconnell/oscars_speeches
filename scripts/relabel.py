"""Re-run a specific labeling task for a specific speech.

Usage:
    python relabel.py --film "lord of the rings" --task plot_hint --test
    python relabel.py --film "lord of the rings" --task plot_hint --test \
        --note "Focus on the fantasy quest, not workplace metaphors"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import LABELS_KEY_COLUMNS, TASK_DEPENDENCIES
from label_speeches import (
    PARSERS,
    TASK_LABEL_COLUMNS,
    build_prompt,
    call_gemini,
    init_gemini,
    load_existing_labels,
    merge_for_output,
    save_labels,
    PROJECT_ROOT,
    SPEECHES_PATH,
    LABELS_PATH,
    MERGED_PATH,
    TEST_SPEECHES_PATH,
    TEST_LABELS_PATH,
    TEST_MERGED_PATH,
)


def find_speech(speeches: pd.DataFrame, film_query: str, category_query: str | None = None) -> pd.Series:
    """Find a single speech row by case-insensitive substring match on film_title."""
    mask = speeches["film_title"].str.lower().str.contains(film_query.lower(), na=False)
    if category_query:
        mask &= speeches["category"].str.lower().str.contains(category_query.lower(), na=False)
    matches = speeches[mask]
    if len(matches) == 0:
        raise SystemExit(f"No speeches found matching '{film_query}'"
                         + (f" with category '{category_query}'" if category_query else ""))
    if len(matches) > 1:
        lines = [f"  {r['year']} | {r['category']} | {r['film_title']} | {r['winner_clean']}"
                 for _, r in matches.iterrows()]
        raise SystemExit(
            f"Multiple speeches match '{film_query}':\n" + "\n".join(lines)
            + "\nUse --category to narrow your search."
        )
    return matches.iloc[0]


def relabel(film_query: str, task_name: str, note: str | None, override: str | None, category_query: str | None, test: bool) -> None:
    """Re-run a labeling task for a single speech."""
    if task_name not in PARSERS:
        raise SystemExit(f"Unknown task '{task_name}'. Available: {list(PARSERS)}")

    # Resolve paths
    if test:
        speeches_path, labels_path, merged_path = (
            TEST_SPEECHES_PATH, TEST_LABELS_PATH, TEST_MERGED_PATH)
        print("=== TEST MODE ===")
    else:
        speeches_path, labels_path, merged_path = (
            SPEECHES_PATH, LABELS_PATH, MERGED_PATH)

    # Load data
    speeches = pd.read_csv(speeches_path)
    labels = load_existing_labels(labels_path)

    # Find the speech
    row = find_speech(speeches, film_query, category_query)
    year, category = row["year"], row["category"]
    col = TASK_LABEL_COLUMNS.get(task_name, task_name)
    print(f"Match: {year} | {category} | {row['film_title']} | {row['winner_clean']}")

    # Get old value
    label_mask = (labels["year"] == year) & (labels["category"] == category)
    old_value = None
    if label_mask.any() and col in labels.columns:
        old_value = labels.loc[label_mask, col].iloc[0]
    print(f"Old {col}: {old_value}")

    # Clear the label for this row
    if label_mask.any() and col in labels.columns:
        labels.loc[label_mask, col] = pd.NA

    # Build prompt row — merge dependency columns from labels if needed
    prompt_row = row.copy()
    deps = TASK_DEPENDENCIES.get(task_name, [])
    if deps and label_mask.any():
        for dep_col in deps:
            if dep_col in labels.columns:
                prompt_row[dep_col] = labels.loc[label_mask, dep_col].iloc[0]

    if override:
        # Skip LLM entirely — use the provided value directly
        new_value = override
        print(f"Using manual override for '{task_name}'")
    else:
        prompt = build_prompt(task_name, prompt_row)
        if note:
            prompt += f"\n\nNote from reviewer: {note}"

        # Call Gemini
        client = init_gemini()
        print(f"Calling Gemini for task '{task_name}'...")
        raw = call_gemini(client, prompt)
        if raw is None:
            raise SystemExit("API call failed.")

        parser = PARSERS[task_name]
        new_value = parser(raw)
        if new_value is None:
            raise SystemExit(f"Could not parse response: {raw!r}")

    # Save updated label
    new_label = pd.DataFrame([{
        "year": year,
        "category": category,
        col: new_value,
    }])
    labels = save_labels(labels, new_label, labels_path)

    # Re-export merged CSV
    merge_for_output(speeches, labels, merged_path)

    # Print confirmation
    print(f"\n--- Result ---")
    print(f"Old {col}: {old_value}")
    print(f"New {col}: {new_value}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Re-run a labeling task for a specific speech")
    parser.add_argument("--film", required=True,
                        help="Case-insensitive substring match on film_title")
    parser.add_argument("--task", required=True,
                        help=f"Labeling task to re-run. Options: {list(PARSERS)}")
    parser.add_argument("--note",
                        help="Optional correction note appended to the prompt")
    parser.add_argument("--override",
                        help="Skip LLM — directly set the label to this value")
    parser.add_argument("--category",
                        help="Case-insensitive substring filter on category (e.g. 'directing')")
    parser.add_argument("--test", action="store_true",
                        help="Use test subset files")
    args = parser.parse_args()
    relabel(args.film, args.task, args.note, args.override, args.category, args.test)
