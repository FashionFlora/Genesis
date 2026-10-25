"""Small causal probe for agency_consequence_gated_steering (leaderboard row 177)."""
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.OrganismBrain


def rollout(cls, stream, units=302, seed=19, params=None):
    b = cls(units, stream.shape[-1], 3, stream.shape[1], "cpu", seed=seed, params=params)
    acts = torch.stack([b.act(x).detach() for x in stream])
    return acts, b


def plain(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    return value


def make_stream(steps=128, batch=32, sensors=49):
    # A moving asymmetric RGB patch: total signal changes while bearing stays observable.
    x = torch.zeros(steps, batch, sensors)
    for t in range(steps):
        amp = 0.15 + 0.75 * ((t % 16) / 15.0)
        x[t, :, 3 * 2 + 0] = amp
        x[t, :, 3 * 9 + 0] = 0.5 * amp
        x[t, :, 3 * 2 + 1] = 0.1
    x[:, :, 48] = torch.linspace(0.1, 0.9, steps)[:, None]
    return x


def main():
    parent = load("candidates/agency_consequence_gated_steering/principle_organism.py", "parent")
    ablation = load("candidates/agency_consequence_gated_steering_ablation/principle_organism.py", "ablation")
    stream = make_stream()
    p, bp = rollout(parent, stream)
    a, ba = rollout(ablation, stream)
    gain0, bg = rollout(parent, stream, params={"prediction_gain": 0.0})

    # Last sensor is optional interoception and must be causally isolated here.
    no_energy = stream.clone()
    no_energy[:, :, 48] = 1.0 - no_energy[:, :, 48]
    e1, _ = rollout(parent, stream)
    e2, _ = rollout(parent, no_energy)

    zero = torch.zeros_like(stream)
    z1, _ = rollout(parent, zero)
    z2, _ = rollout(ablation, zero)

    out = {
        "parent_vs_gain0": {
            "action_rmse": float((p - gain0).square().mean().sqrt()),
            "max_abs": float((p - gain0).abs().max()),
            "fraction_changed": float((p - gain0).abs().amax(dim=2).gt(1e-7).float().mean()),
            "predicted_delta_max": float(bg.predicted_delta.abs().max()),
        },
        "parent_vs_ablation": {
            "action_rmse": float((p - a).square().mean().sqrt()),
            "max_abs": float((p - a).abs().max()),
            "fraction_changed": float((p - a).abs().amax(dim=2).gt(1e-7).float().mean()),
            "parent_predicted_delta_max": float(bp.predicted_delta.abs().max()),
            "ablation_predicted_delta_max": float(ba.predicted_delta.abs().max()),
        },
        "energy_last_sensor": {
            "action_rmse": float((e1 - e2).square().mean().sqrt()),
            "max_abs": float((e1 - e2).abs().max()),
        },
        "zero_visual": {
            "parent_vs_ablation_action_rmse": float((z1 - z2).square().mean().sqrt()),
            "parent_bite_sum": float(z1[:, :, 2].sum()),
            "ablation_bite_sum": float(z2[:, :, 2].sum()),
        },
        "n_units": {
            "action_rmse_302_vs_100000": float((p - rollout(parent, stream, units=100000)[0]).square().mean().sqrt()),
            "structure_302": plain(bp.structure()),
            "structure_100000": plain(rollout(parent, stream, units=100000)[1].structure()),
        },
        "source_flags": {
            "uses_world_reward": False,
            "argmax_channel": True,
            "fixed_bite_thresholds": True,
            "sinusoidal_exploration": True,
            "energy_sensor_used": False,
        },
    }
    path = ROOT / "audit/consequence_critic_probe.result.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
