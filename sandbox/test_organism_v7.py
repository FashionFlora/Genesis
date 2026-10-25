"""Fast CPU consistency tests for organism-v7 body mechanics."""

import torch

from worlds.organism_v7 import OrganismWorld, PIXELS_BY_ROOM, MOTORS_BY_ROOM


def test_v7_ladder_has_biological_ability_steps_and_growing_caps():
    from worlds.organism_v7 import BIOLOGICAL_LADDER, V7_CONFIG

    assert [item["room"] for item in BIOLOGICAL_LADDER] == list(range(6))
    assert all(item["stage"] and item["ability"] and item["task"] for item in BIOLOGICAL_LADDER)
    assert all("organism" not in item for item in BIOLOGICAL_LADDER)
    caps = [item["capacity"] for item in BIOLOGICAL_LADDER]
    assert caps == sorted(caps)
    assert V7_CONFIG["life_steps"] > 12000


def test_calibration_preflight_visits_all_rooms_before_long_run():
    from organism_judge_v7 import _preflight_all_rooms

    result = _preflight_all_rooms("cpu")
    assert result["passed"]
    assert [(item["from"], item["to"]) for item in result["transitions"]] == [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 5)]


def test_judge_accepts_an_explicit_lifetime_for_v7_assays():
    from pathlib import Path
    from organism_judge_v7 import judge

    candidate = Path(__file__).resolve().parent.parent / "candidates" / "_organism_random"
    result = judge(candidate, device="cpu", baseline_mode="random", sizes=[302], life_steps=4)

    assert result["protocol"]["steps"] == 4
    assert result["sizes"][0]["summary"]["mean_age"]["mean"] == 4


def test_channel_permutations_are_fixed_per_world_and_seeded_per_batch_row():
    from organism_judge_v7 import _world_permutations

    first = _world_permutations(4, "cpu", 44)
    repeated = _world_permutations(4, "cpu", 44)
    other = _world_permutations(4, "cpu", 45)
    assert all(torch.equal(first[key], repeated[key]) for key in first)
    assert len({tuple(torch.cat([first[key][row].reshape(-1).long() for key in first]).tolist())
                for row in range(4)}) == 4
    assert any(not torch.equal(first[key], other[key]) for key in first)


def test_permutation_changes_only_presented_channels_and_keeps_contract_shapes():
    from organism_judge_v7 import (_permute_motors, _permute_observation,
                                   _world_permutations)

    obs = torch.arange(2 * OrganismWorld.N_SENSORS, dtype=torch.float32).reshape(
        2, OrganismWorld.N_SENSORS)
    permutations = _world_permutations(2, "cpu", 71)
    changed = _permute_observation(obs, permutations)
    assert changed.shape == obs.shape
    assert torch.equal(changed[:, :OrganismWorld.EYE_SENSORS].sort(1).values,
                       obs[:, :OrganismWorld.EYE_SENSORS].sort(1).values)
    assert torch.equal(changed.sort(1).values, obs.sort(1).values)
    motors = torch.tensor([[0.1, 0.2, 0.3, 0.4, 0.5],
                           [0.6, 0.7, 0.8, 0.9, 1.0]])
    mapped = _permute_motors(motors, permutations)
    assert mapped.shape == motors.shape
    assert torch.equal(mapped[:, 3:], motors[:, 3:])
    assert torch.equal(mapped[:, :3].sort(1).values, motors[:, :3].sort(1).values)


def test_full_calibration_rejects_a_shortened_lifetime():
    from pathlib import Path
    from organism_judge_v7 import judge

    candidate = Path(__file__).resolve().parent.parent / "candidates" / "_organism_random"
    try:
        judge(candidate, device="cpu", baseline_mode="baseline_table", life_steps=4)
    except ValueError as exc:
        assert "full default organism lifetime" in str(exc)
    else:
        raise AssertionError("baseline_table accepted a shortened lifetime")


def test_sensor_slots_are_hidden_until_built():
    world = OrganismWorld(batch=1, device="cpu", seed=4)
    obs = world.observe()[:, :OrganismWorld.EYE_SENSORS].reshape(1, OrganismWorld.PIXELS, 3)
    assert bool((obs[:, PIXELS_BY_ROOM[0]:] == 0).all())
    n_sensors, n_motors = world.grow_body(torch.tensor([8]), torch.tensor([4]))
    grown = world.observe()[:, :OrganismWorld.EYE_SENSORS].reshape(1, OrganismWorld.PIXELS, 3)
    assert bool((grown[:, 8:] == 0).all())
    assert bool((world.body_pixels == 8).all())
    assert bool((world.body_motors == 4).all())
    assert int(n_sensors.item()) == 25
    assert int(n_motors.item()) == 4


