#!/usr/bin/env python3
"""Deterministic, reward-free judge for GENESIS principle candidates."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import random
import select
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
SEEDS = (1103, 2029, 7919)
ROBUSTNESS_SEEDS = (3253, 6679, 10427, 15401)
CHANNELS = 12
SOURCE_CHANNELS = 6
PHASE_REGIMES = ("A", "B", "C", "D", "A", "D", "C", "B", "A")
PHASE_COMPLEXITY = (1, 2, 4, 6, 1, 6, 4, 2, 1)
PHASE_LENGTH_MIN = 192
PHASE_LENGTH_MAX = 224
ADAPT_WINDOW = 16
ADAPT_THRESHOLD = 0.18
LEVEL_TIMEOUTS = {1: 900, 2: 900, 3: 1800, 4: 7200}
DEFAULT_STREAM_TIMEOUT = 900
SNAKE_SEEDS = (1301, 2027, 4099)
CRAFTER_SEEDS = (1709, 3251, 7919)
SNAKE_HORIZON = 1000
CRAFTER_HORIZON = 10000
SNAKE_WIDTH = 10
SNAKE_HEIGHT = 10
SNAKE_ACTIONS = 4
CRAFTER_ACTIONS = 17
LEARNING_MIN_IMPROVEMENT = 0.05
LEARNING_MIN_PAIRS_FRACTION = 0.5
CONTROL_EPISODES = 2
CURVE_POINTS = 64
GROK_SHORT_STEPS = 2048
GROK_LONG_STEPS = 16384
GROK_SCALING_STEPS = 1024

# These are filled from the committed reference-candidate runs below. They are
# intentionally fixed so a leaderboard entry cannot change its own gate.
LEVEL_BASELINES = {
    1: {"candidate": "_baseline_online", "score": 20.9957},
    2: {"candidate": "_baseline_online", "score": 10.6251},
    3: {"candidate": "_baseline_snake_wall", "score": 28.3005},
    4: {"candidate": "_baseline_snake_random", "score": 8.8746},
}

LEVEL_WEIGHTS = {
    1: {"prediction_skill_vs_constant": 0.35, "adaptation_score": 0.20,
        "return_memory_score": 0.15, "structure_score": 0.20, "cost_score": 0.10},
    2: {"prediction_skill_vs_constant": 0.35, "adaptation_score": 0.20,
        "return_memory_score": 0.15, "structure_score": 0.20, "cost_score": 0.10},
    3: {"life_score": 0.25, "apple_score": 0.25, "board_coverage_score": 0.10,
        "behavior_diversity_score": 0.15, "structure_score": 0.15, "cost_score": 0.10},
    4: {"crafter_task_score": 0.80, "structure_score": 0.10, "cost_score": 0.10},
}

EDGE_MAPS = {
    "A": (0, 1, 2, 3, 4, 5),
    "B": (1, 3, 5, 0, 2, 4),
    "C": (2, 5, 1, 4, 0, 3),
    "D": (3, 2, 0, 5, 1, 4),
}


class SensoryWorld:
    """A seeded stream with rhythmic channels and hidden causal edges."""

    def __init__(self, seed: int):
        self.seed = int(seed)
        schedule_rng = random.Random(self.seed ^ 0x4A31C2)
        signal_rng = random.Random(self.seed ^ 0x71B9E5)
        self.lengths = [schedule_rng.randint(PHASE_LENGTH_MIN, PHASE_LENGTH_MAX)
                        for _ in PHASE_REGIMES]
        self.boundaries = []
        total = 0
        for length in self.lengths:
            total += length
            self.boundaries.append(total)
        self.signal_rng = signal_rng
        self.rhythm_phase = signal_rng.random() * math.tau
        self.period = 37 + (self.seed % 29)
        self.secondary_period = 71 + (self.seed % 37)
        self.t = 0
        self.obs = self._initial_observation()

    def _source_probability(self, channel: int, time_index: int) -> float:
        phase = 2.0 * math.pi * time_index / self.period + self.rhythm_phase
        second = 2.0 * math.pi * time_index / self.secondary_period
        value = (0.5 + 0.29 * math.sin(phase + channel * 0.31)
                 + 0.13 * math.sin(second - channel * 0.19))
        return min(0.95, max(0.05, value))

    def _initial_observation(self):
        values = []
        for channel in range(SOURCE_CHANNELS):
            values.append(float(self.signal_rng.random() < self._source_probability(channel, 0)))
        values.extend(float(self.signal_rng.randrange(2)) for _ in range(SOURCE_CHANNELS))
        return values

    def phase_at(self, transition: int):
        for index, boundary in enumerate(self.boundaries):
            if transition < boundary:
                return index
        return len(self.boundaries) - 1

    def advance(self):
        phase_index = self.phase_at(self.t)
        regime = PHASE_REGIMES[phase_index]
        complexity = PHASE_COMPLEXITY[phase_index]
        next_time = self.t + 1
        nxt = [0.0] * CHANNELS

        # Six rhythm-driven source channels share hidden periodic structure.
        for channel in range(SOURCE_CHANNELS):
            probability = self._source_probability(channel, next_time)
            nxt[channel] = float(self.signal_rng.random() < probability)

        # The first k output channels are caused by regime-specific sources.
        # Remaining outputs retain themselves with a rhythm-modulated hazard.
        for offset in range(SOURCE_CHANNELS):
            target = SOURCE_CHANNELS + offset
            if offset < complexity:
                source = EDGE_MAPS[regime][offset]
                noise_phase = 2.0 * math.pi * next_time / self.secondary_period + offset
                flip_probability = 0.09 + 0.035 * math.sin(noise_phase)
                nxt[target] = 1.0 if self.obs[source] != 0.0 else 0.0
                if self.signal_rng.random() < flip_probability:
                    nxt[target] = 1.0 - nxt[target]
            else:
                rhythm = 0.5 + 0.5 * math.sin(
                    2.0 * math.pi * next_time / self.period + offset * 0.47 + self.rhythm_phase)
                flip_probability = 0.035 + 0.19 * rhythm
                nxt[target] = self.obs[target]
                if self.signal_rng.random() < flip_probability:
                    nxt[target] = 1.0 - nxt[target]

        self.obs = nxt
        self.t += 1
        active_targets = tuple(range(SOURCE_CHANNELS, SOURCE_CHANNELS + complexity))
        return nxt[:], {
            "phase": phase_index,
            "regime": regime,
            "complexity": complexity,
            "active_targets": active_targets,
        }


class ComplexSensoryWorld:
    """32-channel stream with delayed, nonlinear causes and sparse regime returns."""

    regimes = ("A", "B", "C", "D", "E", "F", "A", "F", "E", "D", "C", "B", "A")
    complexities = (1, 3, 6, 10, 14, 16, 1, 16, 14, 10, 6, 3, 1)
    channels = 32
    source_channels = 16

    def __init__(self, seed: int):
        self.seed = int(seed)
        schedule_rng = random.Random(self.seed ^ 0x5C28A1)
        self.rng = random.Random(self.seed ^ 0x9271D3)
        self.lengths = [schedule_rng.randint(170, 210) for _ in self.regimes]
        self.boundaries = []
        total = 0
        for length in self.lengths:
            total += length
            self.boundaries.append(total)
        self.phase_shift = self.rng.random() * math.tau
        self.slow_period = 83 + self.seed % 31
        self.fast_period = 17 + self.seed % 11
        self.t = 0
        self.obs = self._initial_observation()
        self.history = [self.obs[:]]

    def _source_probability(self, channel, time_index):
        slow = math.sin(math.tau * time_index / self.slow_period + channel * 0.23 + self.phase_shift)
        fast = math.sin(math.tau * time_index / self.fast_period - channel * 0.41)
        return min(0.94, max(0.06, 0.5 + 0.24 * slow + 0.18 * fast))

    def _initial_observation(self):
        values = [float(self.rng.random() < self._source_probability(channel, 0))
                  for channel in range(self.source_channels)]
        values.extend(float(self.rng.randrange(2)) for _ in range(self.source_channels))
        return values

    def phase_at(self, transition):
        for index, boundary in enumerate(self.boundaries):
            if transition < boundary:
                return index
        return len(self.boundaries) - 1

    def advance(self):
        phase = self.phase_at(self.t)
        regime = self.regimes[phase]
        complexity = self.complexities[phase]
        next_time = self.t + 1
        nxt = [0.0] * self.channels
        for channel in range(self.source_channels):
            nxt[channel] = float(self.rng.random() < self._source_probability(channel, next_time))
        for offset in range(self.source_channels):
            target = self.source_channels + offset
            if offset < complexity:
                a = (offset * 3 + ord(regime) - 65) % self.source_channels
                b = (offset * 7 + 2 * (ord(regime) - 65) + 1) % self.source_channels
                c = (offset * 5 + 3 * (ord(regime) - 65) + 2) % self.source_channels
                lag_a = self.history[0][a]
                lag_b = self.history[3][b] if len(self.history) > 3 else self.history[-1][b]
                lag_c = self.history[1][c] if len(self.history) > 1 else self.history[-1][c]
                form = (offset + ord(regime)) % 4
                if form == 0:
                    value = lag_a
                elif form == 1:
                    value = float(lag_a and lag_b)
                elif form == 2:
                    value = float(bool(lag_a) ^ bool(lag_b))
                else:
                    value = float(bool(lag_a and lag_b) ^ bool(lag_c))
                rhythm = 0.5 + 0.5 * math.sin(
                    math.tau * next_time / self.fast_period + offset * 0.37 + self.phase_shift)
                flip = 0.08 + 0.16 * rhythm
                nxt[target] = 1.0 - value if self.rng.random() < flip else value
            else:
                rhythm = 0.5 + 0.5 * math.sin(
                    math.tau * next_time / self.slow_period + offset * 0.19 + self.phase_shift)
                flip = 0.06 + 0.28 * rhythm
                nxt[target] = 1.0 - self.obs[target] if self.rng.random() < flip else self.obs[target]
        self.obs = nxt
        self.history.insert(0, nxt[:])
        del self.history[4:]
        self.t += 1
        active = tuple(range(self.source_channels, self.source_channels + complexity))
        return nxt[:], {"phase": phase, "regime": regime, "complexity": complexity,
                        "active_targets": active}


_WORKER_SOURCE = r'''import contextlib
import importlib.util
import io
import json
import math
import os
import random
import resource
import sys
import time

protocol_out = sys.stdout
random.seed(0)
if hasattr(os, "sched_getaffinity"):
    available_cpus = sorted(os.sched_getaffinity(0))
    if available_cpus:
        os.sched_setaffinity(0, set(available_cpus[:3]))
memory_limit = 6 * 1024 * 1024 * 1024
resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
candidate_path = os.path.abspath(sys.argv[1])
params_override = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
spec = importlib.util.spec_from_file_location("principle", candidate_path)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load principle.py")
module = importlib.util.module_from_spec(spec)
noise = io.StringIO()
with contextlib.redirect_stdout(noise), contextlib.redirect_stderr(noise):
    spec.loader.exec_module(module)
    System = getattr(module, "System", None)
    if System is None:
        raise RuntimeError("principle.py must define class System")
    if params_override is not None:
        module.PARAMS = params_override
    agent = System()

def clean(value, depth=0):
    if depth > 4:
        raise ValueError("response nesting exceeds four levels")
    if hasattr(value, "tolist"):
        value = value.tolist()
    elif hasattr(value, "item") and not isinstance(value, (str, bytes, dict, list, tuple)):
        value = value.item()
    if isinstance(value, dict):
        if len(value) > 256:
            raise ValueError("response dictionary is too large")
        return {str(k): clean(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        if len(value) > 4096:
            raise ValueError("response list is too large")
        return [clean(v, depth + 1) for v in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ValueError("response contains a non-finite or unsupported value")

for line in sys.stdin:
    request = json.loads(line)
    if request is None:
        break
    started = time.process_time()
    try:
        action_mode = isinstance(request, dict) and request.get("__judge_mode__") == "act"
        observation = request["observation"] if action_mode else request
        with contextlib.redirect_stdout(noise), contextlib.redirect_stderr(noise):
            prediction = agent.step(observation)
            action = agent.act(observation) if action_mode else None
            structure = agent.structure()
        response = {"structure": clean(structure), "cpu_seconds": time.process_time() - started}
        if action_mode:
            response["action"] = clean(action)
        else:
            response["prediction"] = clean(prediction)
        if not isinstance(response["structure"], dict):
            raise ValueError("System.structure() must return a dict")
        encoded = json.dumps(response, allow_nan=False, separators=(",", ":"))
        if len(encoded) > 65536:
            raise ValueError("response exceeds 64 KiB")
        protocol_out.write(encoded + "\n")
        protocol_out.flush()
    except BaseException as exc:
        protocol_out.write(json.dumps({"error": type(exc).__name__ + ": " + str(exc)}) + "\n")
        protocol_out.flush()
        break

usage = resource.getrusage(resource.RUSAGE_SELF)
protocol_out.write(json.dumps({
    "worker_done": True,
    "process_cpu_seconds": time.process_time(),
    "peak_rss_kib": int(usage.ru_maxrss),
}) + "\n")
protocol_out.flush()
'''


class CandidateWorker:
    def __init__(self, principle_path: Path, deadline: float, params_override=None):
        env = os.environ.copy()
        env.update({
            "PYTHONHASHSEED": "0",
            "CUDA_VISIBLE_DEVICES": "",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        })
        self.proc = subprocess.Popen(
            [sys.executable, "-I", "-B", "-c", _WORKER_SOURCE,
             str(principle_path.resolve()), json.dumps(params_override) if params_override is not None else "null"],
            cwd=str(ROOT), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1, start_new_session=True,
        )
        self.deadline = deadline

    def _read(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            self.stop()
            raise TimeoutError("candidate exceeded this level's judge limit")
        readable, _, _ = select.select([self.proc.stdout], [], [], remaining)
        if not readable:
            self.stop()
            raise TimeoutError("candidate exceeded this level's judge limit")
        line = self.proc.stdout.readline()
        if not line:
            code = self.proc.poll()
            raise RuntimeError(f"candidate worker exited without a response (exit={code})")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError("candidate worker returned malformed protocol data") from exc
        if "error" in value:
            raise ValueError("candidate failed: " + value["error"])
        return value

    def step(self, observation):
        try:
            self.proc.stdin.write(json.dumps(observation, separators=(",", ":")) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise RuntimeError("candidate worker closed its input") from exc
        return self._read()

    def act(self, observation):
        request = {"__judge_mode__": "act", "observation": observation}
        try:
            self.proc.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise RuntimeError("candidate worker closed its input") from exc
        return self._read()

    def finish(self):
        if self.proc.poll() is None:
            self.proc.stdin.write("null\n")
            self.proc.stdin.flush()
        value = self._read()
        self.proc.wait(timeout=max(0.1, self.deadline - time.monotonic()))
        self._kill_process_group()
        return value

    def _kill_process_group(self):
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def stop(self):
        self._kill_process_group()
        if self.proc.poll() is None:
            self.proc.wait()


def _load_online_baseline():
    path = PROJECT_ROOT / "candidates" / "_baseline_online" / "principle.py"
    spec = __import__("importlib.util", fromlist=["spec_from_file_location"]).spec_from_file_location(
        "_genesis_online_reference", path)
    module = __import__("importlib.util", fromlist=["module_from_spec"]).module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.System


def _brier(prediction, target):
    return sum((float(p) - float(y)) ** 2 for p, y in zip(prediction, target)) / len(target)


def _structure_mass(structure):
    def first(keys):
        for key in keys:
            value = structure.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                value = float(value)
                if math.isfinite(value) and value >= 0.0:
                    return min(value, 1.0e9)
        return 0.0
    units = first(("units", "neurons", "nodes"))
    connections = first(("connections", "synapses", "edges"))
    memory = first(("memory_bytes", "estimated_state_bytes", "state_bytes"))
    return units + connections, memory


def _structure_signature(structure):
    return json.dumps(structure, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _probe_observation(level, seed):
    """Build one target observation and two different histories for a fresh probe."""
    if level in (1, 2):
        world = SensoryWorld(seed) if level == 1 else ComplexSensoryWorld(seed)
        target = world.obs[:]
        first_history = []
        for _ in range(8):
            observation, _metadata = world.advance()
            first_history.append(observation)
        second_history = [list(reversed(observation)) for observation in first_history]
        return target, (first_history, second_history)
    if level == 3:
        world = SnakeWorld(seed)
        target = world.observe()
        first_history, second_history = [], []
        for actions, history in (((0, 1, 2, 3), first_history), ((2, 3, 0, 1), second_history)):
            replay = SnakeWorld(seed)
            for action in actions:
                history.append(replay.observe())
                replay.step(action)
        return target, (first_history, second_history)
    import crafter
    env = crafter.Env(reward=False, length=CONTROL_EPISODES, seed=int(seed))
    target = env.reset()
    first_history = []
    second_history = []
    for action in (0, 1, 2, 3):
        first_history.append(target.tolist() if hasattr(target, "tolist") else target)
        target, _reward, _done, _info = env.step(action)
    target = env.reset()
    for action in (3, 2, 1, 0):
        second_history.append(target.tolist() if hasattr(target, "tolist") else target)
        target, _reward, _done, _info = env.step(action)
    target = env.reset()
    return target.tolist() if hasattr(target, "tolist") else target, (first_history, second_history)


def _probe_structure_state(principle_path, level, seed, deadline, params_override=None):
    target, histories = _probe_observation(level, seed)

    def call(worker, observation):
        response = worker.step(observation) if level in (1, 2) else worker.act(observation)
        return response["structure"]

    fresh = CandidateWorker(principle_path, deadline, params_override)
    try:
        fresh_structure = call(fresh, target)
        fresh.finish()
    except BaseException:
        fresh.stop()
        raise
    fresh_signature = _structure_signature(fresh_structure)
    changed = []
    for history in histories:
        worker = CandidateWorker(principle_path, deadline, params_override)
        try:
            for observation in history:
                call(worker, observation)
            structure = call(worker, target)
            changed.append(_structure_signature(structure) != fresh_signature)
            worker.finish()
        except BaseException:
            worker.stop()
            raise
    return sum(changed) / max(1, len(changed))


def _stream_learning(phases, regimes):
    by_regime = {}
    for index, regime in enumerate(regimes):
        by_regime.setdefault(regime, []).append(index)
    gains = []
    for indexes in by_regime.values():
        if len(indexes) < 2:
            continue
        first = phases[indexes[0]]
        last = phases[indexes[-1]]
        first_error = first["early_active_target_brier"]
        last_error = last["late_active_target_brier"]
        gains.append((first_error - last_error, first_error))
    if not gains:
        return {"learning_improvement": 0.0, "learning_pairs": 0,
                "learning_pairs_improved": 0, "learning_passed": False}
    total_first = sum(first for _gain, first in gains)
    total_gain = sum(gain for gain, _first in gains)
    improvement = max(0.0, min(1.0, total_gain / max(total_first, 0.05)))
    improved = sum(gain > 0.0 for gain, _first in gains)
    required = math.ceil(len(gains) * LEARNING_MIN_PAIRS_FRACTION)
    return {
        "learning_improvement": improvement,
        "learning_pairs": len(gains),
        "learning_pairs_improved": improved,
        "learning_passed": improvement >= LEARNING_MIN_IMPROVEMENT and improved >= required,
        "learning_first_active_target_brier": total_first / len(gains),
        "learning_last_active_target_brier": sum(first - gain for gain, first in gains) / len(gains),
    }


def _control_learning(first_runs, last_runs):
    gains = []
    for first, last in zip(first_runs, last_runs):
        if "life_score" in first:
            first_quality = 0.5 * first["life_score"] + 0.5 * first["apple_score"]
            last_quality = 0.5 * last["life_score"] + 0.5 * last["apple_score"]
        else:
            first_quality = first["achievement_fraction"]
            last_quality = last["achievement_fraction"]
        gains.append(last_quality - first_quality)
    if not gains:
        return {"learning_improvement": 0.0, "learning_pairs": 0,
                "learning_pairs_improved": 0, "learning_passed": False}
    improvement = sum(gains) / len(gains)
    improved = sum(gain > 0.0 for gain in gains)
    required = math.ceil(len(gains) * LEARNING_MIN_PAIRS_FRACTION)
    return {
        "learning_improvement": improvement,
        "learning_pairs": len(gains),
        "learning_pairs_improved": improved,
        "learning_passed": improvement >= LEARNING_MIN_IMPROVEMENT and improved >= required,
        "learning_first_quality": sum(
            (0.5 * run["life_score"] + 0.5 * run["apple_score"])
            if "life_score" in run else run["achievement_fraction"]
            for run in first_runs) / len(first_runs),
        "learning_last_quality": sum(
            (0.5 * run["life_score"] + 0.5 * run["apple_score"])
            if "life_score" in run else run["achievement_fraction"]
            for run in last_runs) / len(last_runs),
    }


def _phase_metrics(rows, phase_count):
    grouped = [[] for _ in range(phase_count)]
    for row in rows:
        grouped[row["phase"]].append(row)
    summaries = []
    for index, phase_rows in enumerate(grouped):
        targets = phase_rows[0]["targets"]
        target_errors = [row["target_brier"] for row in phase_rows]
        width = min(ADAPT_WINDOW, len(target_errors))
        rolling = [sum(target_errors[start:start + width]) / width
                   for start in range(max(1, len(target_errors) - width + 1))]
        hits = [at for at, value in enumerate(rolling) if value <= ADAPT_THRESHOLD]
        adapt = hits[0] + width if hits else len(phase_rows)
        early = sum(target_errors[:width]) / width
        late = sum(target_errors[-width:]) / width
        mass = sum(row["structure_mass"] for row in phase_rows) / len(phase_rows)
        summaries.append({
            "phase": index,
            "transitions": len(phase_rows),
            "complexity_edges": phase_rows[0]["complexity"],
            "active_target_channels": list(targets),
            "mean_brier": sum(row["brier"] for row in phase_rows) / len(phase_rows),
            "mean_active_target_brier": sum(target_errors) / len(target_errors),
            "early_active_target_brier": early,
            "late_active_target_brier": late,
            "adaptation_steps": adapt,
            "adaptation_hit_threshold": bool(hits),
            "mean_structure_mass": mass,
        })
    return summaries


def _rank(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        average = (start + end - 1) / 2.0
        for position in range(start, end):
            ranks[order[position]] = average
        start = end
    return ranks


def _correlation(left, right):
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    covariance = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right))
    variance_left = sum((a - mean_left) ** 2 for a in left)
    variance_right = sum((b - mean_right) ** 2 for b in right)
    denominator = math.sqrt(variance_left * variance_right)
    return covariance / denominator if denominator else 0.0


def _constant_string_numbers(tree):
    """Count numeric values smuggled through calls such as int('16')."""
    numeric_calls = {"int", "float", "eval", "ord", "len"}
    derived = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id not in numeric_calls or not node.args:
            continue
        value = node.args[0]
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        derived += 1
        if node.func.id == "eval":
            try:
                expression = ast.parse(value.value, mode="eval")
            except SyntaxError:
                continue
            derived += sum(1 for child in ast.walk(expression)
                           if isinstance(child, ast.Constant)
                           and isinstance(child.value, (int, float, complex))
                           and not isinstance(child.value, bool))
    return derived


def _format_dependent_branches(tree):
    """Find conditionals that inspect the protocol shape instead of state."""
    count = 0
    tests = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.While)):
            tests.append(node.test)
    for test in tests:
        for node in ast.walk(test):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "isinstance":
                    count += 1
                elif (node.func.id == "len" and node.args
                      and isinstance(node.args[0], ast.Name)
                      and node.args[0].id in {"obs", "observation"}):
                    count += 1
    return count


def _read_principle(path: Path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    params_node = None
    params_value = {}
    for node in tree.body:
        value_node = None
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "PARAMS" in names:
                value_node = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "PARAMS":
                value_node = node.value
        if value_node is not None:
            if params_node is not None:
                raise ValueError("principle.py may define PARAMS only once at module scope")
            params_node = node
            try:
                params_value = ast.literal_eval(value_node)
            except (ValueError, TypeError) as exc:
                raise ValueError("PARAMS must be a literal dictionary of numbers") from exc
    if params_node is not None:
        if not isinstance(params_value, dict):
            raise ValueError("PARAMS must be a dictionary")
        for key, value in params_value.items():
            if not isinstance(key, str):
                raise ValueError("PARAMS keys must be strings")
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or not math.isfinite(float(value))):
                raise ValueError(f"PARAMS[{key!r}] must be a finite int or float")

    params_literal_ids = ({id(node) for node in ast.walk(params_node)
                           if isinstance(node, ast.Constant)
                           and isinstance(node.value, (int, float, complex))
                           and not isinstance(node.value, bool)}
                          if params_node is not None else set())

    numeric = sum(1 for node in ast.walk(tree)
                  if isinstance(node, ast.Constant)
                  and isinstance(node.value, (int, float, complex))
                  and not isinstance(node.value, bool)
                  and id(node) not in params_literal_ids)
    derived_numeric = _constant_string_numbers(tree)
    numeric += derived_numeric
    format_branches = _format_dependent_branches(tree)
    branches = 0
    occupied_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Match)):
            branches += 1
        elif isinstance(node, ast.BoolOp):
            branches += max(0, len(node.values) - 1)
        if hasattr(node, "lineno"):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            occupied_lines.update(range(start, end + 1))
    counts = {
        "numeric_literals": numeric,
        "conditional_branches": branches,
        "ast_covered_lines": len(occupied_lines),
        "physical_lines": len(source.splitlines()),
        "parameter_count": len(params_value),
        "derived_numeric_literals": derived_numeric,
        "format_dependent_branches": format_branches,
    }
    return counts, params_value


def _elegance(ast_counts):
    penalty = (0.012 * max(0, ast_counts["numeric_literals"] - 4)
               + 0.025 * ast_counts["conditional_branches"]
               + 0.080 * ast_counts["format_dependent_branches"]
               + 0.060 * ast_counts["derived_numeric_literals"]
               + 0.0015 * max(0, ast_counts["ast_covered_lines"] - 18)
               + 0.004 * max(0, ast_counts["parameter_count"] - 4))
    return max(0.10, 1.0 - penalty), min(0.90, penalty)


def _run_seed(principle_path: Path, seed: int, deadline: float, params_override=None):
    world = SensoryWorld(seed)
    worker = CandidateWorker(principle_path, deadline, params_override)
    online_class = _load_online_baseline()
    online = online_class()
    observation = world.obs[:]
    rows = []
    cpu_samples = []
    peak_memory_bytes = []
    try:
        for _ in range(world.boundaries[-1]):
            response = worker.step(observation)
            prediction = response.get("prediction")
            if not isinstance(prediction, list) or len(prediction) != CHANNELS:
                raise ValueError(f"System.step must return {CHANNELS} probabilities")
            if any(not isinstance(item, (int, float)) or isinstance(item, bool)
                   or not math.isfinite(float(item)) or item < 0.0 or item > 1.0
                   for item in prediction):
                raise ValueError("prediction entries must be finite probabilities in [0, 1]")
            structure = response.get("structure")
            if not isinstance(structure, dict):
                raise ValueError("System.structure() must return a dict")
            mass, memory_bytes = _structure_mass(structure)
            cpu_samples.append(float(response.get("cpu_seconds", 0.0)))
            peak_memory_bytes.append(memory_bytes)

            online_prediction = online.step(observation)
            next_observation, metadata = world.advance()
            target_brier = sum((prediction[target] - next_observation[target]) ** 2
                               for target in metadata["active_targets"])
            target_brier /= len(metadata["active_targets"])
            rows.append({
                "phase": metadata["phase"],
                "complexity": metadata["complexity"],
                "targets": metadata["active_targets"],
                "brier": _brier(prediction, next_observation),
                "constant_brier": 0.25,
                "persistence_brier": _brier(observation, next_observation),
                "online_brier": _brier(online_prediction, next_observation),
                "target_brier": target_brier,
                "structure_mass": mass,
            })
            observation = next_observation
        worker_info = worker.finish()
    except BaseException:
        worker.stop()
        raise

    phases = _phase_metrics(rows, len(PHASE_REGIMES))
    learning = _stream_learning(phases, PHASE_REGIMES)
    adapt_values = [phase["adaptation_steps"] / max(phase["transitions"], 1)
                    for phase in phases[1:]]
    adaptation_score = 1.0 - sum(adapt_values) / len(adapt_values)

    first_by_regime = {}
    return_components = []
    for phase_index, phase in enumerate(phases):
        regime = PHASE_REGIMES[phase_index]
        if regime not in first_by_regime:
            first_by_regime[regime] = phase
            continue
        first = first_by_regime[regime]
        first_error = first["early_active_target_brier"]
        returned_error = phase["early_active_target_brier"]
        error_gain = max(0.0, min(1.0,
            (first_error - returned_error) / max(first_error, 0.05)))
        first_speed = first["adaptation_steps"] / max(first["transitions"], 1)
        return_speed = phase["adaptation_steps"] / max(phase["transitions"], 1)
        speed_gain = max(0.0, min(1.0, first_speed - return_speed))
        return_components.append(0.5 * error_gain + 0.5 * speed_gain)
    memory_score = sum(return_components) / len(return_components) if return_components else 0.0

    phase_masses = [phase["mean_structure_mass"] for phase in phases]
    target_complexities = [phase["complexity_edges"] for phase in phases]
    rho = _correlation(_rank(phase_masses), _rank(target_complexities))
    direction_hits = sum(
        1 for index in range(1, len(phases))
        if (phase_masses[index] - phase_masses[index - 1])
        * (target_complexities[index] - target_complexities[index - 1]) > 0.0
    )
    direction_score = direction_hits / max(1, len(phases) - 1)
    observable_structure_score = 0.5 * max(0.0, rho) + 0.5 * direction_score
    structure_state_score = _probe_structure_state(principle_path, 1, seed, deadline, params_override)
    structure_score = observable_structure_score * structure_state_score

    total_brier = sum(row["brier"] for row in rows) / len(rows)
    constant_brier = sum(row["constant_brier"] for row in rows) / len(rows)
    persistence_brier = sum(row["persistence_brier"] for row in rows) / len(rows)
    online_brier = sum(row["online_brier"] for row in rows) / len(rows)
    prediction_score = max(0.0, min(1.0, 1.0 - total_brier / constant_brier))
    cpu_seconds = sum(cpu_samples)
    transitions = len(rows)
    cpu_ms_per_step = 1000.0 * cpu_seconds / max(1, transitions)
    rss_mb = float(worker_info.get("peak_rss_kib", 0)) / 1024.0
    state_mb = (sum(peak_memory_bytes) / max(1, len(peak_memory_bytes))) / (1024.0 * 1024.0)
    cost_score = 1.0 - (
        0.45 * min(1.0, cpu_ms_per_step / 5.0)
        + 0.35 * min(1.0, rss_mb / 512.0)
        + 0.20 * min(1.0, state_mb / 64.0)
    )
    return {
        "seed": seed,
        "transitions": transitions,
        "mean_brier": total_brier,
        "baseline_brier": {
            "constant_0_5": constant_brier,
            "persistence": persistence_brier,
            "online_pairwise": online_brier,
        },
        "prediction_skill_vs_constant": prediction_score,
        "adaptation_score": adaptation_score,
        "return_memory_score": memory_score,
        "structure_score": structure_score,
        "observable_structure_score": observable_structure_score,
        "structure_state_score": structure_state_score,
        **learning,
        "structure_spearman": rho,
        "structure_direction_fraction": direction_score,
        "cost_score": cost_score,
        "resources": {
            "agent_cpu_seconds": cpu_seconds,
            "agent_cpu_ms_per_step": cpu_ms_per_step,
            "worker_process_cpu_seconds": worker_info.get("process_cpu_seconds"),
            "worker_peak_rss_mb": rss_mb,
            "reported_state_mb_mean": state_mb,
        },
        "phases": phases,
    }


def _mean(runs, key):
    return sum(run[key] for run in runs) / len(runs)


def _score_runs(runs):
    metrics = {
        key: _mean(runs, key)
        for key in ("prediction_skill_vs_constant", "adaptation_score", "return_memory_score",
                    "structure_score", "cost_score", "learning_improvement",
                    "learning_pairs_improved", "learning_pairs")
    }
    metrics["learning_passed"] = (
        metrics["learning_improvement"] >= LEARNING_MIN_IMPROVEMENT
        and metrics["learning_pairs_improved"] >= math.ceil(
            metrics["learning_pairs"] * LEARNING_MIN_PAIRS_FRACTION))
    metrics["mean_brier"] = _mean(runs, "mean_brier")
    metrics["baseline_brier"] = {
        baseline: sum(run["baseline_brier"][baseline] for run in runs) / len(runs)
        for baseline in ("constant_0_5", "persistence", "online_pairwise")
    }
    weighted = (
        0.35 * metrics["prediction_skill_vs_constant"]
        + 0.20 * metrics["adaptation_score"]
        + 0.15 * metrics["return_memory_score"]
        + 0.20 * metrics["structure_score"]
        + 0.10 * metrics["cost_score"]
    )
    return metrics, 100.0 * weighted


def _run_complex_stream_seed(principle_path, seed, deadline, params_override=None):
    world = ComplexSensoryWorld(seed)
    worker = CandidateWorker(principle_path, deadline, params_override)
    online = _load_online_baseline()()
    observation = world.obs[:]
    rows, cpu_samples, state_bytes = [], [], []
    try:
        for _ in range(world.boundaries[-1]):
            response = worker.step(observation)
            prediction = response.get("prediction")
            if not isinstance(prediction, list) or len(prediction) != world.channels:
                raise ValueError(f"System.step must return {world.channels} probabilities")
            if any(not isinstance(item, (int, float)) or isinstance(item, bool)
                   or not math.isfinite(float(item)) or not 0 <= item <= 1 for item in prediction):
                raise ValueError("prediction entries must be finite probabilities in [0, 1]")
            mass, memory = _structure_mass(response.get("structure", {}))
            cpu_samples.append(float(response.get("cpu_seconds", 0.0)))
            state_bytes.append(memory)
            online_prediction = online.step(observation)
            next_observation, metadata = world.advance()
            active = metadata["active_targets"]
            rows.append({
                "phase": metadata["phase"], "regime": metadata["regime"],
                "complexity": metadata["complexity"], "targets": active,
                "brier": _brier(prediction, next_observation),
                "constant_brier": 0.25,
                "persistence_brier": _brier(observation, next_observation),
                "online_brier": _brier(online_prediction, next_observation),
                "target_brier": sum((prediction[i] - next_observation[i]) ** 2 for i in active) / len(active),
                "structure_mass": mass,
            })
            observation = next_observation
        worker_info = worker.finish()
    except BaseException:
        worker.stop()
        raise
    phases = _phase_metrics(rows, len(world.regimes))
    learning = _stream_learning(phases, world.regimes)
    adapt_values = [phase["adaptation_steps"] / max(phase["transitions"], 1) for phase in phases[1:]]
    adaptation = 1.0 - sum(adapt_values) / len(adapt_values)
    first_by_regime, memory_parts = {}, []
    for phase_index, phase in enumerate(phases):
        regime = world.regimes[phase_index]
        if regime not in first_by_regime:
            first_by_regime[regime] = phase
            continue
        first = first_by_regime[regime]
        error_gain = max(0.0, min(1.0, (first["early_active_target_brier"]
                         - phase["early_active_target_brier"])
                         / max(first["early_active_target_brier"], 0.05)))
        first_speed = first["adaptation_steps"] / max(first["transitions"], 1)
        return_speed = phase["adaptation_steps"] / max(phase["transitions"], 1)
        memory_parts.append(0.5 * error_gain + 0.5 * max(0.0, min(1.0, first_speed - return_speed)))
    memory = sum(memory_parts) / len(memory_parts) if memory_parts else 0.0
    masses = [phase["mean_structure_mass"] for phase in phases]
    complexities = [phase["complexity_edges"] for phase in phases]
    rho = _correlation(_rank(masses), _rank(complexities))
    directions = sum(1 for index in range(1, len(phases))
                     if (masses[index] - masses[index - 1])
                     * (complexities[index] - complexities[index - 1]) > 0)
    direction_score = directions / max(1, len(phases) - 1)
    transitions = len(rows)
    brier = sum(row["brier"] for row in rows) / transitions
    baseline_brier = {name: sum(row[key] for row in rows) / transitions for name, key in (
        ("constant_0_5", "constant_brier"), ("persistence", "persistence_brier"),
        ("online_pairwise", "online_brier"))}
    cpu = sum(cpu_samples)
    cpu_ms = cpu * 1000 / transitions
    rss_mb = worker_info.get("peak_rss_kib", 0) / 1024.0
    state_mb = (sum(state_bytes) / transitions) / (1024 * 1024)
    cost = _cost_score(cpu, transitions, rss_mb, state_mb)
    observable_structure_score = 0.5 * max(0.0, rho) + 0.5 * direction_score
    structure_state_score = _probe_structure_state(principle_path, 2, seed, deadline, params_override)
    return {
        "seed": seed, "transitions": transitions, "mean_brier": brier,
        "baseline_brier": baseline_brier,
        "prediction_skill_vs_constant": max(0.0, min(1.0, 1.0 - brier / 0.25)),
        "adaptation_score": adaptation, "return_memory_score": memory,
        "structure_score": observable_structure_score * structure_state_score,
        "observable_structure_score": observable_structure_score,
        "structure_state_score": structure_state_score,
        **learning,
        "structure_spearman": rho, "structure_direction_fraction": direction_score,
        "cost_score": cost,
        "resources": {"agent_cpu_seconds": cpu, "agent_cpu_ms_per_step": cpu_ms,
                      "worker_process_cpu_seconds": worker_info.get("process_cpu_seconds"),
                      "worker_peak_rss_mb": rss_mb, "reported_state_mb_mean": state_mb},
        "phases": phases,
    }


def _cost_score(cpu_seconds, steps, rss_mb, state_mb):
    cpu_ms = 1000.0 * cpu_seconds / max(1, steps)
    return 1.0 - (0.45 * min(1.0, cpu_ms / 5.0)
                  + 0.35 * min(1.0, rss_mb / 512.0)
                  + 0.20 * min(1.0, state_mb / 64.0))


class SnakeWorld:
    """Deterministic 10x10 Snake; head direction is encoded in the bit board."""

    def __init__(self, seed):
        self.rng = random.Random(int(seed))
        self.body = [(5, 5), (4, 5), (3, 5)]
        self.direction = 1
        self.apple = self._spawn_apple()
        self.visited = {self.body[0]}
        self.steps = 0
        self.apples = 0
        self.done = False

    def _spawn_apple(self):
        free = [(x, y) for y in range(SNAKE_HEIGHT) for x in range(SNAKE_WIDTH)
                if (x, y) not in self.body]
        return self.rng.choice(free) if free else None

    def observe(self):
        bits = [0] * (7 * SNAKE_WIDTH * SNAKE_HEIGHT)
        head_x, head_y = self.body[0]
        bits[self.direction * 100 + head_y * 10 + head_x] = 1
        for x, y in self.body[1:]:
            bits[400 + y * 10 + x] = 1
        if self.apple is not None:
            x, y = self.apple
            bits[500 + y * 10 + x] = 1
        return bits

    def step(self, action):
        if action not in range(SNAKE_ACTIONS):
            raise ValueError("Snake System.act must return an integer from 0 through 3")
        if action != (self.direction + 2) % SNAKE_ACTIONS:
            self.direction = action
        dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0))[self.direction]
        head = (self.body[0][0] + dx, self.body[0][1] + dy)
        eating = head == self.apple
        collision_body = self.body if eating else self.body[:-1]
        crashed = (not 0 <= head[0] < SNAKE_WIDTH or not 0 <= head[1] < SNAKE_HEIGHT
                   or head in collision_body)
        self.steps += 1
        if crashed:
            self.done = True
        else:
            self.body.insert(0, head)
            if eating:
                self.apples += 1
                self.apple = self._spawn_apple()
                if self.apple is None:
                    self.done = True
            else:
                self.body.pop()
            self.visited.add(head)
        return {"steps": self.steps, "apples": self.apples, "snake_length": len(self.body),
                "board_coverage": len(self.visited) / 100.0, "done": self.done,
                "complexity": len(self.body)}


def _game_structure_score(masses, complexities):
    rho = _correlation(_rank(masses), _rank(complexities))
    directional = [(masses[i] - masses[i - 1]) * (complexities[i] - complexities[i - 1])
                   for i in range(1, len(masses)) if complexities[i] != complexities[i - 1]]
    direction = sum(value > 0 for value in directional) / max(1, len(directional))
    return 0.5 * max(0.0, rho) + 0.5 * direction, rho, direction


def _action_value(response, action_count):
    action = response.get("action")
    if isinstance(action, bool) or not isinstance(action, int) or not 0 <= action < action_count:
        raise ValueError(f"System.act must return an integer in [0, {action_count})")
    return action


def _run_snake_seed(principle_path, seed, deadline, params_override=None):
    worker = CandidateWorker(principle_path, deadline, params_override)
    masses, complexities, actions, cpu_samples, state_bytes = [], [], [], [], []
    episode_runs = []
    try:
        for _episode in range(CONTROL_EPISODES):
            world = SnakeWorld(seed)
            episode_actions = []
            while world.steps < SNAKE_HORIZON and not world.done:
                response = worker.act(world.observe())
                action = _action_value(response, SNAKE_ACTIONS)
                actions.append(action)
                episode_actions.append(action)
                info = response["structure"]
                mass, memory = _structure_mass(info)
                cpu_samples.append(float(response.get("cpu_seconds", 0.0)))
                state_bytes.append(memory)
                row = world.step(action)
                masses.append(mass)
                complexities.append(row["complexity"])
            episode_runs.append({
                "survival_steps": len(episode_actions), "apples_eaten": world.apples,
                "board_coverage": len(world.visited) / 100.0,
                "behavior_diversity": _action_diversity(episode_actions),
                "life_score": len(episode_actions) / SNAKE_HORIZON,
                "apple_score": min(1.0, world.apples / 5.0),
                "board_coverage_score": len(world.visited) / 100.0,
                "behavior_diversity_score": _action_diversity(episode_actions),
                "unique_action_triplets": len({tuple(episode_actions[index:index + 3])
                                               for index in range(max(0, len(episode_actions) - 2))}),
                "final_snake_length": len(world.body),
            })
        worker_info = worker.finish()
    except BaseException:
        worker.stop()
        raise
    action_counts = [actions.count(index) for index in range(SNAKE_ACTIONS)]
    total_actions = max(1, len(actions))
    probabilities = [count / total_actions for count in action_counts if count]
    entropy = -sum(value * math.log(value) for value in probabilities) / math.log(SNAKE_ACTIONS)
    triplets = {tuple(actions[index:index + 3]) for index in range(max(0, len(actions) - 2))}
    diversity = sum(run["behavior_diversity"] for run in episode_runs) / len(episode_runs)
    structure, rho, direction = _game_structure_score(masses, complexities)
    observable_structure_score = structure
    structure_state_score = _probe_structure_state(principle_path, 3, seed, deadline, params_override)
    structure *= structure_state_score
    turns = len(actions)
    cpu = sum(cpu_samples)
    rss_mb = worker_info.get("peak_rss_kib", 0) / 1024.0
    state_mb = (sum(state_bytes) / max(1, len(state_bytes))) / (1024 * 1024)
    return {
        "seed": seed, "survival_steps": _mean(episode_runs, "survival_steps"),
        "apples_eaten": _mean(episode_runs, "apples_eaten"),
        "board_coverage": _mean(episode_runs, "board_coverage"),
        "behavior_diversity": diversity, "action_entropy": entropy,
        "life_score": _mean(episode_runs, "life_score"),
        "apple_score": _mean(episode_runs, "apple_score"),
        "board_coverage_score": _mean(episode_runs, "board_coverage_score"),
        "behavior_diversity_score": diversity,
        "unique_action_triplets": len(triplets), "structure_score": structure,
        "observable_structure_score": observable_structure_score,
        "structure_state_score": structure_state_score,
        "structure_spearman": rho, "structure_direction_fraction": direction,
        "cost_score": _cost_score(cpu, turns, rss_mb, state_mb),
        "resources": {"agent_cpu_seconds": cpu, "agent_cpu_ms_per_step": cpu * 1000 / max(1, turns),
                      "worker_process_cpu_seconds": worker_info.get("process_cpu_seconds"),
                      "worker_peak_rss_mb": rss_mb, "reported_state_mb_mean": state_mb},
        "final_snake_length": episode_runs[-1]["final_snake_length"], "transitions": turns,
        **_control_learning(episode_runs[:1], episode_runs[-1:]),
        "episodes": episode_runs,
    }


def _action_diversity(actions):
    action_counts = [actions.count(index) for index in range(SNAKE_ACTIONS)]
    total_actions = max(1, len(actions))
    probabilities = [count / total_actions for count in action_counts if count]
    entropy = -sum(value * math.log(value) for value in probabilities) / math.log(SNAKE_ACTIONS)
    triplets = {tuple(actions[index:index + 3]) for index in range(max(0, len(actions) - 2))}
    return 0.5 * entropy + 0.5 * min(1.0, len(triplets) / 64.0)


def _crafter_complexity(image, previous):
    import numpy as np
    sample = np.asarray(image, dtype=np.uint8)[::4, ::4].reshape(-1, 3)
    colors = len(np.unique(sample, axis=0)) / max(1, len(sample))
    motion = 0.0 if previous is None else float(np.mean(np.abs(
        sample.astype(np.int16) - np.asarray(previous, dtype=np.int16)))) / 255.0
    return min(1.0, colors * 8.0 + motion * 4.0), sample


def _run_crafter_seed(principle_path, seed, deadline, params_override=None):
    import crafter
    import numpy as np
    worker = CandidateWorker(principle_path, deadline, params_override)
    achievements = set()
    masses, complexities, cpu_samples, state_bytes = [], [], [], []
    episode_runs = []
    try:
        for _episode in range(CONTROL_EPISODES):
            env = crafter.Env(reward=False, length=CRAFTER_HORIZON, seed=int(seed))
            observation = env.reset()
            previous_sample = None
            episode_achievements = set()
            episode_steps = 0
            while episode_steps < CRAFTER_HORIZON:
                image = np.asarray(observation, dtype=np.uint8)
                complexity, previous_sample = _crafter_complexity(image, previous_sample)
                response = worker.act(image.tolist())
                action = _action_value(response, CRAFTER_ACTIONS)
                mass, memory = _structure_mass(response["structure"])
                cpu_samples.append(float(response.get("cpu_seconds", 0.0)))
                state_bytes.append(memory)
                observation, _reward, done, info = env.step(action)
                names = {name for name, count in info["achievements"].items() if count > 0}
                achievements.update(names)
                episode_achievements.update(names)
                masses.append(mass)
                complexities.append(complexity)
                episode_steps += 1
                if done:
                    break
            episode_runs.append({"survival_steps": episode_steps,
                                 "achievement_count": len(episode_achievements),
                                 "achievement_fraction": len(episode_achievements) / 22.0})
        worker_info = worker.finish()
    except BaseException:
        worker.stop()
        raise
    structure, rho, direction = _game_structure_score(masses, complexities)
    observable_structure_score = structure
    structure_state_score = _probe_structure_state(principle_path, 4, seed, deadline, params_override)
    structure *= structure_state_score
    cpu = sum(cpu_samples)
    rss_mb = worker_info.get("peak_rss_kib", 0) / 1024.0
    state_mb = (sum(state_bytes) / max(1, len(state_bytes))) / (1024 * 1024)
    return {
        "seed": int(seed), "survival_steps": _mean(episode_runs, "survival_steps"),
        "achievements": sorted(achievements), "achievement_count": len(achievements),
        "structure_score": structure, "observable_structure_score": observable_structure_score,
        "structure_state_score": structure_state_score,
        "structure_spearman": rho, "structure_direction_fraction": direction,
        "mean_observation_complexity": sum(complexities) / max(1, len(complexities)),
        "cost_score": _cost_score(cpu, sum(run["survival_steps"] for run in episode_runs), rss_mb, state_mb),
        "resources": {"agent_cpu_seconds": cpu, "agent_cpu_ms_per_step": cpu * 1000 / max(1, sum(run["survival_steps"] for run in episode_runs)),
                      "worker_process_cpu_seconds": worker_info.get("process_cpu_seconds"),
                      "worker_peak_rss_mb": rss_mb, "reported_state_mb_mean": state_mb},
        "transitions": sum(run["survival_steps"] for run in episode_runs),
        **_control_learning(episode_runs[:1], episode_runs[-1:]),
        "episodes": episode_runs,
    }


def _crafter_score_percent(rates):
    if not rates:
        return 0.0
    return math.expm1(sum(math.log1p(value) for value in rates.values()) / len(rates))


def _score_level_runs(level, runs):
    if level in (1, 2):
        return _score_runs(runs)
    if level == 3:
        metrics = {key: _mean(runs, key) for key in LEVEL_WEIGHTS[level]}
        metrics.update({key: _mean(runs, key) for key in
                        ("learning_improvement", "learning_pairs_improved", "learning_pairs")})
        metrics.update({"mean_survival_steps": _mean(runs, "survival_steps"),
                        "mean_apples_eaten": _mean(runs, "apples_eaten"),
                        "mean_board_coverage": _mean(runs, "board_coverage"),
                        "mean_behavior_diversity": _mean(runs, "behavior_diversity")})
    else:
        metrics = {key: _mean(runs, key) for key in ("structure_score", "cost_score")}
        metrics.update({key: _mean(runs, key) for key in
                        ("learning_improvement", "learning_pairs_improved", "learning_pairs")})
        all_names = None
        try:
            import crafter
            all_names = list(crafter.constants.achievements)
        except Exception:
            all_names = sorted({name for run in runs for name in run["achievements"]})
        rates = {name: 100.0 * sum(name in run["achievements"] for run in runs) / len(runs)
                 for name in all_names}
        task_percent = _crafter_score_percent(rates)
        metrics["crafter_score_percent"] = task_percent
        metrics["achievement_success_rate_percent"] = rates
        metrics["crafter_task_score"] = max(0.0, min(1.0, task_percent / 100.0))
        metrics["mean_survival_steps"] = _mean(runs, "survival_steps")
        metrics["mean_achievements"] = _mean(runs, "achievement_count")
    metrics["learning_passed"] = (
        metrics["learning_improvement"] >= LEARNING_MIN_IMPROVEMENT
        and metrics["learning_pairs_improved"] >= math.ceil(
            metrics["learning_pairs"] * LEARNING_MIN_PAIRS_FRACTION))
    weighted = sum(LEVEL_WEIGHTS[level][key] * metrics[key] for key in LEVEL_WEIGHTS[level])
    return metrics, 100.0 * weighted


def _evaluate_level(level, principle_path, params, deadline):
    seeds = SEEDS if level in (1, 2) else SNAKE_SEEDS if level == 3 else CRAFTER_SEEDS

    def run(seed, override=None):
        if level == 1:
            return _run_seed(principle_path, seed, deadline, override)
        if level == 2:
            return _run_complex_stream_seed(principle_path, seed, deadline, override)
        if level == 3:
            return _run_snake_seed(principle_path, seed, deadline, override)
        return _run_crafter_seed(principle_path, seed, deadline, override)

    runs = [run(seed) for seed in seeds]
    metrics, unpenalized = _score_level_runs(level, runs)
    robustness_runs, ratios = [], []
    for perturb_seed in ROBUSTNESS_SEEDS if params else ():
        perturbed_params, factors = _perturb_params(params, perturb_seed)
        perturbed_runs, error = [], None
        try:
            perturbed_runs = [run(seed, perturbed_params) for seed in seeds]
            _, perturbed_score = _score_level_runs(level, perturbed_runs)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            perturbed_score = 0.0
        ratio = (max(0.0, min(1.0, perturbed_score / unpenalized)) if unpenalized > 0
                 else (1.0 if perturbed_score <= 0 else 0.0))
        ratios.append(ratio)
        robustness_runs.append({"perturbation_seed": perturb_seed, "multipliers": factors,
                                "params": perturbed_params,
                                "score_without_elegance": perturbed_score,
                                "ratio_to_nominal": ratio, "runs": perturbed_runs,
                                "error": error})
    robustness = sum(ratios) / len(ratios) if ratios else 1.0
    return {"score_unpenalized": unpenalized, "score_components": metrics,
            "robustness": robustness, "robustness_runs": robustness_runs,
            "runs": runs, "seeds": list(seeds)}


def _perturb_params(params, seed):
    rng = random.Random(seed)
    changed = {}
    factors = {}
    low = math.log(0.5)
    high = math.log(2.0)
    for key, value in params.items():
        factor = math.exp(rng.uniform(low, high))
        factors[key] = factor
        if isinstance(value, int):
            changed[key] = max(1, int(math.floor(value * factor + 0.5)))
        else:
            changed[key] = value * factor
    return changed, factors


def judge(candidate_dir: Path, author: str, timeout_seconds=None, only_level=None):
    principle_path = (candidate_dir / "principle.py").resolve()
    if not principle_path.is_file():
        raise FileNotFoundError(f"candidate must contain {principle_path}")
    ast_counts, params = _read_principle(principle_path)
    started = time.monotonic()
    elegance, complexity_penalty = _elegance(ast_counts)
    world_agnostic = ast_counts["format_dependent_branches"] == 0
    levels = {}
    highest_passed = 0
    level_sequence = (only_level,) if only_level is not None else (1, 2, 3, 4)
    last_result = None
    stop_reason = "all_levels_passed"
    for level in level_sequence:
        limit = LEVEL_TIMEOUTS[level]
        level_timeout = min(limit, timeout_seconds) if timeout_seconds is not None else limit
        deadline = time.monotonic() + level_timeout
        level_started = time.monotonic()
        try:
            result = _evaluate_level(level, principle_path, params, deadline)
            error = None
        except Exception as exc:
            result = {"score_unpenalized": 0.0, "score_components": {},
                      "robustness": 0.0, "robustness_runs": [], "runs": [],
                      "seeds": list(SEEDS if level in (1, 2) else SNAKE_SEEDS if level == 3 else CRAFTER_SEEDS)}
            error = f"{type(exc).__name__}: {exc}"
        score = result["score_unpenalized"] * elegance * result["robustness"]
        baseline = LEVEL_BASELINES[level]
        threshold = baseline["score"] * 1.25
        passed = (score >= threshold and result["robustness"] >= 0.7
                  and result["score_components"].get("learning_passed", False)
                  and world_agnostic)
        stage = {
            **result, "score": score, "passed": passed,
            "best_baseline": baseline["candidate"], "best_baseline_score": baseline["score"],
            "pass_threshold_score": threshold, "pass_threshold_robustness": 0.7,
            "pass_learning": LEARNING_MIN_IMPROVEMENT,
            "world_agnostic": world_agnostic,
            "wall_seconds": time.monotonic() - level_started,
        }
        if error:
            stage["error"] = error
        levels[str(level)] = stage
        last_result = stage
        if only_level is not None:
            # Calibration is deliberately independent; it never claims a
            # ladder level without checking all preceding levels.
            highest_passed = 0
            stop_reason = "calibration_only"
            break
        if passed:
            highest_passed = level
        else:
            stop_reason = f"level_{level}_threshold_failed"
            break
    if last_result is None:
        raise RuntimeError("no level evaluated")
    if only_level is not None:
        reported_level = only_level
    else:
        reported_level = highest_passed
    reported = levels.get(str(reported_level)) if reported_level else None
    if reported is None:
        reported_score = 0.0
        reported_unpenalized = 0.0
        reported_components = {}
        reported_robustness = 0.0
        reported_runs = []
        reported_robustness_runs = []
    else:
        reported_score = reported["score"]
        reported_unpenalized = reported["score_unpenalized"]
        reported_components = reported["score_components"]
        reported_robustness = reported["robustness"]
        reported_runs = reported["runs"]
        reported_robustness_runs = reported["robustness_runs"]
    return {
        "candidate": candidate_dir.name,
        "author": author,
        "highest_passed_level": highest_passed,
        "stop_reason": stop_reason,
        "reported_score_level": reported_level,
        "score": reported_score,
        "score_unpenalized": reported_unpenalized,
        "score_components": reported_components,
        "robustness": reported_robustness,
        "world_agnostic": world_agnostic,
        "params": params,
        "robustness_runs": reported_robustness_runs,
        "levels": levels,
        "elegance": {
            **ast_counts,
            "penalty": complexity_penalty,
            "multiplier": elegance,
        },
        "principle_sha256": hashlib.sha256(principle_path.read_bytes()).hexdigest(),
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "protocol": {
            "seeds": list(SEEDS),
            "channels": CHANNELS,
            "phase_regimes": list(PHASE_REGIMES),
            "phase_complexity_edges": list(PHASE_COMPLEXITY),
            "phase_length_jitter_range": [PHASE_LENGTH_MIN, PHASE_LENGTH_MAX],
            "adaptation_window": ADAPT_WINDOW,
            "adaptation_threshold_active_target_brier": ADAPT_THRESHOLD,
            "learning_min_improvement": LEARNING_MIN_IMPROVEMENT,
            "learning_min_pairs_fraction": LEARNING_MIN_PAIRS_FRACTION,
            "control_episodes_per_seed": CONTROL_EPISODES,
            "robustness_seeds": list(ROBUSTNESS_SEEDS) if params else [],
            "level_timeouts_seconds": LEVEL_TIMEOUTS,
            "snake_seeds": list(SNAKE_SEEDS), "snake_horizon": SNAKE_HORIZON,
            "crafter_seeds": list(CRAFTER_SEEDS), "crafter_horizon": CRAFTER_HORIZON,
            "level_weights": LEVEL_WEIGHTS,
            "baseline_gates": LEVEL_BASELINES,
            "only_level": only_level,
        },
        "runs": reported_runs,
        "wall_seconds": time.monotonic() - started,
    }


def _append_leaderboard(row):
    path = ROOT / "leaderboard.jsonl"
    encoded = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
    try:
        import fcntl
        with path.open("a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except ImportError:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(encoded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="candidate directory containing principle.py")
    parser.add_argument("--author", default="unspecified")
    parser.add_argument("--timeout", type=int, default=None,
                        help="optional wall-clock limit per evaluated level (capped at that level's protocol limit)")
    parser.add_argument("--only-level", type=int, choices=(1, 2, 3, 4), default=None,
                        help="evaluate one level for baseline calibration; skips ladder progression")
    args = parser.parse_args()
    if args.candidate.is_absolute():
        candidate_dir = args.candidate
    else:
        candidate_dir = Path.cwd() / args.candidate
        if not candidate_dir.is_dir():
            candidate_dir = PROJECT_ROOT / args.candidate
    if args.timeout is not None and args.timeout <= 0:
        parser.error("--timeout must be positive")
    if not candidate_dir.is_dir():
        parser.error(f"candidate directory does not exist: {candidate_dir}")
    result = judge(candidate_dir, args.author, args.timeout, args.only_level)
    _append_leaderboard(result)
    print(json.dumps({
        "candidate": result["candidate"],
        "author": result["author"],
        "highest_passed_level": result["highest_passed_level"],
        "reported_score_level": result["reported_score_level"],
        "world_agnostic": result["world_agnostic"],
        "stop_reason": result["stop_reason"],
        "score": round(result["score"], 4),
        "robustness": round(result["robustness"], 4),
        "score_components": result["score_components"],
        "levels": {key: {"score": round(value["score"], 4), "robustness": round(value["robustness"], 4),
                         "passed": value["passed"], "best_baseline_score": value["best_baseline_score"],
                         "error": value.get("error")}
                   for key, value in result["levels"].items()},
        "elegance": result["elegance"],
        "principle_sha256": result["principle_sha256"],
        "leaderboard": str(ROOT / "leaderboard.jsonl"),
        "wall_seconds": round(result["wall_seconds"], 3),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
