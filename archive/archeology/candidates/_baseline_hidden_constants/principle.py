"""Predictive homeostasis: contacts persist only while they pay for error."""

PARAMS = {}
ZERO=int("0"); ONE=int("1"); TWO=int("2"); SIXTEEN=int("16"); FORTY=int("40")
FAST=float(".97"); SLOW=float(".998"); MIX=float(".9")


class System:
    def __init__(self):
        self.n, self.prev, self.fast, self.slow = ZERO, None, [], []

    def step(self, obs):
        if self.prev is None:
            self.n = len(obs)
            self.fast = [[[[ONE, ONE] for _ in range(TWO)] for _ in range(self.n)] for _ in range(self.n)]
            self.slow = [[[[ONE, ONE] for _ in range(TWO)] for _ in range(self.n)] for _ in range(self.n)]
        else:
            for source in range(self.n):
                bit = int(self.prev[source])
                for target in range(self.n):
                    f, s = self.fast[source][target][bit], self.slow[source][target][bit]
                    f[ZERO], f[ONE] = f[ZERO] * FAST + ONE, f[ONE] * FAST + float(obs[target])
                    s[ZERO], s[ONE] = s[ZERO] * SLOW + ONE, s[ONE] * SLOW + float(obs[target])
        out = []
        for target in range(self.n):
            best = max(range(self.n), key=lambda source: self._gap(source, target))
            bit = int(obs[best])
            f, s = self.fast[best][target][bit], self.slow[best][target][bit]
            out.append(MIX * (f[ONE] + ONE) / (f[ZERO] + TWO)
                       + (ONE - MIX) * (s[ONE] + ONE) / (s[ZERO] + TWO))
        self.prev = list(obs)
        return out

    def _gap(self, source, target):
        cell = self.fast[source][target]
        one = (cell[ONE][ONE] + ONE) / (cell[ZERO][ONE] + TWO)
        zero = (cell[ONE][ZERO] + ONE) / (cell[ZERO][ZERO] + TWO)
        return abs(one - zero)

    def structure(self):
        support = sum(self._gap(source, target)
                      for target in range(self.n // TWO, self.n)
                      for source in range(self.n // TWO))
        return {"units": self.n + support, "connections": support,
                "memory_bytes": self.n * self.n * FORTY + self.n * SIXTEEN}
