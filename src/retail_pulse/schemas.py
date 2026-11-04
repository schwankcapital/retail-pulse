from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Product(StrictModel):
    store_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    sku: str = Field(min_length=1, max_length=64)
    upc: str = Field(pattern=r"^[0-9]{8,14}$")
    title: str = Field(min_length=1, max_length=160)
    zone_id: str
    camera_id: str
    shelf_capacity: int = Field(ge=1, le=10000)
    case_pack: int = Field(ge=1, le=1000)
    lead_days: int = Field(ge=0, le=90)
    roi: list[float] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def valid_roi(self):
        x1, y1, x2, y2 = self.roi
        if not 0 <= x1 < x2 <= 1 or not 0 <= y1 < y2 <= 1:
            raise ValueError("ROI is [x1,y1,x2,y2] normalized to [0,1]")
        return self


class Timed(StrictModel):
    at: datetime

    @field_validator("at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None:
            raise ValueError("Timestamp must include UTC offset; normalize source time before ingestion")
        return value.astimezone(timezone.utc)


class Transaction(Timed):
    event_id: str
    store_id: str
    sku: str
    kind: Literal["opening", "receipt", "sale", "return", "disposal", "adjustment"]
    quantity: int
    source: str = "csv"
    business_ref: str = ""

    @model_validator(mode="after")
    def positive(self):
        if self.kind != "adjustment" and self.quantity < 0:
            raise ValueError("Only adjustments may be negative")
        return self

    @property
    def delta(self) -> int:
        return -self.quantity if self.kind in {"sale", "disposal"} else self.quantity


class Observation(Timed):
    observation_id: str
    store_id: str
    sku: str
    zone_id: str
    end_at: datetime
    kind: Literal["shelf_state", "removal", "restock", "misplacement", "damage", "count"]
    availability: Literal["available", "unavailable", "unknown"] = "unknown"
    count_min: int | None = Field(default=None, ge=0, le=100000)
    count_max: int | None = Field(default=None, ge=0, le=100000)
    count_scope: Literal["visible", "shelf", "whole_store_verified"] = "visible"
    confidence: float = Field(ge=0, le=1)
    visibility: float = Field(ge=0, le=1)
    evidence_id: str
    origin: Literal["demo_replay", "muse", "manual"]
    note: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def consistency(self):
        if self.end_at.tzinfo is None:
            raise ValueError("end_at must include timezone")
        self.end_at = self.end_at.astimezone(timezone.utc)
        if self.end_at <= self.at:
            raise ValueError("Observation end must be later than start")
        if (self.count_min is None) != (self.count_max is None):
            raise ValueError("Provide both count bounds or neither")
        if self.count_min is not None and self.count_min > self.count_max:
            raise ValueError("Count bounds are reversed")
        if self.count_scope == "whole_store_verified" and self.origin == "muse":
            raise ValueError("Muse cannot certify whole-store inventory from shelf footage")
        if self.kind != "shelf_state" and self.availability != "unknown":
            raise ValueError("Only shelf_state observations establish availability intervals")
        return self


class RFIDRead(Timed):
    read_id: str
    scan_id: str
    epc: str
    store_id: str
    sku: str
    zone_id: str = "store"


class BarcodeScan(Timed):
    scan_id: str
    store_id: str
    sku: str
    upc: str
    zone_id: str
    action: str = "observed"


class Evidence(StrictModel):
    evidence_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,128}$")
    path: str
    media_type: Literal["video", "image", "fixture"]
    store_id: str
    camera_id: str
    start_at: datetime
    duration_seconds: float = Field(ge=0)
    seconds_to_world: float = Field(default=1, gt=0)
    sha256: str
    synthetic: bool = False

    @field_validator("start_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None:
            raise ValueError("Evidence timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)


class VisualEvent(StrictModel):
    """The provider schema does not let an LLM choose its own evidence path or store."""
    sku: str
    zone_id: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    kind: Literal["shelf_state", "removal", "restock", "misplacement", "damage"]
    availability: Literal["available", "unavailable", "unknown"]
    count_min: int | None
    count_max: int | None
    confidence: float = Field(ge=0, le=1)
    visibility: float = Field(ge=0, le=1)
    note: str


class VisualBatch(StrictModel):
    events: list[VisualEvent]
    limitations: list[str]


class AgentAnswer(StrictModel):
    answer: str
    evidence_ids: list[str]
    metric_ids: list[str]
    caveats: list[str]
    suggested_actions: list[str]


class QueryRequest(StrictModel):
    question: str = Field(min_length=3, max_length=2000)
    store_id: str = "DEMO_01"
    mode: Literal["demo", "meta"] | None = None
    role: Literal["business", "health"] = "business"
