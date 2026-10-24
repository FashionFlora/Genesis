"""Small structural measurement on the real organism world."""

import json
import resource
import sys

import torch

from sandbox.worlds.organism import OrganismWorld
from candidates.growth_metabolic_graph.principle_organism import OrganismBrain


def heap_bytes(brain):
    total = sys.getsizeof(brain.keys) + sys.getsizeof(brain.key_to_index)
    total += sum(sys.getsizeof(key) for key in brain.keys)
    for tensor in (brain.colors, brain.weights, brain.use, brain.exists, brain.previous_active):
        total += tensor.nelement() * tensor.element_size()
    return total


def run(units, pruning, steps=1500, seed=31):
    batch, device = 8, "cpu"
    world = OrganismWorld(batch=batch, device=device, seed=seed)
    params = None if pruning else {"prune_use": -1.0, "prune_weight": -1.0}
    brain = OrganismBrain(units, OrganismWorld.N_SENSORS, OrganismWorld.N_MOTORS,
                          batch, device, seed, params)
    marks = {0, 32, 128, 512, 1024, steps - 1}
    trace = []
    for tick in range(steps):
        actions = brain.act(world.observe())
        world.step(actions)
        if tick in marks:
            trace.append({
                "step": tick + 1,
                "units": brain.structure()["units"],
                "connections": brain.structure()["connections"],
                "estimated_state_bytes": heap_bytes(brain),
                "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "mean_room": float(world.room.float().mean()),
                "survival_fraction": float(world.alive.float().mean()),
            })
    return {"brain_units": units, "pruning": pruning, "trace": trace}


if __name__ == "__main__":
    for size in (302, 1000, 10000, 100000):
        for pruning in (True, False):
            print(json.dumps(run(size, pruning), sort_keys=True))
