"""Small deterministic assay for growth, pruning, memory, and prediction error."""
import json
import resource
import sys
from pathlib import Path
import torch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from candidates.growth_energy_vector.principle_organism import OrganismBrain


def run(n_units, steps=2000):
    batch, sensors = 64, 49
    brain = OrganismBrain(n_units, sensors, 3, batch, "cpu", seed=11)
    gen = torch.Generator().manual_seed(17)
    prototypes = torch.rand(4, sensors, generator=gen)
    snapshots = []
    error = 0.0
    for t in range(steps):
        # Learn four recurring contexts, then leave the last one unused long
        # enough to test whether local use preserves only needed units.
        phase = (t // 100) % 4
        context = phase if t < 400 else (3 if t >= 1800 else (t // 100) % 3)
        x = prototypes[context][None, :].expand(batch, -1).clone()
        x += torch.rand(batch, sensors, generator=gen) * 0.02
        brain.act(x)
        error += brain.last_prediction_error.mean().item()
        if t in (0, 99, 199, 399, 499, 1199, 1799, 1899, 1999):
            structure = brain.structure()
            snapshots.append({"step": t, **structure})
    return {"capacity": n_units, "snapshots": snapshots,
            "mean_sensor_prediction_error": error / steps,
            "model_tensor_bytes": sum(t.numel() * t.element_size() for t in
                                       (brain.centers, brain.utility, brain.active, brain.actions)),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


if __name__ == "__main__":
    print(json.dumps([run(n) for n in (302, 1000, 10000, 100000)], sort_keys=True))
