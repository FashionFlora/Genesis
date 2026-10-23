"""Sensory provenance weights the same resource flow that preserves a contact."""

PARAMS = {"decay": 0.97, "flow": 1.0, "maintenance": 0.04,
          "error_cost": 0.01}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.contacts = []

    def step(self, observation):
        unit = PARAMS["flow"] / PARAMS["flow"]
        zero, two, threshold = unit - unit, unit + unit, unit + unit + unit
        if not self.contacts:
            self.width = len(observation)
            self.contacts = [[source, target, [zero, zero], [zero, zero], unit]
                             for target in range(self.width)
                             for source in range(self.width)]
        if self.previous is not None:
            groups = [[] for _ in range(self.width)]
            for contact in self.contacts:
                source, target, positive, seen, mass = contact
                state = int(self.previous[source])
                q = (positive[state] + unit) / (seen[state] + two)
                error = (q - float(observation[target])) ** two
                provenance = unit + float(self.previous[source])
                groups[target].append((contact, error, provenance))
                retention = PARAMS["decay"] ** (unit / max(mass, unit))
                for bit in (False, True):
                    positive[bit] *= retention
                    seen[bit] *= retention
                seen[state] += unit
                positive[state] += float(observation[target])
            alive = []
            for group in groups:
                normalizer = sum(provenance / (unit + error)
                                 for _contact, error, provenance in group)
                for contact, error, provenance in group:
                    source, target, positive, seen, mass = contact
                    share = provenance / (unit + error) / normalizer
                    contact[4] += (PARAMS["flow"] * share
                                   - PARAMS["maintenance"]
                                   - PARAMS["error_cost"] * error)
                    if contact[4] <= zero:
                        continue
                    while contact[4] >= threshold:
                        contact[4] *= unit / two
                        alive.append([source, target, positive.copy(), seen.copy(), contact[4]])
                    alive.append(contact)
            self.contacts = alive
        prediction = [unit / two] * self.width
        for target in range(self.width):
            choices = [contact for contact in self.contacts if contact[1] == target]
            if choices:
                contact = max(choices, key=lambda item: item[4] * (abs(
                    (item[2][1] + unit) / (item[3][1] + two)
                    - (item[2][0] + unit) / (item[3][0] + two))
                    + PARAMS["error_cost"]))
                state = int(observation[contact[0]])
                prediction[target] = ((contact[2][state] + unit)
                                      / (contact[3][state] + two))
        self.previous = list(observation)
        return prediction

    def structure(self):
        return {"units": self.width + len(self.contacts),
                "connections": len(self.contacts),
                "resource": sum(contact[4] for contact in self.contacts)}
