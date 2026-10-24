"""Measure demand-grown niches, pruning, return, prediction, and storage."""
import json
import resource
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from candidates.growth_demand_expansion.principle import OrganismBrain


def run(n_units, contexts=24, steps_per_context=80, quiet_steps=1400):
    batch, sensors = 64, 49
    brain = OrganismBrain(n_units, sensors, 3, batch, "cpu", seed=11)
    gen = torch.Generator().manual_seed(17)
    prototypes = torch.rand(contexts, sensors, generator=gen)
    snapshots, error, t = [], 0.0, 0
    phases = (("learn", contexts, contexts * steps_per_context),
              ("withdraw", contexts - 1, quiet_steps),
              ("return", contexts, steps_per_context))
    for phase, _, length in phases:
        for i in range(length):
            context = (i // steps_per_context) % contexts if phase == "learn" else (0 if phase == "withdraw" else contexts - 1)
            x = prototypes[context][None, :].expand(batch, -1).clone()
            x += torch.rand(batch, sensors, generator=gen) * 0.02
            brain.act(x)
            error += brain.last_prediction_error.mean().item()
            if i in (0, length - 1) or (phase == "withdraw" and i in (99, 699)):
                snapshots.append({"phase": phase, "step": t, **brain.structure()})
            t += 1
    tensors = (brain.centers, brain.utility, brain.active, brain.actions)
    return {"capacity": n_units, "snapshots": snapshots,
            "mean_sensor_prediction_error": error / t,
            "model_tensor_bytes": sum(v.numel() * v.element_size() for v in tensors),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


if __name__ == "__main__":
    results = [run(n) for n in (302, 1000, 10000, 100000)]
    out = Path(__file__).with_name("growth_demand_expansion_measure.json")
    out.write_text(json.dumps(results, sort_keys=True, indent=2) + "\n")
    print(json.dumps(results, sort_keys=True))
