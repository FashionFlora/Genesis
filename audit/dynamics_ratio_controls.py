"""Small contract and cue-dependence audit for dynamics_energy_ratio.

This is diagnostic only; it does not append a leaderboard result.
"""

import hashlib
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "candidates/dynamics_energy_ratio/principle_organism.py"


def load():
    spec = importlib.util.spec_from_file_location("dynamics_ratio", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(n_sensors, rows):
    module = load()
    brain = module.OrganismBrain(302, n_sensors, 3, 1, "cpu", seed=0)
    actions = []
    states = []
    for row in rows:
        actions.append(brain.act(torch.as_tensor(row, dtype=torch.float32).reshape(1, -1))[0].tolist())
        states.append({
            "eye_width": brain.eye_width,
            "energy_index": brain.energy_index,
            "previous_energy": float(brain.previous_energy[0]),
            "previous_context": int(brain.previous_context[0]),
            "previous_color": int(brain.previous_color[0]),
            "mass_sum": float(brain.mass[0].sum()),
            "evidence_sum": float(brain.evidence[0].sum()),
        })
    return actions, states


def main():
    # A nonzero visual scene makes the action path observable.  The last
    # sensor is varied only in the no-interoception contract test.
    eye = torch.zeros(48)
    eye[8:11] = torch.tensor([0.8, 0.1, 0.0])
    eye[11:14] = torch.tensor([0.1, 0.8, 0.0])
    with_energy_0 = torch.cat((eye, torch.tensor([0.0])))
    with_energy_1 = torch.cat((eye, torch.tensor([1.0])))

    # n_sensors=48 is the judge's no-interoception shape.  The candidate's
    # indexing should not expose any energy state in this mode.
    no_intero_a, no_intero_states_a = run(48, [eye, eye])
    altered = eye.clone()
    altered[-1] = 1.0
    no_intero_b, no_intero_states_b = run(48, [altered, altered])

    # The first four green pixels are a world cue.  Flip the cue while
    # keeping all pixels used by the visual selector unchanged.
    cue_a = with_energy_0.clone()
    cue_b = with_energy_0.clone()
    cue_a[[1, 7]] = 0.8  # green channels of even pixels 0 and 2
    cue_b[[4, 10]] = 0.8  # green channels of odd pixels 1 and 3
    cue_a2 = with_energy_1.clone()
    cue_b2 = with_energy_1.clone()
    cue_a2[[1, 7]] = 0.8
    cue_b2[[4, 10]] = 0.8
    cue_actions_a, cue_states_a = run(49, [cue_a, cue_a2])
    cue_actions_b, cue_states_b = run(49, [cue_b, cue_b2])

    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    result = {
        "source_sha256": digest,
        "no_intero": {
            "reported_eye_width": no_intero_states_a[0]["eye_width"],
            "reported_energy_index": no_intero_states_a[0]["energy_index"],
            "action_delta_when_last_eye_channel_changes": max(
                abs(x - y) for x, y in zip(no_intero_a[1], no_intero_b[1])
            ),
            "state_a": no_intero_states_a,
            "state_b": no_intero_states_b,
        },
        "cue_flip": {
            "second_action_delta": max(
                abs(x - y) for x, y in zip(cue_actions_a[1], cue_actions_b[1])
            ),
            "first_action_delta": max(
                abs(x - y) for x, y in zip(cue_actions_a[0], cue_actions_b[0])
            ),
            "state_a": cue_states_a,
            "state_b": cue_states_b,
        },
    }
    out = ROOT / "audit/dynamics_ratio_controls.result.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
