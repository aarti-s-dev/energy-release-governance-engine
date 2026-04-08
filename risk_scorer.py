from __future__ import annotations

from pathlib import Path
from typing import Iterable

from arge.integrations.github import GitDiffProviderProtocol
from arge.logging_config import configure_logging
from arge.models import RiskAssessment


class RiskScorer:
    """Classify pull requests into release-risk buckets.

    Args:
        sensitive_files: Filenames considered sensitive.
        high_risk_threshold: Threshold above which line count becomes high risk.
        logger_name: Logger name to use.
    """

    def __init__(
        self,
        sensitive_files: Iterable[str] | None = None,
        high_risk_threshold: int = 50,
        logger_name: str = "arge.risk.scorer",
    ) -> None:
        self.sensitive_files = set(sensitive_files or {"auth.py", "permissions.py", "secrets.py", "settings.py"})
        self.high_risk_threshold = high_risk_threshold
        self.logger = configure_logging(logger_name)

    def classify(self, lines_changed: int, files: Iterable[str]) -> RiskAssessment:
        """Classify release risk for a set of changed files.

        Args:
            lines_changed: Total changed lines.
            files: Changed file paths.

        Returns:
            A risk assessment object.
        """
        files = list(files)
        file_names = {Path(file_path).name for file_path in files}
        reasons: list[str] = []

        self.logger.info(
            "Scoring release risk with threshold=%s files=%s lines_changed=%s",
            self.high_risk_threshold,
            len(files),
            lines_changed,
        )

        if lines_changed > self.high_risk_threshold:
            reasons.append(f"More than {self.high_risk_threshold} lines changed")

        sensitive_hits = sorted(file_names.intersection(self.sensitive_files))
        if sensitive_hits:
            reasons.append(f"Sensitive files changed: {', '.join(sensitive_hits)}")

        if reasons:
            self.logger.warning("High risk detected: %s", "; ".join(reasons))
            return RiskAssessment(
                risk_level="High Risk",
                reasons=reasons,
                changed_files=files,
                lines_changed=lines_changed,
                sensitive_files_touched=sensitive_hits,
            )

        self.logger.info("Low risk detected. No high-risk signals found.")
        return RiskAssessment(
            risk_level="Low Risk",
            reasons=["No high-risk signals detected"],
            changed_files=files,
            lines_changed=lines_changed,
            sensitive_files_touched=[],
        )


class PullRequestRiskAnalyzer:
    """High-level service that combines a diff provider with the risk scorer.

    Args:
        diff_provider: Provider for PR file and line change data.
        scorer: Risk scorer instance.
        logger_name: Logger name to use.
    """

    def __init__(
        self,
        diff_provider: GitDiffProviderProtocol,
        scorer: RiskScorer | None = None,
        logger_name: str = "arge.risk.analyzer",
    ) -> None:
        self.diff_provider = diff_provider
        self.scorer = scorer or RiskScorer()
        self.logger = configure_logging(logger_name)

    def analyze(self, base_sha: str, head_sha: str) -> RiskAssessment:
        """Analyze a pull request diff and return a risk assessment.

        Args:
            base_sha: Base commit SHA.
            head_sha: Head commit SHA.

        Returns:
            A risk assessment object.
        """
        self.logger.info("Analyzing pull request diff base_sha=%s head_sha=%s", base_sha, head_sha)
        files = self.diff_provider.get_changed_files(base_sha, head_sha)
        lines_changed = self.diff_provider.get_line_delta(base_sha, head_sha)
        return self.scorer.classify(lines_changed=lines_changed, files=files)
