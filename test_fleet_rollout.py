from arge.release.fleet_rollout import FleetRolloutSimulation


def test_fleet_rollout_uses_three_canary_waves() -> None:
    simulation = FleetRolloutSimulation().simulate(build_minutes=12, approved=True)
    wave_names = [wave["name"] for wave in simulation["waves"]]
    assert wave_names == ["Canary", "Ramp", "Fleet"]
    traffic = [wave["traffic_percent"] for wave in simulation["waves"]]
    assert traffic == [1, 10, 100]


def test_build_time_increases_for_high_risk_changes() -> None:
    sim = FleetRolloutSimulation()
    assert sim.estimate_build_minutes(lines_changed=90, risk_level="High Risk") > sim.estimate_build_minutes(lines_changed=10, risk_level="Low Risk")
