"""Small reproducible audit of the growth_metabolic_graph organism controller."""

import importlib.util
from pathlib import Path

import torch


PATH = Path(__file__).parents[1] / "candidates/growth_metabolic_graph/principle_organism.py"
spec = importlib.util.spec_from_file_location("growth", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load():
    return module.OrganismBrain(
        n_units=302, n_sensors=49, n_motors=3, batch=1, device="cpu", seed=0
    )


def main():
    brain = load()
    blank = torch.zeros(1, 49)
    first = brain.act(blank)
    constant_energy = torch.cat((torch.zeros(1, 48), torch.tensor([[0.95]])), 1)
    outputs = [first]
    for _ in range(10):
        outputs.append(brain.act(constant_energy))
    print("blank_action", first[0].tolist())
    print("constant_energy_nodes", brain.node_count)
    print("constant_energy_weights", sorted({round(v[0], 8) for v in brain.nodes[0].values()}))
    print("constant_energy_action", outputs[-1][0].tolist())

    # One visible red pixel causes biting and the fixed forward command before learning.
    red = torch.zeros(1, 49)
    red[0, 0] = 1.0
    red[0, -1] = 0.95
    action = brain.act(red)
    print("single_red_action", action[0].tolist())
    print("single_red_nodes", brain.node_count)
    for _ in range(10):
        brain.act(red)
    print("single_red_constant_energy_nodes", brain.node_count)
    print("single_red_constant_energy_weights", sorted({round(v[0], 8) for v in brain.nodes[0].values()}))


if __name__ == "__main__":
    main()
