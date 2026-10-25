"""Vectorized between-life evolution for organism family candidates."""

import argparse
import datetime
import fcntl
import importlib.util
import json
import math
import random
import sys
import time
from contextlib import nullcontext
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
sys.path.insert(0, str(ROOT))
from organism_judge import STEPS, run_life
from worlds.organism import OrganismWorld
from worlds.organism_config import WORLD_CONFIG

GPU_SLOT = None


def _select_protocol(version):
    """Switch the between-life evaluator while keeping the family API stable."""
    global STEPS, run_life, OrganismWorld, WORLD_CONFIG, GPU_SLOT
    GPU_SLOT = None
    if version == "v7":
        from organism_judge_v7 import STEPS as protocol_steps, run_life as protocol_run_life
        from organism_judge_v7 import _gpu_slot as gpu_slot
        from worlds.organism_v7 import OrganismWorld as protocol_world, V7_CONFIG
        STEPS, run_life, OrganismWorld, WORLD_CONFIG = protocol_steps, protocol_run_life, protocol_world, V7_CONFIG
        GPU_SLOT = gpu_slot


def _load_family(directory):
    path = directory / "family.py"
    spec = importlib.util.spec_from_file_location("organism_family", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not isinstance(module.GENOME, dict) or not module.GENOME:
        raise ValueError("family.py must define a nonempty GENOME dictionary")
    if not callable(getattr(module, "OrganismBrain", None)):
        raise ValueError("family.py must define OrganismBrain")
    for name, domain in module.GENOME.items():
        if not isinstance(name, str) or not isinstance(domain, (tuple, list)):
            raise ValueError("GENOME values must be (min, max) bounds or lists of options")
        if isinstance(domain, tuple) and (len(domain) != 2 or not all(isinstance(v, (int, float)) for v in domain)):
            raise ValueError(f"invalid continuous domain: {name}")
        if isinstance(domain, list) and not domain:
            raise ValueError(f"empty discrete domain: {name}")
    return module


def _sample_genome(module, count, rng, device):
    values = {}
    for name, domain in module.GENOME.items():
        if isinstance(domain, tuple):
            low, high = map(float, domain)
            values[name] = torch.tensor([rng.uniform(low, high) for _ in range(count)],
                                        device=device, dtype=torch.float32)
        else:
            values[name] = torch.tensor([rng.randrange(len(domain)) for _ in range(count)],
                                        device=device, dtype=torch.long)
    return values


def _encode(genome, module):
    return {key: value.detach().cpu().tolist() for key, value in genome.items()}


def _fitness(module, genome, units, device, world_seed, worlds_per_genome, life_steps):
    population = next(iter(genome.values())).shape[0]
    batch = population * worlds_per_genome
    expanded = {name: value.repeat_interleave(worlds_per_genome) for name, value in genome.items()}
    brain = module.OrganismBrain(n_units=units, n_sensors=OrganismWorld.N_SENSORS,
                                n_motors=OrganismWorld.N_MOTORS, batch=batch,
                                device=device, seed=world_seed + 1729, genome=expanded)
    result = run_life(brain, batch, device, world_seed, steps=life_steps, n_units=units)
    scores = torch.tensor([sample["rooms_reached"] for sample in result["samples"]],
                          dtype=torch.float32).view(population, worlds_per_genome)
    survival = torch.tensor([sample["survival"] for sample in result["samples"]],
                            dtype=torch.float32).view(population, worlds_per_genome)
    # The judge's rooms-reached score is primary; survival breaks exact ties.
    fitness = scores.mean(1) + survival.mean(1) * 1e-3
    return fitness, scores.mean(1), survival.mean(1), scores + survival * 1e-3


def _mutate(parent_a, parent_b, module, rng, scale):
    child = {}
    for name, domain in module.GENOME.items():
        a, b = parent_a[name], parent_b[name]
        choose_b = torch.rand(a.shape, device=a.device) < 0.5
        value = torch.where(choose_b, b, a).clone()
        mutate = torch.rand(a.shape, device=a.device) < 0.25
        if isinstance(domain, tuple):
            width = float(domain[1]) - float(domain[0])
            changed = value + torch.randn(value.shape, device=value.device) * width * scale
            value = torch.where(mutate, changed, value)
            value.clamp_(float(domain[0]), float(domain[1]))
        else:
            random_options = torch.randint(len(domain), value.shape, device=value.device)
            value = torch.where(mutate, random_options, value)
        child[name] = value
    return child


def _select(genome, indexes):
    return {name: value[indexes].clone() for name, value in genome.items()}


def _ci(values):
    mean = sum(values) / len(values)
    sem = (sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1) / len(values)) ** 0.5
    return [mean - 1.96 * sem, mean + 1.96 * sem]


