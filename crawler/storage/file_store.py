import hashlib
import os
import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

from .. import config
from ..fetcher import Fetcher


def safe_filename(name: str, max_len: int = 120) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:max_len] if len(name) > max_len else name


def md5_10(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:10]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def save_raw_html(source_url: str, title_hint: str, html: str) -> (str, str):
    """
    返回: (path, sha256)
    按 年/月 进行分层存储，文件名包含 url hash 与标题提示。
    """
    now = datetime.utcnow()
    year = str(now.year)
    month = f"{now.month:02d}"

    rel_dir = os.path.join(config.RAW_HTML_DIR, year, month)
    os.makedirs(rel_dir, exist_ok=True)

    base = safe_filename(title_hint) or "policy"
    suffix = md5_10(source_url)
    filename = f"{base}_{suffix}.html"
    out_path = os.path.join(rel_dir, filename)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    return out_path, sha256_text(html)


def download_attachment(url: str, fetcher: Fetcher, title_hint: Optional[str] = "") -> str:
    """
    下载附件到 attachments 目录；返回保存路径
    """
    resp = fetcher.get_response(url, stream=True)
    path = urlparse(url).path
    ext = os.path.splitext(path)[1] or ".bin"

    base = safe_filename(title_hint) if title_hint else "attachment"
    filename = f"{base}_{md5_10(url)}{ext}"
    out_path = os.path.join(config.ATTACH_DIR, filename)

    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 64):
            if chunk:
                f.write(chunk)
    return out_path


