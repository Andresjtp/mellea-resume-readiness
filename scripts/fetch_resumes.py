"""Download the Hugging Face resume dataset and save it as data/resumes.json."""

from __future__ import annotations

import csv
import io
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATASET_URL = "https://huggingface.co/datasets/Sachinkelenjaguri/Resume_dataset"
CSV_URL = f"{DATASET_URL}/resolve/main/UpdatedResumeDataSet.csv"  # direct link to the raw CSV file
# Paths are based on this file's location, so the script works from any folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = PROJECT_ROOT / "data" / "resumes.json"


def fix_encoding(text: str) -> str:
    """Repair UTF-8 text that was mis-decoded as Latin-1 in the source (e.g. "NaÃ¯ve" -> "Naïve")."""
    try:
        return text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text


def main() -> int:
    """Download, convert, and save the resumes. Returns the exit code: 0 = success, 1 = download failed."""
    try:
        with urllib.request.urlopen(CSV_URL, timeout=60) as resp:
            text = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"Hugging Face download failed: {e}", file=sys.stderr)
        return 1

    # Each CSV row has a "Category" and a "Resume" column; keep both, with the text repaired.
    resumes = [
        {"category": row["Category"], "resume": fix_encoding(row["Resume"])}
        for row in csv.DictReader(io.StringIO(text, newline=""))
    ]

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": DATASET_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(resumes),
        "resumes": resumes,
    }
    OUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(resumes)} resumes to {OUT_FILE.relative_to(PROJECT_ROOT)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
