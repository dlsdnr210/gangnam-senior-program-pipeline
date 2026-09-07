"""환경변수와 프로젝트 설정을 한 곳에서 관리한다."""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_DIR / ".env")


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {
        "1", "true", "yes", "y", "on"
    }


@dataclass(frozen=True)
class Settings:
    project_dir: Path = PROJECT_DIR

    base_domain: str = "https://www.gangnam.go.kr"
    list_url: str = (
        "https://www.gangnam.go.kr/office/gnsw/board/"
        "gnsw_www7/list.do"
    )
    mid: str = "gnsw_notice"

    start_page: int = _env_int("CRAWL_START_PAGE", 1)
    end_page: int = _env_int("CRAWL_END_PAGE", 15)

    request_interval: float = _env_float("REQUEST_INTERVAL", 0.5)
    connect_timeout: int = _env_int("CONNECT_TIMEOUT", 5)
    read_timeout: int = _env_int("READ_TIMEOUT", 30)
    max_retries: int = _env_int("MAX_RETRIES", 3)
    backoff_factor: float = _env_float("BACKOFF_FACTOR", 0.8)

    db_enabled: bool = _env_bool("DB_ENABLED", False)
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = _env_int("DB_PORT", 3306)
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "senior_program_db")

    center_name: str = "강남노인종합복지관"
    region: str = "서울특별시 강남구"

    @property
    def raw_list_dir(self) -> Path:
        return self.project_dir / "data" / "raw" / "list"

    @property
    def raw_detail_dir(self) -> Path:
        return self.project_dir / "data" / "raw" / "detail"

    @property
    def interim_dir(self) -> Path:
        return self.project_dir / "data" / "interim"

    @property
    def processed_dir(self) -> Path:
        return self.project_dir / "data" / "processed"

    @property
    def state_dir(self) -> Path:
        return self.project_dir / "data" / "state"

    @property
    def log_dir(self) -> Path:
        return self.project_dir / "logs"


settings = Settings()
