from __future__ import annotations

from arge.integrations.github import GitDiffProviderFactory, MockGitDiffProvider
from arge.integrations.jira import JiraClientFactory, MockJiraClient


def test_jira_factory_defaults_to_mock_when_env_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("JIRA_DOMAIN", raising=False)
    monkeypatch.delenv("JIRA_USER_EMAIL", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    mock_file = tmp_path / "mock_jira.json"
    mock_file.write_text('{}', encoding='utf-8')

    client, source = JiraClientFactory.create(mock_data_file=mock_file)

    assert isinstance(client, MockJiraClient)
    assert source == "Mock Simulation"


def test_github_factory_defaults_to_mock_when_env_missing(monkeypatch) -> None:
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("PR_NUMBER", raising=False)

    client, source = GitDiffProviderFactory.create()

    assert isinstance(client, MockGitDiffProvider)
    assert source == "Mock Simulation"
