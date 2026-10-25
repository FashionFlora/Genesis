"""Matched organism-v4 audit for delayed, energy-affordable sensory growth."""

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sandbox.worlds.organism import OrganismWorld
from candidates.growth_delayed_support.principle_organism import OrganismBrain


class LargeRoomWorld(OrganismWorld):
    ROOM_SIDES = tuple(side * 2 for side in OrganismWorld.ROOM_SIDES)


def tensor_bytes(brain):
    return sum(value.nelement() * value.element_size()
               for value in vars(brain).values() if isinstance(value, torch.Tensor))


def run(label, *, threshold=0.18, large_rooms=False, steps=6000, seed=31):
    batch = 8
    world_type = LargeRoomWorld if large_rooms else OrganismWorld
    world = world_type(batch=batch, device="cpu", seed=seed)
    brain = OrganismBrain(302, world.N_SENSORS, world.N_MOTORS, batch, "cpu", seed,
                          {"growth_support": threshold})
    marks = {64, 256, 1024, 2048, 4096, steps}
    curve = []
    max_support = 0.0
    support_ticks = 0
    for tick in range(1, steps + 1):
        actions = brain.act(world.observe())
        if brain.support.numel():
            max_support = max(max_support, float(brain.support.max()))
            support_ticks += int((brain.support > 0).any())
        if tick in marks:
            counts = brain.exists.sum(dim=1)
            curve.append({
                "step": tick,
                "units_mean": float(counts.float().mean()),
                "units_max": int(counts.max()),
                "allocated_slots": len(brain.keys),
                "connections_mean": float(counts.float().mean()),
                "tensor_bytes_shared": tensor_bytes(brain),
                "rooms_mean": float(world.room.float().mean()),
                "survival": float(world.alive.float().mean()),
                "energy_mean": float(world.energy.mean()),
            })
        world.step(actions)
    return {
        "label": label,
        "seed": seed,
        "batch": batch,
        "steps": steps,
        "room_scale": 2 if large_rooms else 1,
        "growth_support_threshold": threshold,
        "max_support": max_support,
        "ticks_with_support": support_ticks,
        "curve": curve,
    }


if __name__ == "__main__":
    torch.set_num_threads(1)
    runs = [
        run("support_0.18"),
        run("no_growth_ablation", threshold=1e6),
        run("support_0.18_large_rooms", large_rooms=True),
    ]
    output = Path(__file__).with_name("growth_delayed_audit.jsonl")
    output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in runs))
    for row in runs:
        print(json.dumps(row, sort_keys=True))
