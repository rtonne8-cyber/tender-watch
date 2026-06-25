"""Tier 1 fetcher: Find a Tender (UK) OCDS API."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.common import fetch_ocds_releases_multi_stage, normalise_ocds_release

API_URL = "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages"
SOURCE = "find_a_tender"

# Pipeline/planning + active tender stages only — explicitly excludes
# award/contract/implementation per the project's scope (we track upcoming
# and live opportunities, not what's already been won or signed).
STAGES = ["planning", "tender"]


def _notice_url(release):
    return f"https://www.find-tender.service.gov.uk/Notice/{release.get('id')}"


def fetch(max_records=500):
    releases = fetch_ocds_releases_multi_stage(
        API_URL, {"limit": 100}, STAGES, max_records_per_stage=max_records
    )
    return [normalise_ocds_release(r, SOURCE, tier=1, url_builder=_notice_url) for r in releases]


if __name__ == "__main__":
    records = fetch()
    print(f"{SOURCE}: fetched {len(records)} records")
    if not records:
        print("ERROR: no records returned", file=sys.stderr)
        sys.exit(1)
    print("Sample record:")
    print(records[0])
