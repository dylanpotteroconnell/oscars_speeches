"""Incremental LLM labeling pipeline for Oscar speeches.

Reads cleaned_speeches.csv, calls Gemini to label speeches using prompt
templates from the prompts/ directory, and stores results in labels.csv.

Each task (e.g. distinctiveness) has:
  - A markdown prompt template in prompts/{task}.md
  - A parser entry in PARSERS

Usage:
    python scripts/label_speeches.py
"""

from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai

from config import LABELS_KEY_COLUMNS, TASKS, TASK_DEPENDENCIES

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# Default (production) paths; overridden by --test flag.
SPEECHES_PATH = PROJECT_ROOT / "data" / "cleaned_speeches.csv"
LABELS_PATH = PROJECT_ROOT / "data" / "labels.csv"
MERGED_PATH = PROJECT_ROOT / "data" / "speeches_with_labels.csv"

TEST_SPEECHES_PATH = PROJECT_ROOT / "data" / "test_speeches.csv"
TEST_LABELS_PATH = PROJECT_ROOT / "data" / "test_labels.csv"
TEST_MERGED_PATH = PROJECT_ROOT / "data" / "test_speeches_with_labels.csv"


# --- API setup ---

def init_gemini() -> genai.Client:
    """Load API key from .env and return configured client."""
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to .env")
    return genai.Client(api_key=api_key)


MODEL_NAME = "gemini-2.0-flash"


# --- Data loading ---

def load_existing_labels(path: Path = LABELS_PATH) -> pd.DataFrame:
    """Load existing labels or create empty DataFrame with key columns."""
    if path.exists():
        df = pd.read_csv(path)
        print(f"Loaded {len(df)} existing labels from {path.name}")
        return df
    print("No existing labels file; starting fresh.")
    return pd.DataFrame(columns=LABELS_KEY_COLUMNS)


def find_unlabeled(
    speeches: pd.DataFrame,
    labels: pd.DataFrame,
    label_name: str,
) -> pd.DataFrame:
    """Return speech rows that don't have a value for label_name."""
    merged = speeches.merge(labels, on=LABELS_KEY_COLUMNS, how="left")
    if label_name not in merged.columns:
        return speeches.copy()
    mask = merged[label_name].isna()
    unlabeled = speeches.loc[mask].reset_index(drop=True)
    print(f"Found {len(unlabeled)} rows needing '{label_name}' label "
          f"(out of {len(speeches)} total)")
    return unlabeled


# --- Prompt loading ---

def load_prompt(task_name: str) -> str:
    """Load a prompt template from prompts/{task_name}.md."""
    path = PROMPTS_DIR / f"{task_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def build_prompt(task_name: str, row: pd.Series) -> str:
    """Load prompt template and fill placeholders from row columns.

    The row may include columns from prior labels (merged in by the pipeline)
    so that downstream tasks can reference earlier outputs.
    """
    template = load_prompt(task_name)
    return template.format(**row.to_dict())


# --- Response parsers ---

REDACT_PATTERN = re.compile(r"\[REDACT:\s*(.*?)\]")


def parse_int_score(text: str) -> int | None:
    """Parse a single integer 1-5 from model response."""
    text = text.strip()
    try:
        score = int(text)
        if 1 <= score <= 5:
            return score
        print(f"  Score out of range: {score}")
        return None
    except ValueError:
        print(f"  Could not parse score from: {text!r}")
        return None


def parse_text(text: str) -> str | None:
    """Return stripped text, or None if empty."""
    text = text.strip()
    return text if text else None


def parse_redacted_speech(text: str) -> str | None:
    """Return the redacted speech text. Speeches with no redactions are valid."""
    text = text.strip()
    return text if text else None


def parse_quoted_sentence(text: str) -> str | None:
    """Extract a quoted sentence from the response."""
    text = text.strip().strip('"').strip("'").strip()
    return text if text else None


# --- Redaction utilities (for downstream use) ---

def render_redacted(marked_up: str) -> str:
    """Replace [REDACT: ...] with blanks for display."""
    return REDACT_PATTERN.sub("______", marked_up)


def extract_redactions(marked_up: str) -> list[str]:
    """Pull out the list of redacted strings in order."""
    return REDACT_PATTERN.findall(marked_up)


# Map task names to their response parsers.
PARSERS: dict[str, callable] = {
    "distinctiveness": parse_int_score,
    "redaction": parse_redacted_speech,
    "plot_hint": parse_quoted_sentence,
    "snippet_selection": parse_text,
    "snippet_grading": parse_int_score,
}

# Map task names to the label column they produce (when it differs from the
# task name).  Tasks not listed here store into a column named after the task.
TASK_LABEL_COLUMNS: dict[str, str] = {
    "redaction": "redacted_speech",
    "snippet_selection": "golden_snippet",
}


# --- Gemini call ---

def call_gemini(client: genai.Client, prompt: str) -> str | None:
    """Send prompt to Gemini and return raw response text."""
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"  API error: {e}")
        return None


# --- Generic labeling ---

