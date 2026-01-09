import argparse
import json
import random
import time
from typing import List

from .. import config
from ..fetcher import Fetcher
from ..parser.detail_parser import parse_detail
from ..storage.file_store import download_attachment, save_raw_html
from ..storage.sqlite_store import (
    get_pending_details,
    init_db,
    upsert_policy_detail,
    update_list_status,
)


def run(limit: int = 50, max_retry: int = 5) -> None:
    init_db()
    fetcher = Fetcher()
    processed = 0
    extra_sleep_counter = 0

    while True:
        batch = get_pending_details(limit=limit, max_retry=max_retry)
        if not batch:
            break

        for row in batch:
            id_val = row["id"]
            url = row["url"]
            title = row.get("title", "")
            try:
                html = fetcher.get_text(
                    url,
                    accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                )
                raw_path, raw_sha256 = save_raw_html(url, title, html)
                parsed = parse_detail(html, url)

                main_text = parsed.get("main_text", "")
                if not main_text or len(main_text) < config.MIN_CONTENT_LENGTH:
                    # 视为解析失败，重试
                    update_list_status(id_val, "PENDING_DETAIL", retry_increment=True)
                    time.sleep(config.random_detail_interval())
                    continue

                attachments = parsed.get("attachments", []) or []
                downloaded = []
                for att in attachments:
                    try:
                        p = download_attachment(att["url"], fetcher, title_hint=title)
                        downloaded.append({"url": att["url"], "path": p, "text": att.get("text", "")})
                        time.sleep(0.3)
                    except Exception as e:
                        downloaded.append({"url": att["url"], "error": str(e), "text": att.get("text", "")})

                upsert_policy_detail(
                    {
                        "id": id_val,
                        "content": main_text,
                        "attachments_json": json.dumps(downloaded, ensure_ascii=False),
                        "parser_version": config.PARSER_VERSION,
                        "raw_html_path": raw_path,
                        "raw_html_sha256": raw_sha256,
                        "source_url": url,
                        "fetched_at": config.now_iso(),
                        "parsed_at": config.now_iso(),
                    }
                )
                update_list_status(id_val, "DONE", retry_increment=False)
            except Exception:
                update_list_status(id_val, "PENDING_DETAIL", retry_increment=True)

            processed += 1
            extra_sleep_counter += 1
            time.sleep(config.random_detail_interval())
            if extra_sleep_counter % config.DETAIL_REQUEST_EXTRA_SLEEP_EVERY == 0:
                time.sleep(config.DETAIL_REQUEST_EXTRA_SLEEP_SEC)

    return None


def main():
    parser = argparse.ArgumentParser(description="详情任务：抓取 PENDING_DETAIL 并补齐详情")
    parser.add_argument("--limit", type=int, default=50, help="每批次处理条数")
    parser.add_argument("--max-retry", type=int, default=5, help="最大重试次数")
    args = parser.parse_args()
    run(limit=args.limit, max_retry=args.max_retry)


if __name__ == "__main__":
    main()


