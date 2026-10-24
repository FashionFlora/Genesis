"""Ablation: remove directional steering from the flow-homeostasis brain."""
import importlib.util
from pathlib import Path

path = Path(__file__).with_name("principle.py")
spec = importlib.util.spec_from_file_location("flow_principle", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OrganismBrain(module.OrganismBrain):
    def act(self, sensors):
        out = super().act(sensors)
        out[:, 0] = 0
        return out
