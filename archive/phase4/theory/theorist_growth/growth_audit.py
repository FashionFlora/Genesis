"""Long-horizon, per-organism growth audit on the organism-v4 world."""

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sandbox.worlds.organism import OrganismWorld
from candidates.growth_signed_trace.principle_organism import (
    OrganismBrain as SignedTrace,
)
from candidates.growth_metabolic_graph.principle_organism import (
    OrganismBrain as MetabolicGraph,
)


class LargeRoomWorld(OrganismWorld):
    ROOM_SIDES = tuple(side * 2 for side in OrganismWorld.ROOM_SIDES)


def state_bytes(brain):
    total = sys.getsizeof(brain.keys) + sys.getsizeof(brain.key_to_index)
    total += sum(sys.getsizeof(key) for key in brain.keys)
    for value in vars(brain).values():
        if isinstance(value, torch.Tensor):
            total += value.nelement() * value.element_size()
    return total


def counts_per_organism(brain):
    exists = getattr(brain, "exists", None)
    if exists is None:
        return [int(brain.structure()["units"])] * brain.batch
    return exists.sum(dim=1).to(torch.int64).cpu().tolist()


def run(label, brain_type, *, pruning=True, large_rooms=False, steps=6000, seed=31):
    batch = 8
    device = "cpu"
    world_type = LargeRoomWorld if large_rooms else OrganismWorld
    world = world_type(batch=batch, device=device, seed=seed)
    params = None if pruning else {"prune_use": -1.0, "prune_weight": -1.0}
    brain = brain_type(302, world.N_SENSORS, world.N_MOTORS, batch, device, seed, params)
    marks = {1, 64, 256, 1024, 2048, 4096, steps}
    curve = []
    prior_flip_bites = world.flip_bites.clone()
    prior_correct_bites = world.flip_correct_bites.clone()
    total_flip_bites = torch.zeros(batch, device=device)
    total_correct_bites = torch.zeros(batch, device=device)
    for tick in range(1, steps + 1):
        actions = brain.act(world.observe())
        world.step(actions)
        total_flip_bites += torch.where(
            world.flip_bites >= prior_flip_bites,
            world.flip_bites - prior_flip_bites,
            world.flip_bites,
        )
        total_correct_bites += torch.where(
            world.flip_correct_bites >= prior_correct_bites,
            world.flip_correct_bites - prior_correct_bites,
            world.flip_correct_bites,
        )
        prior_flip_bites.copy_(world.flip_bites)
        prior_correct_bites.copy_(world.flip_correct_bites)
        if tick in marks:
            per_org = counts_per_organism(brain)
            curve.append({
                "step": tick,
                "units_mean": sum(per_org) / batch,
                "units_min": min(per_org),
                "units_max": max(per_org),
                "connections_mean": sum(per_org) / batch,
                "state_bytes_per_organism": state_bytes(brain) / batch,
                "rooms_mean": float(world.room.float().mean()),
                "survival": float(world.alive.float().mean()),
                "energy_mean": float(world.energy.mean()),
                "food_gains_per_organism": float(world.visits.sum()) / batch,
                "post_reversal_correct_fraction": float(
                    total_correct_bites.sum() / total_flip_bites.sum().clamp_min(1)
                ),
            })
    return {
        "label": label,
        "brain": brain_type.__name__,
        "pruning": pruning,
        "room_scale": 2 if large_rooms else 1,
        "n_units_cap": 302,
        "curve": curve,
    }


if __name__ == "__main__":
    torch.set_num_threads(1)
    runs = [
        run("signed_trace_pruning", SignedTrace),
        run("signed_trace_no_pruning", SignedTrace, pruning=False),
        run("metabolic_graph_parent", MetabolicGraph),
        run("signed_trace_large_rooms", SignedTrace, large_rooms=True),
    ]
    for result in runs:
        print(json.dumps(result, sort_keys=True))
