"""Small audit probes for organism candidates; writes only a compact result file."""
import hashlib
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    "life_metabolic_trace",
    "dynamics_energy_trace",
    "axiom_energy_trace",
    "axiom_capacity_correlation",
    "growth_trace",
    "agency_trace",
]


def load(name):
    path = ROOT / "candidates" / name / "principle_organism.py"
    spec = importlib.util.spec_from_file_location("audit_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return path, module


def structure_plain(value):
    if isinstance(value, dict):
        return {key: structure_plain(item) for key, item in value.items()}
    if torch.is_tensor(value):
        return value.detach().cpu().tolist()
    return value


def main():
    torch.manual_seed(123)
    report = []
    for name in TARGETS:
        path, module = load(name)
        kwargs = dict(n_sensors=49, n_motors=3, batch=2, device="cpu", seed=7)
        brains = []
        for units in (302, 10000):
            try:
                brain = module.OrganismBrain(n_units=units, **kwargs)
                brains.append(brain)
            except TypeError:
                brain = module.OrganismBrain(n_units=units, **kwargs)
                brains.append(brain)
        sensors = torch.zeros(2, 49)
        sensors[:, 0] = 1.0
        sensors[:, 2] = 0.4
        sensors[:, 48] = 0.95
        outputs = []
        structures = []
        for brain in brains:
            outputs.append(brain.act(sensors.clone()).detach())
            structures.append(structure_plain(brain.structure()))
        same_units = bool(torch.allclose(outputs[0], outputs[1], atol=1e-7, rtol=1e-7))
        same_structure = structures[0] == structures[1]
        # A second action with a large positive energy jump isolates the endogenous update.
        jump = sensors.clone()
        jump[:, 48] = 1.0
        before = []
        after = []
        for brain in brains:
            before.append(structure_plain(brain.structure()))
            brain.act(jump.clone())
            after.append(structure_plain(brain.structure()))
        report.append({
            "candidate": name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "units_302_vs_10000_output_identical": same_units,
            "units_302_vs_10000_structure_identical": same_structure,
            "structure_before_energy_jump": before,
            "structure_after_energy_jump": after,
            "output_302": outputs[0].tolist(),
            "output_10000": outputs[1].tolist(),
        })
    out = ROOT / "audit" / "invariant_probe.result.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
