"""재시도와 타임아웃이 적용된 HTTP 클라이언트."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import settings

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}


def build_session() -> requests.Session:
    retry = Retry(
        total=settings.max_retries,
        connect=settings.max_retries,
        read=settings.max_retries,
        status=settings.max_retries,
        backoff_factor=settings.backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def fetch(session: requests.Session, url: str) -> requests.Response:
    response = session.get(
        url,
        timeout=(
            settings.connect_timeout,
            settings.read_timeout,
        ),
    )
    response.raise_for_status()
    return response
