"""Fast revision and slow retention are coupled views of one relation."""

PARAMS = {"base": 0.97, "shock": 0.35, "floor": 0.55, "slow": 0.997,
          "support": 4.0, "recall": 0.35}


class System:
    def __init__(self):
        self.previous = self.prediction = None
        self.fast = self.slow = None
        self.mass = 0

    def step(self, obs):
        n = len(obs)
        if self.fast is None:
            self.fast = [[[[0.0, 0.0] for _ in range(2)] for _ in range(n)] for _ in range(n)]
            self.slow = [[[[0.0, 0.0] for _ in range(2)] for _ in range(n)] for _ in range(n)]
        errors = [0.5] * n if self.prediction is None else [abs(float(x) - p) for x, p in zip(obs, self.prediction)]
        for i in range(n):
            for j in range(n):
                decay = max(PARAMS["floor"], PARAMS["base"] - PARAMS["shock"] * max(0.0, errors[j] - 0.1))
                for bank, rate in ((self.fast, decay), (self.slow, PARAMS["slow"])):
                    for cell in bank[i][j]:
                        cell[0] *= rate
                        cell[1] *= rate
                    if self.previous is not None:
                        cell = bank[i][j][self.previous[i]]
                        cell[0] += 1.0
                        cell[1] += float(obs[j])
        out, active = [], 0
        for j in range(n):
            strengths = []
            estimates = []
            for i in range(n):
                fs, ss = self.fast[i][j], self.slow[i][j]
                def stats(pair):
                    a, b = pair
                    return ((b[1] + 1) / (b[0] + 2), (a[1] + 1) / (a[0] + 2),
                            abs((b[1] + 1) / (b[0] + 2) - (a[1] + 1) / (a[0] + 2)) * (a[0] + b[0]) / (a[0] + b[0] + PARAMS["support"]))
                f1, f0, strength = stats(fs)
                s1, s0, _ = stats(ss)
                state = int(obs[i])
                fast_count = sum(cell[0] for cell in fs)
                slow_count = sum(cell[0] for cell in ss)
                recall = PARAMS["recall"] * slow_count / (slow_count + fast_count + 1.0)
                estimates.append((1.0 - recall) * (f1 if state else f0) + recall * (s1 if state else s0))
                strengths.append(strength)
            i = max(range(n), key=strengths.__getitem__)
            out.append(estimates[i] if strengths[i] > 0 else 0.5)
            active += int(i != j and strengths[i] > 0.2)
        self.mass = active
        self.previous, self.prediction = [int(x) for x in obs], out
        return out

    def structure(self):
        return {"units": self.mass, "connections": self.mass,
                "memory_bytes": len(self.fast) ** 2 * 128 if self.fast else 0}
