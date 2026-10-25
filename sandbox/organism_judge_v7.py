"""Continuous-life evaluation for the versioned organism-v7 ladder."""

import ast
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager, nullcontext
import fcntl
import hashlib
import importlib.util
import inspect
import json
import math
import multiprocessing
import time
from pathlib import Path

import torch

try:
    from worlds.organism_v7 import OrganismWorld, BIOLOGICAL_LADDER, V7_CONFIG
except ModuleNotFoundError:
    from sandbox.worlds.organism_v7 import OrganismWorld, BIOLOGICAL_LADDER, V7_CONFIG

WORLD_CONFIG = V7_CONFIG


ROOT = Path(__file__).resolve().parent
SIZES = WORLD_CONFIG["brain_sizes"]
STEPS = WORLD_CONFIG["life_steps"]
PROTOCOL_VERSION = "organism-v7p"
QUICK_STEPS = 12000
CALIBRATION_UNITS = WORLD_CONFIG["calibration_units"]
SMOKE_STEPS = WORLD_CONFIG["scale_smoke_steps"]
HIDDEN_STEPS = min(STEPS, 12000)
MIN_WORLDS = 1  # liczba partii; 1 partia = 1024 światy
STRUCTURE_INTERVAL = 256
GPU_SLOTS = 6


def _world_permutations(batch, device, seed, include_energy=True):
    """Create fixed, private channel permutations for one batched life."""
    generator = torch.Generator(device=device).manual_seed(int(seed) + 271828)
    pixels = torch.stack([torch.randperm(OrganismWorld.PIXELS, device=device, generator=generator)
                          for _ in range(batch)])
    colors = torch.stack([torch.randperm(WORLD_CONFIG["color_count"], device=device, generator=generator)
                          for _ in range(batch)])
    motors = torch.stack([torch.randperm(3, device=device, generator=generator)
                          for _ in range(batch)])
    energy_position = None
    if include_energy:
        energy_position = torch.randint(0, OrganismWorld.EYE_SENSORS + 1,
                                        (batch,), device=device, generator=generator)
    return {"pixels": pixels, "colors": colors, "motors": motors,
            "energy_position": energy_position}


def _permute_observation(observation, permutations):
    """Rename eye pixels/colors and hide the interoceptive slot position."""
    if permutations is None:
        return observation
    batch = observation.shape[0]
    eye_size = OrganismWorld.EYE_SENSORS
    eye = observation[:, :eye_size].reshape(batch, OrganismWorld.PIXELS,
                                             WORLD_CONFIG["color_count"])
    eye = torch.gather(eye, 1, permutations["pixels"][:, :, None].expand(-1, -1, eye.shape[2]))
    eye = torch.gather(eye, 2, permutations["colors"][:, None, :].expand(-1, eye.shape[1], -1))
    eye = eye.flatten(1)
    if observation.shape[1] == eye_size:
        return eye
    energy_position = permutations["energy_position"]
    source = torch.arange(observation.shape[1], device=observation.device)[None, :].expand(batch, -1)
    source = torch.where(source == energy_position[:, None],
                         torch.full_like(source, eye_size),
                         source - (source > energy_position[:, None]).long())
    return torch.cat((eye, observation[:, eye_size:eye_size + 1]), 1).gather(1, source)


def _permute_motors(motors, permutations):
    """Map candidate turn/drive/bite channels back to world semantics."""
    if permutations is None:
        return motors
    core = motors[:, :3].gather(1, permutations["motors"])
    return torch.cat((core, motors[:, 3:]), 1)


@contextmanager
def _gpu_slot():
    """Allow a bounded number of concurrent organism runs."""
    import time

    handles = [(ROOT / f".gpu.slot{index}.lock").open("a+") for index in range(GPU_SLOTS)]
    acquired = None
    try:
        while True:
            for handle in handles:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = handle
                    break
                except BlockingIOError:
                    continue
            if acquired is not None:
                break
            time.sleep(0.1)
        yield
    finally:
        for handle in handles:
            if handle is acquired:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()


