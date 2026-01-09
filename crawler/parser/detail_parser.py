import re
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_detail(html: str, base_url: str) -> Dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    candidates: List[tuple] = []
    for selector in [
        "div.pages_content", "div.article", "div.content", "div.TRS_Editor",
        "article", "div#UCAP-CONTENT", "div#content", "div.main"
    ]:
        for node in soup.select(selector):
            txt = node.get_text("\n", strip=True)
            if txt and len(txt) > 200:
                candidates.append((len(txt), txt, selector))

    if not candidates:
        main_text = soup.get_text("\n", strip=True)
        chosen = "fallback_fullpage"
    else:
        candidates.sort(reverse=True, key=lambda x: x[0])
        _, main_text, chosen = candidates[0]

    attachments: List[Dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(" ", strip=True)
        full = urljoin(base_url, href)
        if re.search(r"\.(pdf|doc|docx|wps|zip)(\?|$)", full, re.I):
            attachments.append({"text": text, "url": full})

    # 去重
    seen = set()
    uniq = []
    for att in attachments:
        if att["url"] in seen:
            continue
        seen.add(att["url"])
        uniq.append(att)

    return {
        "chosen_selector": chosen,
        "main_text": main_text,
        "attachments": uniq,
    }


