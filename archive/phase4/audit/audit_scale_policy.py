"""Small code audit for fixed-size organism policies.

This probes implementation behavior, not judge performance. It keeps the eye
input identical while changing only n_units and then changes energy/eye geometry
to expose direct sensor-to-motor paths.
"""

import importlib.util
from pathlib import Path

import torch


def load(path):
    spec = importlib.util.spec_from_file_location("audited_candidate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def main():
    path = Path("candidates/axiom_causal_homeostasis/principle_organism.py")
    Brain = load(path)
    # Four pixels, three colour channels, plus one interoceptive channel.
    eye = torch.zeros(2, 48)
    eye[0, 0] = 1.0          # colour 0 at pixel 0
    eye[1, 6 + 1] = 1.0      # colour 1 at pixel 2
    energies = torch.tensor([0.2, 0.8])
    sensors = torch.cat((eye, energies[:, None]), dim=1)

    outputs = {}
    for units in (302, 1_000, 10_000, 100_000):
        brain = Brain(units, sensors.shape[1], 3, sensors.shape[0], "cpu", seed=7)
        outputs[units] = brain.act(sensors).detach()
        print("n_units", units, "structure", brain.structure(), "action", outputs[units].tolist())

    for units in (1_000, 10_000, 100_000):
        same = torch.equal(outputs[302], outputs[units])
        print("same_action_as_302", units, same)

    # Fixed eye, varying energy: isolates the explicit speed map in act().
    brain = Brain(302, sensors.shape[1], 3, 3, "cpu", seed=7)
    fixed_eye = eye[:1].expand(3, -1)
    energy_probe = torch.tensor([[0.1], [0.5], [0.9]])
    probe = torch.cat((fixed_eye, energy_probe), dim=1)
    print("fixed_eye_energy_actions", brain.act(probe).detach().tolist())

    # Same energy, rotate the one-hot eye signal across pixels.
    brain = Brain(302, sensors.shape[1], 3, 3, "cpu", seed=7)
    rotated = torch.zeros(3, 49)
    for row, pixel in enumerate((0, 1, 2)):
        rotated[row, pixel * 3] = 1.0
        rotated[row, -1] = 0.5
    print("rotated_eye_actions", brain.act(rotated).detach().tolist())


if __name__ == "__main__":
    main()
