"""Shared constants for the Oscars speeches pipeline."""

MIN_YEAR = 1993

# Map raw category strings to canonical names.
# Any category not listed here will be dropped.
TARGET_CATEGORIES: dict[str, str] = {
    # Best Picture
    "Best Picture": "Best Picture",
    "Best Motion Picture": "Best Picture",
    "Outstanding Motion Picture": "Best Picture",
    # Directing
    "Directing": "Directing",
    # Lead acting
    "Actor in a Leading Role": "Actor in a Leading Role",
    "Actor": "Actor in a Leading Role",
    "Actress in a Leading Role": "Actress in a Leading Role",
    "Actress": "Actress in a Leading Role",
    # Supporting acting
    "Actor in a Supporting Role": "Actor in a Supporting Role",
    "Actress in a Supporting Role": "Actress in a Supporting Role",
    # Writing – Original
    "Writing (Original Screenplay)": "Writing (Original Screenplay)",
    "Writing (Screenplay Written Directly for the Screen)": "Writing (Original Screenplay)",
    "Writing (Story and Screenplay--written directly for the screen)": "Writing (Original Screenplay)",
    "Writing (Story and Screenplay)": "Writing (Original Screenplay)",
    # Writing – Adapted
    "Writing (Adapted Screenplay)": "Writing (Adapted Screenplay)",
    "Writing (Screenplay Based on Material Previously Produced or Published)": "Writing (Adapted Screenplay)",
    "Writing (Screenplay--based on material from another medium)": "Writing (Adapted Screenplay)",
    "Writing (Screenplay Based on Material from Another Medium)": "Writing (Adapted Screenplay)",
    "Writing (Screenplay Adapted from Other Material)": "Writing (Adapted Screenplay)",
}

# --- Labeling pipeline ---

# Labeling tasks, in execution order.  Each entry corresponds to a
# prompts/{task}.md file and a parser in label_speeches.py.  Tasks later
# in the list may depend
# on labels produced by earlier tasks (e.g. snippet_selection needs
# redacted_speech from the redaction task).
TASKS: list[str] = [
    "distinctiveness",
    "redaction",
    "plot_hint",
    # These depend on earlier tasks' output — see TASK_DEPENDENCIES:
    "snippet_selection",   # needs redacted_speech from redaction
    "snippet_grading",     # needs golden_snippet from snippet_selection
]

# Maps a task to the label columns it needs from previous tasks.
# Used by the pipeline to merge prior labels into the row before prompting.
TASK_DEPENDENCIES: dict[str, list[str]] = {
    "snippet_selection": ["redacted_speech"],
    "snippet_grading": ["golden_snippet"],
}

# Composite key used to join speeches with labels
LABELS_KEY_COLUMNS = ["year", "category"]

# Canonical category names (for validation)
CANONICAL_CATEGORIES = sorted(set(TARGET_CATEGORIES.values()))

# Column names for output
OUTPUT_COLUMNS = [
    "year",
    "ceremony",
    "category",
    "film_title",
    "winner_raw",
    "winner_clean",
    "speech_clean",
]
