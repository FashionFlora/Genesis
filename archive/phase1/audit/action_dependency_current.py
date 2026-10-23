"""Differential probe for resource_flow_return_action's Snake action state."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "candidates/resource_flow_return_action/principle.py"


def load():
    spec = importlib.util.spec_from_file_location("resource_flow_return_action_probe", PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.System


def obs(apple=None, extra_body=None):
    row = [0] * 700
    # Direction plane 0: head at (5, 5); body plane 4.
    row[55] = 1
    row[400 + 55] = 1
    if extra_body is not None:
        row[400 + extra_body] = 1
    if apple is not None:
        row[500 + apple] = 1
    return row


def trace(second):
    system = load()()
    first_action = system.act(obs(11))
    second_action = system.act(second)
    return {
        "first_action": first_action,
        "second_action": second_action,
        "action_mass_after_second": list(system.action_mass),
    }


def main():
    baseline = trace(obs(11))
    apple_toggle = trace(obs(12))
    body_toggle = trace(obs(11, extra_body=56))
    result = {
        "test": "differential action-resource dependency",
        "baseline_same_apple": baseline,
        "apple_only_toggle": apple_toggle,
        "body_only_toggle": body_toggle,
        "apple_mass_delta": [b - a for a, b in zip(
            baseline["action_mass_after_second"], apple_toggle["action_mass_after_second"]
        )],
        "body_mass_delta": [b - a for a, b in zip(
            baseline["action_mass_after_second"], body_toggle["action_mass_after_second"]
        )],
    }
    out = ROOT / "audit/action_dependency_current_result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