def test_body_construction_and_upkeep_cost_energy():
    world = OrganismWorld(batch=1, device="cpu", seed=5)
    initial = world.energy.clone()
    world.grow_body(torch.tensor([4]), torch.tensor([2]))
    assert bool((world.energy < initial).all())
    after_build = world.energy.clone()
    world.grow_body(torch.tensor([4]), torch.tensor([2]))
    assert bool((world.energy < after_build).all())
    assert int(world.body_growth_events.item()) == 1


def test_body_requests_cannot_build_without_energy_and_old_motor_output_still_works():
    world = OrganismWorld(batch=1, device="cpu", seed=6)
    world.energy.zero_()
    world.grow_body(torch.tensor([16]), torch.tensor([5]))
    assert int(world.body_pixels.item()) == PIXELS_BY_ROOM[0]
    assert int(world.body_motors.item()) == MOTORS_BY_ROOM[0]
    world.step(torch.zeros(1, 3))


def test_each_room_keeps_observation_masks_consistent():
    world = OrganismWorld(batch=1, device="cpu", seed=7)
    for room in range(OrganismWorld.ROOMS):
        world.room.fill_(room)
        world.patch_energy.zero_()
        world.patch_energy[:, 0] = 1
        world.food[:, 0] = world.pos
        world.decoy[:, 0] = False
        world.observe()
        assert bool(world.bite_mask[:, 0].all())
        assert bool((world.bite_mask <= world._available_mask()).all())
        world.patch_energy[:, 0] = 0
        hidden = world.observe()
        assert not bool(world.visible_mask[:, 0].any())
        assert not bool(world.bite_mask[:, 0].any())
        assert torch.equal(hidden[:, -1], world.energy)


def test_yolk_is_finite_and_pays_metabolism_until_depleted():
    world = OrganismWorld(batch=1, device="cpu", seed=8,
                          params={"yolk_energy": 0.001})
    start = world.yolk.clone()
    for _ in range(32):
        world.step(torch.zeros(1, 3))
    assert bool((world.yolk < start).all())
    assert int(world.yolk_depleted_at.item()) >= 0


def test_world_families_and_hidden_family_are_visible_only_through_eye():
    world = OrganismWorld(batch=8, device="cpu", seed=9)
    assert len(set(world.world_family.tolist())) > 1
    hidden = OrganismWorld(batch=2, device="cpu", seed=9,
                           params={"hidden_world": True})
    assert bool((hidden.world_family == 3).all())
    assert hidden.observe().shape[1] == OrganismWorld.N_SENSORS


def test_social_group_shares_food_state_but_keeps_separate_rows():
    world = OrganismWorld(batch=4, device="cpu", seed=10,
                          params={"social_group_size": 2})
    assert world.social_group.tolist() == [0, 0, 1, 1]
    assert int(world.world_family[0]) == int(world.world_family[1])
    assert int(world.room_context[0]) == int(world.room_context[1])
    assert world.observe().shape == (4, OrganismWorld.N_SENSORS)
    world.step(torch.zeros(4, 3))
    assert world.task_events.shape == (4, 6)


def test_social_partner_changes_rgb_eye_only_for_its_group():
    world = OrganismWorld(batch=4, device="cpu", seed=12,
                          params={"social_group_size": 2})
    world.pos[:] = torch.tensor([[0.0, 0.0], [0.4, 0.0],
                                 [0.0, 0.0], [4.0, 0.0]])
    world.heading.zero_()
    before = world.observe()
    world.pos[1] = torch.tensor([0.4, 0.4])
    after = world.observe()
    assert not torch.equal(before[0, :OrganismWorld.EYE_SENSORS],
                           after[0, :OrganismWorld.EYE_SENSORS])
    assert torch.equal(before[2], after[2])


