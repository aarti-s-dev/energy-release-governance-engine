from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

DATA_FILE = Path("release_metadata.json")

st.set_page_config(page_title="ARGE Stakeholder Hub", layout="wide")


def load_data() -> dict:
    """Load dashboard metadata from disk.

    Returns:
        Parsed metadata dictionary.
    """
    if not DATA_FILE.exists():
        return {}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def status_chip(label: str, value: str) -> str:
    """Render a compact status chip string.

    Args:
        label: Entity label.
        value: Human-readable state.

    Returns:
        Decorated status string.
    """
    emoji = {
        "Approved": "✅",
        "Pending": "🟡",
        "Blocked": "⛔",
        "Queued": "🚚",
        "Not Started": "⚪",
        "Live API": "🟢",
        "Mock Simulation": "🧪",
    }.get(value, "ℹ️")
    return f"{label}: {emoji} {value}"


data = load_data()
latest = data.get("latest_report", {})
fleet = data.get("fleet_rollout", {})
data_source = data.get("data_source", latest.get("data_source", "Mock Simulation"))

st.sidebar.title("Runtime Status")
st.sidebar.success(status_chip("Data Source", data_source))
st.sidebar.caption("Live API mode is used only when the expected credentials are present.")

st.title("Automated Release Governance Engine")
st.caption("Stakeholder Hub")

col1, col2, col3 = st.columns(3)
col1.metric("Current Release Version", data.get("current_release_version", "v1.0.0"))
col2.metric("Fleet Rollout ETA (min)", fleet.get("eta_minutes", 0))
col3.metric("JIRA Gate", latest.get("jira_status", "Unknown"))

st.subheader("Sign-offs")
signoffs = data.get("signoffs", {})
qa, eng, prod = st.columns(3)
qa.info(status_chip("QA", signoffs.get("QA", "Pending")))
eng.info(status_chip("Engineering", signoffs.get("Engineering", "Pending")))
prod.info(status_chip("Product", signoffs.get("Product", "Pending")))

st.subheader("Latest Release Readiness Snapshot")
left, right = st.columns([2, 1])
with left:
    st.write(f"**Linked Ticket:** {latest.get('ticket', '')}")
    st.write(f"**PR Number:** {latest.get('pr_number', '')}")
    st.write(f"**Risk Level:** {latest.get('risk_level', '')}")
    st.write(f"**Lines Changed:** {latest.get('lines_changed', 0)}")
    st.write(f"**Data Source:** {latest.get('data_source', data_source)}")
    st.write("**Changed Files:**")
    st.code("\n".join(latest.get("changed_files", [])) or "No files captured")
with right:
    st.success(status_chip(fleet.get("name", "Fleet Rollout Simulation"), fleet.get("status", "Unknown")))
    st.metric("Estimated Build Time", fleet.get("build_minutes", 0))

st.subheader("Fleet Rollout Simulation")
if fleet.get("waves"):
    st.dataframe(fleet["waves"], use_container_width=True)
else:
    st.write("No rollout simulation available yet.")

st.subheader("Release History")
history = data.get("history", [])
if history:
    st.dataframe(history, use_container_width=True)
else:
    st.write("No release history yet.")

last_updated = data.get("last_updated")
if last_updated:
    try:
        ts = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        st.caption(f"Last updated: {ts.isoformat()}")
    except ValueError:
        st.caption(f"Last updated: {last_updated}")
