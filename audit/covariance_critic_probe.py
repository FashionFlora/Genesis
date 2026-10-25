"""Implementation audit for axiom_metabolic_covariance_budget.

This is a causal smoke test, not an organism-world score. Each variant is
loaded in its own module namespace and differs in one named mechanism.
"""
import importlib.util
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem + str(path), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_brain(mod, sensors=49, batch=32, seed=19, params=None, n_units=302):
    return mod.OrganismBrain(n_units, sensors, 3, batch, "cpu", seed=seed, params=params)


def rollout(mod, xs, sensors=49, seed=19, params=None, n_units=302):
    b = make_brain(mod, sensors=sensors, batch=xs[0].shape[0], seed=seed,
                   params=params, n_units=n_units)
    ys = []
    for x in xs:
        ys.append(b.act(x).detach().clone())
    return torch.stack(ys), b


def stream(seed=123, steps=80, batch=32):
    g = torch.Generator().manual_seed(seed)
    xs = []
    for _ in range(steps):
        x = torch.rand(batch, 49, generator=g)
        x[:, -1] = torch.rand(batch, generator=g)
        xs.append(x)
    return xs


def bright_stream(steps=16, batch=32, pixel=6, color=0):
    xs = []
    for t in range(steps):
        x = torch.zeros(batch, 49)
        x[:, pixel * 3 + color] = 0.9
        x[:, -1] = 0.5
        xs.append(x)
    return xs


def permute_rgb(xs):
    out = []
    for x in xs:
        y = x.clone()
        eye = y[:, :48].reshape(x.shape[0], 16, 3)
        y[:, :48] = eye[..., [1, 0, 2]].reshape(x.shape[0], 48)
        out.append(y)
    return out


def permute_pixels(xs, shift=1):
    out = []
    for x in xs:
        y = x.clone()
        eye = y[:, :48].reshape(x.shape[0], 16, 3)
        y[:, :48] = eye.roll(shift, dims=1).reshape(x.shape[0], 48)
        out.append(y)
    return out


def rmse(a, b):
    return float(torch.sqrt(torch.mean((a - b) ** 2)))


def main():
    path = ROOT / "candidates/axiom_metabolic_covariance_budget/principle_organism.py"
    mod = load(path)
    xs = stream()
    nominal, brain = rollout(mod, xs)
    no_learning, _ = rollout(mod, xs, params={"learning_rate": 0.0})
    # Isolate reserve-dependent forgetting from the energy-delta write by
    # keeping learning active and changing only trace coupling.
    no_forgetting_coupling, _ = rollout(mod, xs, params={"energy_coupling": 0.0})
    no_trace, _ = rollout(mod, xs, params={"trace_decay": 0.0})

    # Inputs with and without the optional interoception channel.
    rgb = [x[:, :48].clone() for x in xs]
    rgb_out, rgb_brain = rollout(mod, rgb, sensors=48)
    neutral = [x.clone().index_fill(1, torch.tensor([48]), 0.5) for x in xs]
    neutral_out, _ = rollout(mod, neutral)

    permuted_out, _ = rollout(mod, permute_rgb(xs))
    pixel_shift_out, _ = rollout(mod, permute_pixels(xs))
    first_four_zero = [x.clone() for x in xs]
    for x in first_four_zero:
        x[:, :12] = 0.0
    first_four_out, _ = rollout(mod, first_four_zero)
    bright = bright_stream()
    bright_out, _ = rollout(mod, bright)
    bright_no_pulse, _ = rollout(mod, bright, params={"learning_rate": 0.0})
    small_out, small_brain = rollout(mod, xs, n_units=302)
    large_out, large_brain = rollout(mod, xs, n_units=100000)

    return {
        "random_stream": {
            "learning_rate_zero_rmse": rmse(nominal, no_learning),
            "energy_coupling_zero_rmse": rmse(nominal, no_forgetting_coupling),
            "trace_decay_zero_rmse": rmse(nominal, no_trace),
            "rgb_only_vs_neutral_energy_rmse": rmse(rgb_out, neutral_out),
            "rgb_channel_swap_rmse": rmse(nominal, permuted_out),
            "pixel_shift_rmse": rmse(nominal, pixel_shift_out),
            "first_four_pixels_zero_rmse": rmse(nominal, first_four_out),
            "n_units_302_vs_100000_rmse": rmse(small_out, large_out),
        },
        "bright_fixed_stream": {
            "nominal_bite_count": int(bright_out[:, :, 2].sum()),
            "learning_zero_bite_count": int(bright_no_pulse[:, :, 2].sum()),
            "nominal_vs_learning_zero_rmse": rmse(bright_out, bright_no_pulse),
            "bite_ages_nominal": [int(i) for i in torch.where(bright_out[:, 0, 2] > 0)[0]],
        },
        "structure": {
            "302": small_brain.structure(),
            "100000": large_brain.structure(),
            "rgb_only": rgb_brain.structure(),
        },
        "source_flags": {
            needle: needle in (ROOT / "candidates/axiom_metabolic_covariance_budget/principle.py").read_text()
            for needle in ["eye[:, 4:]", "age.remainder(5)", "total > 0.04", "concentration > 0.42"]
        },
    }


if __name__ == "__main__":
    result = main()
    out = ROOT / "audit/covariance_critic_probe.result.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(result, indent=2, default=str))
