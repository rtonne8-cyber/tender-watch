"""Tier 2 fetcher: Public Contracts Scotland (PCS).

PCS has no public API or per-search RSS feed for notices (verified June 2026 —
RSS on this site is documented only for the News section). The search page is
a classic ASP.NET WebForms postback form (Telerik controls, ViewState),
so this fetcher replays a minimal keyword-search POST per query term and
parses the resulting result-row HTML directly. The CPV tree picker is not
touched — keyword search alone is sufficient to recover candidates, and the
existing keyword/Haiku scoring gate downstream filters relevance, same as
every other ambiguous record.

No CPV codes or description are available from the result row (only title,
buyer, deadline, notice type, reference, OCID), so these records can never
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

SOURCE = "pcs_scotland"
BASE_URL = "https://www.publiccontractsscotland.gov.uk"
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


def _parse_date_ddMonyy(text):
    try:
        return datetime.strptime(text.strip(), "%d-%b-%y").replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


def _field_value(item_div, label):
    span = item_div.find("span", class_="ns-item-title", string=lambda s: s and label in s)
    if span is None or span.next_sibling is None:
        return None
    return str(span.next_sibling).strip()


def _parse_results(html):
    soup = BeautifulSoup(html, "html.parser")
    records = []
    for row in soup.find_all("tr", class_="pcs-tbl-row"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        date_cell, detail_cell = cells[0], cells[1]

        link = detail_cell.find("a", class_="ns-list-link")
        if link is None or not link.get("href"):
            continue
        title = link.contents[0].strip() if link.contents else link.get_text(strip=True)

        item_div = detail_cell.find("div", class_="ns-item")
        if item_div is None:
            continue
        reference = _field_value(item_div, "Reference No")
        buyer = _field_value(item_div, "Published By")
        deadline_text = _field_value(item_div, "Deadline Date")
        notice_type = _field_value(item_div, "Notice Type") or ""

        if "award" in notice_type.lower():
            continue  # only pipeline/open stages, same intent as other fetchers

        published_text = date_cell.contents[0].strip() if date_cell.contents else None
        published = _parse_date_ddmmyyyy(published_text) if published_text else None
        deadline = _parse_date_ddMonyy(deadline_text) if deadline_text else None

        if not reference:
            continue

        records.append(
            {
                "id": f"{SOURCE}-{reference}",
                "source": SOURCE,
                "tier": 2,
                "title": title or "(untitled)",
                "buyer": buyer or "(unknown buyer)",
                "description": "",
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
        "ctl00$maincontent$txtKeywords": term,
        "ctl00$maincontent$btnSearch": "Search",
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
            print(f"  [pcs_scotland] search '{term}' failed: {exc}", file=sys.stderr)
        time.sleep(1)  # be polite between postbacks to a stateful gov.uk form
    return records


if __name__ == "__main__":
    records = fetch()
    print(f"{SOURCE}: fetched {len(records)} records")
    if not records:
        print("ERROR: no records returned", file=sys.stderr)
        sys.exit(1)
    print("Sample record:")
    print(records[0])
