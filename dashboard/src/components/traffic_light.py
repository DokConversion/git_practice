from enum import Enum
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import config


class KPIStatus(Enum):
    GREEN   = "green"
    YELLOW  = "yellow"
    RED     = "red"
    UNKNOWN = "grey"


STATUS_COLORS = {
    KPIStatus.GREEN:   config.COLOR_GREEN,
    KPIStatus.YELLOW:  config.COLOR_YELLOW,
    KPIStatus.RED:     config.COLOR_RED,
    KPIStatus.UNKNOWN: config.COLOR_GREY,
}

STATUS_EMOJI = {
    KPIStatus.GREEN:   "🟢",
    KPIStatus.YELLOW:  "🟡",
    KPIStatus.RED:     "🔴",
    KPIStatus.UNKNOWN: "⚫",
}

STATUS_LABEL = {
    KPIStatus.GREEN:   "On Track",
    KPIStatus.YELLOW:  "Leichte Abweichung",
    KPIStatus.RED:     "Kritische Abweichung",
    KPIStatus.UNKNOWN: "Kein Ziel gesetzt",
}


def compute_status(
    actual: float,
    target: float | None,
    direction: str,
    green_threshold: float = config.TRAFFIC_GREEN_PCT,
    yellow_threshold: float = config.TRAFFIC_YELLOW_PCT,
) -> KPIStatus:
    if target is None or target == 0:
        return KPIStatus.UNKNOWN

    if direction == "minimize":
        # Lower is better; over-target = bad
        deviation = (actual - target) / target
    elif direction == "maximize":
        # Higher is better; under-target = bad
        deviation = (target - actual) / target
    elif direction == "pace":
        # Pacing ratio vs 1.0 ideal (symmetric)
        deviation = abs(actual - target) / target
    else:
        return KPIStatus.UNKNOWN

    deviation = max(deviation, 0.0)  # beating target = green

    if deviation <= green_threshold:
        return KPIStatus.GREEN
    elif deviation <= yellow_threshold:
        return KPIStatus.YELLOW
    else:
        return KPIStatus.RED


def worst_status(statuses: list[KPIStatus]) -> KPIStatus:
    priority = [KPIStatus.RED, KPIStatus.YELLOW, KPIStatus.GREEN, KPIStatus.UNKNOWN]
    for s in priority:
        if s in statuses:
            return s
    return KPIStatus.UNKNOWN
