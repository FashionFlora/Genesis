"""Small, non-judge audit for the two organism candidates.

It checks whether the reported mechanism is invariant to skull capacity and
whether it is really a sensor/energy rule rather than a fixed world controller.
"""
import importlib.util
import hashlib
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def brain(path, units, seed=7):
    mod = load(path, path.replace('/', '_').replace('.', '_'))
    return mod.OrganismBrain(units, 49, 3, 4, 'cpu', seed=seed)


def sensors(energy, color=1, pixel=5):
    x = torch.zeros(4, 49)
    x[:, 48] = energy
    x[:, pixel * 3 + color] = 0.8
    x[:, (pixel + 1) * 3 + color] = 0.5
    return x


def run_sequence(path, units, energies):
    b = brain(path, units)
    out = []
    for e in energies:
        out.append(b.act(sensors(float(e))).detach())
    return torch.stack(out), b.structure()


def main():
    candidates = {
        'dynamics_energy_trace': 'candidates/dynamics_energy_trace/principle_organism.py',
        'life_metabolic_context': 'candidates/life_metabolic_context/principle_organism.py',
    }
    result = {}
    energies = [0.95, 1.0, 0.95, 0.7, 0.95, 1.0]
    for name, path in candidates.items():
        a, structure_302 = run_sequence(path, 302, energies)
        b, structure_10000 = run_sequence(path, 10000, energies)
        rgb_a, _ = run_sequence(path, 302, [0.95, 1.0, 0.95])
        # Exchange red and green in the same physical stimulus.
        mod = load(path, path.replace('/', '_').replace('.', '_') + '_rgb')
        rgb_brain = mod.OrganismBrain(302, 49, 3, 4, 'cpu', seed=7)
        x = sensors(0.95, color=0)
        y = sensors(0.95, color=1)
        rgb_diff = float((rgb_brain.act(x) - rgb_brain.act(y)).abs().max())
        result[name] = {
            'source_sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            'max_action_diff_units_302_vs_10000': float((a - b).abs().max()),
            'max_action_diff_energy_sequence': float((rgb_a[1:] - rgb_a[:-1]).abs().max()),
            'max_action_diff_red_vs_green_same_geometry': rgb_diff,
            'structure_302': structure_302,
            'structure_10000': structure_10000,
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    (ROOT / 'audit/critic_probe.result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
