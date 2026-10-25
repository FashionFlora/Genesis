"""Versioned organism-v7 world with energy-priced body growth."""

import math

import torch

from .organism import OrganismWorld as _OrganismWorld
from .organism_config import WORLD_CONFIG as V6_CONFIG


# v7 has its own protocol parameters.  Keeping this copy local prevents a
# v6 calibration from silently changing when the developmental world grows.
V7_CONFIG = {
    **V6_CONFIG,
    "version": "organism-v7",
    "life_steps": 50000,
    "yolk_energy": 1.50,
    "yolk_decay_fraction": 1.0,
    "world_families": 3,
    "hidden_world_family": 3,
    "social_group_size": 1,
    "reversal_times": (4000, 12000, 20000, 28000, 36000, 44000),
}


BIOLOGICAL_LADDER = (
    {"room": 0, "stage": "temporal comparison",
     "capacity": 8, "ability": "temporal gradient comparison and adaptation",
     "task": "compare successive samples while the nutrient gradient drifts"},
    {"room": 1, "stage": "habituation and preference learning",
     "capacity": 32, "ability": "habituation, simple association, preference learning",
     "task": "habituate to a repeated cue and retain a two-choice preference"},
    {"room": 2, "stage": "association and delayed memory",
     "capacity": 64, "ability": "classical conditioning, sensitization, long-term memory",
     "task": "condition a visual cue and retain it across a long delay"},
    {"room": 3, "stage": "reversal and contextual place memory",
     "capacity": 128, "ability": "reversal, place learning, context",
     "task": "reverse a cue, remember a place, and use room context"},
    {"room": 4, "stage": "relations, route memory and quantity",
     "capacity": 256, "ability": "same/different, route memory, small-number discrimination",
     "task": "match or mismatch visual exemplars while following a remembered route"},
    {"room": 5, "stage": "spatial map and episodic memory",
     "capacity": 512, "ability": "spatial maps, latent and episodic-like memory",
     "task": "use landmarks and a latent map after a delayed episode"},
)

PIXELS_BY_ROOM = (2, 3, 4, 6, 8, 12)
MOTORS_BY_ROOM = (1, 1, 2, 3, 4, 5)
MAX_PIXELS = 16
MAX_MOTORS = 5
BODY_BUILD_COST = 0.025
BODY_MAINTENANCE_COST = 0.000015
TASK_DELAY_STEPS = 96
TASK_PLACE_RADIUS = 0.42


