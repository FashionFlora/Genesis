"""Small deterministic probe: normalized local credit under regime changes."""
import torch


def run(seed=17, steps=2400):
    g = torch.Generator().manual_seed(seed)
    # Two contexts, two colors. The controller must infer a context-dependent
    # choice; the hidden mapping reverses at 800 and returns at 1600.
    context = torch.randint(0, 2, (steps,), generator=g)
    reward_color = torch.where(context == 0, 0, 1)
    phase = torch.arange(steps)
    reward_color = torch.where((phase >= 800) & (phase < 1600), 1 - reward_color, reward_color)
    mass = torch.zeros(2, 2)
    evidence = torch.zeros(2, 2)
    previous = torch.zeros(steps, dtype=torch.long)
    errors = []
    for t in range(steps):
        # Tie-breaking at birth is deterministic; later choices use the table.
        selected = int(evidence[:, context[t]].argmax()) if mass[:, context[t]].sum() else 0
        previous[t] = selected
        if t:
            mass *= 0.94
            evidence *= 0.94
            mass[previous[t - 1], context[t - 1]] += 1
            evidence[previous[t - 1], context[t - 1]] += 0.18 if previous[t - 1] == reward_color[t - 1] else -0.06
        estimate = evidence / mass.clamp_min(1)
        errors.append(float(selected != reward_color[t]))
    a = sum(errors[700:800]) / 100
    b = sum(errors[1500:1600]) / 100
    c = sum(errors[2200:2300]) / 100
    return a, b, c


if __name__ == "__main__":
    vals = [run(seed) for seed in range(20)]
    print("probe_error_pre_change=%.3f post_change=%.3f return=%.3f" % tuple(torch.tensor(vals).mean(0)))
