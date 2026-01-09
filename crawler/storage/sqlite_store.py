import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .. import config


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS policy_list (
                id TEXT PRIMARY KEY,
                url TEXT,
                pubtime TEXT,
                title TEXT,
                status TEXT,
                retry INTEGER DEFAULT 0,
                puborg TEXT,
                pcode TEXT,
                summary TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_policy_list_status ON policy_list(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_policy_list_updated ON policy_list(updated_at)")

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS policy_detail (
                id TEXT PRIMARY KEY,
                content TEXT,
                attachments_json TEXT,
                parser_version TEXT,
                raw_html_path TEXT,
                raw_html_sha256 TEXT,
                source_url TEXT,
                fetched_at TEXT,
                parsed_at TEXT
            )
            """
        )
        conn.commit()


def upsert_policy_list(row: Dict[str, Any]) -> None:
    """
    row 需要包含：
      id, url, pubtime, title, status, retry, puborg, pcode, summary
    幂等：状态不回退（DONE/FAILED 不被 PENDING_DETAIL 覆盖）
    """
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO policy_list (id, url, pubtime, title, status, retry, puborg, pcode, summary)
            VALUES (:id, :url, :pubtime, :title, :status, :retry, :puborg, :pcode, :summary)
            ON CONFLICT(id) DO UPDATE SET
                url=excluded.url,
                pubtime=excluded.pubtime,
                title=excluded.title,
                summary=excluded.summary,
                puborg=excluded.puborg,
                pcode=excluded.pcode,
                updated_at = datetime('now'),
                status = CASE
                    WHEN policy_list.status IN ('DONE','FAILED') THEN policy_list.status
                    ELSE excluded.status
                END
            """
        , row)
        conn.commit()


def update_list_status(id_val: str, status: str, retry_increment: bool = False) -> None:
    with get_conn() as conn:
        c = conn.cursor()
        if retry_increment:
            c.execute(
                """
                UPDATE policy_list
                SET status=?, retry=retry+1, updated_at=datetime('now')
                WHERE id=?
                """,
                (status, id_val),
            )
        else:
            c.execute(
                """
                UPDATE policy_list
                SET status=?, updated_at=datetime('now')
                WHERE id=?
                """,
                (status, id_val),
            )
        conn.commit()


def get_pending_details(limit: int = 50, max_retry: int = 5) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT id, url, title, pubtime, retry
            FROM policy_list
            WHERE status='PENDING_DETAIL' AND retry < ?
            ORDER BY updated_at ASC
            LIMIT ?
            """,
            (max_retry, limit),
        )
        rows = c.fetchall()
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, r)) for r in rows]


def upsert_policy_detail(row: Dict[str, Any]) -> None:
    """
    row 需要包含：
      id, content, attachments_json(json str), parser_version,
      raw_html_path, raw_html_sha256, source_url, fetched_at, parsed_at
    """
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO policy_detail
            (id, content, attachments_json, parser_version, raw_html_path, raw_html_sha256, source_url, fetched_at, parsed_at)
            VALUES
            (:id, :content, :attachments_json, :parser_version, :raw_html_path, :raw_html_sha256, :source_url, :fetched_at, :parsed_at)
            ON CONFLICT(id) DO UPDATE SET
                content=excluded.content,
                attachments_json=excluded.attachments_json,
                parser_version=excluded.parser_version,
                raw_html_path=excluded.raw_html_path,
                raw_html_sha256=excluded.raw_html_sha256,
                source_url=excluded.source_url,
                fetched_at=excluded.fetched_at,
                parsed_at=excluded.parsed_at
            """
        , row)
        conn.commit()


