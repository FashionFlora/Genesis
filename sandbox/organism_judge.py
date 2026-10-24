"""Continuous-life evaluation for the single organism-v4 protocol."""

import ast
import hashlib
import importlib.util
import json
import math
import time
from pathlib import Path

import torch

try:
    from worlds.organism import OrganismWorld
    from worlds.organism_config import WORLD_CONFIG
except ModuleNotFoundError:
    from sandbox.worlds.organism import OrganismWorld
    from sandbox.worlds.organism_config import WORLD_CONFIG


ROOT = Path(__file__).resolve().parent
SIZES = WORLD_CONFIG["brain_sizes"]
STEPS = WORLD_CONFIG["life_steps"]
PROTOCOL_VERSION = WORLD_CONFIG["version"]
CALIBRATION_UNITS = WORLD_CONFIG["calibration_units"]
SMOKE_STEPS = WORLD_CONFIG["scale_smoke_steps"]
MIN_WORLDS = 8
STRUCTURE_INTERVAL = 256


def load_brain(path, n_units, batch, device, seed, n_sensors):
    spec = importlib.util.spec_from_file_location("organism_candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    brain = module.OrganismBrain(n_units=n_units, n_sensors=n_sensors, n_motors=OrganismWorld.N_MOTORS,
                                 batch=batch, device=device, seed=seed)
    return module, brain


