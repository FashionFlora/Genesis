"""Reference policies for the GENESIS Crafter benchmark."""

import importlib
import numpy as np


class RandomAgent:
    uses_backprop = False

    def __init__(self, seed=0, action_count=17):
        self.rng = np.random.default_rng(seed)
        self.action_count = action_count

    def act(self, obs):
        return int(self.rng.integers(self.action_count))

    def observe(self, obs, action, next_obs, done, info_bez_nagrody):
        pass


class PixelNoveltyAgent:
    """Reward-free count-based visual novelty policy; intentionally not a learning method claim."""
    uses_backprop = False

    def __init__(self, seed=0, action_count=17, bins=8):
        self.rng = np.random.default_rng(seed)
        self.action_count = action_count
        self.bins = bins
        self.counts = {}
        self.last_action = None

    def act(self, obs):
        state = np.asarray(obs)[::8, ::8, :].astype(np.uint16) // (256 // self.bins)
        key = bytes(state.astype(np.uint8).ravel())
        # Stochastic exploration with an action conditioned on current-state novelty counts.
        n = np.array([self.counts.get((key, a), 0) for a in range(self.action_count)])
        weights = 1.0 / (1.0 + n)
        self.last_action = int(self.rng.choice(self.action_count, p=weights / weights.sum()))
        return self.last_action

    def observe(self, obs, action, next_obs, done, info_bez_nagrody):
        state = np.asarray(obs)[::8, ::8, :].astype(np.uint16) // (256 // self.bins)
        key = bytes(state.astype(np.uint8).ravel())
        pair = (key, int(action))
        self.counts[pair] = self.counts.get(pair, 0) + 1
        if done:
            self.counts.clear()


def discover_agent(spec, seed, action_count):
    if spec == "random":
        return RandomAgent(seed, action_count)
    if spec in {"pixel_novelty", "novelty"}:
        return PixelNoveltyAgent(seed, action_count)
    module_name, class_name = spec.split(":", 1)
    cls = getattr(importlib.import_module(module_name), class_name)
    return cls(seed=seed, action_count=action_count)


def declared_backprop(agent):
    return bool(getattr(agent, "uses_backprop", False))


def audit_tensors(agent):
    try:
        import torch
    except ImportError:
        return False
    visited = set()
    def walk(value):
        if id(value) in visited:
            return []
        visited.add(id(value))
        if isinstance(value, torch.Tensor):
            return [value]
        if isinstance(value, dict):
            return sum((walk(v) for v in value.values()), [])
        if isinstance(value, (list, tuple, set)):
            return sum((walk(v) for v in value), [])
        if hasattr(value, "__dict__") and not isinstance(value, type):
            return walk(vars(value))
        return []
    return any(t.requires_grad for t in walk(agent))


def install_backward_audit():
    """Patch Tensor.backward during the run. Returns restore callback and mutable count."""
    import torch
    original = torch.Tensor.backward
    count = {"calls": 0}
    def counted(tensor, *args, **kwargs):
        count["calls"] += 1
        return original(tensor, *args, **kwargs)
    torch.Tensor.backward = counted
    def restore():
        torch.Tensor.backward = original
    return count, restore


def audit_state_dict(agent):
    """Use if a policy has modules; parameter scan supplements object traversal."""
    try:
        import torch
    except ImportError:
        return False
    if hasattr(agent, "parameters"):
        return any(p.requires_grad for p in agent.parameters())
    return audit_tensors(agent)
