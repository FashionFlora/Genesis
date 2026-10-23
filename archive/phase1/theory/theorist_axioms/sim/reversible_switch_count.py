"""Count surprise-triggered state exchanges on return and null streams."""
import importlib.util
import json
import random
import statistics
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "candidates/reversible_surprise/principle.py"
source = SOURCE.read_text()
source = source.replace("self.width = False", "self.switches = 0\n        self.width = False")
source = source.replace(
    "for source in range(self.width):\n                    self.active",
    "self.switches += self.width\n                for source in range(self.width):\n                    self.active",
)
module = types.ModuleType("instrumented")
exec(compile(source, str(SOURCE), "exec"), module.__dict__)

PHASE = 500
SEEDS = range(40)


def run(seed, null=False):
    rng = random.Random(seed)
    system = module.System()
    for index in range(PHASE * 3):
        source = int(rng.random() < 0.5)
        values = [int(rng.random() < 0.5) for _ in range(4)]
        target = None if null else (0 if index < PHASE or index >= 2 * PHASE else 1)
        if target is not None:
            values[target] = source ^ int(target == 1) ^ int(rng.random() < 0.08)
        system.step([source] + values[1:])
    return system.switches


result = {
    "seeds": len(SEEDS),
    "phase_steps": PHASE,
    "exchanges_per_target_seed": statistics.mean(run(seed) for seed in SEEDS),
    "exchanges_per_null_seed": statistics.mean(run(seed, True) for seed in SEEDS),
    "exchanges_per_target_step": statistics.mean(run(seed) for seed in SEEDS) / (3 * PHASE),
    "exchanges_per_null_step": statistics.mean(run(seed, True) for seed in SEEDS) / (3 * PHASE),
}
Path(__file__).with_name("reversible_switch_count_result.json").write_text(
    json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
