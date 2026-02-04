"""Scrape acceptance speeches from aaspeechesdb.oscars.org using Playwright.

Usage:
    python scripts/scrape_academy.py
    python scripts/scrape_academy.py --start-year 2020 --end-year 2020

Requires: pip install playwright && playwright install chromium
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "academy_scraped.csv"

# URL template: returns all results for a given year on one page (NP=255)
SEARCH_URL = (
    "https://aaspeechesdb.oscars.org/results.aspx"
    "?QY=find%20(year%20term%20ct%20{year})"
    "&AC=QBE_QUERY&RF=WebReportList&DF=WebReportOscars&MR=0&NP=255"
)

# Ceremony number = year - 1927 (e.g. 2020 -> 93rd)
def year_to_ceremony(year: int) -> int:
    return year - 1927


def parse_results_list(html: str) -> list[dict]:
    """Parse the results list page to get basic info for each record.

    Each result looks like one of:
      <a href="javascript:ExpandRecord(N);">Category</a> -- <i>Film</i>; Winner
      <a href="javascript:ExpandRecord(N);">Category</a> -- <i>Film</i>
      <a href="javascript:ExpandRecord(N);">Category</a> -- Winner (no film italic)
    """
    # Pattern with film title and optional winner
    pattern = re.compile(
        r'ExpandRecord\((\d+)\);">'
        r'([^<]+)'                # category
        r'</a>\s*--\s*'
        r'(?:<i>([^<]+)</i>)?'    # optional film title in <i>
        r'(?:;\s*)?'              # optional semicolon separator
        r'(.*?)'                  # winner (may be empty)
        r'</p>',
        re.DOTALL,
    )
    results = []
    for m in pattern.finditer(html):
        film = (m.group(3) or "").strip()
        winner = m.group(4).strip()
        # If no film in <i>, the text after -- is the winner
        if not film and winner:
            # Check if there's untagged text that's actually the winner
            pass
        results.append({
            "record_num": int(m.group(1)),
            "category": m.group(2).strip(),
            "film_title": film,
            "winner": winner,
        })
    return results


def extract_speech_text(page: Page) -> str | None:
    """Extract speech text from an expanded record.

    The speech is inside a <p class="MInormal"> tag within a <font> block.
    The text uses <br> tags for line breaks.
    """
    el = page.query_selector("p.MInormal")
    if not el:
        return None

    # Get inner HTML and convert <br> to newlines
    inner = el.inner_html()
    # Remove the "WINNER NAME:" header at the start
    text = re.sub(r"<br\s*/?>", "\n", inner, flags=re.IGNORECASE)
    # Strip all remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Clean up whitespace
    text = text.strip()

    # Skip if empty or just the winner header
    if not text or len(text) < 20:
        return None

    return text


def scrape_year(page: Page, year: int) -> list[dict]:
    """Scrape all speeches for a given year. Returns list of row dicts."""
    url = SEARCH_URL.format(year=year)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)

    html = page.content()

    # Get record count
    count_match = re.search(r"(\d+)\s+records?\s+found", html, re.IGNORECASE)
    if not count_match:
        print(f"  {year}: No records found on page, skipping")
        return []

    num_records = int(count_match.group(1))
    print(f"  {year}: {num_records} records found")

    # Parse the results list for category/film/winner info
    results = parse_results_list(html)
    print(f"  {year}: parsed {len(results)} result entries")

    ceremony = year_to_ceremony(year)
    rows = []

    for info in results:
        n = info["record_num"]
        try:
            # Expand record to get speech text
            page.evaluate(f"ExpandRecord({n})")
            time.sleep(2)
            page.wait_for_load_state("domcontentloaded")

            speech = extract_speech_text(page)

            if speech:
                row = {
                    "year": year,
                    "ceremony": ceremony,
                    "category": info["category"],
                    "film_title": info["film_title"],
                    "winner": info["winner"],
                    "speech": speech,
                }
                rows.append(row)
                print(f"    [{n}/{num_records}] {info['category']} - {info['winner']} ({len(speech)} chars)")
            else:
                print(f"    [{n}/{num_records}] {info['category']} - {info['winner']} (no speech)")

            # Go back to results list
            page.go_back(wait_until="domcontentloaded", timeout=30000)
            time.sleep(1.5)

        except Exception as e:
            print(f"    [{n}/{num_records}] ERROR: {e}")
            # Try to recover by navigating back to the results page
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
            except Exception:
                pass

    return rows


def save_rows(rows: list[dict], path: Path) -> None:
    """Write scraped rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["year", "ceremony", "category", "film_title", "winner", "speech"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} rows to {path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape Academy Awards speeches")
    parser.add_argument("--start-year", type=int, default=2017)
    parser.add_argument("--end-year", type=int, default=2024)
    args = parser.parse_args()

    all_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for year in range(args.start_year, args.end_year + 1):
            print(f"\nScraping {year}...")
            rows = scrape_year(page, year)
            all_rows.extend(rows)
            print(f"  Got {len(rows)} speeches for {year}")
            time.sleep(2)  # Be polite between years

        browser.close()

    save_rows(all_rows, OUT_PATH)


if __name__ == "__main__":
    main()
