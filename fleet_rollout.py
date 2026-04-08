from __future__ import annotations

import math

from arge.logging_config import configure_logging
from arge.models import FleetWave


class FleetRolloutSimulation:
    """Simulates a staged fleet rollout using canary waves."""

    def __init__(self, logger_name: str = "arge.release.fleet") -> None:
        self.logger = configure_logging(logger_name)
        self.wave_plan = (
            ("Canary", 1, 0.35),
            ("Ramp", 10, 0.75),
            ("Fleet", 100, 1.25),
        )

    def estimate_build_minutes(self, lines_changed: int, risk_level: str) -> int:
        base_minutes = 8
        size_penalty = math.ceil(lines_changed / 25)
        risk_penalty = 6 if risk_level == "High Risk" else 0
        build_minutes = max(5, base_minutes + size_penalty + risk_penalty)
        self.logger.info(
            "Estimated build time: %s minutes (lines_changed=%s risk_level=%s)",
            build_minutes,
            lines_changed,
            risk_level,
        )
        return build_minutes

    def simulate(self, build_minutes: int, approved: bool) -> dict:
        status = "Queued" if approved else "Blocked"
        cumulative = 0
        waves: list[FleetWave] = []

        self.logger.info("Simulating fleet rollout: build_minutes=%s approved=%s", build_minutes, approved)
        for name, traffic_percent, multiplier in self.wave_plan:
            duration = max(2, math.ceil(build_minutes * multiplier))
            cumulative += duration
            waves.append(
                FleetWave(
                    name=name,
                    traffic_percent=traffic_percent,
                    duration_minutes=duration,
                    cumulative_eta_minutes=cumulative,
                    status=status,
                )
            )

        return {
            "name": "Fleet Rollout Simulation",
            "build_minutes": build_minutes,
            "eta_minutes": cumulative,
            "status": status,
            "waves": [wave.to_dict() for wave in waves],
        }
