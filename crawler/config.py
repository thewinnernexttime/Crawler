import os
import random
from datetime import datetime

# API 与会话配置
API_URL = "https://sousuo.www.gov.cn/search-gov/data"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://sousuo.www.gov.cn/zcwjk/policyDocumentLibrary?q=&t=zhengcelibrary&orpro=",
}

# 可通过环境变量覆盖敏感 Cookie，例如：export CRAWLER_TFSTK="xxx"
DEFAULT_COOKIES = {
    "wdcid": os.getenv("CRAWLER_WDCID", "6f8bb86d9f9d20c1"),
    "tfstk": os.getenv("CRAWLER_TFSTK", "XXX"),
    "ariatheme": "0",
    "ariaStatus": "false",
    "ariafontScale": "1",
}

# 速率与重试
RETRY_MAX = 3
RETRY_BACKOFF_BASE = 1.5
RETRY_BACKOFF_JITTER = 0.3  # 额外抖动

LIST_REQUEST_INTERVAL_SEC = 0.8
DETAIL_REQUEST_INTERVAL_MIN = 1.0
DETAIL_REQUEST_INTERVAL_MAX = 2.5
DETAIL_REQUEST_EXTRA_SLEEP_EVERY = 20
DETAIL_REQUEST_EXTRA_SLEEP_SEC = 5.0

# 质量阈值
MIN_CONTENT_LENGTH = 200

# 解析器版本（页面结构变更时，手动提升版本号）
PARSER_VERSION = "v1"

# 路径配置
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "crawler.db")

GOV_BASE_DIR = os.path.join(PROJECT_ROOT, "gov_policies")
DETAILS_DIR = os.path.join(GOV_BASE_DIR, "details")
ATTACH_DIR = os.path.join(GOV_BASE_DIR, "attachments")
RAW_HTML_DIR = os.path.join(GOV_BASE_DIR, "raw_html")
for d in (GOV_BASE_DIR, DETAILS_DIR, ATTACH_DIR, RAW_HTML_DIR):
    os.makedirs(d, exist_ok=True)


def random_detail_interval() -> float:
    return random.uniform(DETAIL_REQUEST_INTERVAL_MIN, DETAIL_REQUEST_INTERVAL_MAX)


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