def _generation_progress(fitness_mean, score_best, initial_fitness_mean, initial_score_best):
    return {"fitness_mean_from_initial": fitness_mean - initial_fitness_mean,
            "score_best_from_initial": score_best - initial_score_best}


def _lock(deadline):
    handle = (ROOT / ".gpu.lock").open("a+")
    while time.monotonic() < deadline:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return handle
        except BlockingIOError:
            time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))
    handle.close()
    return None


def _save_candidate(directory, module, genome, best_index):
    fixed = {name: (float(value[best_index]) if isinstance(module.GENOME[name], tuple)
                    else int(value[best_index]))
             for name, value in genome.items()}
    code = f'''"""Best fixed genome from between-life family evolution."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("evolved_family", Path(__file__).with_name("family.py"))
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)
PARAMS = {fixed!r}
GENOME = PARAMS

class OrganismBrain:
    def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0, params=None):
        self.torch = __import__("torch")
        chosen = {{**GENOME, **(params or {{}})}}
        values = {{key: self.torch.full((batch,), value, device=device) for key, value in chosen.items()}}
        self.brain = _family.OrganismBrain(n_units, n_sensors, n_motors, batch, device,
                                           seed=seed, genome=values)

    def act(self, sensors):
        return self.brain.act(sensors)

    def structure(self):
        return self.brain.structure() if hasattr(self.brain, "structure") else None
'''
    target = directory / "principle_organism.py"
    target.write_text(code, encoding="utf-8")
    return fixed, target


