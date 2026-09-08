"""콘솔과 파일에 동시에 기록하는 로깅 설정."""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import settings


def setup_logger(name: str = "senior_pipeline") -> logging.Logger:
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    log_path = (
        settings.log_dir
        / f"pipeline_{datetime.now(ZoneInfo("Asia/Seoul")):%Y%m%d}.log"
    )
    file_handler = logging.FileHandler(
        log_path,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