def test_social_group_contest_has_one_deterministic_winner():
    world = OrganismWorld(batch=2, device="cpu", seed=13,
                          params={"social_group_size": 2, "yolk_energy": 0.0})
    world.pos[:] = world.food[:, 0]
    world.patch_energy.zero_()
    world.patch_energy[:, 0] = 1
    world.decoy[:, 0] = False
    world.patch_color[:, 0] = world.food_channel
    world.energy.fill_(0.5)
    world.step(torch.tensor([[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]))
    assert bool(world.last_gain[0])
    assert not bool(world.last_gain[1])
    assert bool((world.patch_energy[:, 0] == 0).all())


def test_stage_advancement_waits_for_developmental_body():
    world = OrganismWorld(batch=1, device="cpu", seed=11)
    world.room.fill_(1)
    world.t = 2047
    world.room_age.fill_(500)
    world.flip_time.fill_(0)
    world.flip_bites.fill_(8)
    world.flip_correct_bites.fill_(8)
    world.energy_window.fill_(20)
    world.window_n.fill_(64)
    world.mastered_colors[:, 0] = True
    world.body_pixels.fill_(2)
    world.body_motors.fill_(1)
    world.step(torch.zeros(1, 3))
    assert int(world.room.item()) == 1
    world.t = 2111
    world.room_age.fill_(500)
    world.energy_window.fill_(20)
    world.window_n.fill_(64)
    world.body_pixels.fill_(3)
    world.step(torch.zeros(1, 3))
    assert int(world.room.item()) == 2


def test_forced_short_life_visits_every_room_transition_without_index_errors():
    world = OrganismWorld(batch=2, device="cpu", seed=12,
                          params={"yolk_energy": 0.01})
    for room in range(OrganismWorld.ROOMS):
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
        world.body_pixels.fill_(PIXELS_BY_ROOM[-1])
        world.body_motors.fill_(MOTORS_BY_ROOM[-1])
        before_events = world.task_events.clone()
        world.step(torch.zeros(2, 3))
        assert world.task_events.shape == before_events.shape
        if room < OrganismWorld.ROOMS - 1:
            assert bool((world.room == room + 1).all()), f"failed forced transition {room}->{room + 1}"
        else:
            assert bool((world.room == room).all())
        assert bool((world.room < OrganismWorld.ROOMS).all())


def test_stage_assays_use_distinct_observable_rules():
    world = OrganismWorld(batch=1, device="cpu", seed=13)
    world.patch_energy.zero_()
    world.patch_energy[:, :4] = 1
    world.decoy.zero_()
    world.room_context.zero_()
    world.context_color[:, 0] = 0
    world.target_shape.zero_()
    world.patch_color[:, :4] = 0
    world.food_shape[:, :4] = 0

    world.room.fill_(3)
    world.place_anchor[:] = world.food[:, 0]
    world.food[:, 1] = world.food[:, 0] + torch.tensor([1.0, 0.0])
    place_mask = world._edible_mask()
    assert bool(place_mask[0, 0]) and not bool(place_mask[0, 1])

    world.room.fill_(4)
    world.target_color.fill_(0)
    world.concept_rule.fill_(0)
    world.quantity_target.fill_(2)
    world.patch_color[:, 1] = 1
    concept_mask = world._edible_mask()
    assert bool(concept_mask[0, 0]) and not bool(concept_mask[0, 1])

    world.concept_rule.fill_(1)
    different_mask = world._edible_mask()
    assert not bool(different_mask[0, 0]) and bool(different_mask[0, 1])

    world.room.fill_(5)
    world.route_mask.zero_()
    world.route_mask[:, 2] = True
    map_mask = world._edible_mask()
    assert bool(map_mask[0, 2]) and not bool(map_mask[0, 0])


def test_growing_calibration_memory_covers_highest_room_shape():
    from organism_judge_v7 import _baseline

    world = OrganismWorld(batch=1, device="cpu", seed=14)
    world.room.fill_(5)
    world.food_shape.fill_(4)
    world.target_shape.fill_(4)
    obs = world.observe()
    state = {"generator": torch.Generator(device="cpu").manual_seed(15)}
    action = _baseline("growing", obs, world, state)
    assert action.shape == (1, 3)


def test_calibration_requires_advanced_disjoint_gain_over_table():
    from organism_judge_v7 import _calibration_checks

    def control(reach, score, body=0.0, yolk=1.0):
        fractions = [{"mean": value, "ci95": [value - 0.01, value + 0.01]}
                     for value in reach]
        return {"room_reach_fraction": fractions,
                "rooms_reached": {"mean": score},
                "body_growth": {"body_growth_events": {"mean": body}},
                "yolk_depleted_fraction": {"mean": yolk}}

    table = control([1.0, 0.8, 0.4, 0.2, 0.1, 0.05], 1.5)
    early_fail = control([1.0, 0.2, 0.1, 0.05, 0.02, 0.01], 0.5)
    growing = control([1.0, 0.95, 0.7, 0.5, 0.2, 0.1], 2.0)
    rows = {"random": early_fail, "braitenberg": early_fail, "delta": early_fail,
            "table": table, "growing": growing,
            "body_growth": control([1.0, 0.8, 0.4, 0.2, 0.1, 0.05], 1.5, body=1)}
    assert _calibration_checks(rows)["passed"]

    for room in range(2, 6):
        growing["room_reach_fraction"][room]["ci95"] = table["room_reach_fraction"][room]["ci95"]
    assert not _calibration_checks(rows)["passed"]
