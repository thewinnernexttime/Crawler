import time
from typing import Any, Dict, Optional

import requests

from . import config


class Fetcher:
    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        proxies: Optional[Dict[str, str]] = None,
        timeout: int = 20,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(headers or config.DEFAULT_HEADERS)
        if cookies:
            self.session.cookies.update(cookies)
        else:
            self.session.cookies.update(config.DEFAULT_COOKIES)
        if proxies:
            self.session.proxies.update(proxies)

        self.timeout = timeout

    def _sleep_for_backoff(self, attempt: int) -> None:
        sleep_sec = (config.RETRY_BACKOFF_BASE ** attempt) + (config.RETRY_BACKOFF_JITTER * attempt)
        time.sleep(sleep_sec)

    def _handle_status_delay(self, status_code: int) -> None:
        if status_code == 403:
            # 降级：延迟较长，便于避开限制
            time.sleep(5.0)
        elif status_code == 429:
            # 明显限流：更多延迟
            time.sleep(10.0)

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        last_error = None
        for attempt in range(config.RETRY_MAX + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code in (403, 429):
                    self._handle_status_delay(resp.status_code)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_error = e
                if attempt >= config.RETRY_MAX:
                    break
                self._sleep_for_backoff(attempt + 1)
        raise RuntimeError(f"GET JSON failed after retries: {last_error}")

    def get_text(self, url: str, accept: Optional[str] = None) -> str:
        last_error = None
        for attempt in range(config.RETRY_MAX + 1):
            try:
                headers = dict(self.session.headers)
                if accept:
                    headers["Accept"] = accept
                resp = self.session.get(url, headers=headers, timeout=self.timeout)
                if resp.status_code in (403, 429):
                    self._handle_status_delay(resp.status_code)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or "utf-8"
                return resp.text
            except Exception as e:
                last_error = e
                if attempt >= config.RETRY_MAX:
                    break
                self._sleep_for_backoff(attempt + 1)
        raise RuntimeError(f"GET TEXT failed after retries: {last_error}")

    def get_response(self, url: str, stream: bool = False) -> requests.Response:
        last_error = None
        for attempt in range(config.RETRY_MAX + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout, stream=stream)
                if resp.status_code in (403, 429):
                    self._handle_status_delay(resp.status_code)
                resp.raise_for_status()
                return resp
            except Exception as e:
                last_error = e
                if attempt >= config.RETRY_MAX:
                    break
                self._sleep_for_backoff(attempt + 1)
        raise RuntimeError(f"GET response failed after retries: {last_error}")


