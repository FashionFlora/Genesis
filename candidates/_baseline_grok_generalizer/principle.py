"""Test fixture that applies the hidden XOR rule without memorizing examples."""


class System:
    def step(self, obs):
        prediction = [0.5 for _ in obs]
        if len(obs) >= 4:
            prediction[3] = float(bool(obs[0]) ^ bool(obs[1]) ^ bool(obs[2]))
        return prediction

    def structure(self):
        return {"units": 4, "connections": 3, "memory_bytes": 64}
