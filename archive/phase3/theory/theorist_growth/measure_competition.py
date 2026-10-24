"""Measure demand-driven growth, pruning, return, prediction, and storage."""
import json
import resource
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from candidates.growth_demand_competition.principle_organism import OrganismBrain


def run(n_units, contexts=24, steps_per_context=80, quiet_steps=1400):
    batch, sensors = 64, 49
    brain = OrganismBrain(n_units, sensors, 3, batch, "cpu", seed=11)
    gen = torch.Generator().manual_seed(17)
    prototypes = torch.rand(contexts, sensors, generator=gen)
    snapshots = []
    error = 0.0
    phases = (("learn", contexts, contexts * steps_per_context),
              ("withdraw", contexts - 1, quiet_steps),
              ("return", contexts, steps_per_context))
    t = 0
    for phase, n_contexts, length in phases:
      for i in range(length):
        if phase == "learn":
            context = (i // steps_per_context) % contexts
        elif phase == "withdraw":
            context = 0
        else:
            context = contexts - 1
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
            "model_tensor_bytes": sum(t.numel() * t.element_size() for t in tensors),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


if __name__ == "__main__":
    results = [run(n) for n in (302, 1000, 10000, 100000)]
    out = Path(__file__).with_name("growth_demand_competition_measure.json")
    out.write_text(json.dumps(results, sort_keys=True, indent=2) + "\n")
    print(json.dumps(results, sort_keys=True))