def load_brain(path, n_units, batch, device, seed, n_sensors, params=None):
    spec = importlib.util.spec_from_file_location("organism_candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    values = getattr(module, "PARAMS", None) if params is None else params
    arguments = {"n_units": n_units, "n_sensors": n_sensors,
                 "n_motors": OrganismWorld.N_MOTORS, "batch": batch,
                 "device": device, "seed": seed}
    signature = inspect.signature(module.OrganismBrain)
    if "params" in signature.parameters or any(item.kind == item.VAR_KEYWORD
                                                for item in signature.parameters.values()):
        arguments["params"] = values
    brain = module.OrganismBrain(**arguments)
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


def _independence_test(module, n_units, device, seed, n_sensors, params=None):
    """Perturb one row and require all other rows to remain identical."""
    width = 4

    def fresh():
        torch.manual_seed(seed)
        arguments = {"n_units": n_units, "n_sensors": n_sensors,
                     "n_motors": OrganismWorld.N_MOTORS, "batch": width,
                     "device": device, "seed": seed}
        signature = inspect.signature(module.OrganismBrain)
        if "params" in signature.parameters or any(item.kind == item.VAR_KEYWORD
                                                    for item in signature.parameters.values()):
            arguments["params"] = params
        return module.OrganismBrain(**arguments)

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
        if first.ndim != 2 or second.ndim != 2 or first.shape[0] != width or second.shape[0] != width:
            return False
        if first.shape[1] not in (3, OrganismWorld.N_MOTORS) or second.shape[1] not in (3, OrganismWorld.N_MOTORS):
            return False
        if not torch.allclose(first[1:], second[1:], atol=1e-6, rtol=1e-6):
            return False
    return True


def load_independent_brain(path, n_units, batch, device, seed, n_sensors, params=None):
    module, brain = load_brain(path, n_units, batch, device, seed, n_sensors, params)
    if not _independence_test(module, n_units, device, seed + 7919, n_sensors, params):
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
    if mode == "table":
        mode = "control"
    if mode == "body_growth":
        mode = "control"
    if mode == "growing":
        if "q" not in state:
            # Room 5 can emit shape ids 0..4.  Keep one slot per room so the
            # calibration learner cannot index past its shape memory.
            state["q"] = torch.full((batch, 3, world.ROOMS, 2), 0.5, device=obs.device)
            state["q_count"] = torch.zeros_like(state["q"])
            state["place_known"] = torch.zeros(batch, world.MAX_PATCHES, dtype=torch.bool, device=obs.device)
            state["place_shape"] = torch.zeros(batch, world.MAX_PATCHES, dtype=torch.long, device=obs.device)
            state["place_color"] = torch.zeros_like(state["place_shape"])
            state["place_position"] = torch.zeros(batch, world.MAX_PATCHES, 2, device=obs.device)
            state["place_value"] = torch.full((batch, world.MAX_PATCHES), 0.5, device=obs.device)
            state["learned_color"] = torch.full((batch, 2), -1, dtype=torch.long, device=obs.device)
            state["feedback_t"] = -1
            state["previous_context"] = world.room_context.clone()
            state["previous_room"] = world.room.clone()
            state["explore_step"] = torch.zeros(batch, dtype=torch.long, device=obs.device)
        if world.t > state["feedback_t"]:
            hit = world.last_bite & (world.last_bite_index >= 0)
            if hit.any():
                row = torch.arange(batch, device=obs.device)
                # last_bite_index is the first touched patch; last_patch is
                # the patch that actually supplied a positive reward.
                patch = torch.where(world.last_gain, world.last_patch,
                                    world.last_bite_index).clamp_min(0)
                color = world.patch_color[row, patch]
                shape = world.food_shape[row, patch]
                context = state["previous_context"]
                count = state["q_count"][row, color, shape, context]
                old = state["q"][row, color, shape, context]
                reward = world.last_gain.float()
                updated = (old * count + reward) / (count + 1)
                state["q"][row, color, shape, context] = torch.where(hit, updated, old)
                state["q_count"][row, color, shape, context] = count + hit.float()
                state["place_value"][row, patch] = torch.where(
                    hit, reward, state["place_value"][row, patch])
                state["learned_color"][row, context] = torch.where(
                    world.last_gain, color, state["learned_color"][row, context])
            state["feedback_t"] = world.t

        changed_room = world.room != state["previous_room"]
        if changed_room.any():
            state["q"][changed_room] = 0.5
            state["q_count"][changed_room] = 0
            state["place_known"][changed_room] = False
            state["learned_color"][changed_room] = -1
        state["previous_room"] = world.room.clone()

        visible = world.visible_mask
        state["place_known"] |= visible
        state["place_position"] = torch.where(visible[:, :, None], world.food, state["place_position"])
        state["place_shape"] = torch.where(visible, world.food_shape, state["place_shape"])
        state["place_color"] = torch.where(visible, world.patch_color, state["place_color"])
        row = torch.arange(batch, device=obs.device)[:, None]
        q = state["q"][row, state["place_color"], state["place_shape"], world.room_context[:, None]]
        seen = state["place_known"] & world._available_mask()
        value = torch.where(state["q_count"][row, state["place_color"], state["place_shape"],
                                               world.room_context[:, None]] > 0,
                            q, torch.full_like(q, 0.5))
        value = torch.where(seen, value, torch.full_like(value, -1))
        # Once a color has earned a positive reward in this context, commit to
        # that learned color. This prevents distance tie-breaking from biting
        # fresh, untested colors after the learner has identified the target.
        trusted = (state["q_count"][row, state["place_color"], state["place_shape"],
                                  world.room_context[:, None]] > 0) & (q >= 0.60)
        has_trusted = (trusted & seen).any(dim=1, keepdim=True)
        value = torch.where(has_trusted & ~trusted, torch.full_like(value, -1), value)
        locked_color = state["learned_color"].gather(1, world.room_context[:, None])
        has_locked = locked_color >= 0
        value = torch.where(has_locked & (state["place_color"] != locked_color),
                            torch.full_like(value, -1), value)
        distance = torch.linalg.vector_norm(state["place_position"] - world.pos[:, None, :], dim=2)
        value = value - distance * 0.025
        value = torch.where(state["place_shape"] == world.target_shape[:, None], value, value - 0.12)
        best_value, target = value.max(dim=1)
        has_target = best_value > -0.05
        target_position = state["place_position"][torch.arange(batch, device=obs.device), target]
        delta = target_position - world.pos
        bearing = torch.remainder(torch.atan2(delta[:, 1], delta[:, 0]) - world.heading + math.pi,
                                  2 * math.pi) - math.pi
        near = torch.linalg.vector_norm(delta, dim=1) < world.params["touch_radius"]
        explore_turn = torch.rand(batch, device=obs.device, generator=state["generator"]) * 0.7 - 0.35
        output = torch.stack((torch.where(has_target, (bearing / 0.42).clamp(-1, 1), explore_turn),
                              torch.where(has_target, torch.ones_like(bearing), torch.full_like(bearing, 0.7)),
                              (near & has_target).float()), dim=1)
        state["previous_context"] = world.room_context.clone()
        state["explore_step"] += 1
        return output
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
    growth["units_by_stage"] = []
    for stage, entry in enumerate(BIOLOGICAL_LADDER):
        stage_points = [point["units"] for point in curve
                        if point["units"] is not None and point.get("stage") is not None
                        and point["stage"] >= stage]
        growth["units_by_stage"].append({
            "stage": stage, "stage_name": entry["stage"],
            "observed_units_mean": (sum(stage_points) / len(stage_points) if stage_points else None),
            "capacity_metadata": entry["capacity"],
        })
    return growth


def _new_growth(n_units, interval=STRUCTURE_INTERVAL):
    return {"interval": int(interval), "n_units": n_units, "curve": [],
            "errors": [], "limit_violations": [], "available": False}


def run_life(brain, batch, device, seed, interoception=True, baseline=None, steps=STEPS,
             n_units=None, structure_interval=STRUCTURE_INTERVAL, world_params=None,
             permutation=False):
    params = dict(world_params or {})
    world = OrganismWorld(batch, device, seed, interoception=interoception, params=params)
    permutations = (_world_permutations(batch, device, seed, interoception)
                    if permutation else None)
    if baseline != "body_growth" and not callable(getattr(brain, "request_body", None)):
        # Legacy brains keep the v6 fixed body without a construction charge.
        world.body_pixels.fill_(WORLD_CONFIG["pixels"])
        world.body_motors.fill_(OrganismWorld.N_MOTORS)
    baseline_state = {"generator": torch.Generator(device=device).manual_seed(seed + 104729)}
    growth = _new_growth(n_units, structure_interval)
    if brain is not None:
        _capture_structure(growth, brain, batch, 0, n_units)
        if growth["curve"]:
            growth["curve"][-1]["stage"] = float(world.room.float().mean())
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
    body_curve = []
    for t in range(steps):
        obs = _permute_observation(world.observe(), permutations)
        request = getattr(brain, "request_body", None) if brain is not None else None
        if callable(request):
            desired = torch.as_tensor(request(obs), device=device)
            if desired.shape != (batch, 2):
                raise ValueError(f"request_body must return {(batch, 2)}, got {tuple(desired.shape)}")
            n_sensors, n_motors = world.grow_body(desired[:, 0], desired[:, 1])
            changed = getattr(brain, "body_changed", None)
            if callable(changed):
                changed(n_sensors, n_motors)
        elif baseline == "body_growth" and t == 256:
            world.grow_body(torch.full((batch,), OrganismWorld.PIXELS, device=device),
                            torch.full((batch,), OrganismWorld.N_MOTORS, device=device))
        if t % structure_interval == 0:
            body_curve.append({"step": t, "pixels": float(world.body_pixels.float().mean()),
                               "motors": float(world.body_motors.float().mean()),
                               "sensors": float((world.body_pixels.float() * 3 + int(interoception)).mean()),
                               "stage": float(world.room.float().mean()),
                               "energy_spent": float(world.body_energy_spent.mean()),
                               "yolk_remaining": float(getattr(world, "yolk", torch.zeros(batch, device=device)).mean())})
        out = _baseline(baseline, obs, world, baseline_state) if baseline else brain.act(obs)
        out = torch.as_tensor(out, device=device, dtype=torch.float32)
        if out.ndim != 2 or out.shape[0] != batch or out.shape[1] not in (3, OrganismWorld.N_MOTORS):
            raise ValueError(f"act must return [batch, 3] or [batch, {OrganismWorld.N_MOTORS}], got {tuple(out.shape)}")
        if out.shape[1] < OrganismWorld.N_MOTORS:
            out = torch.nn.functional.pad(out, (0, OrganismWorld.N_MOTORS - out.shape[1]))
        out = _permute_motors(out, permutations)

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
            if growth["curve"]:
                growth["curve"][-1]["stage"] = float(world.room.float().mean())
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
        if growth["curve"]:
            growth["curve"][-1]["stage"] = float(world.room.float().mean())
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
            "body_pixels": int(world.body_pixels[index]),
            "body_motors": int(world.body_motors[index]),
            "body_growth_events": int(world.body_growth_events[index]),
            "body_energy_spent": float(world.body_energy_spent[index]),
            "yolk_initial": float(getattr(world, "yolk_initial", 0.0)),
            "yolk_remaining": float(getattr(world, "yolk", torch.zeros(batch, device=device))[index]),
            "yolk_depleted_at": int(getattr(world, "yolk_depleted_at", torch.full((batch,), -1, device=device))[index]),
            "world_family": int(getattr(world, "world_family", torch.zeros(batch, dtype=torch.long, device=device))[index]),
            "stage_windows": [float(world.room[index] >= room) for room in range(world.ROOMS)],
            "task_events": [float(value) for value in getattr(
                world, "task_events", torch.zeros(batch, world.ROOMS, device=device))[index]],
            "task_progress": [float(value) for value in getattr(
                world, "task_progress", torch.zeros(batch, world.ROOMS, device=device))[index]],
            "routine": routine[index],
        })
    return {"samples": samples, "trajectory": {"steps": ticks, "rooms": levels,
            "survival": alive, "energy": energy, "foraging": patch, "escapes": escapes},
            "growth": growth, "body_growth": {"curve": body_curve},
            "permutation": {"enabled": bool(permutation),
                             "motor_channels": 3,
                             "energy_position_shuffled": bool(permutation and interoception)}}


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
        for key in ("units", "connections", "stage"):
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
               "escape_events", "foraging_between_patches", "mean_energy", "yolk_remaining",
               "yolk_depleted_at")}
    result["yolk_depleted_fraction"] = _ci([
        float(sample["yolk_depleted_at"] >= 0) for sample in samples])
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
    result["body_growth"] = {
        key: _ci([sample[key] for sample in samples])
        for key in ("body_pixels", "body_motors", "body_growth_events", "body_energy_spent")}
    result["development"] = {
        "stages": [entry["stage"] for entry in BIOLOGICAL_LADDER],
        "stage_windows": [_ci([sample["stage_windows"][room] for sample in samples])
                          for room in range(OrganismWorld.ROOMS)],
        "world_families": sorted({sample["world_family"] for sample in samples}),
        "task_events": [_ci([sample["task_events"][index] for sample in samples])
                        for index in range(6)],
        "task_progress": [_ci([sample["task_progress"][index] for sample in samples])
                          for index in range(6)],
    }
    trajectories = [row.get("trajectory", {}) for row in rows]
    steps = sorted({step for trajectory in trajectories for step in trajectory.get("steps", [])})
    result["development"]["life_windows"] = []
    for step in steps:
        points = []
        for trajectory in trajectories:
            if step in trajectory.get("steps", []):
                index = trajectory["steps"].index(step)
                points.append({key: trajectory[key][index] for key in ("rooms", "survival", "energy")})
        if points:
            result["development"]["life_windows"].append({
                "step": step,
                **{key: _ci([point[key] for point in points]) for key in ("rooms", "survival", "energy")}})
    body_curves = [row.get("body_growth", {}).get("curve", []) for row in rows]
    result["body_growth"]["curve"] = []
    for step in sorted({point["step"] for curve in body_curves for point in curve}):
        at_step = [point for curve in body_curves for point in curve if point["step"] == step]
        result["body_growth"]["curve"].append({
            "step": step,
            **{key: sum(point[key] for point in at_step) / len(at_step)
               for key in ("pixels", "motors", "sensors", "stage", "energy_spent", "yolk_remaining")}})
    result["room_names"] = [entry["stage"] for entry in BIOLOGICAL_LADDER]
    return result


