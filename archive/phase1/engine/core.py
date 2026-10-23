"""Small, dependency-light helpers shared by the Crafter runner."""

import math


def action_id(action, action_count):
    """Validate an action returned by an agent and normalize it to ``int``."""
    if action_count <= 0:
        raise ValueError("action_count must be positive")
    if isinstance(action, bool):
        raise TypeError("boolean values are not valid actions")
    try:
        value = int(action)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError(f"agent action must be an integer, got {type(action).__name__}") from exc
    if value != action or not 0 <= value < action_count:
        raise ValueError(f"action {action!r} is outside [0, {action_count})")
    return value


def crafter_score(success_rates):
    """Compute Crafter's geometric-mean achievement score from percent rates."""
    if not success_rates:
        raise ValueError("at least one achievement rate is required")
    values = [float(rate) for rate in success_rates.values()]
    if any(not math.isfinite(rate) or rate < 0 for rate in values):
        raise ValueError("achievement rates must be finite and non-negative")
    return math.expm1(sum(math.log1p(rate) for rate in values) / len(values))


def agent_info(info):
    """Return only the allowlisted, reward-free fields visible to a Crafter agent."""
    visible = {}
    for key in ("inventory", "discount", "semantic", "player_pos"):
        if key not in info:
            continue
        value = info[key]
        if key == "inventory":
            visible[key] = dict(value)
        elif key == "discount":
            visible[key] = float(value)
        elif hasattr(value, "copy"):
            visible[key] = value.copy()
        else:
            visible[key] = value
    return visible
