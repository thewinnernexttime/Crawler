import requests
import json
import time
import os

API = "https://sousuo.www.gov.cn/search-gov/data"
SAVE_DIR = "gov_policies"
os.makedirs(SAVE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://sousuo.www.gov.cn/zcwjk/policyDocumentLibrary?q=&t=zhengcelibrary&orpro=",
}

COOKIES = {
    "wdcid": "6f8bb86d9f9d20c1",
    "tfstk": "glTmnrf87TwQL2yr-R7j0mTCSlmRcZ_1IdUOBNBZ4TW7DrhfX32wTBswHZC9qOvlFrUAkZlMIpJcXdAsG1WwQdX9D03pGI_17vdiJ2dfZyG7yKfV3alN_szqwiyNNVZP7vHKyY3K29QwMx9NSQRPF14NgiJNa7W5To7N3Gyz46WPQNJN0_RPtsq4gizV4bf1Us7N7dRrZ1BPQN7wQQlg9YBA3OTrBVewT66GoUfcm9RoAP4aMsydpIJUSPXciimkgT4a7UxwJZR1K42PeCRBbgYiyz_6wHvMbLla7OxPtpfpH4zc73Jk-MRSKr6D4KTGkMggs_xHaKYDZfEkILRBAZ8qCrBXbQ8NeElTS9-pOafWWYaVI3-wki__3xfkoBYMjgub4kuSLP1r6Ur_fi55Z9e87liE8r-1kbcuYsjVNsz-Zbqsoi55Z9hoZk8h0_14y",
    "ariatheme": "0",
    "ariaStatus": "false",
    "ariafontScale": "1",
}

def fetch_page(keyword: str, page: int = 1, page_size: int = 10):
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
        "p": page,          # page
        "n": page_size,     # page size
        "inpro": "",
        "bmfl": "",
        "dup": "",
        "orpro": "",
        "type": "gwyzcwjk",
    }

    with requests.Session() as s:
        s.headers.update(HEADERS)
        s.cookies.update(COOKIES)

        resp = s.get(API, params=params, timeout=15)

        # 关键调试
        print("URL:", resp.url)
        print("Status:", resp.status_code)
        print("Content-Type:", resp.headers.get("Content-Type"))

        resp.raise_for_status()
        return resp.json()

def extract_items(data: dict):
    # 你的数据里真正的列表在这里：
    list_vo = (
        data.get("searchVO", {})
            .get("catMap", {})
            .get("gongwen", {})
            .get("listVO", [])
    )

    items = []
    for it in list_vo:
        items.append({
            "title": it.get("title", "").replace("<em>", "").replace("</em>", ""),
            "pubtimeStr": it.get("pubtimeStr", ""),
            "puborg": it.get("puborg", ""),
            "pcode": it.get("pcode", ""),
            "summary": it.get("summary", "").replace("<em>", "").replace("</em>", ""),
            "url": it.get("url", ""),
            "index": it.get("index", ""),
            "id": it.get("id", ""),
        })
    return items

def main(keyword="管理条例", max_pages=2, page_size=10):
    all_items = []

    for p in range(1, max_pages + 1):
        print(f"\nFetching page {p} ...")
        data = fetch_page(keyword, page=p, page_size=page_size)
        items = extract_items(data)

        if not items:
            print("No items, stop.")
            break

        print(f"Got {len(items)} items")
        all_items.extend(items)

        time.sleep(0.8)  # ✅ 稳妥一点

    # 保存
    out_path = os.path.join(SAVE_DIR, f"policy_{keyword}_p1-{len(all_items)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print("Saved:", out_path)

if __name__ == "__main__":
    main(keyword="管理条例", max_pages=2, page_size=50)