def _param_variants(params):
    if not isinstance(params, dict):
        return []
    variants = []
    for factor in (0.7, 1.4):
        changed = {}
        for key, value in params.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                changed[key] = max(1, int(value * factor)) if isinstance(value, int) else value * factor
            else:
                changed[key] = value
        variants.append((factor, changed))
    return variants


def _calibration_checks(rows):
    """Protocol gates for the one-batch v7 calibration record."""
    early = all(rows[name]["room_reach_fraction"][1]["mean"] < 0.50
                for name in ("random", "braitenberg", "delta"))
    table = rows["table"]["room_reach_fraction"]
    growing = rows["growing"]["room_reach_fraction"]
    # The table must clear the two first assays with a positive CI above the
    # zero floor; absolute 50/25% cutoffs would conflate a short lower assay
    # with the intended later-stage stall.
    table_lower = all(
        table[room]["ci95"][0] > 0.0
        for room in (1, 2))
    stall = table[-1]["mean"] < 0.50
    separation = [
        growing[room]["ci95"][0] > table[room]["ci95"][1]
        for room in range(1, len(growing))]
    advanced_separation = any(separation[room - 1]
                              for room in range(2, len(separation)))
    growing_ahead = (rows["growing"]["rooms_reached"]["mean"] >
                     rows["table"]["rooms_reached"]["mean"])
    body_summary = rows["body_growth"]
    body = body_summary.get("body_growth", body_summary)
    body_ok = body.get("body_growth_events", {}).get("mean", 0.0) > 0
    yolk_spent = all(rows[name].get("yolk_depleted_fraction", {}).get("mean", 0.0) >= 0.5
                     for name in ("random", "table"))
    curves_decrease = all(
        all(summary["room_reach_fraction"][index]["mean"] >=
            summary["room_reach_fraction"][index + 1]["mean"]
            for index in range(len(summary["room_reach_fraction"]) - 1))
        for summary in rows.values())
    return {
        "early_controls_fail": early,
        "table_lower_stages": table_lower,
        "table_stalls": stall,
        "growing_exceeds_table_disjoint_ci": advanced_separation and growing_ahead,
        "growing_separation_by_room": separation,
        "curves_monotone_reported": curves_decrease,
        "body_growth_charged": body_ok,
        "random_and_table_outlive_yolk": yolk_spent,
        "passed": bool(early and table_lower and stall and advanced_separation
                        and growing_ahead and body_ok and yolk_spent and curves_decrease),
    }


