from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from arge.logging_config import configure_logging
from arge.models import JiraAssessment, RiskAssessment
from arge.release.fleet_rollout import FleetRolloutSimulation


class ReleaseMetadataStore:
    def __init__(self, path: str | Path, logger_name: str = "arge.release.metadata") -> None:
        self.path = Path(path)
        self.logger = configure_logging(logger_name)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            self.logger.warning("Metadata file %s does not exist. Initializing a fresh store.", self.path)
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.logger.info("Persisted release metadata to %s", self.path)

    @staticmethod
    def increment_version(version: str) -> str:
        prefix, patch = version.rsplit(".", 1)
        return f"{prefix}.{int(patch) + 1}"

    def update(
        self,
        jira: JiraAssessment,
        risk: RiskAssessment,
        pr_number: str,
        fleet_simulation: FleetRolloutSimulation,
        data_source: str = "Mock Simulation",
    ) -> dict[str, Any]:
        metadata = self.load()
        current_version = metadata.get("current_release_version", "v1.0.0")
        new_version = self.increment_version(current_version)
        timestamp = datetime.now(timezone.utc).isoformat()
        build_minutes = fleet_simulation.estimate_build_minutes(risk.lines_changed, risk.risk_level)
        fleet = fleet_simulation.simulate(build_minutes=build_minutes, approved=jira.approved)

        signoffs = {
            "QA": "Pending" if jira.approved else "Blocked",
            "Engineering": "Approved" if jira.approved else "Blocked",
            "Product": "Approved" if jira.approved else "Pending",
        }

        entry = {
            "timestamp": timestamp,
            "version": new_version,
            "ticket": jira.ticket,
            "jira_status": jira.status,
            "risk_level": risk.risk_level,
            "pr_number": pr_number,
            "lines_changed": risk.lines_changed,
            "fleet_eta_minutes": fleet["eta_minutes"],
            "data_source": data_source,
        }

        metadata["current_release_version"] = new_version
        metadata["data_source"] = data_source
        metadata["last_updated"] = timestamp
        metadata["signoffs"] = signoffs
        metadata["fleet_rollout"] = fleet
        metadata["latest_report"] = {
            "ticket": jira.ticket,
            "jira_status": jira.status,
            "risk_level": risk.risk_level,
            "changed_files": risk.changed_files,
            "lines_changed": risk.lines_changed,
            "pr_number": pr_number,
            "sensitive_files_touched": risk.sensitive_files_touched,
            "data_source": data_source,
        }
        metadata.setdefault("history", []).append(entry)
        self.save(metadata)
        return metadata
