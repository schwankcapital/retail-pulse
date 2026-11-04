from __future__ import annotations

import os
import math
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


def flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).lower().strip()
    if value not in {"true", "false", "1", "0", "yes", "no"}:
        raise ValueError(f"{name} must be true or false")
    return value in {"true", "1", "yes"}


@dataclass(frozen=True)
class Settings:
    home: Path = Path("runtime")
    mode: str = "demo"
    api_key: str = field(default="", repr=False)
    base_url: str = "https://api.meta.ai/v1"
    muse_model: str = "muse-spark-1.3"
    sam_model: str = "sam-3.1"
    external_media: bool = False
    contributor: bool = False
    budget: float = 20.0
    reservation: float = 0.50
    input_price: float = 1.25
    cache_price: float = 0.15
    output_price: float = 4.25
    sam_image_price: float = 0.0025
    sam_frame_price: float = 0.0002
    max_rounds: int = 5
    max_tokens: int = 5000
    timeout: float = 180.0
    max_media_mb: int = 25
    max_video_seconds: int = 90
    api_token: str = field(default="", repr=False)
    timezone: str = "America/Denver"
    open_hour: int = 8
    close_hour: int = 20
    min_confidence: float = 0.75
    min_visibility: float = 0.70
    rfid_detection_probability: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "home", Path(self.home).resolve())
        if self.mode not in {"demo", "meta"}:
            raise ValueError("Mode must be demo or meta")
        ZoneInfo(self.timezone)
        for name in ("budget", "reservation", "input_price", "cache_price", "output_price",
                     "sam_image_price", "sam_frame_price", "timeout"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite nonnegative number")
        if self.timeout <= 0 or self.max_tokens < 1 or self.max_media_mb < 1 or self.max_video_seconds < 1:
            raise ValueError("Timeout, token limit and media limits must be positive")
        if not 0 <= self.open_hour < self.close_hour <= 24:
            raise ValueError("Require 0 <= OPEN_HOUR < CLOSE_HOUR <= 24")
        if self.budget <= 0 or self.reservation <= 0 or not 1 <= self.max_rounds <= 12:
            raise ValueError("Invalid budget, reservation, or agent-round limit")
        if self.rfid_detection_probability is not None and not 0 < self.rfid_detection_probability < 1:
            raise ValueError("RFID probability must be strictly between 0 and 1")
        if not (0 <= self.min_confidence <= 1 and 0 <= self.min_visibility <= 1):
            raise ValueError("Confidence/visibility thresholds must be in [0, 1]")
        if "contributor" in self.muse_model and not self.contributor:
            raise ValueError("Contributor mode requires explicit ALLOW_CONTRIBUTOR_MODE=true")
        if self.base_url != "https://api.meta.ai/v1":
            raise ValueError("Only the verified Meta API endpoint is allowed in this release")
        for sub in ("media", "reports", "models", "cache", "raw", "quarantine"):
            (self.home / sub).mkdir(parents=True, exist_ok=True)

    @property
    def db_path(self) -> Path:
        return self.home / "retail_pulse.sqlite3"

    @classmethod
    def from_env(cls, **overrides) -> "Settings":
        load_dotenv(override=False)
        p = os.getenv("RFID_DETECTION_PROBABILITY", "").strip()
        values = dict(
            home=Path(os.getenv("RETAIL_PULSE_HOME", "runtime")),
            mode=os.getenv("RETAIL_PULSE_MODE", "demo"), api_key=os.getenv("MODEL_API_KEY", ""),
            base_url=os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/"),
            muse_model=os.getenv("MUSE_MODEL", "muse-spark-1.3"),
            sam_model=os.getenv("SAM_MODEL", "sam-3.1"),
            external_media=flag("ALLOW_EXTERNAL_MEDIA"), contributor=flag("ALLOW_CONTRIBUTOR_MODE"),
            budget=float(os.getenv("API_BUDGET_USD", "20")),
            reservation=float(os.getenv("API_CALL_RESERVATION_USD", ".5")),
            input_price=float(os.getenv("MUSE_INPUT_USD_PER_MILLION", "1.25")),
            cache_price=float(os.getenv("MUSE_CACHED_USD_PER_MILLION", ".15")),
            output_price=float(os.getenv("MUSE_OUTPUT_USD_PER_MILLION", "4.25")),
            sam_image_price=float(os.getenv("SAM_IMAGE_USD", ".0025")),
            sam_frame_price=float(os.getenv("SAM_FRAME_USD", ".0002")),
            max_rounds=int(os.getenv("MAX_AGENT_ROUNDS", "5")),
            max_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "5000")),
            timeout=float(os.getenv("META_TIMEOUT_SECONDS", "180")),
            max_media_mb=int(os.getenv("MAX_MEDIA_MB", "25")),
            max_video_seconds=int(os.getenv("MAX_VIDEO_SECONDS", "90")),
            api_token=os.getenv("RETAIL_PULSE_API_TOKEN", ""),
            timezone=os.getenv("STORE_TIMEZONE", "America/Denver"),
            open_hour=int(os.getenv("OPEN_HOUR", "8")), close_hour=int(os.getenv("CLOSE_HOUR", "20")),
            min_confidence=float(os.getenv("MIN_OBSERVATION_CONFIDENCE", ".75")),
            min_visibility=float(os.getenv("MIN_VISIBILITY", ".70")),
            rfid_detection_probability=float(p) if p else None,
        )
        values.update(overrides)
        return cls(**values)