def _smoke_brain(path, units, device, seed, n_sensors, baseline):
    try:
        brain = None if baseline else load_brain(path, units, 1, device, seed, n_sensors)[1]
        life = run_life(brain, 1, device, seed + 17, n_sensors > OrganismWorld.EYE_SENSORS,
                         baseline, SMOKE_STEPS, n_units=units)
        return {"units": units, "steps": SMOKE_STEPS, "ok": True, "growth": life["growth"]}
    except Exception as exc:
        return {"units": units, "steps": SMOKE_STEPS, "ok": False,
                "error": f"{type(exc).__name__}: {exc}"}


def _calibration_worker(candidate_dir, author, device, seeds, mode,
                        no_interoception, sizes, social_group_size, life_steps=STEPS):
    result = judge(candidate_dir, author, device, seeds, mode,
                   no_interoception, sizes, social_group_size, life_steps)
    return mode, result["sizes"][0]["summary"], result.get("permuted_summary")


def _preflight_all_rooms(device):
    """Exercise every room transition on a tiny batch before long calibration."""
    batch = 2
    world = OrganismWorld(batch=batch, device=device, seed=1207,
                          params={"yolk_energy": 0.01})
    transitions = []
    try:
        for room in range(world.ROOMS):
            world.room.fill_(room)
            world.t = 2111
            world.room_age.fill_(1000)
            world.flip_time.fill_(0)
            world.flip_bites.fill_(20)
            world.flip_correct_bites.fill_(20)
            world.energy_window.fill_(20)
            world.window_n.fill_(64)
            world.mastered_colors.zero_()
            world.mastered_colors[:, :2] = True
            world.body_pixels.fill_(world.PIXELS)
            world.body_motors.fill_(world.N_MOTORS)
            before_shape = tuple(world.task_events.shape)
            world.observe()
            world.step(torch.zeros(batch, 3, device=device))
            if tuple(world.task_events.shape) != before_shape:
                raise RuntimeError("task event shape changed during preflight")
            expected = room if room == world.ROOMS - 1 else room + 1
            if not bool((world.room == expected).all()):
                raise RuntimeError(f"forced transition {room}->{expected} failed")
            if not bool((world.room < world.ROOMS).all()):
                raise RuntimeError("room index exceeded ladder")
            transitions.append({"from": room, "to": expected})
    except Exception as exc:
        return {"passed": False, "error": f"{type(exc).__name__}: {exc}",
                "transitions": transitions}
    return {"passed": True, "batch": batch, "transitions": transitions}


