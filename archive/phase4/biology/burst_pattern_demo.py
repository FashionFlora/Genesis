"""Toy ablation: hold spike count fixed while changing burst size."""


def burst_sizes(spikes):
    sizes = []
    current = 0
    for active in spikes:
        if active:
            current += 1
        elif current:
            sizes.append(current)
            current = 0
    if current:
        sizes.append(current)
    return sizes


def branch_signal(spikes, threshold=10):
    return sum(size >= threshold for size in burst_sizes(spikes))


def make_spikes(burst_size, n_bursts, gap=4, window=200):
    spikes = []
    for _ in range(n_bursts):
        spikes.extend([1] * burst_size)
        spikes.extend([0] * gap)
    assert len(spikes) <= window
    spikes.extend([0] * (window - len(spikes)))
    return spikes


def main():
    print("bursts spikes bins mean_rate burst_events mean_rate_ablation")
    for burst_size in (1, 2, 4, 8, 16):
        n_bursts = 32 // burst_size
        spikes = make_spikes(burst_size, n_bursts)
        assert sum(spikes) == 32
        print(
            f"{n_bursts} {sum(spikes)} {len(spikes)} "
            f"{sum(spikes) / len(spikes):.3f} {branch_signal(spikes)} 0"
        )


if __name__ == "__main__":
    main()
