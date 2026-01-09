import argparse
import time
from typing import Dict

from .. import config
from ..fetcher import Fetcher
from ..parser.list_parser import build_params, parse_items
from ..storage.sqlite_store import init_db, upsert_policy_list


def run(keyword: str, max_pages: int = 2, page_size: int = 50) -> None:
    init_db()
    fetcher = Fetcher()

    for page in range(1, max_pages + 1):
        params = build_params(keyword, page=page, page_size=page_size)
        data = fetcher.get_json(config.API_URL, params=params)
        items = parse_items(data)
        if not items:
            break

        for it in items:
            # 使用接口 id 作为主键（若空则退化为 index，再退化为 url）
            id_val = it.get("id") or it.get("index") or it.get("url")
            row: Dict[str, str] = {
                "id": id_val,
                "url": it.get("url", ""),
                "pubtime": it.get("pubtimeStr", ""),
                "title": it.get("title", ""),
                "status": "PENDING_DETAIL",
                "retry": 0,
                "puborg": it.get("puborg", ""),
                "pcode": it.get("pcode", ""),
                "summary": it.get("summary", ""),
            }
            upsert_policy_list(row)

        time.sleep(config.LIST_REQUEST_INTERVAL_SEC)


def main():
    parser = argparse.ArgumentParser(description="列表任务：抓取政策列表并入库")
    parser.add_argument("--keyword", required=True, help="搜索关键字")
    parser.add_argument("--max-pages", type=int, default=2, help="最大页数")
    parser.add_argument("--page-size", type=int, default=50, help="每页数量")
    args = parser.parse_args()

    run(keyword=args.keyword, max_pages=args.max_pages, page_size=args.page_size)


if __name__ == "__main__":
    main()


