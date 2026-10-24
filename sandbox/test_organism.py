"""Fast CPU consistency tests for organism-v4."""

import torch

from worlds.organism import OrganismWorld


def _world(batch=2, seed=3):
    return OrganismWorld(batch=batch, device="cpu", seed=seed)


def test_depleted_patch_is_invisible_and_not_biteable():
    world = _world()
    world.patch_energy[:] = 0
    world.decoy[:] = False
    world.patch_energy[:, 0] = 1
    world.pos[:] = world.food[:, 0]
    visible = world.observe().clone()
    world.patch_energy[:, 0] = 0
    hidden = world.observe().clone()
    eye = slice(0, OrganismWorld.EYE_SENSORS)
    assert bool((visible[:, eye] > hidden[:, eye]).any())
    assert torch.equal(hidden[:, eye], torch.zeros_like(hidden[:, eye]))
    motors = torch.zeros(world.batch, OrganismWorld.N_MOTORS)
    motors[:, 2] = 1
    world.step(motors)
    assert not bool(world.last_bite.any())


def test_bite_mask_matches_visible_available_patch():
    world = _world()
    world.pos[:] = world.food[:, 0]
    world.patch_energy[:, 0] = 1
    world.decoy[:, 0] = False
    world.observe()
    assert bool(world.bite_mask[:, 0].all())
    motors = torch.zeros(world.batch, OrganismWorld.N_MOTORS)
    motors[:, 2] = 1
    gain = world.step(motors)
    assert bool(world.last_bite.all())
    assert bool(gain.all())
    world.patch_energy[:, 0] = 0
    world.observe()
    assert not bool(world.bite_mask[:, 0].any())
    world.step(motors)
    assert not bool(world.last_bite.any())


def test_energy_accounts_for_motion_and_food():
    world = _world(batch=1)
    initial = world.energy.clone()
    speed = world.params["base_speed"] + world.params["speed_gain"]
    expected_cost = (world.params["energy_decay"] * world.params["energy_decay_factor"]
                     * world.params["room_zero_energy_factor"]
                     + world.params["move_cost"] * world.params["move_cost_factor"] * abs(speed))
    world.step(torch.tensor([[0.0, 1.0, 0.0]]))
    assert torch.allclose(world.energy, initial - expected_cost)
    world.pos[:] = world.food[:, 0]
    world.patch_energy[:, 0] = 1
    before_food = world.energy.clone()
    world.step(torch.tensor([[0.0, 0.0, 1.0]]))
    expected = before_food - world.params["energy_decay"] * world.params["energy_decay_factor"] * world.params["room_zero_energy_factor"]
    expected = (expected + world.params["food_gain"]).clamp(max=1)
    assert torch.allclose(world.energy, expected)


def test_signed_drive_supports_reverse_and_stop():
    world = _world(batch=1)
    origin = world.pos.clone()
    heading = world.heading.clone()
    world.step(torch.tensor([[0.0, 0.0, 0.0]]))
    assert torch.allclose(world.pos, origin)
    world.pos.copy_(origin)
    world.heading.copy_(heading)
    world.step(torch.tensor([[0.0, -1.0, 0.0]]))
    displacement = world.pos - origin
    expected = -(world.params["base_speed"] + world.params["speed_gain"])
    direction = torch.stack((heading.cos(), heading.sin()), 1)
    assert torch.allclose(displacement, expected * direction)


def test_reversal_changes_edible_color():
    world = _world(batch=1)
    world.t = world.REVERSAL_TIMES[0]
    old = world.food_channel.clone()
    world.step(torch.zeros(1, OrganismWorld.N_MOTORS))
    assert bool(torch.ne(world.food_channel, old).all())


def test_room_advancement_requires_mastery():
    world = _world(batch=1)
    world.t = (world.params["minimum_time_first"]
               + world.params["energy_window_steps"] - 1)
    world.room_age[:] = 0
    world.energy_window[:] = 0
    world.window_n[:] = 0
    world.flip_bites[:] = 100
    world.flip_correct_bites[:] = 100
    world.step(torch.zeros(1, OrganismWorld.N_MOTORS))
    assert int(world.room.item()) == 0


def test_room_advancement_occurs_when_all_criteria_hold():
    world = _world(batch=1)
    world.t = world.params["minimum_time_first"] + world.params["energy_window_steps"] - 1
    world.room_age[:] = world.ROOM_DWELL[0]
    world.energy_window[:] = world.params["energy_mastery_threshold"] * world.params["energy_window_steps"] + 1
    world.window_n[:] = world.params["energy_window_steps"]
    world.flip_bites[:] = world.params["required_bites"][0]
    world.flip_correct_bites[:] = world.params["required_bites"][0]
    world.mastered_colors[:, :world.params["required_reversals"][0]] = True
    world.step(torch.zeros(1, OrganismWorld.N_MOTORS))
    assert int(world.room.item()) == 1


def test_batch_rows_are_independent():
    first = _world(batch=2, seed=11)
    second = _world(batch=2, seed=11)
    motors = torch.zeros(2, OrganismWorld.N_MOTORS)
    changed = motors.clone()
    changed[0] = torch.tensor([1.0, 1.0, 1.0])
    first.step(changed)
    second.step(motors)
    assert torch.allclose(first.energy[1], second.energy[1])
    assert torch.allclose(first.pos[1], second.pos[1])


def test_candidate_batch_outputs_are_row_independent():
    from organism_judge import _independence_test

    class RowBrain:
        def __init__(self, n_units, n_sensors, n_motors, batch, device, seed=0):
            self.batch = batch

        def act(self, sensors):
            return sensors[:, :OrganismWorld.N_MOTORS]

    class Module:
        OrganismBrain = RowBrain

    assert _independence_test(Module, 302, "cpu", 13, OrganismWorld.N_SENSORS)


def test_observation_has_no_reward_channel():
    world = _world()
    assert world.observe().shape[1] == OrganismWorld.N_SENSORS
    assert not hasattr(world, "reward")
    assert not hasattr(world, "observe_reward")


def test_world_parameters_are_all_documented():
    from worlds.organism_config import PARAMETER_DESCRIPTIONS, WORLD_CONFIG

    assert set(WORLD_CONFIG) == set(PARAMETER_DESCRIPTIONS)


def test_ordinary_candidate_has_no_reward_hook():
    from organism_judge import _calibration_hooks

    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "candidates" / "_organism_random" / "principle_organism.py"
    assert not _calibration_hooks(path)


def test_example_candidate_reports_structure_growth():
    from organism_judge import load_brain, run_life
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "candidates" / "_organism_random" / "principle_organism.py"
    _, brain = load_brain(path, 302, 1, "cpu", 19, OrganismWorld.N_SENSORS)
    result = run_life(brain, 1, "cpu", 23, steps=257, n_units=302)
    growth = result["growth"]
    assert growth["curve"]
    assert growth["initial"]["units"] == 302
    assert growth["final"]["units"] == 302
    assert growth["ratio_to_n_units"] == 1.0


if __name__ == "__main__":
    tests = [(name, value) for name, value in globals().items()
             if name.startswith("test_") and callable(value)]
    for name, test in tests:
        test()
        print(f"PASS {name}")
    print(f"{len(tests)} organism consistency tests passed")
