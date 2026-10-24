"""Small causal probes for the axiom tournament.

This is an audit aid, not a replacement for the organism judge.  It checks
whether the reported mechanisms affect actions and whether declared brain
size affects the actual state.
"""
import importlib.util
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "candidates" / name / "principle.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def probe(name, sensors):
    module = load(name)
    common = dict(n_sensors=sensors.shape[1], n_motors=3, batch=sensors.shape[0],
                 device="cpu", seed=7)
    brain = module.OrganismBrain(n_units=302, **common)
    first = brain.act(sensors).detach()
    second = brain.act(sensors).detach()
    # A positive energy jump is the only teaching event available to these brains.
    jumped = sensors.clone()
    jumped[:, -1] = jumped[:, -1] + 0.5
    after_jump = brain.act(jumped).detach()

    no_learning = module.OrganismBrain(n_units=302, **common)
    no_learning = module.OrganismBrain(n_units=302, params={
        "rate": 0.0, "learn_rate": 0.0, "trace_decay": 0.0,
        "decay": 0.0, "explore": 1.0, "explore_turn": 1.0,
    }, **common)
    baseline = no_learning.act(sensors).detach()

    sizes = []
    for units in (302, 1000, 10000, 100000):
        b = module.OrganismBrain(n_units=units, **common)
        sizes.append((units, b.structure(), sum(v.numel() for v in b.__dict__.values()
                                                 if torch.is_tensor(v))))
    return {
        "first": first.tolist(),
        "repeat_delta": (second - first).abs().max().item(),
        "energy_jump_delta": (after_jump - second).abs().max().item(),
        "parameter_probe_delta": (baseline - first).abs().max().item(),
        "sizes": sizes,
    }


def main():
    # One bright red eye pixel and an otherwise blank retina.  The final
    # channel is interoception; the same visual cue is used for both candidates.
    obs = torch.zeros(1, 49)
    obs[0, 0] = 1.0
    obs[0, 48] = 0.5
    for name in ("axiom_homeostasis", "axiom_flow_homeostasis"):
        print(name, probe(name, obs))


if __name__ == "__main__":
    main()
