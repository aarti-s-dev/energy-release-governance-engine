from __future__ import annotations

import json
import re
from pathlib import Path

from arge.integrations.jira import JiraClientProtocol
from arge.logging_config import configure_logging
from arge.models import JiraAssessment


class TicketExtractor:
    """Extract JIRA ticket identifiers from GitHub metadata."""

    TICKET_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")

    @classmethod
    def extract_ticket(cls, text: str | None) -> str | None:
        """Extract a JIRA ticket from free-form text.

        Args:
            text: Branch name, PR title, or PR body.

        Returns:
            The first matching ticket ID, or None.
        """
        match = cls.TICKET_RE.search(text or "")
        return match.group(1) if match else None

    @classmethod
    def from_github_event(cls, event_path: str | Path | None) -> tuple[str | None, str]:
        """Extract a JIRA ticket from a GitHub event payload.

        Args:
            event_path: Path to the GitHub event JSON file.

        Returns:
            A tuple of (ticket, source_field).
        """
        if not event_path or not Path(event_path).exists():
            return None, "event_path_unavailable"

        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        pull_request = event.get("pull_request", {})
        head = pull_request.get("head", {})
        candidates = [
            (head.get("ref", ""), "pull_request.head.ref"),
            (pull_request.get("title", ""), "pull_request.title"),
            (pull_request.get("body", ""), "pull_request.body"),
            (event.get("ref_name") or event.get("ref", ""), "event.ref"),
        ]

        for candidate, source in candidates:
            ticket = cls.extract_ticket(candidate)
            if ticket:
                return ticket, source
        return None, "not_found"


class JiraGate:
    """Release gate that validates linked JIRA approval state.

    Args:
        jira_client: Client used to fetch JIRA issue data.
        logger_name: Logger name to use.
    """

    def __init__(self, jira_client: JiraClientProtocol, logger_name: str = "arge.jira.gate") -> None:
        self.jira_client = jira_client
        self.logger = configure_logging(logger_name)

    def evaluate(self, ticket: str, source: str = "environment") -> JiraAssessment:
        """Evaluate whether a ticket is approved for release.

        Args:
            ticket: JIRA ticket identifier.
            source: Where the ticket was discovered.

        Returns:
            A JIRA assessment describing the gate outcome.

        Raises:
            ValueError: If the ticket does not exist.
        """
        self.logger.info("Evaluating JIRA gate for ticket=%s source=%s", ticket, source)
        issue = self.jira_client.get_issue(ticket)
        if not issue:
            self.logger.error("Ticket %s was not found in JIRA data source", ticket)
            raise ValueError(f"Ticket {ticket} not found in configured JIRA data source")

        status = issue.get("status", "Unknown")
        ALLOWED_STATUSES = {"Approved", "Done", "Resolved"}
        approved = status in ALLOWED_STATUSES
        if approved:
            self.logger.info("JIRA gate passed: ticket=%s status=%s", ticket, status)
        else:
            self.logger.warning("JIRA gate blocked: ticket=%s status=%s", ticket, status)
        return JiraAssessment(ticket=ticket, status=status, approved=approved, source=source)