def _calibration_hooks(path):
    """Find reward-channel declarations without executing candidate code."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "observe_reward":
            found.append("observe_reward")
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "CALIBRATION_ONLY" for target in targets):
                found.append("CALIBRATION_ONLY")
        if isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name) and node.target.id == "CALIBRATION_ONLY":
            found.append("CALIBRATION_ONLY")
    return sorted(set(found))


def _record_disqualification(candidate, hooks):
    path = ROOT / "disqualified.tsv"
    line = f"{candidate}\torganism reward channel: {', '.join(hooks)}\n"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if not any(row.split("\t", 1)[0] == candidate for row in existing.splitlines() if row.strip()):
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def _independence_test(module, n_units, device, seed, n_sensors):
    """Perturb one row and require all other rows to remain identical."""
    width = 4

    def fresh():
        torch.manual_seed(seed)
        return module.OrganismBrain(n_units=n_units, n_sensors=n_sensors, n_motors=OrganismWorld.N_MOTORS,
                                    batch=width, device=device, seed=seed)

    left, right = fresh(), fresh()
    gen = torch.Generator(device=device).manual_seed(seed + 1)
    sequence = [torch.rand(width, n_sensors, device=device, generator=gen) for _ in range(70)]
    perturbed = [item.clone() for item in sequence]
    perturbed[1][0].add_(3.0)
    for step, (original, changed) in enumerate(zip(sequence, perturbed)):
        torch.manual_seed(seed + step + 2)
        first = left.act(original)
        torch.manual_seed(seed + step + 2)
        second = right.act(changed)
        if first.shape != (width, OrganismWorld.N_MOTORS) or second.shape != (width, OrganismWorld.N_MOTORS):
            return False
        if not torch.allclose(first[1:], second[1:], atol=1e-6, rtol=1e-6):
            return False
    return True


def load_independent_brain(path, n_units, batch, device, seed, n_sensors):
    module, brain = load_brain(path, n_units, batch, device, seed, n_sensors)
    if not _independence_test(module, n_units, device, seed + 7919, n_sensors):
        raise ValueError("candidate couples organisms across batch rows")
    return brain


def _baseline(mode, obs, world, state):
    """Run a built-in observation-only calibration controller."""
    batch = obs.shape[0]
    if mode == "random":
        generator = state["generator"]
        return torch.stack((torch.rand(batch, device=obs.device, generator=generator) * 2 - 1,
                            torch.rand(batch, device=obs.device, generator=generator),
                            torch.rand(batch, device=obs.device, generator=generator)), 1)
    channel_count = WORLD_CONFIG["color_count"]
    pixels = WORLD_CONFIG["pixels"]
    eye_rgb = obs[:, :pixels * channel_count].reshape(batch, pixels, channel_count)
    if mode == "braitenberg":
        red = eye_rgb[:, :, 0]
        turn = (red * torch.sin(world.angles)).sum(1) * 2
        return torch.stack((turn.tanh(), torch.full_like(turn, .7), (red.max(1).values > .5).float()), 1)
    if mode not in ("delta", "control"):
        raise ValueError(f"unknown baseline: {mode}")
    if "weights" not in state:
        state["weights"] = torch.zeros(batch, channel_count, device=obs.device)
        state["previous_energy"] = world.energy.clone()
        state["previous_color"] = torch.zeros(batch, dtype=torch.long, device=obs.device)
        state["previous_bite"] = torch.zeros(batch, dtype=torch.bool, device=obs.device)
        state["steps"] = 0
    energy_delta = (world.energy - state["previous_energy"]) * state["previous_bite"]
    no_food_drop = (world.energy - state["previous_energy"] < -0.003) & ~state["previous_bite"]
    state["weights"] = torch.where(no_food_drop[:, None], state["weights"] * 0.25, state["weights"])
    if mode == "control":
        low_energy = world.energy < WORLD_CONFIG["learning_reset_energy"]
        state["weights"] = torch.where(low_energy[:, None], state["weights"] * 0.05, state["weights"])
    state["weights"].scatter_add_(1, state["previous_color"][:, None], energy_delta.clamp(-.05, .2)[:, None])
    state["previous_energy"] = world.energy.clone()
    evidence = eye_rgb.sum(1)
    weights = state["weights"]
    confidence = (weights.abs().sum(1) > .001).float()[:, None]
    learning_rate = .80 if mode == "delta" else 1.20
    if mode == "control" and state["steps"] < channel_count * 64:
        color = torch.full((batch,), (state["steps"] // 64) % channel_count,
                           dtype=torch.long, device=obs.device)
    else:
        color = (learning_rate * weights + .25 * (1 - confidence) * evidence).argmax(1)
    selected = eye_rgb.gather(2, color[:, None, None].expand(-1, pixels, 1))[:, :, 0]
    state["previous_color"] = color
    state["steps"] += 1
    turn = torch.atan2((selected * torch.sin(world.angles)[None]).sum(1),
                       (selected * torch.cos(world.angles)[None]).sum(1)) / math.pi
    return torch.stack((turn, torch.full_like(turn, .72), (selected.max(1).values > .08).float()), 1)


def _routine_rows(world, action_counts, position_counts, high_new, high_steps,
                  early_sum, early_n, late_sum, late_n):
    """Summarize behavior without contributing to advancement or score."""
    def entropy(counts):
        total = counts.sum(-1, keepdim=True)
        prob = counts / total.clamp_min(1)
        return -(prob * prob.clamp_min(1e-12).log()).sum(-1)

    action_window_entropy = entropy(action_counts)
    position_window_entropy = entropy(position_counts)
    early_mean = early_sum / early_n.clamp_min(1)[:, :, None]
    late_mean = late_sum / late_n.clamp_min(1)[:, :, None]
    change = torch.linalg.vector_norm(late_mean - early_mean, dim=2)
    rows = []
    for index in range(world.batch):
        action_windows = action_window_entropy[index].tolist()
        position_windows = position_window_entropy[index].tolist()
        action_mean = [sum(values) / len(values) for values in action_windows if values]
        position_mean = [sum(values) / len(values) for values in position_windows if values]
        rows.append({
            "action_entropy": action_mean,
            "position_entropy": position_mean,
            "action_entropy_windows": action_windows,
            "position_entropy_windows": position_windows,
            "high_energy_new_place_rate": (high_new[index] / high_steps[index].clamp_min(1)).tolist(),
            "post_mastery_action_change": change[index].tolist(),
        })
    return rows


def _structure_number(value, batch):
    """Return one observable structure value, averaging explicit batch values."""
    if value is None:
        return None
    try:
        tensor = torch.as_tensor(value).detach().float().cpu()
    except (TypeError, ValueError, RuntimeError):
        return None
    if not tensor.numel():
        return None
    if tensor.ndim and tensor.shape[0] == batch and batch > 1:
        tensor = tensor.reshape(batch, -1).mean(dim=1)
    return float(tensor.mean().item())


def _structure_max(value):
    if value is None:
        return None
    try:
        tensor = torch.as_tensor(value).detach().float().cpu()
    except (TypeError, ValueError, RuntimeError):
        return None
    return float(tensor.max().item()) if tensor.numel() else None


def _structure_metrics(value, batch):
    """Normalize the organism structure contract to units/connections."""
    if isinstance(value, dict):
        units = value.get("units")
        connections = value.get("connections")
        if units is None:
            units = value.get("structure", value.get("mass", value.get("complexity")))
        return {"units": _structure_number(units, batch),
                "connections": _structure_number(connections, batch),
                "_units_max": _structure_max(units)}
    if isinstance(value, (tuple, list)) and value and all(isinstance(item, dict) for item in value):
        per_organism = [_structure_metrics(item, 1) for item in value]
        averaged = {key: (sum(item[key] for item in per_organism if item[key] is not None) /
                          len([item for item in per_organism if item[key] is not None])
                          if any(item[key] is not None for item in per_organism) else None)
                    for key in ("units", "connections")}
        averaged["_units_max"] = max((item["_units_max"] for item in per_organism
                                       if item["_units_max"] is not None), default=None)
        return averaged
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return {"units": _structure_number(value[0], batch),
                "connections": _structure_number(value[1], batch),
                "_units_max": _structure_max(value[0])}
    return {"units": _structure_number(value, batch), "connections": None,
            "_units_max": _structure_max(value)}


def _capture_structure(growth, brain, batch, step, n_units):
    structure = getattr(brain, "structure", None)
    if not callable(structure):
        return
    try:
        metrics = _structure_metrics(structure(), batch)
    except Exception as exc:  # structure is observational and cannot affect the score
        growth["errors"].append({"step": step, "error": f"{type(exc).__name__}: {exc}"})
        return
    if metrics["units"] is None and metrics["connections"] is None:
        growth["errors"].append({"step": step, "error": "structure() returned no numeric units/connections"})
        return
    units_max = metrics.pop("_units_max", metrics["units"])
    point = {"step": int(step), **metrics}
    if n_units is not None and units_max is not None and units_max > n_units:
        point["limit_violation"] = True
        growth["limit_violations"].append({"step": int(step), "units": units_max,
                                            "n_units": int(n_units)})
    growth["curve"].append(point)


def _finish_growth(growth, n_units):
    curve = growth["curve"]
    growth["available"] = bool(curve)
    if not curve:
        growth.update({"initial": None, "final": None, "maximum": None,
                       "ratio_to_n_units": None,
                       "units_ratio_to_n_units": {"initial": None, "final": None, "maximum": None},
                       "limit_exceeded": bool(growth["limit_violations"])})
        return growth
    units = [point["units"] for point in curve if point["units"] is not None]
    connections = [point["connections"] for point in curve if point["connections"] is not None]
    growth["initial"] = curve[0]
    growth["final"] = curve[-1]
    growth["maximum"] = {
        "units": max(units) if units else None,
        "connections": max(connections) if connections else None,
    }
    max_units = growth["maximum"]["units"]
    growth["ratio_to_n_units"] = (max_units / n_units
                                   if max_units is not None and n_units else None)
    growth["units_ratio_to_n_units"] = {
        "initial": (growth["initial"]["units"] / n_units
                    if growth["initial"]["units"] is not None and n_units else None),
        "final": (growth["final"]["units"] / n_units
                  if growth["final"]["units"] is not None and n_units else None),
        "maximum": growth["ratio_to_n_units"],
    }
    growth["limit_exceeded"] = bool(growth["limit_violations"])
    return growth


def _new_growth(n_units, interval=STRUCTURE_INTERVAL):
    return {"interval": int(interval), "n_units": n_units, "curve": [],
            "errors": [], "limit_violations": [], "available": False}


def run_life(brain, batch, device, seed, interoception=True, baseline=None, steps=STEPS,
             n_units=None, structure_interval=STRUCTURE_INTERVAL):
    world = OrganismWorld(batch, device, seed, interoception=interoception)
    baseline_state = {"generator": torch.Generator(device=device).manual_seed(seed + 104729)}
    growth = _new_growth(n_units, structure_interval)
    if brain is not None:
        _capture_structure(growth, brain, batch, 0, n_units)
    levels, alive, energy, patch, escapes, ticks = [], [], [], [], [], []
    post_flip_food = torch.zeros(batch, device=device)
    reversal_latency = torch.full((batch,), float(steps), device=device)
    reversal_seen = torch.zeros(batch, dtype=torch.bool, device=device)
    rooms = world.ROOMS
    action_bins = WORLD_CONFIG["routine_action_bins"]
    position_bins = WORLD_CONFIG["routine_position_grid"] ** 2
    windows = (steps + WORLD_CONFIG["routine_window_steps"] - 1) // WORLD_CONFIG["routine_window_steps"]
    action_counts = torch.zeros(batch, rooms, windows, action_bins, device=device)
    position_counts = torch.zeros(batch, rooms, windows, position_bins, device=device)
    seen_positions = torch.zeros(batch, rooms, position_bins, dtype=torch.bool, device=device)
    high_new = torch.zeros(batch, rooms, device=device)
    high_steps = torch.zeros(batch, rooms, device=device)
    early_sum = torch.zeros(batch, rooms, OrganismWorld.N_MOTORS, device=device)
    late_sum = torch.zeros(batch, rooms, OrganismWorld.N_MOTORS, device=device)
    early_n = torch.zeros(batch, rooms, device=device)
    late_n = torch.zeros(batch, rooms, device=device)
    completed_steps = 0
    for t in range(steps):
        obs = world.observe()
        out = _baseline(baseline, obs, world, baseline_state) if baseline else brain.act(obs)
        out = torch.as_tensor(out, device=device, dtype=torch.float32)
        if out.shape != (batch, OrganismWorld.N_MOTORS):
            raise ValueError(f"act must return {(batch, OrganismWorld.N_MOTORS)}, got {tuple(out.shape)}")

        room = world.room
        turn_bin = ((out[:, 0].clamp(-1, 1) + 1) * 1.5).long().clamp(0, 2)
        speed_bin = (out[:, 1] > 0).long()
        bite_bin = (out[:, 2] > 0).long()
        code = turn_bin * 4 + speed_bin * 2 + bite_bin
        window = t // WORLD_CONFIG["routine_window_steps"]
        action_index = (room * windows * action_bins + window * action_bins + code)[:, None]
        action_counts.view(batch, -1).scatter_add_(1, action_index,
                                                     torch.ones(batch, 1, device=device))
        side = world._side()
        grid = WORLD_CONFIG["routine_position_grid"]
        xy = ((world.pos / side[:, None] + 0.5) * grid).long().clamp(0, grid - 1)
        position = xy[:, 0] * grid + xy[:, 1]
        position_index = (room * windows * position_bins + window * position_bins + position)[:, None]
        position_counts.view(batch, -1).scatter_add_(1, position_index,
                                                      torch.ones(batch, 1, device=device))
        was_seen = seen_positions[torch.arange(batch, device=device), room, position]
        high = world.energy > WORLD_CONFIG["high_energy_threshold"]
        high_steps[torch.arange(batch, device=device), room] += high
        high_new[torch.arange(batch, device=device), room] += high & ~was_seen
        seen_positions[torch.arange(batch, device=device), room, position] = True
        early = world.room_age < WORLD_CONFIG["routine_window_steps"]
        early_sum[torch.arange(batch, device=device), room] += out * early[:, None]
        early_n[torch.arange(batch, device=device), room] += early
        late = ~early
        late_sum[torch.arange(batch, device=device), room] += out * late[:, None]
        late_n[torch.arange(batch, device=device), room] += late

        gain = world.step(out)
        completed_steps = t + 1
        if brain is not None and completed_steps % structure_interval == 0:
            _capture_structure(growth, brain, batch, completed_steps, n_units)
        if baseline:
            baseline_state["previous_bite"] = out[:, 2] > 0
        if t >= WORLD_CONFIG["reversal_times"][0]:
            post_flip_food += gain.float()
            reached = (post_flip_food >= WORLD_CONFIG["reversal_food_target"]) & ~reversal_seen
            reversal_latency = torch.where(reached, torch.full_like(reversal_latency, t - WORLD_CONFIG["reversal_times"][0]), reversal_latency)
            reversal_seen |= reached
        if t % WORLD_CONFIG["routine_window_steps"] == WORLD_CONFIG["routine_window_steps"] - 1:
            ticks.append(t)
            levels.append(world.room.float().mean().item())
            alive.append(world.alive.float().mean().item())
            energy.append(world.energy.mean().item())
            patch.append(world.visits.float().mean().item())
            escapes.append(world.escape_events.float().mean().item())
            if not bool(world.alive.any()):
                break
    if brain is not None and completed_steps and (not growth["curve"] or
                                                  growth["curve"][-1]["step"] != completed_steps):
        _capture_structure(growth, brain, batch, completed_steps, n_units)
    _finish_growth(growth, n_units)
    samples = []
    routine = _routine_rows(world, action_counts, position_counts, high_new, high_steps,
                            early_sum, early_n, late_sum, late_n)
    for index in range(batch):
        samples.append({
            "rooms_reached": float(world.room[index]),
            "room_reach_fraction": [float(world.room[index] >= room) for room in range(world.ROOMS)],
            "room_time": [float(world.room_time[index, room]) for room in range(world.ROOMS)],
            "survival": float(world.alive[index]),
            "mean_age": float(world.age[index]),
            "reversal_latency": float(reversal_latency[index]),
            "place_memory": float(world.patch_seen[index].sum()),
            "escape_events": float(world.escape_events[index]),
            "foraging_between_patches": float(world.patch_transitions[index]),
            "mean_energy": float(world.energy[index]),
            "routine": routine[index],
        })
    return {"samples": samples, "trajectory": {"steps": ticks, "rooms": levels,
            "survival": alive, "energy": energy, "foraging": patch, "escapes": escapes},
            "growth": growth}


def _ci(values):
    if not values:
        return {"mean": 0.0, "ci95": [0.0, 0.0]}
    mean = sum(values) / len(values)
    sem = (sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1) / len(values)) ** 0.5
    return {"mean": mean, "ci95": [mean - 1.96 * sem, mean + 1.96 * sem]}


def _growth_summary(rows, n_units):
    curves = [row.get("growth", {}).get("curve", []) for row in rows]
    points = []
    for step in sorted({point["step"] for curve in curves for point in curve}):
        at_step = [point for curve in curves for point in curve if point["step"] == step]
        point = {"step": step}
        for key in ("units", "connections"):
            values = [item[key] for item in at_step if item.get(key) is not None]
            point[key] = sum(values) / len(values) if values else None
        points.append(point)
    growth = _new_growth(n_units)
    growth["curve"] = points
    growth["errors"] = [error for row in rows for error in row.get("growth", {}).get("errors", [])]
    growth["limit_violations"] = [violation for row in rows
                                   for violation in row.get("growth", {}).get("limit_violations", [])]
    return _finish_growth(growth, n_units)


def _summary(rows, n_units=None):
    samples = [sample for row in rows for sample in row["samples"]]
    result = {key: _ci([sample[key] for sample in samples]) for key in
              ("rooms_reached", "survival", "mean_age", "reversal_latency", "place_memory",
               "escape_events", "foraging_between_patches", "mean_energy")}
    result["room_reach_fraction"] = []
    for room in range(OrganismWorld.ROOMS):
        values = [sample["room_reach_fraction"][room] for sample in samples]
        n, p, z = len(values), sum(values) / len(values), 1.96
        denominator = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denominator
        half = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / denominator
        result["room_reach_fraction"].append({"mean": p, "ci95": [center - half, center + half]})
    result["room_time"] = []
    for room in range(OrganismWorld.ROOMS):
        values = [sample["room_time"][room] for sample in samples if sample["room_time"][room] >= 0]
        result["room_time"].append({"mean": sum(values) / len(values) if values else STEPS,
                                     "ci95": _ci(values)["ci95"] if values else [STEPS, STEPS], "n": len(values)})
    result["routine"] = []
    for room in range(OrganismWorld.ROOMS):
        action_windows = []
        position_windows = []
        for sample in samples:
            action_windows.extend(sample["routine"]["action_entropy_windows"][room])
            position_windows.extend(sample["routine"]["position_entropy_windows"][room])
        result["routine"].append({
            "action_entropy": _ci([sample["routine"]["action_entropy"][room] for sample in samples]),
            "position_entropy": _ci([sample["routine"]["position_entropy"][room] for sample in samples]),
            "action_entropy_windows": _ci(action_windows),
            "position_entropy_windows": _ci(position_windows),
            "high_energy_new_place_rate": _ci([sample["routine"]["high_energy_new_place_rate"][room] for sample in samples]),
            "post_mastery_action_change": _ci([sample["routine"]["post_mastery_action_change"][room] for sample in samples]),
        })
    result["growth"] = _growth_summary(rows, n_units)
    return result


def _smoke_brain(path, units, device, seed, n_sensors, baseline):
    try:
        brain = None if baseline else load_brain(path, units, 1, device, seed, n_sensors)[1]
        life = run_life(brain, 1, device, seed + 17, n_sensors > OrganismWorld.EYE_SENSORS,
                         baseline, SMOKE_STEPS, n_units=units)
        return {"units": units, "steps": SMOKE_STEPS, "ok": True, "growth": life["growth"]}
    except Exception as exc:
        return {"units": units, "steps": SMOKE_STEPS, "ok": False,
                "error": f"{type(exc).__name__}: {exc}"}


def judge(candidate_dir, author="unspecified", device=None, seeds=MIN_WORLDS,
          baseline_mode=None, no_interoception=False):
    path = Path(candidate_dir) / "principle_organism.py"
    if not path.is_file():
        raise FileNotFoundError(path)
    if seeds < MIN_WORLDS:
        raise ValueError(f"organism calibration requires at least {MIN_WORLDS} worlds")
    hooks = _calibration_hooks(path) if baseline_mode is None else []
    if hooks:
        _record_disqualification(path.parent.name, hooks)
        return {"track": "organism", "candidate": path.parent.name, "author": author,
                "sizes": [], "score": 0.0, "wall_seconds": 0.0,
                "device": str(device or "cpu"), "interoception": not no_interoception,
                "principle_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "disqualified": hooks, "growth": _new_growth(CALIBRATION_UNITS),
                "protocol": {"version": PROTOCOL_VERSION}}
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    started = time.perf_counter()
    n_sensors = OrganismWorld.N_SENSORS if not no_interoception else OrganismWorld.N_SENSORS - 1
    rows = []
    tick = time.perf_counter()
    for seed in range(seeds):
        brain = None
        if baseline_mode is None:
            try:
                brain = load_independent_brain(path, CALIBRATION_UNITS, WORLD_CONFIG["batch_size"], device, seed + 1729, n_sensors)
            except ValueError as exc:
                reason = str(exc)
                _record_disqualification(path.parent.name, [reason])
                return {"track": "organism", "candidate": path.parent.name, "author": author,
                        "sizes": [], "score": 0.0, "wall_seconds": time.perf_counter() - started,
                        "device": str(device), "disqualified": [reason],
                        "growth": _new_growth(CALIBRATION_UNITS),
                        "protocol": {"version": PROTOCOL_VERSION}}
        rows.append(run_life(brain, WORLD_CONFIG["batch_size"], device, seed * 101 + 7,
                             not no_interoception, baseline_mode,
                             n_units=CALIBRATION_UNITS))
    summary = _summary(rows, CALIBRATION_UNITS)
    growth = summary["growth"]
    sizes = [{"units": CALIBRATION_UNITS, "batch": WORLD_CONFIG["batch_size"],
              "summary": summary, "score": summary["rooms_reached"]["mean"],
              "growth": growth,
              "worlds": seeds * WORLD_CONFIG["batch_size"], "trajectories": rows if seeds <= 2 else [],
              "wall_seconds": time.perf_counter() - tick}]
    for units in SIZES:
        if units != CALIBRATION_UNITS:
            sizes.append(_smoke_brain(path, units, device, units + 31, n_sensors, baseline_mode))
    result = {
        "track": "organism_calibration" if baseline_mode else "organism",
        "candidate": path.parent.name,
        "author": author,
        "sizes": sizes,
        "score": summary["rooms_reached"]["mean"],
        "growth": growth,
        "wall_seconds": time.perf_counter() - started,
        "device": str(device),
        "interoception": not no_interoception,
        "baseline": baseline_mode,
        "principle_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "protocol": {"version": PROTOCOL_VERSION, "worlds_per_calibration": seeds * WORLD_CONFIG["batch_size"],
                      "batches": seeds, "batch_size": WORLD_CONFIG["batch_size"], "steps": STEPS,
                      "calibration_units": CALIBRATION_UNITS, "scale_smoke_steps": SMOKE_STEPS,
                      "sizes": list(SIZES), "rooms": OrganismWorld.ROOMS, "sensors": n_sensors,
                      "pixels": OrganismWorld.PIXELS, "max_food": OrganismWorld.MAX_PATCHES},
    }
    return result


def append_result(result):
    target = ROOT / ("organism_calibration.jsonl" if result["track"] == "organism_calibration" else "leaderboard.jsonl")
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, sort_keys=True) + "\n")
