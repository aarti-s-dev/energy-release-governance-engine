from arge.gates.risk_scorer import RiskScorer


def test_high_risk_due_to_line_count() -> None:
    risk = RiskScorer().classify(80, ["service.py"])
    assert risk.risk_level == "High Risk"
    assert any("50 lines" in reason for reason in risk.reasons)


def test_high_risk_due_to_sensitive_file() -> None:
    risk = RiskScorer().classify(10, ["src/auth.py"])
    assert risk.risk_level == "High Risk"
    assert any("Sensitive files" in reason for reason in risk.reasons)


def test_low_risk() -> None:
    risk = RiskScorer().classify(10, ["src/app.py"])
    assert risk.risk_level == "Low Risk"
    assert risk.reasons == ["No high-risk signals detected"]
