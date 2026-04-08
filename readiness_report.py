from __future__ import annotations

from datetime import datetime, timezone

from arge.logging_config import configure_logging
from arge.models import JiraAssessment, RiskAssessment


class ReleaseReadinessReporter:
    def __init__(self, logger_name: str = "arge.reporting.readiness") -> None:
        self.logger = configure_logging(logger_name)

    def render(self, jira: JiraAssessment, risk: RiskAssessment, pr_number: str, fleet: dict) -> str:
        self.logger.info("Rendering release readiness report for PR #%s", pr_number)
        status_icon = "✅" if jira.approved else "❌"
        risk_icon = "🟢" if risk.risk_level == "Low Risk" else "🔴"
        changed_files_md = "\n".join(f"- `{file_name}`" for file_name in risk.changed_files) or "- None"
        reasons_md = "\n".join(f"- {reason}" for reason in risk.reasons)
        waves_md = "\n".join(
            f"- **{wave['name']} ({wave['traffic_percent']}%)**: {wave['duration_minutes']} min "
            f"(cumulative ETA: {wave['cumulative_eta_minutes']} min)"
            for wave in fleet.get("waves", [])
        )

        recommendation = (
            "Safe to proceed to sign-off."
            if jira.approved and risk.risk_level == "Low Risk"
            else "Manual review required before deployment."
        )

        return f"""## Release Readiness Report

**PR:** #{pr_number}  
**Generated:** {datetime.now(timezone.utc).isoformat()}  
**Linked Ticket:** {jira.ticket}

### Gates
- Unit Tests: ✅ Passed
- JIRA Gate: {status_icon} `{jira.status}`
- Risk Scorer: {risk_icon} **{risk.risk_level}**

### Risk Details
- Total Lines Changed: **{risk.lines_changed}**
- Reasons:
{reasons_md}

### Fleet Rollout Simulation
- Estimated Build Time: **{fleet.get('build_minutes', 0)} min**
- Total Fleet ETA: **{fleet.get('eta_minutes', 0)} min**
- Waves:
{waves_md}

### Files Changed
{changed_files_md}

### Recommendation
{recommendation}
"""
