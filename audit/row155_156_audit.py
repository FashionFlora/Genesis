"""Contract and source audit for organism leaderboard rows 155 and 156."""

import hashlib
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    source = ROOT / f"candidates/{name}/principle_organism.py"
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return source, module


growth_source, growth = load("growth_local_eligibility")
life_source, life = load("life_metabolic_ratio")

# A legal no-interoception observation is exactly 16 RGB pixels, or 48 values.
low = torch.zeros((1, 48))
high = low.clone()
low[0, 47] = 0.05
high[0, 47] = 0.95

brain_low = growth.OrganismBrain(302, 48, 3, 1, "cpu", seed=5)
brain_high = growth.OrganismBrain(302, 48, 3, 1, "cpu", seed=5)
action_low = brain_low.act(low)
action_high = brain_high.act(high)

life_brain = life.OrganismBrain(302, 48, 3, 1, "cpu", seed=5)
life_action_low = life_brain.act(low)
life_action_high = life_brain.act(high)

result = {
    "rows": {
        "155_life_metabolic_ratio": hashlib.sha256(life_source.read_bytes()).hexdigest(),
        "156_growth_local_eligibility": hashlib.sha256(growth_source.read_bytes()).hexdigest(),
    },
    "valid_no_interoception_shape": {"sensors": 48, "pixels": 16},
    "growth_local_eligibility": {
        "pixels_parsed": brain_low.pixels,
        "declared_energy_index": 47,
        "action_delta_when_only_last_rgb_channel_changes": float((action_low - action_high).abs().max()),
        "actions": [action_low.tolist(), action_high.tolist()],
    },
    "life_metabolic_ratio": {
        "pixels_parsed": life_brain.eye_width,
        "has_energy": life_brain.has_energy,
        "action_delta_when_only_last_rgb_channel_changes": float((life_action_low - life_action_high).abs().max()),
    },
}
output = ROOT / "audit/row155_156_audit.result.json"
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
