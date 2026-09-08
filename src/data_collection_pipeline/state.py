"""증분 수집을 위한 마지막 처리 상태 저장."""

import json

from .config import settings

STATE_FILE = settings.state_dir / "crawl_state.json"


def load_seen_urls() -> set[str]:
    if not STATE_FILE.exists():
        return set()

    data = json.loads(
        STATE_FILE.read_text(encoding="utf-8")
    )
    return set(data.get("seen_detail_urls", []))


def save_seen_urls(urls: set[str]) -> None:
    settings.state_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    payload = {
        "seen_detail_urls": sorted(urls),
    }
    STATE_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
