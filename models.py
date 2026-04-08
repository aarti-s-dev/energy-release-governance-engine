from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class JiraAssessment:
    ticket: str
    status: str
    approved: bool
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RiskAssessment:
    risk_level: str
    reasons: list[str]
    changed_files: list[str]
    lines_changed: int
    sensitive_files_touched: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FleetWave:
    name: str
    traffic_percent: int
    duration_minutes: int
    cumulative_eta_minutes: int
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
