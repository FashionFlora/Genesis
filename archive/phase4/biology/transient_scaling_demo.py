"""Toy check: a positional signal can stay aligned to a growing domain."""

from math import exp


def profile(domain_size, gradient_length, points=101):
    return [exp(-(i / (points - 1) * domain_size) / gradient_length)
            for i in range(points)]


def mse(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)


def main():
    sizes = (1.0, 1.5, 2.0)
    reference = profile(sizes[0], sizes[0])
    scaled_errors = []
    frozen_errors = []
    for size in sizes[1:]:
        scaled_errors.append(mse(reference, profile(size, size)))
        frozen_errors.append(mse(reference, profile(size, 1.0)))
    print("domain_sizes=1.0,1.5,2.0")
    print(f"scaled_gradient_mean_mse={sum(scaled_errors)/len(scaled_errors):.6f}")
    print(f"frozen_gradient_mean_mse={sum(frozen_errors)/len(frozen_errors):.6f}")


if __name__ == "__main__":
    main()
