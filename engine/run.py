"""Run deterministic Crafter benchmark episodes."""

import argparse
import json
import os
import platform
import subprocess
import time

import crafter
import numpy as np

from agents import discover_agent, declared_backprop, audit_tensors
from core import action_id, crafter_score, agent_info


def evaluate(agent, seeds, steps, run_dir):
    os.makedirs(run_dir, exist_ok=True)
    started = time.time()
    episodes = []
    observed = {name: [] for name in crafter.constants.achievements}
    for seed in seeds:
        env = crafter.Env(reward=False, length=min(10000, steps), seed=int(seed))
        obs = env.reset()
        achieved = set()
        n = 0
        episode_steps = 0
        episode_index = 0
        seed_episodes = []
        while n < steps:
            action = action_id(agent.act(obs), len(env.action_names))
            next_obs, _reward, done, info = env.step(action)
            achieved.update(name for name, count in info["achievements"].items() if count > 0)
            agent.observe(obs, action, next_obs, done, agent_info(info))
            obs = next_obs
            n += 1
            episode_steps += 1
            if done or episode_steps >= min(10000, steps):
                for name in observed:
                    observed[name].append(name in achieved)
                seed_episodes.append({"episode": episode_index, "steps": episode_steps,
                                      "achievements": sorted(achieved)})
                episode_index += 1
                if n >= steps:
                    break
                obs = env.reset()
                achieved = set()
                episode_steps = 0
        episodes.append({"seed": int(seed), "total_steps": n, "episodes": seed_episodes})
    rates = {name: 100.0 * sum(flags) / len(flags) for name, flags in observed.items()}
    try:
        code_version = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        code_version = None
    try:
        import torch
        torch_ver, cuda, gpu_name = torch.__version__, torch.cuda.is_available(), None
        if cuda:
            gpu_name = torch.cuda.get_device_name(0)
    except ImportError:
        torch_ver, cuda, gpu_name = None, False, None
    result = {
        "schema_version": 1,
        "run_id": os.path.basename(run_dir),
        "agent": type(agent).__name__,
        "agent_uses_backprop_declared": declared_backprop(agent),
        "audit": {
            "requires_grad_tensor_seen": audit_tensors(agent),
            "backward_calls": None,
            "limitations": ["Tensor scan only reaches agent-owned reachable objects.",
                            "backward interception is not enabled; functional autograd calls and custom backward paths may evade detection."],
        },
        "config": {"steps_per_episode": steps, "episode_horizon": min(10000, steps), "seeds": [int(s) for s in seeds],
                   "reward_blind": True, "crafter_version": getattr(crafter, "__version__", "unknown"),
                   "achievement_names": list(observed)},
        "code_version": code_version,
        "python": platform.python_version(),
        "numpy": np.__version__, "torch": torch_ver,
        "device": {"cuda_available": cuda, "gpu_name": gpu_name,
                   "cpu_count": os.cpu_count()},
        "started_unix": started, "duration_seconds": time.time() - started,
        "episodes": episodes,
        "achievement_success_rate_percent": rates,
        "crafter_score_percent": crafter_score(rates),
        "crafter_score_formula": "exp((1/22) * sum_i(log(1 + s_i))) - 1; s_i is success rate in percent",
    }
    with open(os.path.join(run_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--agent", default="random", help="random, pixel_novelty, or python.module:Class")
    p.add_argument("--steps", type=int, default=100000)
    p.add_argument("--episodes", type=int, default=1)
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--run-id")
    p.add_argument("--output", default="experiments")
    args = p.parse_args()
    if args.steps <= 0 or args.episodes <= 0:
        p.error("steps and episodes must be positive")
    agent = discover_agent(args.agent, args.seed, len(crafter.constants.actions))
    run_id = args.run_id or time.strftime("%Y%m%dT%H%M%S") + "_" + args.agent.replace(":", "_")
    result = evaluate(agent, [args.seed + i for i in range(args.episodes)], args.steps,
                      os.path.join(args.output, run_id))
    print(json.dumps({"run_id": run_id, "crafter_score_percent": result["crafter_score_percent"],
                      "result": os.path.join(args.output, run_id, "result.json")}))


if __name__ == "__main__":
    main()
