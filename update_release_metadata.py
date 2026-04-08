from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from arge.logging_config import configure_logging
from arge.models import JiraAssessment, RiskAssessment
from arge.release.fleet_rollout import FleetRolloutSimulation
from arge.release.metadata_store import ReleaseMetadataStore


logger = configure_logging("arge.cli.update_release_metadata")


def main() -> int:
    """Update the JSON metadata store for the dashboard.

    Returns:
        Process exit code.
    """
    load_dotenv()
    metadata_file = Path(os.getenv("RELEASE_METADATA_FILE", "release_metadata.json"))
    risk_input = Path(os.getenv("RISK_INPUT", "risk_report.json"))
    ticket = os.getenv("JIRA_TICKET", "Unknown")
    jira_status = os.getenv("JIRA_STATUS", "Unknown")
    pr_number = os.getenv("PR_NUMBER", "unknown")
    data_source = os.getenv("ARGE_DATA_SOURCE", "Mock Simulation")

    risk_payload = json.loads(risk_input.read_text(encoding="utf-8"))
    risk_payload.pop("data_source", None)
    risk = RiskAssessment(**risk_payload)
    jira = JiraAssessment(ticket=ticket, status=jira_status, approved=jira_status == "Approved", source="workflow")

    store = ReleaseMetadataStore(metadata_file)
    metadata = store.update(
        jira=jira,
        risk=risk,
        pr_number=pr_number,
        fleet_simulation=FleetRolloutSimulation(),
        data_source=data_source,
    )
    logger.info("Release metadata updated for PR #%s", pr_number)
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
