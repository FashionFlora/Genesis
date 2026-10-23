"""Clock-based test adversary with its hand-set tuning exposed in PARAMS."""

PARAMS = {
    "phase_length": 208,
    "regime_0": 0, "regime_1": 1, "regime_2": 2, "regime_3": 3,
    "regime_4": 0, "regime_5": 3, "regime_6": 2, "regime_7": 1, "regime_8": 0,
    "active_0": 1, "active_1": 2, "active_2": 4, "active_3": 6,
    "active_4": 1, "active_5": 6, "active_6": 4, "active_7": 2, "active_8": 1,
    "source_a_0": 0, "source_a_1": 1, "source_a_2": 2,
    "source_a_3": 3, "source_a_4": 4, "source_a_5": 5,
    "source_b_0": 1, "source_b_1": 3, "source_b_2": 5,
    "source_b_3": 0, "source_b_4": 2, "source_b_5": 4,
    "source_c_0": 2, "source_c_1": 5, "source_c_2": 1,
    "source_c_3": 4, "source_c_4": 0, "source_c_5": 3,
    "source_d_0": 3, "source_d_1": 2, "source_d_2": 0,
    "source_d_3": 5, "source_d_4": 1, "source_d_5": 4,
    "causal_high": 0.9, "causal_low": 0.1,
    "memory_high": 0.8, "memory_low": 0.2,
    "prior": 0.5,
    "unit_bytes": 128, "connection_bytes": 64,
}


class System:
    def __init__(self):
        self.clock = 0
        self.regime = 0
        self.active = 1
        self.units = 1
        self.connections = 1

    def step(self, obs):
        self.clock += 1
        slot = min(self.clock // PARAMS["phase_length"], 8)
        regimes = tuple(PARAMS[f"regime_{index}"] for index in range(9))
        active = tuple(PARAMS[f"active_{index}"] for index in range(9))
        self.regime = int(regimes[slot]) % 4
        self.active = int(active[slot])
        self.units = self.active
        self.connections = self.active

        maps = (
            tuple(PARAMS[f"source_a_{index}"] for index in range(6)),
            tuple(PARAMS[f"source_b_{index}"] for index in range(6)),
            tuple(PARAMS[f"source_c_{index}"] for index in range(6)),
            tuple(PARAMS[f"source_d_{index}"] for index in range(6)),
        )
        sources = maps[self.regime]
        prediction = [PARAMS["prior"] for _ in obs]
        for offset in range(min(6, len(obs) - 6)):
            target = 6 + offset
            if offset < self.active:
                prediction[target] = (PARAMS["causal_high"] if obs[int(sources[offset]) % 6]
                                      else PARAMS["causal_low"])
            else:
                prediction[target] = (PARAMS["memory_high"] if obs[target]
                                      else PARAMS["memory_low"])
        return prediction

    def structure(self):
        return {
            "units": self.units,
            "connections": self.connections,
            "memory_bytes": (self.units * PARAMS["unit_bytes"]
                             + self.connections * PARAMS["connection_bytes"]),
        }
