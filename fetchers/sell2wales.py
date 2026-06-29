"""Tier 2 fetcher: Sell2Wales.

Same platform family and constraint as fetchers/pcs_scotland.py: no public API
or per-search RSS for notices (verified June 2026), so this replays a
keyword-search POST against the site's own ASP.NET WebForms search and parses
the result-row HTML. Unlike PCS, Sell2Wales's result rows include the full
notice description (via an aria-label attribute) and an OCID, which gives the
downstream keyword scorer real text to match against rather than title-only.

No CPV codes are available from the result row, so these records can never
auto-score via the CPV allowlist path — they always go through keyword match
or the Haiku gate.
"""

import os
import sys
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.common import USER_AGENT

SOURCE = "sell2wales"
BASE_URL = "https://www.sell2wales.gov.wales"
SEARCH_URL = f"{BASE_URL}/search/search_mainpage.aspx"
DEFAULT_TIMEOUT = 30

# Plain substring terms (this is the site's own free-text search, not regex)
# covering the same T&D ground as scoring/keywords.yaml's keyword list.
SEARCH_TERMS = [
    "substation",
    "switchgear",
    "transmission line",
    "distribution network",
    "overhead line",
    "underground cable",
    "grid connection",
    "transformer",
]


def _hidden_fields(html):
    soup = BeautifulSoup(html, "html.parser")
    fields = {}
    for name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
        tag = soup.find("input", {"name": name})
        fields[name] = tag["value"] if tag else ""
    return fields


def _parse_date_ddmmyyyy(text):
    try:
        return datetime.strptime(text.strip(), "%d/%m/%Y").replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


def _properties(result_div):
    props = {}
    for prop_div in result_div.find_all("div", class_="notice-property"):
        label_span = prop_div.find("span", class_="notice-refno")
        if label_span is None:
            continue
        value_span = label_span.find_next_sibling("span")
        if value_span is None:
            continue
        label = label_span.get_text(strip=True).rstrip(":").lower()
        props[label] = value_span.get_text(strip=True)
    return props


def _description(result_div):
    span = result_div.find("span", id=lambda v: v and v.startswith("lblDescription_"))
    if span is None:
        return ""
    return span.get("aria-label") or span.get_text(strip=True)


def _parse_results(html):
    soup = BeautifulSoup(html, "html.parser")
    records = []
    for result_div in soup.find_all("div", class_="search-result"):
        link = result_div.find("a", class_="notice-title")
        if link is None or not link.get("href"):
            continue
        title = link.get_text(strip=True)

        props = _properties(result_div)
        reference = props.get("reference no")
        if not reference:
            continue

        notice_type = props.get("notice type") or ""
        if "award" in notice_type.lower():
            continue  # only pipeline/open stages, same intent as other fetchers

        published = _parse_date_ddmmyyyy(props.get("publication date") or "")
        deadline = _parse_date_ddmmyyyy(props.get("deadline date") or "")

        records.append(
            {
                "id": f"{SOURCE}-{reference}",
                "source": SOURCE,
                "tier": 2,
                "title": title or "(untitled)",
                "buyer": props.get("published by") or "(unknown buyer)",
                "description": _description(result_div),
                "cpv_codes": [],
                "primary_cpv": None,
                "value_low": None,
                "value_high": None,
                "currency": "GBP",
                "published_date": published.isoformat() if published else None,
                "deadline_date": deadline.isoformat() if deadline else None,
                "url": f"{BASE_URL}{link['href']}",
            }
        )
    return records


def _search_one(session, term):
    resp = session.get(SEARCH_URL, headers={"User-Agent": USER_AGENT}, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    fields = _hidden_fields(resp.text)

    payload = {
        **fields,
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "ctl00$MainBody$txtKeywords": term,
        "ctl00$MainBody$btnSearch": "Search",
    }
    resp = session.post(
        SEARCH_URL,
        data=payload,
        headers={"User-Agent": USER_AGENT},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return _parse_results(resp.text)


def fetch():
    session = requests.Session()
    seen = set()
    records = []
    for term in SEARCH_TERMS:
        try:
            for record in _search_one(session, term):
                if record["id"] in seen:
                    continue
                seen.add(record["id"])
                records.append(record)
        except Exception as exc:  # noqa: BLE001 - one bad search term must not kill the rest
            print(f"  [sell2wales] search '{term}' failed: {exc}", file=sys.stderr)
        time.sleep(1)  # be polite between postbacks to a stateful gov.wales form
    return records


if __name__ == "__main__":
    records = fetch()
    print(f"{SOURCE}: fetched {len(records)} records")
    if not records:
        print("ERROR: no records returned", file=sys.stderr)
        sys.exit(1)
    print("Sample record:")
    print(records[0])
