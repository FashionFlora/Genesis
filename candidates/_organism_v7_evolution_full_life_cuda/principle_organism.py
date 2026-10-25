"""Best fixed genome from between-life family evolution."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("evolved_family", Path(__file__).with_name("family.py"))
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)
PARAMS = {'trace_decay': 0.925304114818573, 'evidence_gain': 0.5029569864273071, 'speed': 0.11360165476799011, 'bite_threshold': 0.12538029253482819}
GENOME = PARAMS

class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = __import__("torch")
        chosen = {**GENOME, **(params or {})}
        values = {key: self.torch.full((batch,), value, device=device) for key, value in chosen.items()}
        self.brain = _family.OrganismBrain(n_units, n_sensors, n_motors, batch, device,
                                           seed=seed, genome=values)

    def act(self, sensors):
        return self.brain.act(sensors)

    def structure(self):
        return self.brain.structure() if hasattr(self.brain, "structure") else None