def label_task(
    client: genai.Client,
    unlabeled: pd.DataFrame,
    task_name: str,
    delay: float = 0.5,
) -> pd.DataFrame:
    """Label all unlabeled rows for a given task. Returns new labels."""
    parser = PARSERS[task_name]
    col = TASK_LABEL_COLUMNS.get(task_name, task_name)
    results = []
    for i, (_, row) in enumerate(unlabeled.iterrows()):
        print(f"  [{i + 1}/{len(unlabeled)}] {row['year']} {row['category']}: "
              f"{row['winner_clean'][:30]}...")
        raw = call_gemini(client, build_prompt(task_name, row))
        if raw is not None:
            parsed = parser(raw)
            if parsed is not None:
                results.append({
                    "year": row["year"],
                    "category": row["category"],
                    col: parsed,
                })
        if delay > 0:
            time.sleep(delay)
    new_labels = pd.DataFrame(results)
    print(f"Successfully labeled {len(new_labels)} / {len(unlabeled)} rows")
    return new_labels


# --- Persistence ---

def save_labels(
    existing: pd.DataFrame,
    new_labels: pd.DataFrame,
    path: Path = LABELS_PATH,
) -> pd.DataFrame:
    """Merge new label columns into existing labels and save.

    Uses a left join so that new_labels only fills in its own columns
    without clobbering other label columns already present in existing.
    """
    if new_labels.empty:
        print("No new labels to save.")
        return existing

    # Columns being added/updated by this task
    new_cols = [c for c in new_labels.columns if c not in LABELS_KEY_COLUMNS]

    if existing.empty:
        combined = new_labels.copy()
    else:
        # Update existing labels with new values.  Set key columns as index so
        # combine_first aligns rows correctly, then new_labels values take
        # priority over existing values for the same (year, category, column).
        existing_ix = existing.set_index(LABELS_KEY_COLUMNS)
        new_ix = new_labels.set_index(LABELS_KEY_COLUMNS)
        combined = new_ix.combine_first(existing_ix).reset_index()

    combined = combined.sort_values(LABELS_KEY_COLUMNS).reset_index(drop=True)
    combined.to_csv(path, index=False)
    print(f"Saved {len(combined)} labels ({len(combined.columns) - len(LABELS_KEY_COLUMNS)} label columns) to {path.name}")
    return combined


def merge_for_output(
    speeches: pd.DataFrame,
    labels: pd.DataFrame,
    path: Path = MERGED_PATH,
) -> pd.DataFrame:
    """Left-join labels onto speeches and write merged output."""
    merged = speeches.merge(labels, on=LABELS_KEY_COLUMNS, how="left")
    merged.to_csv(path, index=False)
    print(f"Wrote merged output ({len(merged)} rows) to {path.name}")
    return merged


# --- Pipeline ---

def run_pipeline(test: bool = False) -> pd.DataFrame:
    """Run the full incremental labeling pipeline."""
    if test:
        speeches_path, labels_path, merged_path = (
            TEST_SPEECHES_PATH, TEST_LABELS_PATH, TEST_MERGED_PATH)
        print("=== TEST MODE (20-speech subset) ===")
    else:
        speeches_path, labels_path, merged_path = (
            SPEECHES_PATH, LABELS_PATH, MERGED_PATH)

    speeches = pd.read_csv(speeches_path)
    print(f"Loaded {len(speeches)} speeches from {speeches_path.name}")

    labels = load_existing_labels(labels_path)
    client = init_gemini()

    for task_name in TASKS:
        if task_name not in PARSERS:
            print(f"Skipping unknown task '{task_name}' (no parser registered)")
            continue

        col = TASK_LABEL_COLUMNS.get(task_name, task_name)
        unlabeled = find_unlabeled(speeches, labels, col)

        if unlabeled.empty:
            print(f"All rows already labeled for '{task_name}'.")
            continue

        # Merge any prior labels that this task depends on into the rows
        # so the prompt template can reference them (e.g. {redacted_speech}).
        deps = TASK_DEPENDENCIES.get(task_name, [])
        if deps:
            missing = [d for d in deps if d not in labels.columns]
            if missing:
                print(f"Skipping '{task_name}': missing dependency columns {missing}")
                continue
            unlabeled = unlabeled.merge(
                labels[LABELS_KEY_COLUMNS + deps],
                on=LABELS_KEY_COLUMNS,
                how="left",
            )

        new_labels = label_task(client, unlabeled, task_name)
        labels = save_labels(labels, new_labels, labels_path)

    # Produce merged output
    merged = merge_for_output(speeches, labels, merged_path)

    # Verification
    print("\n--- Verification ---")
    for task_name in TASKS:
        col = TASK_LABEL_COLUMNS.get(task_name, task_name)
        if col in merged.columns:
            coverage = merged[col].notna().sum()
            print(f"'{task_name}' ({col}) coverage: {coverage} / {len(merged)}")
            if merged[col].dtype in ("int64", "float64"):
                print(f"  Distribution:\n{merged[col].value_counts().sort_index()}")
            else:
                print(f"  (text column — {coverage} non-null values)")

    return merged


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM labeling pipeline")
    parser.add_argument("--test", action="store_true",
                        help="Run on 20-speech test subset instead of full dataset")
    args = parser.parse_args()
    run_pipeline(test=args.test)
