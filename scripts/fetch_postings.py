from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_URL = "https://data.usajobs.gov/api/search"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def load_dotenv(path: Path) -> None:
    """Minimal .env loader (KEY=VALUE lines) so we don't need an extra dependency."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def search(keyword: str, location: str, count: int, radius: int, series: str | None, api_key: str, email: str) -> dict:
    params = {
        "Keyword": keyword,
        "LocationName": location,
        "Radius": radius,
        "ResultsPerPage": count,
        "Fields": "Full",  # includes the full job summary and major duties
    }
    if series:
        params["JobCategoryCode"] = series  # e.g. "2210;1550"
    req = urllib.request.Request(
        f"{API_URL}?{urllib.parse.urlencode(params)}",
        headers={
            "Host": "data.usajobs.gov",
            "User-Agent": email,
            "Authorization-Key": api_key,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def normalize(item: dict) -> dict:
    """Flatten a USAJOBS search result into the fields the analyzer cares about."""
    d = item.get("MatchedObjectDescriptor", {})
    details = d.get("UserArea", {}).get("Details", {})
    pay = (d.get("PositionRemuneration") or [{}])[0]
    return {
        "id": d.get("PositionID") or item.get("MatchedObjectId"),
        "title": d.get("PositionTitle"),
        "organization": d.get("OrganizationName"),
        "department": d.get("DepartmentName"),
        "locations": [loc.get("LocationName") for loc in d.get("PositionLocation", [])],
        "schedule": [s.get("Name") for s in d.get("PositionSchedule", [])],
        "salary": {
            "min": pay.get("MinimumRange"),
            "max": pay.get("MaximumRange"),
            "per": pay.get("Description"),
        },
        "categories": [c.get("Name") for c in d.get("JobCategory", [])],
        "summary": details.get("JobSummary"),
        "duties": details.get("MajorDuties", []),
        "qualifications": d.get("QualificationSummary"),
        "education": details.get("Education"),
        "requirements": details.get("Requirements"),
        "url": d.get("PositionURI"),
        "published": d.get("PublicationStartDate"),
        "closes": d.get("ApplicationCloseDate"),
        "source": "usajobs",
    }


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--keyword", default="", help='free-text keyword, e.g. "software developer" (default: none)')
    parser.add_argument("--location", default="Miami, FL")
    parser.add_argument("--count", type=int, default=20, help="number of postings to save (max 500)")
    parser.add_argument("--radius", type=int, default=50, help="search radius in miles around --location")
    parser.add_argument(
        "--series",
        default="2210;1550",
        help='federal occupational series, semicolon-separated (default: "2210;1550" = IT Management + '
        'Computer Science, where federal software jobs are listed); pass "" to search all jobs',
    )
    parser.add_argument("--out", type=Path, help="output file (default: data/postings_<keyword-or-series>_<location>.json)")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("USAJOBS_API_KEY")
    email = os.environ.get("USAJOBS_EMAIL")
    if not api_key or not email:
        print("Missing USAJOBS_API_KEY and/or USAJOBS_EMAIL in .env (see README > Test data).", file=sys.stderr)
        return 1

    try:
        raw = search(args.keyword, args.location, args.count, args.radius, args.series, api_key, email)
    except urllib.error.HTTPError as e:
        print(f"USAJOBS request failed: HTTP {e.code} {e.reason}", file=sys.stderr)
        return 1

    result = raw.get("SearchResult", {})
    postings = [normalize(item) for item in result.get("SearchResultItems", [])]

    name = slugify(args.keyword) or (f"series-{slugify(args.series)}" if args.series else "all")
    out = args.out or DATA_DIR / f"postings_{name}_{slugify(args.location)}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "query": {
            "keyword": args.keyword,
            "location": args.location,
            "radius_miles": args.radius,
            "series": args.series,
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_available": result.get("SearchResultCountAll"),
        "count": len(postings),
        "postings": postings,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    shown = out.resolve()
    if shown.is_relative_to(PROJECT_ROOT):
        shown = shown.relative_to(PROJECT_ROOT)
    print(f"Saved {len(postings)} postings ({payload['total_available']} available) to {shown}")
    if len(postings) < args.count:
        print("Fewer results than requested; try a broader --keyword or a larger --radius.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