def judge(candidate_dir, author="unspecified", device=None, seeds=MIN_WORLDS,
          baseline_mode=None, no_interoception=False, sizes=None, social_group_size=1,
          life_steps=STEPS, quick=False, permutation=True):
    path = Path(candidate_dir) / "principle_organism.py"
    if not path.is_file():
        raise FileNotFoundError(path)
    if seeds < MIN_WORLDS:
        raise ValueError(f"organism calibration requires at least {MIN_WORLDS} worlds")
    if quick:
        if life_steps == STEPS:
            life_steps = QUICK_STEPS
        elif life_steps != QUICK_STEPS:
            raise ValueError("quick organism mode uses exactly 12000 steps")
        if seeds != 1:
            raise ValueError("quick organism mode uses one batch of 1024 worlds")
    if life_steps < 1:
        raise ValueError("life_steps must be positive")
    if baseline_mode == "baseline_table":
        if life_steps != STEPS:
            raise ValueError("baseline_table requires the full default organism lifetime")
        started = time.perf_counter()
        modes = ("random", "braitenberg", "delta", "table", "growing", "body_growth")
        worker_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        preflight = _preflight_all_rooms(worker_device)
        if not preflight["passed"]:
            raise RuntimeError(f"v7 preflight failed: {preflight['error']}")
        rows = {}
        with ProcessPoolExecutor(max_workers=len(modes),
                                 mp_context=multiprocessing.get_context("spawn")) as pool:
            futures = [pool.submit(_calibration_worker, str(candidate_dir), author,
                                   worker_device, seeds, mode, no_interoception,
                                   sizes, social_group_size, life_steps)
                       for mode in modes]
            for future in futures:
                mode, summary, permuted_summary = future.result()
                rows[mode] = summary
                if permuted_summary is not None:
                    rows[mode]["permuted_summary"] = permuted_summary
        small = rows["table"]["room_reach_fraction"]
        growing = rows["growing"]["room_reach_fraction"]
        separation = []
        for room in range(1, OrganismWorld.ROOMS):
            lower = growing[room]["ci95"][0]
            upper = small[room]["ci95"][1]
            separation.append({"room": room + 1, "positive_lower": lower,
                               "negative_upper": upper, "disjoint": lower > upper})
        fractions = rows["growing"]["room_reach_fraction"]
        stage = max((index for index, item in enumerate(fractions) if item["mean"] >= 0.5), default=0)
        checks = _calibration_checks(rows)
        hidden_rows = [run_life(None, WORLD_CONFIG["batch_size"], worker_device, 500003,
                                not no_interoception, baseline="growing",
                                steps=HIDDEN_STEPS,
                                world_params={"hidden_world": True,
                                              "social_group_size": social_group_size})]
        hidden_summary = _summary(hidden_rows, CALIBRATION_UNITS)
        return {"track": "organism_calibration", "candidate": "organism-v7p-final",
                "author": author, "baseline": "baseline_table", "baseline_table": rows,
                "sizes": [], "score": rows["growing"]["rooms_reached"]["mean"],
                "achieved_stage": {**BIOLOGICAL_LADDER[stage],
                                   "world_fraction": fractions[stage]["mean"]},
                "new_room_ci_separation": separation,
                "preflight": preflight,
                "calibration_checks": checks,
                "calibration_passed": checks["passed"],
                "generalization": {"family": WORLD_CONFIG["hidden_world_family"],
                                   "steps": HIDDEN_STEPS, "summary": hidden_summary},
                "wall_seconds": time.perf_counter() - started,
                "device": str(worker_device),
                "interoception": not no_interoception,
                "principle_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "protocol": {"version": PROTOCOL_VERSION,
                             "worlds_per_calibration": seeds * WORLD_CONFIG["batch_size"],
                             "worlds_per_baseline": seeds * WORLD_CONFIG["batch_size"],
                             "batches": seeds, "batch_size": WORLD_CONFIG["batch_size"],
                             "steps": life_steps, "rooms": OrganismWorld.ROOMS,
                             "sensors": OrganismWorld.N_SENSORS - int(no_interoception),
                             "pixels": OrganismWorld.PIXELS, "max_food": OrganismWorld.MAX_PATCHES,
                             "yolk_energy": WORLD_CONFIG["yolk_energy"],
                             "world_families": WORLD_CONFIG["world_families"],
                             "hidden_world_family": WORLD_CONFIG["hidden_world_family"],
                             "ladder": list(BIOLOGICAL_LADDER)}}
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
    if str(device).startswith("cuda"):
        total = torch.cuda.get_device_properties(torch.device(device)).total_memory
        cuda_device = torch.device(device)
        cuda_index = cuda_device.index if cuda_device.index is not None else torch.cuda.current_device()
        torch.cuda.set_per_process_memory_fraction(min(1.0, 40 * 1024**3 / total), cuda_index)
    requested_sizes = sorted(set(int(size) for size in (sizes or (CALIBRATION_UNITS,))))
    if CALIBRATION_UNITS not in requested_sizes:
        requested_sizes.insert(0, CALIBRATION_UNITS)
    if any(size < 1 or size > 100000 for size in requested_sizes):
        raise ValueError("organism sizes must be between 1 and 100000 units")
    started = time.perf_counter()
    n_sensors = OrganismWorld.N_SENSORS if not no_interoception else OrganismWorld.N_SENSORS - 1
    results_by_size = {}
    units_to_run = [CALIBRATION_UNITS] if baseline_mode else requested_sizes
    for units in units_to_run:
        rows = []
        tick = time.perf_counter()
        try:
            with (_gpu_slot() if str(device).startswith("cuda") else nullcontext()):
                for seed in range(seeds):
                    brain = None
                    if baseline_mode is None:
                        try:
                            brain = load_independent_brain(path, units, WORLD_CONFIG["batch_size"], device,
                                                           seed + 1729, n_sensors)
                        except ValueError as exc:
                            reason = str(exc)
                            _record_disqualification(path.parent.name, [reason])
                            return {"track": "organism", "candidate": path.parent.name, "author": author,
                                    "sizes": [], "score": 0.0, "wall_seconds": time.perf_counter() - started,
                                    "device": str(device), "disqualified": [reason],
                                    "growth": _new_growth(units),
                                    "protocol": {"version": PROTOCOL_VERSION}}
                    rows.append(run_life(brain, WORLD_CONFIG["batch_size"], device, seed * 101 + 7,
                                         not no_interoception, baseline_mode, n_units=units,
                                         steps=life_steps,
                                         world_params={"social_group_size": social_group_size},
                                         permutation=bool(permutation and baseline_mode is None)))
        finally:
            pass
        summary = _summary(rows, units)
        permuted_summary = None
        if baseline_mode and baseline_mode != "baseline_table":
            permuted_rows = []
            with (_gpu_slot() if str(device).startswith("cuda") else nullcontext()):
                for seed in range(seeds):
                    permuted_rows.append(run_life(None, WORLD_CONFIG["batch_size"], device,
                                                  seed * 101 + 7, not no_interoception,
                                                  baseline_mode, n_units=units,
                                                  steps=life_steps,
                                                  world_params={"social_group_size": social_group_size},
                                                  permutation=True))
            permuted_summary = _summary(permuted_rows, units)
        results_by_size[units] = {"units": units, "batch": WORLD_CONFIG["batch_size"],
                                  "summary": summary, "score": summary["rooms_reached"]["mean"],
                                  "growth": summary["growth"],
                                  "worlds": seeds * WORLD_CONFIG["batch_size"],
                                  "trajectories": rows if seeds <= 2 else [],
                                  "wall_seconds": time.perf_counter() - tick}
        if permuted_summary is not None:
            results_by_size[units]["permuted_summary"] = permuted_summary
    summary = results_by_size[CALIBRATION_UNITS]["summary"]
    growth = summary["growth"]
    comparison_summary = None
    if baseline_mode is None and permutation:
        comparison_rows = []
        with (_gpu_slot() if str(device).startswith("cuda") else nullcontext()):
            for seed in range(seeds):
                comparison_brain = load_independent_brain(
                    path, CALIBRATION_UNITS, WORLD_CONFIG["batch_size"], device,
                    seed + 1729, n_sensors)
                comparison_rows.append(run_life(
                    comparison_brain, WORLD_CONFIG["batch_size"], device,
                    seed * 101 + 7, not no_interoception, n_units=CALIBRATION_UNITS,
                    steps=life_steps, world_params={"social_group_size": social_group_size},
                    permutation=False))
        comparison_summary = _summary(comparison_rows, CALIBRATION_UNITS)
    robustness = []
    if baseline_mode is None:
        spec = importlib.util.spec_from_file_location("organism_params", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for factor, params in _param_variants(getattr(module, "PARAMS", None)):
            rows = []
            with (_gpu_slot() if str(device).startswith("cuda") else nullcontext()):
                for seed in range(seeds):
                    brain = load_independent_brain(path, CALIBRATION_UNITS,
                                                   WORLD_CONFIG["batch_size"], device,
                                                   seed + 1729, n_sensors, params)
                    rows.append(run_life(brain, WORLD_CONFIG["batch_size"], device,
                                         seed * 101 + 7, not no_interoception,
                                         n_units=CALIBRATION_UNITS,
                                         steps=life_steps,
                                         world_params={"social_group_size": social_group_size},
                                         permutation=True))
            perturbed = _summary(rows, CALIBRATION_UNITS)
            base_score = summary["rooms_reached"]["mean"]
            changed_score = perturbed["rooms_reached"]["mean"]
            robustness.append({"factor": factor, "score": changed_score,
                               "ratio_to_nominal": (changed_score / base_score if base_score > 0
                                                    else (1.0 if changed_score == 0 else 0.0)),
                               "summary": perturbed})
    scale = {str(units): value for units, value in results_by_size.items()}
    size_curve = [{"units": units, "rooms_reached": item["score"],
                   "ci95": item["summary"]["rooms_reached"]["ci95"]}
                  for units, item in sorted(results_by_size.items())]
    result = {
        "track": ("organism_quick" if quick else
                   ("organism_calibration" if baseline_mode else "organism")),
        "candidate": path.parent.name,
        "author": author,
        "sizes": list(results_by_size.values()),
        "scale": scale,
        "size_curve": size_curve,
        "robustness": robustness,
        "score": summary["rooms_reached"]["mean"],
        "growth": growth,
        "wall_seconds": time.perf_counter() - started,
        "device": str(device),
        "interoception": not no_interoception,
        "baseline": baseline_mode,
        "permutation": bool(permutation and not baseline_mode),
        "comparison_without_permutation": comparison_summary,
        "social_assay": {"group_size": int(social_group_size),
                         "enabled": bool(social_group_size > 1),
                         "visible_through_eye": bool(social_group_size > 1),
                         "separate_brains": True},
        "principle_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "protocol": {"version": PROTOCOL_VERSION, "worlds_per_calibration": seeds * WORLD_CONFIG["batch_size"],
                      "batches": seeds, "batch_size": WORLD_CONFIG["batch_size"], "steps": life_steps,
                      "calibration_units": CALIBRATION_UNITS, "scale_smoke_steps": SMOKE_STEPS,
                      "sizes": list(results_by_size), "rooms": OrganismWorld.ROOMS, "sensors": n_sensors,
                      "pixels": OrganismWorld.PIXELS, "max_food": OrganismWorld.MAX_PATCHES,
                      "yolk_energy": WORLD_CONFIG["yolk_energy"],
                      "world_families": WORLD_CONFIG["world_families"],
                      "hidden_world_family": WORLD_CONFIG["hidden_world_family"],
                      "ladder": list(BIOLOGICAL_LADDER),
                      "description": "v7 organism-capacity ladder with energy-priced body growth",
                      "input_permutation": bool(permutation and not baseline_mode),
                      "motor_permutation": bool(permutation and not baseline_mode),
                      "quick": bool(quick)},
    }
    if baseline_mode and baseline_mode != "baseline_table":
        result["permuted_summary"] = results_by_size[CALIBRATION_UNITS].get("permuted_summary")
    reached = [item["mean"] for item in summary["room_reach_fraction"]]
    stage = max(index for index, fraction in enumerate(reached) if fraction >= 0.5)
    result["achieved_stage"] = {**BIOLOGICAL_LADDER[stage], "world_fraction": reached[stage]}
    return result


def append_result(result):
    target = ROOT / ("organism_calibration.jsonl" if result["track"] == "organism_calibration"
                     else "organism_quick.jsonl" if result["track"] == "organism_quick"
                     else "leaderboard.jsonl")
    with target.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(json.dumps(result, sort_keys=True) + "\n")
        handle.flush()
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
