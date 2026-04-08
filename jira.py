from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol

import requests

from arge.logging_config import configure_logging
from arge.utils.env import env_vars_present, log_mock_mode


class JiraClientProtocol(Protocol):
    """Protocol for JIRA issue clients."""

    def get_issue(self, ticket: str) -> dict[str, Any] | None:
        """Fetch issue metadata for a ticket.

        Args:
            ticket: JIRA ticket identifier such as ARGE-123.

        Returns:
            The issue payload when found, otherwise None.
        """


class MockJiraClient:
    """Mock JIRA client backed by a local JSON file.

    Args:
        data_file: Path to the mock issue dataset.
        logger_name: Logger name to use.
    """

    def __init__(self, data_file: str | Path, logger_name: str = "arge.jira.client.mock") -> None:
        self.data_file = Path(data_file)
        self.logger = configure_logging(logger_name)

    def get_issue(self, ticket: str) -> dict[str, Any] | None:
        """Load an issue from mock data.

        Args:
            ticket: JIRA ticket identifier.

        Returns:
            The issue payload when present, otherwise None.
        """
        self.logger.info("Loading mock JIRA data from %s", self.data_file)
        data = json.loads(self.data_file.read_text(encoding="utf-8"))
        return data.get(ticket)


class RealJiraClient:
    """JIRA client that fetches issue data from Atlassian Cloud.

    Args:
        domain: Atlassian site domain prefix.
        email: Atlassian account email for basic auth.
        api_token: Atlassian API token.
        timeout_seconds: HTTP timeout in seconds.
        logger_name: Logger name to use.
    """

    def __init__(
        self,
        domain: str,
        email: str,
        api_token: str,
        timeout_seconds: int = 10,
        logger_name: str = "arge.jira.client.real",
    ) -> None:
        self.domain = domain
        self.email = email
        self.api_token = api_token
        self.timeout_seconds = timeout_seconds
        self.logger = configure_logging(logger_name)

    def get_issue(self, ticket: str) -> dict[str, Any] | None:
        """Fetch an issue from the live JIRA REST API.

        Args:
            ticket: JIRA ticket identifier.

        Returns:
            A normalized issue payload or None when not found.
        """
        url = f"https://{self.domain}.atlassian.net/rest/api/3/issue/{ticket}"
        self.logger.info("Fetching live JIRA issue %s", ticket)
        response = requests.get(
            url,
            auth=(self.email, self.api_token),
            headers={"Accept": "application/json"},
            timeout=self.timeout_seconds,
        )
        if response.status_code == 404:
            self.logger.warning("Live JIRA issue %s was not found", ticket)
            return None
        response.raise_for_status()
        payload = response.json()
        return {
            "key": payload.get("key", ticket),
            "status": payload.get("fields", {}).get("status", {}).get("name", "Unknown"),
            "summary": payload.get("fields", {}).get("summary", ""),
        }


class JiraClientFactory:
    """Factory that returns live or mock JIRA clients based on environment state."""

    REQUIRED_ENV_VARS = ("JIRA_DOMAIN", "JIRA_USER_EMAIL", "JIRA_API_TOKEN")

    @classmethod
    def create(
        cls,
        mock_data_file: str | Path,
        logger_name: str = "arge.jira.client.factory",
    ) -> tuple[JiraClientProtocol, str]:
        """Create the best available JIRA client.

        Args:
            mock_data_file: Path to the mock issue dataset.
            logger_name: Logger name to use.

        Returns:
            A tuple containing the client and the source label.
        """
        logger = configure_logging(logger_name)
        if env_vars_present(cls.REQUIRED_ENV_VARS):
            logger.info("JIRA credentials detected: using live Atlassian API client.")
            return (
                RealJiraClient(
                    domain=os.environ["JIRA_DOMAIN"],
                    email=os.environ["JIRA_USER_EMAIL"],
                    api_token=os.environ["JIRA_API_TOKEN"],
                ),
                "Live API",
            )

        missing = [name for name in cls.REQUIRED_ENV_VARS if not os.getenv(name)]
        log_mock_mode(missing)
        return MockJiraClient(mock_data_file), "Mock Simulation"
