"""Small deterministic probes for the organism-v4 metabolic_causal_sparse claim."""

import json
import sys

import torch

sys.path.insert(0, "candidates/metabolic_causal_sparse")
from principle_organism import OrganismBrain  # noqa: E402


def sensors(batch, color, pixel=0, energy=0.5, pixels=16):
    x = torch.zeros(batch, pixels * 3 + 1)
    x[:, pixel * 3 + color] = 1.0
    x[:, -1] = energy
    return x


def main():
    brain = OrganismBrain(302, 49, 3, batch=2, device="cpu")
    # Different worlds introduce different links in the same batched process.
    first = torch.zeros(2, 49)
    first[0, 0] = 1.0  # red, pixel 0
    first[1, 1] = 1.0  # green, pixel 0
    a0 = brain.act(first)
    struct0 = brain.structure()["units"].tolist()
    # A positive outcome after a bite writes a color-conditioned trace.
    a1 = brain.act(sensors(2, color=0, energy=0.8))
    a2 = brain.act(sensors(2, color=1, energy=0.8))
    # The motor speed is an instantaneous affine function of energy.
    lo = brain.act(sensors(2, color=0, energy=0.2))[:, 1]
    hi = brain.act(sensors(2, color=0, energy=0.8))[:, 1]
    # Empty eyes expose whether pruning is driven by use/energy rather than
    # a task signal; run long enough to cross the configured use threshold.
    empty = torch.zeros(2, 49)
    for _ in range(300):
        empty[:, -1] = 0.1
        brain.act(empty)
    struct_end = brain.structure()["units"].tolist()

    # Matched current eye: only the previous color differs.  A changed bite
    # here is evidence for a consequence trace rather than current evidence.
    paired = []
    for previous_color in (0, 1):
        probe = OrganismBrain(302, 49, 3, batch=1, device="cpu")
        probe.act(sensors(1, color=previous_color, energy=0.5))
        paired.append(probe.act(sensors(1, color=1, energy=0.8))[0].tolist())

    # With no energy consequence, unused links should disappear if pruning is
    # actually driven by scarcity/use rather than retained weights.
    prune_probe = OrganismBrain(302, 49, 3, batch=1, device="cpu")
    prune_probe.act(sensors(1, color=0, energy=0.5))
    for _ in range(300):
        prune_probe.act(torch.zeros(1, 49).scatter(1, torch.tensor([[48]]), 0.5))
    prune_units = int(prune_probe.structure()["units"][0])
    print(json.dumps({
        "initial_action": a0.tolist(),
        "post_positive_action": a1.tolist(),
        "post_other_color_action": a2.tolist(),
        "structure_after_first_batch_rows": struct0,
        "structure_after_300_empty_steps": struct_end,
        "speed_energy_0.2": lo.tolist(),
        "speed_energy_0.8": hi.tolist(),
        "matched_current_eye_after_previous_color_0_vs_1": paired,
        "units_after_300_unused_steps_no_energy_change": prune_units,
        "global_key_pool": len(brain.keys),
        "global_key_colors": sorted(set(brain.colors.tolist())),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
