"""Tier 1 fetcher: Contracts Finder (UK) OCDS API."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.common import fetch_ocds_releases, normalise_ocds_release

API_URL = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"
SOURCE = "contracts_finder"


def _notice_url(release):
    return f"https://www.contractsfinder.service.gov.uk/Notice/{release.get('id')}"


def fetch(max_records=500):
    releases = fetch_ocds_releases(API_URL, {"order": "desc", "limit": 100}, max_records=max_records)
    return [normalise_ocds_release(r, SOURCE, tier=1, url_builder=_notice_url) for r in releases]


if __name__ == "__main__":
    records = fetch()
    print(f"{SOURCE}: fetched {len(records)} records")
    if not records:
        print("ERROR: no records returned", file=sys.stderr)
        sys.exit(1)
    print("Sample record:")
    print(records[0])
