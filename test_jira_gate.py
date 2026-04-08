from arge.gates.jira_gate import TicketExtractor


def test_extract_ticket_from_branch_name() -> None:
    assert TicketExtractor.extract_ticket("feature/ARGE-123-release-gate") == "ARGE-123"


def test_extract_ticket_missing() -> None:
    assert TicketExtractor.extract_ticket("feature/no-ticket") is None
