"""Deterministic mechanism probes for the newest dynamics candidate."""

import json
import sys

import torch

sys.path.insert(0, "theory/theorist_dynamics/metabolic_turn_test")
from principle_organism import OrganismBrain  # noqa: E402


def brain():
    return OrganismBrain(302, 49, 3, batch=1, device="cpu")


def eye(pixel=0, energy=0.8):
    x = torch.zeros(1, 49)
    x[0, pixel * 3] = 1.0
    x[0, -1] = energy
    return x


def main():
    outputs = {}
    for turn_trace, ignored in ((-2.0, (0.0, 0.0)), (2.0, (0.0, 0.0)),
                                (-2.0, (100.0, -100.0))):
        b = brain()
        b.previous_energy.fill_(0.8)
        b.action_trace[0, 0] = torch.tensor([turn_trace, *ignored])
        outputs[(turn_trace, ignored)] = b.act(eye()).tolist()

    structural = brain().structure()
    print(json.dumps({
        "turn_trace_minus_2": outputs[(-2.0, (0.0, 0.0))],
        "turn_trace_plus_2": outputs[(2.0, (0.0, 0.0))],
        "same_turn_ignored_speed_bite_trace": outputs[(-2.0, (100.0, -100.0))],
        "structure": structural,
        "fixed_eye_turn": brain().act(eye(pixel=4))[0, 0].item(),
        "speed_at_energy_0_2": brain().act(eye(energy=0.2))[0, 1].item(),
        "speed_at_energy_0_8": brain().act(eye(energy=0.8))[0, 1].item(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