class OrganismWorld(_OrganismWorld):
    """v7 keeps a fixed tensor envelope while per-organism body slots grow."""

    PIXELS = MAX_PIXELS
    N_SENSORS = MAX_PIXELS * 3 + 1
    EYE_SENSORS = MAX_PIXELS * 3
    N_MOTORS = MAX_MOTORS

    def __init__(self, *args, **kwargs):
        params = dict(V7_CONFIG)
        params.update(kwargs.pop("params", {}) or {})
        params["version"] = "organism-v7"
        super().__init__(*args, params=params, **kwargs)
        self.body_pixels = torch.full((self.batch,), PIXELS_BY_ROOM[0],
                                      dtype=torch.long, device=self.device)
        self.body_motors = torch.full((self.batch,), MOTORS_BY_ROOM[0],
                                      dtype=torch.long, device=self.device)
        self.body_growth_events = torch.zeros(self.batch, dtype=torch.long, device=self.device)
        self.body_energy_spent = torch.zeros(self.batch, device=self.device)
        self.yolk_initial = float(params.get("yolk_energy", 0.0))
        if not hasattr(self, "yolk"):
            self.yolk = torch.full((self.batch,), self.yolk_initial, device=self.device)
        if not hasattr(self, "yolk_depleted_at"):
            self.yolk_depleted_at = torch.full((self.batch,), -1, dtype=torch.long, device=self.device)
        if not hasattr(self, "world_family"):
            self.world_family = torch.zeros(self.batch, dtype=torch.long, device=self.device)
        self.hidden_world = bool(params.get("hidden_world", False))
        self.social_group_size = max(1, int(params.get("social_group_size", 1)))
        self.social_group = torch.arange(self.batch, device=self.device) // self.social_group_size
        self.social_group_count = int(self.social_group.max().item() + 1)

    def reset(self):
        super().reset()
        params = self.params
        self.yolk_initial = float(params.get("yolk_energy", 0.0))
        self.yolk = torch.full((self.batch,), self.yolk_initial, device=self.device)
        self.yolk_depleted_at = torch.full((self.batch,), -1, dtype=torch.long, device=self.device)
        self.task_events = torch.zeros(self.batch, 6, device=self.device)
        # Assay state is world state, not an extra sensory channel.  Each
        # field is rendered by the existing RGB eye through food position,
        # shape, or colour.
        self.task_progress = torch.zeros(self.batch, 6, device=self.device)
        self.task_delay_until = torch.full((self.batch,), -1, dtype=torch.long, device=self.device)
        self.place_anchor = self.food[:, 0].clone()
        self.route_waypoints = self.food[:, :3].clone()
        self.route_mask = torch.zeros(self.batch, self.MAX_PATCHES, dtype=torch.bool, device=self.device)
        self.route_mask[:, :3] = True
        self.concept_rule = torch.zeros(self.batch, dtype=torch.long, device=self.device)
        self.quantity_target = torch.ones(self.batch, dtype=torch.long, device=self.device)
        self.episode_anchor = self.food[:, 0].clone()
        if hasattr(self, "body_pixels"):
            self.body_pixels.fill_(PIXELS_BY_ROOM[0])
            self.body_motors.fill_(MOTORS_BY_ROOM[0])
            self.body_growth_events.zero_()
            self.body_energy_spent.zero_()
        family_count = int(params.get("world_families", 3))
        if bool(params.get("hidden_world", False)):
            self.world_family = torch.full((self.batch,), int(params.get("hidden_world_family", family_count)),
                                           dtype=torch.long, device=self.device)
        else:
            self.world_family = torch.randint(family_count, (self.batch,), generator=self.gen, device=self.device)
        # Families change palette and room geometry, while preserving the
        # visual-only contract.  The held-out family uses a fourth palette.
        palette_shift = torch.where(self.world_family >= family_count,
                                    torch.ones_like(self.world_family),
                                    self.world_family % int(params["color_count"]))
        self.patch_color = (self.patch_color + palette_shift[:, None]) % int(params["color_count"])
        self.context_color = (self.context_color + palette_shift[:, None]) % int(params["color_count"])
        self.food_channel = self.context_color.gather(1, self.room_context[:, None])[:, 0]
        family_scale = torch.where(self.world_family >= family_count,
                                   torch.full_like(self.world_family.float(), 1.15),
                                   0.82 + 0.16 * (self.world_family.float() % 3))
        self.food = self.food * family_scale[:, None, None]
        self.shadow = self.shadow * family_scale[:, None]
        self.social_group_size = max(1, int(params.get("social_group_size", 1)))
        self.social_group = torch.arange(self.batch, device=self.device) // self.social_group_size
        self.social_group_count = int(self.social_group.max().item() + 1)
        if self.social_group_size > 1:
            roots = (torch.arange(self.batch, device=self.device) // self.social_group_size) * self.social_group_size
            for name in ("food", "patch_color", "food_shape", "patch_energy", "decoy", "regrow",
                         "world_family", "context_color", "room_context", "target_shape",
                         "target_color", "context_required", "food_channel", "shadow"):
                setattr(self, name, getattr(self, name)[roots].clone())

    def _edible_mask(self, available=None):
        """Apply the room-specific ability assay to the visual food rule."""
        available = self._available_mask() if available is None else available
        base = super()._edible_mask(available)
        context_color = self.context_color.gather(1, self.room_context[:, None])
        contextual = self.patch_color == context_color
        patterned = contextual & (self.food_shape == self.target_shape[:, None])

        # Room 0: temporal comparison/adaptation is the colour reversal
        # already tracked by the base world.
        # Room 1: repeated cue and preference use the contextual rule.
        room2 = self.room == 2
        room3 = self.room == 3
        room4 = self.room == 4
        room5 = self.room == 5
        # Conditioning retains a shape cue across a delay.
        delayed = patterned & ((self.t >= self.task_delay_until)[:, None] | (self.task_delay_until < 0)[:, None])
        base = torch.where(room2[:, None], available & delayed, base)
        # Place/context assay: the conditioned cue is edible only at its
        # remembered place, which remains visible as a landmark in the eye.
        near_place = torch.linalg.vector_norm(self.food - self.place_anchor[:, None, :], dim=2) <= TASK_PLACE_RADIUS
        place_rule = patterned & contextual & near_place
        base = torch.where(room3[:, None], available & place_rule, base)
        # Concept assay: same or different colour relative to the current
        # exemplar, with a small-number (one to three) route prefix.
        same = self.patch_color == self.target_color[:, None]
        relation = torch.where(self.concept_rule[:, None] == 0, same, ~same)
        quantity = torch.arange(self.MAX_PATCHES, device=self.device)[None, :] < self.quantity_target[:, None]
        concept_rule = available & (self.food_shape == self.target_shape[:, None]) & relation & quantity
        base = torch.where(room4[:, None], concept_rule, base)
        # Map/episode assay: after a delay, only the remembered route
        # landmarks are edible.  Their positions and RGB marks are visible.
        map_rule = available & patterned & self.route_mask
        base = torch.where(room5[:, None], map_rule, base)
        return base

    def observe(self):
        obs = super().observe()
        pixels = torch.arange(MAX_PIXELS, device=self.device)[None, :]
        active = pixels < self.body_pixels[:, None]
        rgb = obs[:, :self.EYE_SENSORS].reshape(self.batch, MAX_PIXELS, 3)
        rgb = rgb * active[:, :, None]
        eye = rgb.flatten(1)
        # Social organisms share only visual space: partner locations are
        # rendered as weak blue landmarks, never copied into brain state.
        if self.social_group_size > 1:
            partner = torch.zeros_like(rgb[:, :, 2])
            roots = (torch.arange(self.batch, device=self.device) // self.social_group_size) * self.social_group_size
            for offset in range(1, self.social_group_size):
                other = roots + (torch.arange(self.batch, device=self.device) - roots + offset) % self.social_group_size
                other = other.clamp(max=self.batch - 1)
                same = self.social_group == self.social_group[other]
                delta = self.pos[other] - self.pos
                dist = torch.linalg.vector_norm(delta, dim=1).clamp_min(1e-5)
                bearing = torch.atan2(delta[:, 1], delta[:, 0]) - self.heading
                rel = torch.remainder(bearing + math.pi, 2 * math.pi) - math.pi
                angular = torch.exp(-((torch.remainder(self.angles - rel[:, None] + math.pi, 2 * math.pi) - math.pi) / 0.55).square())
                partner = torch.maximum(partner, angular * (dist < 1.8).float()[:, None] * same.float()[:, None])
            rgb[:, :, 2] = torch.maximum(rgb[:, :, 2], partner)
            eye = rgb.flatten(1)
        if self.interoception:
            return torch.cat((eye, obs[:, -1:]), dim=1)
        return eye

    def _room_positions(self, level):
        positions = super()._room_positions(level)
        if hasattr(self, "world_family"):
            family_count = int(self.params.get("world_families", 3))
            scale = torch.where(self.world_family >= family_count,
                                torch.full_like(self.world_family.float(), 1.15),
                                0.82 + 0.16 * (self.world_family.float() % 3))[:, None, None]
            positions = positions * scale
        return positions

    def grow_body(self, pixel_request, motor_request):
        """Apply per-organism growth requests, charging construction and upkeep."""
        pixels = torch.as_tensor(pixel_request, device=self.device).long().reshape(self.batch)
        motors = torch.as_tensor(motor_request, device=self.device).long().reshape(self.batch)
        pixels = pixels.clamp(min=PIXELS_BY_ROOM[0], max=MAX_PIXELS)
        motors = motors.clamp(min=MOTORS_BY_ROOM[0], max=MAX_MOTORS)
        new_pixels = torch.maximum(self.body_pixels, pixels)
        new_motors = torch.maximum(self.body_motors, motors)
        added = (new_pixels - self.body_pixels) + (new_motors - self.body_motors)
        cost = added.float() * BODY_BUILD_COST
        can_build = self.alive & (self.energy > cost)
        new_pixels = torch.where(can_build, new_pixels, self.body_pixels)
        new_motors = torch.where(can_build, new_motors, self.body_motors)
        built = (new_pixels - self.body_pixels) + (new_motors - self.body_motors)
        self.energy -= built.float() * BODY_BUILD_COST
        self.body_energy_spent += built.float() * BODY_BUILD_COST
        self.body_growth_events += (built > 0).long()
        self.body_pixels = new_pixels
        self.body_motors = new_motors
        maintained_parts = ((self.body_pixels - PIXELS_BY_ROOM[0])
                            + (self.body_motors - MOTORS_BY_ROOM[0])).float()
        upkeep = maintained_parts * BODY_MAINTENANCE_COST
        self.energy -= upkeep
        self.body_energy_spent += upkeep
        sensor_count = self.body_pixels * 3 + int(self.interoception)
        return sensor_count, self.body_motors

    def developmental_state(self):
        """Small public report used by the judge and consistency tests."""
        return {"room": self.room.clone(), "stage": self.room.clone(),
                "pixels": self.body_pixels.clone(), "motors": self.body_motors.clone(),
                "yolk": self.yolk.clone(), "world_family": self.world_family.clone(),
                "social_group": self.social_group.clone(),
                "task_progress": self.task_progress.clone(),
                "concept_rule": self.concept_rule.clone(),
                "quantity_target": self.quantity_target.clone()}

    def step(self, motors):
        m = torch.as_tensor(motors, device=self.device, dtype=torch.float32)
        if m.shape[1] < self.N_MOTORS:
            m = torch.nn.functional.pad(m, (0, self.N_MOTORS - m.shape[1]))
        m = m.clone()
        # Additional actuators contribute bounded turning and propulsion.
        inactive = torch.arange(self.N_MOTORS, device=self.device)[None, :] >= self.body_motors[:, None]
        extra = (m[:, 3:] * ~inactive[:, 3:]).sum(1)
        m[:, 0] = (m[:, 0] + extra).clamp(-1, 1)
        if self.social_group_size > 1:
            heading = self.heading + self.params["turn_gain"] * m[:, 0]
            speed = torch.sign(m[:, 1]) * (self.params["base_speed"]
                                           + self.params["speed_gain"] * m[:, 1].abs())
            predicted = self.pos + speed[:, None] * torch.stack((heading.cos(), heading.sin()), 1)
            distances = torch.linalg.vector_norm(predicted[:, None, :] - self.food, dim=2)
            candidates = ((distances < self.params["touch_radius"]) & self._available_mask()
                          & (m[:, 2, None] > 0) & self.alive[:, None])
            rows = torch.arange(self.batch, device=self.device)
            roots = (rows // self.social_group_size) * self.social_group_size
            winners = candidates.clone()
            for offset in range(1, self.social_group_size):
                other = roots + (rows - roots + offset) % self.social_group_size
                other = other.clamp(max=self.batch - 1)
                same_group = self.social_group == self.social_group[other]
                # One organism wins each contested patch.  Equal distances
                # use the lower row index, so simultaneous bites cannot both
                # consume the shared resource and cannot deadlock the pair.
                other_better = candidates[other] & (
                    (distances[other] < distances)
                    | ((distances[other] == distances) & (other[:, None] < rows[:, None])))
                winners &= ~(same_group[:, None] & other_better)
            m[:, 2] = torch.where(winners.any(1), m[:, 2], torch.zeros_like(m[:, 2]))
        before_patch = self.patch_energy.clone()
        before_room = self.room.clone()
        before_context = self.room_context.clone()
        before_transitions = self.patch_transitions.clone()
        before_room_task = self._edible_mask(self._available_mask())
        gain = super().step(m[:, :3])
        self.task_events[:, 0] += (before_context != self.room_context).float()
        self.task_events[:, 1] += self.last_bite.float()
        self.task_events[:, 2] += self.last_gain.float()
        self.task_events[:, 3] += (before_room != self.room).float()
        self.task_events[:, 4] += self.patch_transitions - before_transitions
        self.task_events[:, 5] += (self.social_group_size > 1) * self.last_gain.float()
        # Count successful observations of each assay separately from food
        # gains.  These counters are diagnostics and never feed advancement.
        self.task_progress[:, 0] += (before_context != self.room_context).float()
        self.task_progress[:, 1] += self.last_bite.float()
        self.task_progress[:, 2] += (self.last_gain & (self.t >= self.task_delay_until)).float()
        self.task_progress[:, 3] += (self.last_gain & before_room_task.gather(1, self.last_bite_index.clamp_min(0)[:, None]).squeeze(1)).float()
        self.task_progress[:, 4] += (self.last_gain & (self.room == 4)).float()
        self.task_progress[:, 5] += (self.last_gain & (self.room == 5)).float()
        entered = self.room != before_room
        for level in range(1, self.ROOMS):
            new = entered & (self.room == level)
            if level == 2:
                self.task_delay_until = torch.where(new, self.t + TASK_DELAY_STEPS, self.task_delay_until)
            if level == 3:
                self.place_anchor = torch.where(new[:, None], self.food[:, 0], self.place_anchor)
            if level == 4:
                self.concept_rule = torch.where(new, (self.rand(self.batch) > 0.5).long(), self.concept_rule)
                self.quantity_target = torch.where(new, (1 + (self.rand(self.batch) * 3).long()), self.quantity_target)
            if level == 5:
                self.task_delay_until = torch.where(new, self.t + TASK_DELAY_STEPS, self.task_delay_until)
                self.route_waypoints = torch.where(new[:, None, None], self.food[:, :3], self.route_waypoints)
                self.route_mask = torch.where(new[:, None],
                                              torch.arange(self.MAX_PATCHES, device=self.device)[None, :] < 3,
                                              self.route_mask)
        if self.social_group_size > 1:
            depleted = (before_patch > 0) & (self.patch_energy <= 0)
            group_depleted = torch.zeros_like(depleted)
            for offset in range(self.social_group_size):
                other = (torch.arange(self.batch, device=self.device) // self.social_group_size) * self.social_group_size + offset
                valid = other < self.batch
                group_depleted |= depleted[other.clamp(max=self.batch - 1)] & valid[:, None]
            self.patch_energy = torch.where(group_depleted, torch.zeros_like(self.patch_energy), self.patch_energy)
        return gain
