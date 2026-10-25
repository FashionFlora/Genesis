"""Implementation probe for the contextual metabolic memory crossover."""

import hashlib
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "candidates/axiom_metabolic_context_budget/principle.py"
OUT = Path(__file__).with_name("axiom_budget_audit.result.json")

spec = importlib.util.spec_from_file_location("budget_candidate", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
brain = module.OrganismBrain(302, 49, 3, 1, "cpu", seed=7)

# Repeated signed energy changes build memory while a visible red signal keeps
# the selected color stable. Only the odd/even green balance changes context.
contexts = []
norms = []
for step in range(160):
    sensors = torch.zeros((1, 49))
    sensors[0, 4 * 3 + 0] = 1.0
    sensors[0, 1] = 1.0 if (step // 20) % 2 else 0.0
    sensors[0, 3 + 1] = 1.0 if (step // 20) % 2 == 0 else 0.0
    sensors[0, 48] = 0.75 if step % 2 else 0.95
    brain.act(sensors)
    contexts.append(int(brain.previous_context.item()))
    norms.append(float(brain.preference.flatten(1).norm(dim=1).item()))

payload = {
    "source": str(SOURCE.relative_to(ROOT)),
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "probe": "synthetic alternating retinal context and energy; 160 CPU steps",
    "context_first_20": contexts[:20],
    "context_second_20": contexts[20:40],
    "context_switches": sum(a != b for a, b in zip(contexts, contexts[1:])),
    "max_preference_l2": max(norms),
    "capacity": module.PARAMS["capacity"],
    "final_preference_l2": norms[-1],
    "fixed_reported_structure": brain.structure(),
}
OUT.write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps(payload, indent=2))
