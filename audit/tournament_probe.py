"""Diagnostic comparison of the current H007 and H006 implementations."""
import hashlib
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = {
    "life_metabolic_context": "candidates/life_metabolic_context/principle_organism.py",
    "energy_trace_simple": "candidates/energy_trace_simple/principle_organism.py",
}


def make_brain(relative_path, units):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OrganismBrain(units, 49, 3, 4, "cpu", seed=7)


def stimulus(energy):
    x = torch.zeros(4, 49)
    x[:, 48] = energy
    x[:, 5 * 3 + 1] = 0.8
    x[:, 6 * 3 + 1] = 0.5
    return x


def run(relative_path, units, energies):
    brain = make_brain(relative_path, units)
    actions = [brain.act(stimulus(energy)).detach() for energy in energies]
    return torch.stack(actions), brain.structure()


def main():
    energies = [0.95, 1.0, 0.95, 0.7, 0.95, 1.0]
    result = {}
    for name, relative_path in CANDIDATES.items():
        actions_small, structure_small = run(relative_path, 302, energies)
        actions_large, structure_large = run(relative_path, 10000, energies)
        steady, _ = run(relative_path, 302, [0.95] * len(energies))
        source = (ROOT / relative_path).read_bytes()
        result[name] = {
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "max_action_diff_units_302_vs_10000": float((actions_small - actions_large).abs().max()),
            "max_action_diff_energy_vs_constant": float((actions_small - steady).abs().max()),
            "structure_302": structure_small,
            "structure_10000": structure_large,
        }
    output = ROOT / "audit/tournament_probe.result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
