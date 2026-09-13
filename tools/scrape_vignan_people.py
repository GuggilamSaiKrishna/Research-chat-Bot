import concurrent.futures
import json
import re
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

import config
from config import FACULTY_JSON

PEOPLE_URL = "https://vignan.ac.in/newvignan/people.php"
GET_FACULTY_URL = "https://vignan.ac.in/newvignan/getfaculty.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _fetch_faculty_ids() -> list[str]:
    response = requests.get(PEOPLE_URL, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.find_all(lambda tag: tag.has_attr("onclick") and "openmodal" in tag["onclick"])
    
    ids = []
    seen = set()
    for card in cards:
        fid = card.get("id")
        if fid and fid not in seen:
            seen.add(fid)
            ids.append(fid)
    return ids


def _fetch_single_profile(fid: str) -> dict | None:
    try:
        res = requests.post(GET_FACULTY_URL, data={"id": fid}, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and data.get("name"):
                return data
    except Exception:
        pass
    return None


def _is_junk_text(text: str) -> bool:
    if not text or not isinstance(text, str):
        return True

    t = text.strip()
    l = t.lower()

    if len(t) < 2:
        return True

    # Check file paths, local files, URLs, PDFs, docs
    if any(k in l for k in ["file:/", "http:/", "https:/", ".pdf", ".doc", ".docx", "downloads/", "c:/", "d:/", "users/admin"]):
        return True

    # Check metrics, numbers, grants, admin text
    noise_patterns = [
        r"h\s*[-_]?\s*index",
        r"i\s*[-_]?\s*10\s*[-_]?\s*index",
        r"citations?\s*:",
        r"\d+\s*citations",
        r"\d+\s*publications",
        r"ph\.?d\.?\s*awarded",
        r"a\.p\.\s*sanctioned",
        r"sanctioned\s*:",
        r"\b\d+\s*rs\.?\b",
        r"\brs\.\b",
        r"dst\s*[-_]?\s*seed",
        r"scopus\s*h-index",
        r"google\s*h-index",
        r"sci\s*publications",
        r"conference\s*publications",
        r"h-index\s*=",
        r"h-index\s*:",
    ]
    for pattern in noise_patterns:
        if re.search(pattern, l):
            return True

    # Pure numbers or date ranges
    if re.match(r"^[\d\.\s\-\:\,/]+$", t):
        return True

    return False


def _is_publication_or_patent(text: str) -> bool:
    l = text.lower().strip()
    if l.startswith("patent") or "patent:" in l:
        return True
    if any(w in l for w in ["derivatives", "preparation of", "novel process", "novel approach", "synthesis of", "journal of", "proceedings of", "international conference", "transaction on"]):
        return True
    if len(text) > 80:
        return True
    return False


def _clean_list(raw_items: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for item in raw_items:
        if not item or not isinstance(item, str):
            continue
        parts = [p.strip() for p in item.split(",") if p.strip()]
        for p in parts:
            if len(p) > 2 and p.lower() not in seen and not _is_junk_text(p):
                seen.add(p.lower())
                cleaned.append(p)
    return cleaned


def parse_raw_profile(raw: dict) -> dict:
    salutation = (raw.get("salutation") or "").strip()
    raw_name = (raw.get("name") or "").strip()
    if salutation and not raw_name.startswith(salutation):
        full_name = f"{salutation} {raw_name.title()}".strip()
    else:
        full_name = raw_name.title()

    department = (raw.get("branch") or raw.get("department") or "N/A").strip()
    designation = (raw.get("desig") or raw.get("actualdesig") or "Faculty").strip().title()
    mobile = (raw.get("contact") or raw.get("personalcontact") or "Not Available").strip()
    email = (raw.get("email") or raw.get("personalemail") or "Not Available").strip()

    # Gather research areas / interests
    raw_interests = []
    for item in raw.get("interests", []) or []:
        if isinstance(item, dict) and item.get("interest"):
            raw_interests.append(item["interest"])
    for item in raw.get("research", []) or []:
        if isinstance(item, dict) and item.get("research"):
            raw_interests.append(item["research"])

    clean_interests = _clean_list(raw_interests)
    research_areas = []
    extra_pubs = []

    for item in clean_interests:
        if _is_publication_or_patent(item):
            extra_pubs.append(item)
        else:
            research_areas.append(item)

    # Gather publications and conferences
    raw_pubs = []
    for item in raw.get("publications", []) or []:
        if isinstance(item, dict) and item.get("publications"):
            raw_pubs.append(item["publications"])
    for item in raw.get("conferences", []) or []:
        if isinstance(item, dict) and item.get("conferences"):
            raw_pubs.append(item["conferences"])

    raw_pubs.extend(extra_pubs)
    publications = _clean_list(raw_pubs)

    return {
        "name": full_name,
        "department": department,
        "designation": designation,
        "mobile_number": mobile,
        "email": email,
        "research_areas": research_areas,
        "publications": publications,
        "empcode": str(raw.get("empcode", "")).strip(),
    }



def scrape_vignan_people(max_workers: int = 20) -> list[dict]:
    """
    Scrape all faculty profiles directly from vignan.ac.in/newvignan/people.php and save to faculty.json.
    """
    print(f"Connecting to {PEOPLE_URL}...", flush=True)
    ids = _fetch_faculty_ids()
    print(f"Found {len(ids)} faculty entries on website. Fetching profile details...", flush=True)

    formatted_profiles = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        raw_results = list(executor.map(_fetch_single_profile, ids))
        for raw in raw_results:
            if raw:
                formatted_profiles.append(parse_raw_profile(raw))

    out_path = Path(FACULTY_JSON)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(formatted_profiles, f, indent=2, ensure_ascii=False)

    print(f"Successfully scraped {len(formatted_profiles)} profiles and updated {FACULTY_JSON}!", flush=True)
    return formatted_profiles


if __name__ == "__main__":
    t0 = time.time()
    profiles = scrape_vignan_people(max_workers=20)
    print(f"Completed scraping in {time.time() - t0:.2f} seconds.", flush=True)

