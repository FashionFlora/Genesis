"""Small, reproducible measurements for the sparse growth candidate.

This is a smoke probe, not an organism-v7 score: it records transient growth
and a causal-free stream prediction assay so the full judge remains the gate.
"""

import importlib.util
import json
from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CANDIDATE = ROOT / "candidates/growth_local_eligibility/principle_organism.py"

from sandbox.organism_judge_v7 import run_life
from sandbox.worlds.organism_v7 import OrganismWorld


def load_candidate():
    spec = importlib.util.spec_from_file_location("growth_candidate", CANDIDATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def organism_probe(module):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows = []
    for units in (302, 1000, 100000):
        for gain in (0.8, 0.0):
            brain = module.OrganismBrain(
                units, OrganismWorld.EYE_SENSORS + 1, 3, 1024, device,
                seed=1103, params={"association_gain": gain})
            life = run_life(brain, 1024, device, 1103, True, None,
                            steps=512, n_units=units)
            growth = life["growth"]
            rows.append({
                "units_limit": units,
                "association_gain": gain,
                "rooms_mean": sum(item["rooms_reached"] for item in life["samples"]) / len(life["samples"]),
                "survival_mean": sum(item["survival"] for item in life["samples"]) / len(life["samples"]),
                "growth_initial": growth["initial"],
                "growth_final": growth["final"],
                "growth_maximum": growth["maximum"],
                "steps": 512,
                "worlds": 1024,
            })
    return rows


def stream_probe():
    spec = importlib.util.spec_from_file_location(
        "growth_stream", ROOT / "candidates/growth_local_eligibility/principle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for channels in (4, 16, 32):
        system = module.System()
        squared = []
        memory = []
        previous = [0] * channels
        for step in range(3000):
            source = [(step * (index + 3) + index * index) % 7 < 3
                      for index in range(channels // 2)]
            values = [int(value) for value in source]
            values.extend(int(source[index % len(source)]) for index in range(channels // 2))
            prediction = system.step(values)
            if step > 100:
                squared.extend((float(prediction[index]) - values[index]) ** 2
                               for index in range(channels))
            state = system.structure()
            memory.append(state["memory_bytes"])
            previous = values
        rows.append({
            "channels": channels,
            "mse_after_warmup": sum(squared) / len(squared),
            "memory_initial_bytes": memory[0],
            "memory_final_bytes": memory[-1],
            "memory_max_bytes": max(memory),
            "steps": 3000,
        })
    return rows


if __name__ == "__main__":
    module = load_candidate()
    result = {"organism_smoke": organism_probe(module), "stream_prediction": stream_probe()}
    output = Path(__file__).with_suffix(".result.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
