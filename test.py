import os
import re
import json
import time
import hashlib
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

API = "https://sousuo.www.gov.cn/search-gov/data"
SAVE_DIR = "gov_policies"
DETAIL_DIR = os.path.join(SAVE_DIR, "details")
ATTACH_DIR = os.path.join(SAVE_DIR, "attachments")
os.makedirs(DETAIL_DIR, exist_ok=True)
os.makedirs(ATTACH_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://sousuo.www.gov.cn/zcwjk/policyDocumentLibrary?q=&t=zhengcelibrary&orpro=",
}

COOKIES = {
    "wdcid": "6f8bb86d9f9d20c1",
    "tfstk": "XXX",
    "ariatheme": "0",
    "ariaStatus": "false",
    "ariafontScale": "1",
}

def fetch_page(keyword: str, page: int = 1, page_size: int = 10, session=None):
    params = {
        "t": "zhengcelibrary",
        "q": keyword,
        "timetype": "timeqb",
        "mintime": "",
        "maxtime": "",
        "sort": "score",
        "sortType": "1",
        "searchfield": "title",
        "pcodeJiguan": "",
        "childtype": "",
        "subchildtype": "",
        "tsbq": "",
        "pubtimeyear": "",
        "puborg": "",
        "pcodeYear": "",
        "pcodeNum": "",
        "filetype": "",
        "p": page,
        "n": page_size,
        "inpro": "",
        "bmfl": "",
        "dup": "",
        "orpro": "",
        "type": "gwyzcwjk",
    }

    s = session or requests.Session()
    s.headers.update(HEADERS)
    s.cookies.update(COOKIES)

    resp = s.get(API, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()

def extract_items(data: dict):
    list_vo = (
        data.get("searchVO", {})
            .get("catMap", {})
            .get("gongwen", {})
            .get("listVO", [])
    )

    items = []
    for it in list_vo:
        items.append({
            "title": (it.get("title") or "").replace("<em>", "").replace("</em>", ""),
            "pubtimeStr": it.get("pubtimeStr", ""),
            "puborg": it.get("puborg", ""),
            "pcode": it.get("pcode", ""),
            "summary": (it.get("summary") or "").replace("<em>", "").replace("</em>", ""),
            "url": it.get("url", ""),
            "index": it.get("index", ""),
            "id": it.get("id", ""),
        })
    return items

def safe_filename(name: str, max_len: int = 120) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:max_len] if len(name) > max_len else name

def hash_url(u: str) -> str:
    return hashlib.md5(u.encode("utf-8")).hexdigest()[:10]

def fetch_detail_html(url: str, session: requests.Session) -> str:
    # 详情页是 html，所以 Accept 可以更通用
    headers = dict(session.headers)
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

    r = session.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text

def extract_main_text_and_attachments(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")

    # 去掉无关脚本样式
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # 常见正文容器（gov.cn 页面可能会变化，这里用“候选+最长文本”策略更稳）
    candidates = []
    for selector in [
        "div.pages_content", "div.article", "div.content", "div.TRS_Editor",
        "article", "div#UCAP-CONTENT", "div#content", "div.main"
    ]:
        for node in soup.select(selector):
            txt = node.get_text("\n", strip=True)
            if txt and len(txt) > 200:
                candidates.append((len(txt), txt, selector))

    if not candidates:
        # 兜底：全页面取文本（不太干净，但保证有内容）
        main_text = soup.get_text("\n", strip=True)
        chosen = "fallback_fullpage"
    else:
        candidates.sort(reverse=True, key=lambda x: x[0])
        _, main_text, chosen = candidates[0]

    # 找附件链接
    attachments = []
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
        "attachments": uniq
    }

def download_file(url: str, session: requests.Session, out_dir: str, hint_name: str = "") -> str:
    r = session.get(url, stream=True, timeout=30)
    r.raise_for_status()

    # 从 url 推断扩展名
    path = urlparse(url).path
    ext = os.path.splitext(path)[1] or ".bin"

    base = safe_filename(hint_name) if hint_name else "attachment"
    filename = f"{base}_{hash_url(url)}{ext}"
    out_path = os.path.join(out_dir, filename)

    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 64):
            if chunk:
                f.write(chunk)

    return out_path

def crawl_details(items, sleep_sec=0.8):
    with requests.Session() as s:
        s.headers.update(HEADERS)
        s.cookies.update(COOKIES)

        results = []
        for i, it in enumerate(items, 1):
            url = it.get("url")
            if not url:
                continue

            print(f"[{i}/{len(items)}] Detail:", it.get("title"), url)

            try:
                html = fetch_detail_html(url, s)
                parsed = extract_main_text_and_attachments(html, url)

                # 保存正文
                detail_name = safe_filename(it.get("title", "policy")) + "_" + hash_url(url) + ".json"
                detail_path = os.path.join(DETAIL_DIR, detail_name)

                record = {
                    **it,
                    "detail_url": url,
                    "chosen_selector": parsed["chosen_selector"],
                    "main_text": parsed["main_text"],
                    "attachments": parsed["attachments"],
                }

                with open(detail_path, "w", encoding="utf-8") as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)

                # 下载附件（可选）
                downloaded = []
                for att in parsed["attachments"]:
                    try:
                        p = download_file(att["url"], s, ATTACH_DIR, hint_name=it.get("title",""))
                        downloaded.append({"url": att["url"], "path": p, "text": att.get("text","")})
                        time.sleep(0.3)
                    except Exception as e:
                        downloaded.append({"url": att["url"], "error": str(e), "text": att.get("text","")})

                record["downloaded_attachments"] = downloaded
                results.append(record)

            except Exception as e:
                print("  !! Failed:", e)
                results.append({**it, "detail_url": url, "error": str(e)})

            time.sleep(sleep_sec)

        return results

if __name__ == "__main__":
    # 1) 先抓列表
    data = fetch_page("管理条例", page=1, page_size=10)
    items = extract_items(data)

    # 2) 再抓详情
    all_details = crawl_details(items, sleep_sec=1.0)

    # 汇总保存
    out = os.path.join(SAVE_DIR, "details_summary.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_details, f, ensure_ascii=False, indent=2)
    print("Saved:", out)
