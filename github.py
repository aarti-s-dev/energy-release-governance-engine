from __future__ import annotations

import os
import subprocess
from typing import Any, Protocol

import requests

from arge.logging_config import configure_logging
from arge.utils.env import env_vars_present, log_mock_mode


class GitDiffProviderProtocol(Protocol):
    """Protocol for pull-request diff providers."""

    def get_changed_files(self, base_sha: str, head_sha: str) -> list[str]:
        """Return changed files between two revisions."""

    def get_line_delta(self, base_sha: str, head_sha: str) -> int:
        """Return total added plus deleted lines between two revisions."""


class MockGitDiffProvider:
    """Git-based diff provider for local and fork-safe demonstration runs.

    Args:
        logger_name: Logger name to use.
    """

    def __init__(self, logger_name: str = "arge.github.diff.mock") -> None:
        self.logger = configure_logging(logger_name)

    def get_changed_files(self, base_sha: str, head_sha: str) -> list[str]:
        """Read changed files from git diff.

        Args:
            base_sha: Base commit SHA.
            head_sha: Head commit SHA.

        Returns:
            A list of changed file paths.
        """
        cmd = ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"]
        self.logger.info("Running mock diff command: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def get_line_delta(self, base_sha: str, head_sha: str) -> int:
        """Read total line delta from git diff.

        Args:
            base_sha: Base commit SHA.
            head_sha: Head commit SHA.

        Returns:
            Total added plus deleted lines.
        """
        cmd = ["git", "diff", "--numstat", f"{base_sha}...{head_sha}"]
        self.logger.info("Running mock numstat command: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        total = 0
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                added = 0 if parts[0] == "-" else int(parts[0])
                deleted = 0 if parts[1] == "-" else int(parts[1])
                total += added + deleted
        return total


class RealGitHubClient:
    """GitHub REST client for reading pull-request file changes.

    Args:
        token: GitHub token.
        repository: Repository in owner/name format.
        pr_number: Pull request number.
        timeout_seconds: HTTP timeout in seconds.
        logger_name: Logger name to use.
    """

    def __init__(
        self,
        token: str,
        repository: str,
        pr_number: str,
        timeout_seconds: int = 10,
        logger_name: str = "arge.github.diff.real",
    ) -> None:
        self.token = token
        self.repository = repository
        self.pr_number = pr_number
        self.timeout_seconds = timeout_seconds
        self.logger = configure_logging(logger_name)

    def _fetch_pr_files(self) -> list[dict[str, Any]]:
        """Fetch all changed files for a pull request.

        Returns:
            A list of GitHub PR file payloads.
        """
        owner, repo = self.repository.split("/", 1)
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{self.pr_number}/files"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        page = 1
        files: list[dict[str, Any]] = []
        while True:
            self.logger.info("Fetching live GitHub PR files page=%s pr=%s", page, self.pr_number)
            response = requests.get(url, headers=headers, params={"per_page": 100, "page": page}, timeout=self.timeout_seconds)
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            files.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return files

    def get_changed_files(self, base_sha: str, head_sha: str) -> list[str]:
        """Return changed filenames for a live pull request.

        Args:
            base_sha: Unused for live API mode.
            head_sha: Unused for live API mode.

        Returns:
            A list of changed file paths.
        """
        del base_sha, head_sha
        return [item.get("filename", "") for item in self._fetch_pr_files() if item.get("filename")]

    def get_line_delta(self, base_sha: str, head_sha: str) -> int:
        """Return total line delta for a live pull request.

        Args:
            base_sha: Unused for live API mode.
            head_sha: Unused for live API mode.

        Returns:
            Total added plus deleted lines.
        """
        del base_sha, head_sha
        return sum(int(item.get("additions", 0)) + int(item.get("deletions", 0)) for item in self._fetch_pr_files())


class GitDiffProviderFactory:
    """Factory that returns live or mock GitHub diff providers."""

    REQUIRED_ENV_VARS = ("GH_TOKEN", "GITHUB_REPOSITORY", "PR_NUMBER")

    @classmethod
    def create(cls, logger_name: str = "arge.github.diff.factory") -> tuple[GitDiffProviderProtocol, str]:
        """Create the best available diff provider.

        Args:
            logger_name: Logger name to use.

        Returns:
            A tuple containing the provider and the source label.
        """
        logger = configure_logging(logger_name)
        if env_vars_present(cls.REQUIRED_ENV_VARS):
            logger.info("GitHub credentials detected: using live GitHub REST API client.")
            return (
                RealGitHubClient(
                    token=os.environ["GH_TOKEN"],
                    repository=os.environ["GITHUB_REPOSITORY"],
                    pr_number=os.environ["PR_NUMBER"],
                ),
                "Live API",
            )

        missing = [name for name in cls.REQUIRED_ENV_VARS if not os.getenv(name)]
        log_mock_mode(missing)
        return MockGitDiffProvider(), "Mock Simulation"