def evolve(args):
    _select_protocol(args.organism_version)
    family_dir = args.family.resolve()
    module = _load_family(family_dir)
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    life_steps = args.steps or STEPS
    rng = random.Random(args.seed)
    population = _sample_genome(module, args.population, rng, device)
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    run_dir = family_dir / "evolution" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    records = []
    best = {"fitness": -math.inf, "genome": None}
    initial_fitness_mean = None
    initial_score_best = None
    evolution_world_seed = rng.randrange(1, 2**31 - 1)
    generations = args.generations
    deadline = started + args.budget_minutes * 60
    for generation in range(generations):
        if time.monotonic() >= deadline:
            break
        # Reuse the same sampled batch in every generation so selection
        # progress is not confounded with a new world draw.
        world_seed = evolution_world_seed
        lock = _lock(deadline) if device == "cuda" else None
        if device == "cuda" and lock is None:
            break
        tick = time.monotonic()
        try:
            slot = GPU_SLOT() if device == "cuda" and GPU_SLOT else nullcontext()
            with slot:
                fitness, score, survival, world_fitness = _fitness(module, population, args.units,
                                                                    device, world_seed, args.worlds,
                                                                    life_steps)
        finally:
            if lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
                lock.close()
        rank = torch.argsort(fitness, descending=True)
        elite_n = max(2, args.population // 4)
        elites = _select(population, rank[:elite_n])
        top = int(rank[0])
        fitness_mean = float(fitness.mean())
        score_best = float(score[top])
        if initial_fitness_mean is None:
            initial_fitness_mean = fitness_mean
            initial_score_best = score_best
        best_record = {name: value[top].item() for name, value in population.items()}
        if float(fitness[top]) > best["fitness"]:
            best = {"fitness": float(fitness[top]), "score": float(score[top]),
                    "survival": float(survival[top]), "genome": best_record,
                    "generation": generation}
        diversity = {name: float(torch.std(value.float(), unbiased=False).item())
                     for name, value in population.items()}
        record = {"generation": generation, "world_seed": world_seed,
                  "worlds_per_genome": args.worlds,
                  "life_result": {"fitness_mean": fitness_mean,
                                  "fitness_best": float(fitness[top]),
                                  "score_best": score_best,
                                  "survival_best": float(survival[top])},
                  "fitness_mean": fitness_mean,
                  "fitness_best": float(fitness[top]),
                  "score_best": score_best,
                  "survival_best": float(survival[top]),
                  "generation_progress": _generation_progress(
                      fitness_mean, score_best, initial_fitness_mean, initial_score_best),
                  "fitness_ci95": _ci(world_fitness[top].tolist()),
                  "diversity": diversity, "seconds": time.monotonic() - tick}
        records.append(record)
        with (run_dir / "curve.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        print(json.dumps(record, sort_keys=True), flush=True)
        if generation + 1 < generations and time.monotonic() < deadline:
            next_gen = {name: [] for name in module.GENOME}
            for index in range(elite_n):
                for name in module.GENOME:
                    next_gen[name].append(elites[name][index])
            while len(next_gen[next(iter(next_gen))]) < args.population:
                a, b = rng.randrange(elite_n), rng.randrange(elite_n)
                child = _mutate(_select(elites, [a]), _select(elites, [b]), module, rng, args.mutation)
                for name in module.GENOME:
                    next_gen[name].append(child[name][0])
            population = {name: torch.stack(values) for name, values in next_gen.items()}
    if not records:
        raise RuntimeError("budget too short to complete one generation")
    (run_dir / "best.json").write_text(json.dumps(best, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "config.json").write_text(json.dumps(vars(args) | {"device": device,
        "life_steps": life_steps,
        "algorithm": "elitist genetic algorithm; 25% elite, 50% uniform crossover, 25% mutation",
        "world_sampling": "same deterministic batch for every generation",
        "mutation_scale": args.mutation, "worlds_per_generation": args.worlds,
        "fitness": "mean rooms_reached + 0.001 * survival tie-break"}, indent=2, default=str) + "\n",
        encoding="utf-8")
    output_name = args.output_name or (family_dir.name + "_evolved")
    evolved = PROJECT / "candidates" / output_name
    evolved.mkdir(exist_ok=True)
    # Ensure the family implementation travels with its fixed-genome candidate.
    (evolved / "family.py").write_text((family_dir / "family.py").read_text(encoding="utf-8"), encoding="utf-8")
    best_genome = {name: [value] for name, value in best["genome"].items()}
    fixed, candidate_path = _save_candidate(evolved, module, best_genome, 0)
    final = {"candidate": evolved.name, "family": family_dir.name, "author": args.author,
             "best": best, "generations": len(records), "seconds": time.monotonic() - started,
             "organism_version": args.organism_version, "life_steps": life_steps,
             "device": device,
             "path": str(candidate_path.relative_to(PROJECT)),
             "run_dir": str(run_dir.relative_to(PROJECT))}
    with (ROOT / "evolution.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(final, sort_keys=True) + "\n")
    print(json.dumps(final, sort_keys=True), flush=True)
    return final


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", type=Path)
    parser.add_argument("--author", default="unspecified")
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--population", type=int, default=32)
    parser.add_argument("--budget-minutes", type=float, default=20)
    parser.add_argument("--worlds", type=int, default=4)
    parser.add_argument("--units", type=int, default=302)
    parser.add_argument("--steps", type=int, default=None,
                        help="life steps per genome (defaults to the selected world protocol)")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto",
                        help="evaluation device; CPU is useful for short generation-mechanics checks")
    parser.add_argument("--output-name", default=None,
                        help="candidate directory name for the selected genome")
    parser.add_argument("--mutation", type=float, default=0.12)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--organism-version", choices=("v6", "v7"), default="v7",
                        help="world protocol used between generations")
    args = parser.parse_args()
    if (args.generations < 1 or args.population < 4 or args.worlds < 1
            or args.budget_minutes <= 0 or (args.steps is not None and args.steps < 1)):
        parser.error("generations>=1, population>=4, worlds>=1, steps>=1 and budget-minutes>0 required")
    evolve(args)


if __name__ == "__main__":
    main()
