"""Small, reproducible static/dynamic checks for organism candidates.

This audit deliberately avoids the judge writer: results are printed and can be
copied into the critic handoff without changing sandbox/leaderboard.jsonl.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "axiom_homeostasis": ROOT / "candidates/axiom_homeostasis/principle.py",
    "odkrywca_metabolic_trace": ROOT / "candidates/odkrywca_metabolic_trace/principle_organism.py",
    "growth_surprise": ROOT / "candidates/growth_surprise/principle_organism.py",
}


def source_flags(path: Path) -> dict[str, object]:
    text = path.read_text()
    tree = ast.parse(text)
    nums = [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))]
    return {
        "lines": len(text.splitlines()),
        "numeric_literals": len(nums),
        "hardcoded_last_sensor": "[:, -1]" in text,
        "fixed_eye_layout": "reshape(self.batch, 16, 3)" in text,
        "fixed_action_bias": any(x in text for x in ("0.35", "0.15", "0.05")),
        "stale_prune_test": "stale =" in text and "utility <" in text,
    }


def load(path: Path):
    spec = importlib.util.spec_from_file_location("audit_candidate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    print("candidate static flags")
    for name, path in TARGETS.items():
        print(name, source_flags(path))

    growth = load(TARGETS["growth_surprise"])
    # A no-interoception observation has exactly 48 eye values.  The candidate
    # still stores the final eye value as previous_energy, which is leakage.
    brain = growth.OrganismBrain(302, 48, 3, 1, "cpu", seed=7)
    import torch
    eye_a = torch.zeros(1, 48)
    eye_b = eye_a.clone(); eye_b[0, -1] = 1.0
    brain.act(eye_a)
    brain.act(eye_b)
    print("growth_no_interoception_previous_energy", float(brain.previous_energy[0]))

    # Once a growth unit is active, utility is updated by +1 every tick while
    # decaying by .994, so the advertised stale-unit predicate is false.
    utility = 1.0
    for _ in range(6000):
        utility = utility * growth.PARAMS["decay"] + 1.0
    print("growth_utility_after_6000_ticks", utility,
          "stale_threshold", 0.015, "stale_possible", utility < 0.015)


if __name__ == "__main__":
    main()
