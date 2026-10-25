"""Toy check: multiplicative scaling preserves relative synaptic strengths."""


weights = [1.0, 2.0]
weights[0] *= 1.5  # Local plasticity changes one input.
before = weights.copy()
target_sum = 3.0
scale = target_sum / sum(weights)
weights = [weight * scale for weight in weights]

print(f"before={before}; scaled={weights}")
print(f"sum={sum(weights):.3f}; ratio={weights[1] / weights[0]:.3f}")
