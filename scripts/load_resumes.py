"""Load the sample resumes from data/resumes.json, or browse them from the command line."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "resumes.json"
PREVIEW_CHARS = 60  # how much resume text each one-line summary shows
SEPARATOR = "-" * 80  # between a resume's header and its text
RESUME_BREAK = "=" * 80  # between resumes


def load_resumes(path: Path | str | None = None) -> list[dict]:
    """Load resumes from data/resumes.json (or `path`) as [{"category", "resume"}, ...]."""
    file = Path(path) if path is not None else DATA_FILE
    if not file.is_file():
        raise FileNotFoundError(f"{file} not found; run `uv run scripts/fetch_resumes.py` first")

    payload = json.loads(file.read_text(encoding="utf-8"))
    resumes = payload.get("resumes") if isinstance(payload, dict) else None
    if not isinstance(resumes, list):
        raise ValueError(f"{file} has no \"resumes\" list")
    return resumes


def category_counts(resumes: list[dict]) -> Counter[str]:
    """Count how many resumes are in each category."""
    return Counter(r["category"] for r in resumes)


def format_category_counts(counts: Counter[str]) -> str:
    """Turn category counts into an alphabetical list with the numbers lined up."""
    width = max(map(len, counts), default=0)
    lines = [f"  {name:<{width}}  {n}" for name, n in sorted(counts.items())]
    return "\n".join([f"{len(counts)} categories:", *lines])


def non_negative_int(value: str) -> int:
    """Argument type that only accepts whole numbers of 0 or more."""
    n = int(value)
    if n < 0:
        raise argparse.ArgumentTypeError(f"must be >= 0, got {n}")
    return n


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Browse the sample resumes in data/resumes.json.")
    parser.add_argument("--category", metavar="NAME", help="only this category (case-insensitive)")
    parser.add_argument("--search", metavar="TEXT", help="only resumes containing TEXT (case-insensitive)")
    parser.add_argument("--unique", action="store_true", help="drop duplicate resume texts, keeping the first")
    parser.add_argument("--limit", type=non_negative_int, metavar="N", help="show at most N resumes")
    parser.add_argument("--index", type=non_negative_int, metavar="I", help="show only resume #I (index in the file)")
    parser.add_argument("--full", action="store_true", help="print the complete resume text")
    parser.add_argument(
        "--max-chars", type=non_negative_int, default=0, metavar="N",
        help="with --full, truncate each resume to N chars (default 0 = no limit)",
    )
    parser.add_argument("--list-categories", action="store_true", help="print category counts and exit")
    return parser.parse_args(argv)


def select(resumes: list[dict], args: argparse.Namespace) -> list[tuple[int, dict]]:
    """Apply the narrowing flags, keeping each resume's original file index."""
    # Pair each resume with its position in the file, e.g. (0, resume), (1, resume), ...
    selected = list(enumerate(resumes))

    # Each filter keeps only the resumes that pass it, so the flags combine.
    # casefold() lowercases text so matching ignores upper/lower case.
    if args.index is not None:
        selected = [(i, r) for i, r in selected if i == args.index]
    if args.category is not None:
        wanted = args.category.casefold()
        selected = [(i, r) for i, r in selected if r["category"].casefold() == wanted]
    if args.search is not None:
        needle = args.search.casefold()
        selected = [(i, r) for i, r in selected if needle in r["resume"].casefold()]
    if args.unique:
        seen: set[str] = set()
        deduped = []
        for i, r in selected:
            if r["resume"] not in seen:
                seen.add(r["resume"])
                deduped.append((i, r))
        selected = deduped
    if args.limit is not None:
        selected = selected[: args.limit]
    return selected


def summary_line(index: int, resume: dict) -> str:
    """One line per resume: index, category, length, and the start of the text."""
    text = resume["resume"]
    collapsed = " ".join(text.split())  # replace newlines and repeated spaces with single spaces
    preview = collapsed[:PREVIEW_CHARS] + ("..." if len(collapsed) > PREVIEW_CHARS else "")
    return f"#{index}  [{resume['category']}]  {len(text)} chars  {preview}"


def full_text(index: int, resume: dict, max_chars: int) -> str:
    """A header line plus the resume text, cut off at max_chars if it is set (0 means no limit)."""
    text = resume["resume"]
    header = f"#{index}  [{resume['category']}]  {len(text)} chars"
    if max_chars and len(text) > max_chars:
        text = f"{text[:max_chars]}\n... [{len(text) - max_chars} more chars]"
    return f"{header}\n{SEPARATOR}\n{text}"


def main(argv: list[str] | None = None) -> int:
    """Run the command line tool. Returns the exit code: 0 = success, 1 = data file problem, 2 = bad flag value."""
    args = parse_args(argv)
    try:
        resumes = load_resumes()
    except (FileNotFoundError, ValueError) as e:
        print(e, file=sys.stderr)
        return 1

    counts = category_counts(resumes)
    if args.list_categories:
        print(format_category_counts(counts))
        return 0

    # Check flag values before filtering so a typo gets a helpful error instead of an empty result.
    if args.category is not None and args.category.casefold() not in {c.casefold() for c in counts}:
        print(f"Unknown category: {args.category!r}", file=sys.stderr)
        print(format_category_counts(counts), file=sys.stderr)
        return 2

    if args.index is not None and args.index >= len(resumes):
        print(f"--index {args.index} out of range (0-{len(resumes) - 1})", file=sys.stderr)
        return 2

    selected = select(resumes, args)
    if not selected:
        print("No resumes match the given filters.")
        return 0

    if args.full:
        print(f"\n{RESUME_BREAK}\n".join(full_text(i, r, args.max_chars) for i, r in selected))
    else:
        for i, r in selected:
            print(summary_line(i, r))

    shown_categories = len({r["category"] for _, r in selected})
    noun = "category" if shown_categories == 1 else "categories"
    print(f"\nShowing {len(selected)} of {len(resumes)} resumes across {shown_categories} {noun}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.stderr.close()
        sys.exit(0)
