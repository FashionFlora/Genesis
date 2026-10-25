"""Batched continuous lives in progressively larger nested rooms."""

import math

import torch
import torch.nn.functional as F

try:
    from .organism_config import WORLD_CONFIG
except ImportError:
    from worlds.organism_config import WORLD_CONFIG


class OrganismWorld:
    """One vectorized organism-v6 world with independent rows."""

    PIXELS = WORLD_CONFIG["pixels"]
    N_SENSORS = PIXELS * WORLD_CONFIG["color_count"] + 1
    EYE_SENSORS = PIXELS * WORLD_CONFIG["color_count"]
    N_MOTORS = WORLD_CONFIG["motor_count"]
    ROOMS = WORLD_CONFIG["rooms"]
    FOOD_COUNTS = WORLD_CONFIG["food_counts"]
    MAX_PATCHES = max(FOOD_COUNTS)
    ROOM_SIDES = WORLD_CONFIG["room_sides"]
    ROOM_DWELL = WORLD_CONFIG["room_dwell"]
    REVERSAL_TIMES = WORLD_CONFIG["reversal_times"]

    def __init__(self, batch=None, device="cuda", seed=0, params=None,
                 interoception=True):
        self.device = torch.device(device)
        self.batch = int(batch if batch is not None else WORLD_CONFIG["batch_size"])
        self.interoception = bool(interoception)
        self.params = {**WORLD_CONFIG, **(params or {})}
        self.gen = torch.Generator(device=self.device).manual_seed(int(seed))
        self.retina_pixels = self.PIXELS + 2 * min(self.ROOMS - 1, 5)
        self.angles = torch.arange(self.PIXELS, device=self.device) * (2 * math.pi / self.PIXELS)
        self.retina_angles = torch.arange(self.retina_pixels, device=self.device) * (2 * math.pi / self.retina_pixels)
        self.reset()

    def rand(self, *shape):
        return torch.rand(shape, device=self.device, generator=self.gen)

    def reset(self):
        b, d = self.batch, self.device
        span = self.params["initial_position_span"]
        self.room = torch.zeros(b, dtype=torch.long, device=d)
        self.pos = self.rand(b, 2) * span - span / 2
        self.heading = self.rand(b) * (2 * math.pi) - math.pi
        self.energy = torch.full((b,), self.params["initial_energy"], device=d)
        self.alive = torch.ones(b, dtype=torch.bool, device=d)
        self.age = torch.zeros(b, device=d)
        self.food_count = torch.tensor(self.FOOD_COUNTS, device=d)
        old_patches = self.FOOD_COUNTS[-1]
        self.food = torch.zeros(b, self.MAX_PATCHES, 2, device=d)
        self.food[:, :old_patches] = self.rand(b, old_patches, 2) * span - span / 2
        self.patch_color = torch.zeros(b, self.MAX_PATCHES, dtype=torch.long, device=d)
        self.patch_color[:, :old_patches] = (self.rand(b, old_patches) * 2).long()
        self.food_shape = torch.zeros(b, self.MAX_PATCHES, dtype=torch.long, device=d)
        self.room_context = (self.rand(b) > 0.5).long()
        self.context_color = torch.zeros(b, 2, dtype=torch.long, device=d)
        first_color = (self.rand(b) > 0.5).long()
        self.context_color[:, 0] = first_color
        self.context_color[:, 1] = 1 - first_color
        self.target_shape = torch.zeros(b, dtype=torch.long, device=d)
        self.target_color = torch.zeros(b, dtype=torch.long, device=d)
        self.context_required = torch.zeros(b, dtype=torch.long, device=d)
        self.decoy = torch.zeros(b, self.MAX_PATCHES, dtype=torch.bool, device=d)
        first = self.FOOD_COUNTS[0]
        decoys = self.rand(b, first) < self.params["decoy_probability"][0]
        decoys[:, 0] = False
        self.decoy[:, :first] = decoys
        shadow_span = self.params["shadow_position_span"]
        self.shadow = self.rand(b, 2) * shadow_span - shadow_span / 2
        self.patch_energy = torch.zeros(b, self.MAX_PATCHES, device=d)
        self.patch_energy[:, :first] = 1
        self.regrow = torch.zeros(b, self.MAX_PATCHES, device=d)
        self.food_channel = self.context_color.gather(1, self.room_context[:, None])[:, 0]
        self.flip_time = torch.full((b,), -1, device=d)
        self.room_time = torch.full((b, self.ROOMS), -1, dtype=torch.long, device=d)
        self.room_time[:, 0] = 0
        self.room_age = torch.zeros(b, dtype=torch.long, device=d)
        self.energy_window = torch.zeros(b, device=d)
        self.window_n = torch.zeros(b, device=d)
        self.t = 0
        self.escape_events = torch.zeros(b, device=d)
        self.visits = torch.zeros(b, device=d)
        self.patch_seen = torch.zeros(b, self.MAX_PATCHES, dtype=torch.bool, device=d)
        self.last_patch = torch.full((b,), -1, dtype=torch.long, device=d)
        self.patch_transitions = torch.zeros(b, device=d)
        self.flip_bites = torch.zeros(b, device=d)
        self.flip_correct_bites = torch.zeros(b, device=d)
        self.mastered_colors = torch.zeros(b, self.params["color_count"], dtype=torch.bool, device=d)
        self.last_gain = torch.zeros(b, dtype=torch.bool, device=d)
        self.last_bite = torch.zeros(b, dtype=torch.bool, device=d)
        self.last_bite_index = torch.full((b,), -1, dtype=torch.long, device=d)
        self.visible_mask = torch.zeros(b, self.MAX_PATCHES, dtype=torch.bool, device=d)
        self.bite_mask = torch.zeros(b, self.MAX_PATCHES, dtype=torch.bool, device=d)

    def _side(self):
        return torch.tensor(self.ROOM_SIDES, device=self.device)[self.room]

    def _room_positions(self, level):
        """Scatter active patches in an annulus scaled to a room."""
        n = self.FOOD_COUNTS[level]
        side = self.ROOM_SIDES[level]
        angle = self.rand(self.batch, n) * (2 * math.pi)
        inner = self.params["room_radius_inner_base"] + self.params["room_radius_inner_gain"] * level
        outer = self.params["room_radius_outer_base"] - self.params["room_radius_outer_decay"] * level
        radius = side * (inner + self.rand(self.batch, n) * outer)
        return torch.stack((radius * angle.cos(), radius * angle.sin()), dim=2)

    def _active_mask(self):
        ids = torch.arange(self.MAX_PATCHES, device=self.device)[None, :]
        return ids < self.food_count[self.room, None]

    def _available_mask(self):
        return self._active_mask() & (self.patch_energy > 0)

    def _edible_mask(self, available=None):
        """Return the food rule for the current room.

        Keeping this rule in one method lets versioned worlds add assays
        without duplicating the physics in ``observe`` and ``step``.
        """
        available = self._available_mask() if available is None else available
        context_color = self.context_color.gather(1, self.room_context[:, None])
        contextual = self.patch_color == context_color
        patterned = contextual & (self.food_shape == self.target_shape[:, None])
        return available & torch.where(
            (self.room < 2)[:, None], contextual,
            torch.where((self.room < 4)[:, None], patterned,
                        patterned & (self.room_context == self.context_required)[:, None]))

    def observe(self):
        delta = self.food - self.pos[:, None, :]
        dist = torch.linalg.vector_norm(delta, dim=2).clamp_min(1e-5)
        bearing = torch.atan2(delta[:, :, 1], delta[:, :, 0]) - self.heading[:, None]
        rel = torch.remainder(bearing + math.pi, 2 * math.pi) - math.pi
        pxang = torch.remainder(self.angles[None, None, :] + math.pi, 2 * math.pi) - math.pi
        width = self.params["pixel_width"]
        angular = torch.exp(-((torch.remainder(pxang - rel[:, :, None] + math.pi, 2 * math.pi) - math.pi) / width).square())
        room_float = self.room.float()
        visible = (dist < self.params["visibility_base"] + self.params["visibility_room_gain"] * room_float[:, None]).float()
        visible *= torch.exp(-dist * (self.params["visibility_decay"] - self.params["visibility_decay_room_gain"] * room_float[:, None]))
        available = self._available_mask()
        self.bite_mask = available & (dist < self.params["touch_radius"])
        strength = visible[:, :, None] * angular * available[:, :, None]
        shape_phase = ((self.food_shape.float()[:, :, None] + 1) * 2
                       * (pxang - rel[:, :, None])
                       + self.food_shape[:, :, None].float() * (math.pi / 2))
        texture = 0.2 + 0.8 * (0.5 + 0.5 * torch.cos(shape_phase))
        strength = torch.where((self.room >= 2)[:, None, None], strength * texture, strength)
        self.visible_mask = strength.amax(dim=2) > 0
        edible = self._edible_mask(available) & ~self.decoy
        channels = self.patch_color
        colors = torch.zeros(self.batch, self.MAX_PATCHES, self.params["color_count"], device=self.device)
        colors.scatter_(2, channels[:, :, None], 1.0)
        eye = (strength[:, :, :, None] * colors[:, :, None, :]).amax(dim=1)

        high_width = width * self.PIXELS / (self.PIXELS + 2 * self.room.float())
        high_pxang = torch.remainder(self.retina_angles[None, None, :] + math.pi, 2 * math.pi) - math.pi
        high_angular = torch.exp(-((torch.remainder(high_pxang - rel[:, :, None] + math.pi, 2 * math.pi) - math.pi) / high_width[:, None, None]).square())
        high_strength = visible[:, :, None] * high_angular * available[:, :, None]
        high_phase = ((self.food_shape.float()[:, :, None] + 1) * 2
                      * (high_pxang - rel[:, :, None])
                      + self.food_shape[:, :, None].float() * (math.pi / 2))
        high_texture = 0.2 + 0.8 * (0.5 + 0.5 * torch.cos(high_phase))
        high_strength = torch.where((self.room >= 2)[:, None, None],
                                    high_strength * high_texture, high_strength)
        eye_high = (high_strength[:, :, :, None] * colors[:, :, None, :]).amax(dim=1)
        eye_high = F.interpolate(eye_high.transpose(1, 2), size=self.PIXELS, mode="linear", align_corners=False).transpose(1, 2)
        eye = torch.where((self.room >= self.params["high_resolution_room"])[:, None, None], eye_high, eye)

        pixels = torch.arange(self.PIXELS, device=self.device)
        cue_mask = (pixels < 4)[None, :]
        cue = ((pixels[None, :] + self.room_context[:, None]) % 2 == 0).float()
        eye[:, :, 1] = torch.where((self.room >= 0)[:, None] & cue_mask,
                                   torch.maximum(eye[:, :, 1], cue * 0.8), eye[:, :, 1])

        sites = torch.arange(self.MAX_PATCHES, device=self.device) < 4
        landmark = (torch.exp(-dist / 0.5)[:, :, None] * angular
                    * (dist < 1.5)[:, :, None] * sites[None, :, None])
        landmark = landmark.amax(dim=1)
        eye[:, :, 2] = torch.where((self.room == self.ROOMS - 1)[:, None],
                                   torch.maximum(eye[:, :, 2], landmark), eye[:, :, 2])

        shadow_delta = self.shadow - self.pos
        shadow_dist = torch.linalg.vector_norm(shadow_delta, dim=1).clamp_min(1e-5)
        shadow_bearing = torch.atan2(shadow_delta[:, 1], shadow_delta[:, 0]) - self.heading
        shadow_rel = torch.remainder(shadow_bearing + math.pi, 2 * math.pi) - math.pi
        shadow_width = self.params["shadow_pixel_width"]
        shadow_angular = torch.exp(-((torch.remainder(self.angles - shadow_rel[:, None] + math.pi, 2 * math.pi) - math.pi) / shadow_width).square())
        shadow_radius = (self.params["shadow_radius"] + self.params["shadow_room_gain"] * room_float).clamp(max=self.params["shadow_radius_cap"])
        looming = (shadow_radius / shadow_dist).clamp(max=1) * (shadow_dist < self.params["shadow_visibility"])
        shadow_eye = shadow_angular * looming[:, None] * (self.room > 0)[:, None]
        high_shadow_angular = torch.exp(-((torch.remainder(self.retina_angles - shadow_rel[:, None] + math.pi, 2 * math.pi) - math.pi) / shadow_width).square())
        high_radius = (self.params["shadow_radius"] + self.params["shadow_high_radius_gain"] * room_float).clamp(max=self.params["shadow_high_radius_cap"])
        high_looming = (high_radius / shadow_dist).clamp(max=1) * (shadow_dist < self.params["shadow_visibility"] + self.params["shadow_visibility_room_gain"] * room_float)
        high_shadow = F.interpolate((high_shadow_angular * high_looming[:, None] * (self.room > 0)[:, None])[:, None, :], size=self.PIXELS, mode="linear", align_corners=False)[:, 0]
        eye[:, :, 0] = torch.maximum(eye[:, :, 0], torch.where(
            (self.room >= self.params["high_resolution_room"])[:, None], high_shadow, shadow_eye))
        eye = torch.where(self.alive[:, None, None], eye, torch.zeros_like(eye)).flatten(1)
        if self.interoception:
            eye = torch.cat((eye, self.energy[:, None]), 1)
        return eye

    def step(self, motors):
        m = torch.as_tensor(motors, device=self.device, dtype=torch.float32).clamp(-1, 1)
        active = self.alive
        self.heading += self.params["turn_gain"] * m[:, 0]
        drive = m[:, 1]
        speed = torch.sign(drive) * (self.params["base_speed"] + self.params["speed_gain"] * drive.abs())
        self.pos += speed[:, None] * torch.stack((self.heading.cos(), self.heading.sin()), 1) * active[:, None]
        self.age += active
        room_float = self.room.float()
        decay_factor = torch.where(self.room == 0, self.params["room_zero_energy_factor"],
                                   1 + self.params["room_energy_linear_gain"] * room_float
                                   + self.params["room_energy_quadratic_gain"] * room_float.square())
        metabolic_cost = (self.params["energy_decay"] * self.params["energy_decay_factor"] * decay_factor
                           + self.params["move_cost"] * self.params["move_cost_factor"] * speed.abs()) * active
        # v7 starts with a finite developmental reserve (the yolk analogue).
        # It pays ordinary metabolism only; construction remains charged to
        # the organism's usable energy in the versioned body interface.
        if hasattr(self, "yolk"):
            covered = torch.minimum(self.yolk, metabolic_cost)
            self.yolk -= covered
            self.energy -= metabolic_cost - covered
            newly_empty = (self.yolk <= 0) & (self.yolk_depleted_at < 0)
            self.yolk_depleted_at = torch.where(newly_empty,
                                                torch.full_like(self.yolk_depleted_at, self.t),
                                                self.yolk_depleted_at)
        else:
            self.energy -= metabolic_cost

        dfood = torch.linalg.vector_norm(self.pos[:, None, :] - self.food, dim=2)
        available = self._available_mask()
        touching = (dfood < self.params["touch_radius"]) & (m[:, 2, None] > 0) & active[:, None]
        edible = self._edible_mask(available) & ~self.decoy
        self.bite_mask = available & (dfood < self.params["touch_radius"]) & active[:, None]
        eating = touching & edible
        decoy_bite = touching & (available & ~edible)
        gain = eating.any(dim=1)
        bite = (touching & available).any(dim=1)
        self.last_bite_index = torch.where(
            bite, touching.float().argmax(dim=1), torch.full_like(self.last_bite_index, -1))
        self.visits += gain
        patch_id = eating.float().argmax(dim=1)
        self.patch_transitions += gain & (self.last_patch >= 0) & (self.last_patch != patch_id)
        self.last_patch = torch.where(gain, patch_id, self.last_patch)
        self.patch_seen |= eating
        self.energy = torch.where(gain, (self.energy + self.params["food_gain"]).clamp(max=1), self.energy)
        after_adaptation = (self.flip_time >= 0) & ((self.t - self.flip_time) >= self.params["adaptation_steps"])
        self.flip_bites += bite.float() * after_adaptation
        self.flip_correct_bites += gain.float() * after_adaptation
        self.energy -= decoy_bite.any(dim=1).float() * (self.params["decoy_cost"] + self.params["decoy_room_cost"] * room_float)

        shadow_delta = self.shadow - self.pos
        shadow_dist = torch.linalg.vector_norm(shadow_delta, dim=1)
        shadow_hit = (shadow_dist < (self.params["shadow_radius"] + self.params["shadow_room_gain"] * room_float).clamp(max=self.params["shadow_radius_cap"])) & (self.room > 0) & active
        self.energy -= shadow_hit.float() * self.params["shadow_cost"]
        self.escape_events += shadow_hit
        side = self._side()
        relocation = self.params["shadow_relocation_factor"]
        self.shadow = torch.where(shadow_hit[:, None],
                                  self.rand(self.batch, 2) * (side[:, None] * 2 * relocation)
                                  - side[:, None] * relocation, self.shadow)

        depleted = eating | decoy_bite
        self.patch_energy = torch.where(depleted, torch.zeros_like(self.patch_energy), self.patch_energy)
        delay = self.params["regrow_base"] + self.params["regrow_room_gain"] * self.room[:, None] + self.params["regrow_level_gain"] * room_float[:, None]
        self.regrow = torch.where(depleted, delay, (self.regrow - 1).clamp_min(0))
        regrown = self._active_mask() & (self.regrow == 0) & (self.patch_energy == 0)
        self.patch_energy = torch.where(regrown, torch.ones_like(self.patch_energy), self.patch_energy)

        flip = (torch.tensor(self.REVERSAL_TIMES, device=self.device) == self.t).any() & active
        if flip.any():
            next_context = 1 - self.room_context
            self.room_context = torch.where(flip, next_context, self.room_context)
            next_color = self.context_color.gather(1, next_context[:, None])[:, 0]
            self.food_channel = torch.where(flip, next_color, self.food_channel)
            self.flip_time = torch.where(flip, torch.full_like(self.flip_time, self.t), self.flip_time)
            self.flip_bites = torch.where(flip, torch.zeros_like(self.flip_bites), self.flip_bites)
            self.flip_correct_bites = torch.where(flip, torch.zeros_like(self.flip_correct_bites), self.flip_correct_bites)

        self.energy_window += self.energy * active
        self.window_n += active
        dwell = torch.tensor(self.ROOM_DWELL, device=self.device)[self.room]
        required_bites = torch.tensor(self.params["required_bites"], device=self.device)[self.room]
        minimum_time = torch.where(self.room == 0, self.params["minimum_time_first"], self.params["minimum_time_later"])
        selectivity = self.flip_correct_bites / self.flip_bites.clamp_min(1)
        window = self.params["energy_window_steps"]
        if hasattr(self, "body_pixels"):
            required_pixels = torch.tensor((2, 3, 4, 6, 8, 12), device=self.device)[self.room]
            required_motors = torch.tensor((1, 1, 2, 3, 4, 5), device=self.device)[self.room]
            body_ready = (self.body_pixels >= required_pixels) & (self.body_motors >= required_motors)
        else:
            body_ready = torch.ones_like(active)
        mastery = ((self.t >= minimum_time) & (self.t % window == window - 1)
                   & (self.window_n >= window) & (self.room_age >= dwell)
                   & (self.flip_bites >= required_bites) & (selectivity >= self.params["selectivity_threshold"])
                   & body_ready
                   & active)
        mastered_now = mastery & (self.flip_time >= 0)
        self.mastered_colors.scatter_(1, self.food_channel[:, None],
                                      self.mastered_colors.gather(1, self.food_channel[:, None]) | mastered_now[:, None])
        required_reversals = torch.tensor(self.params["required_reversals"], device=self.device)[self.room]
        color_count = self.mastered_colors.sum(1)
        advance = mastery & (color_count >= required_reversals) & (self.room < self.ROOMS - 1)
        for level in range(1, self.ROOMS):
            new = advance & (self.room == level - 1)
            new_n = self.FOOD_COUNTS[level]
            self.room_time[:, level] = torch.where(new, torch.full_like(self.room_time[:, level], self.t), self.room_time[:, level])
            self.food[:, :new_n] = torch.where(new[:, None, None], self._room_positions(level), self.food[:, :new_n])
            self.patch_energy[:, :new_n] = torch.where(new[:, None], torch.ones_like(self.patch_energy[:, :new_n]), self.patch_energy[:, :new_n])
            self.regrow[:, :new_n] = torch.where(new[:, None], torch.zeros_like(self.regrow[:, :new_n]), self.regrow[:, :new_n])
            if level >= 1:
                fresh_color = (self.rand(self.batch, new_n) * self.params["color_count"]).long()
                self.patch_color[:, :new_n] = torch.where(new[:, None], fresh_color, self.patch_color[:, :new_n])
                first_color = (self.rand(self.batch) * self.params["color_count"]).long()
                second_color = (first_color + 1 + (self.rand(self.batch) > 0.5).long()) % self.params["color_count"]
                self.context_color[:, 0] = torch.where(new, first_color, self.context_color[:, 0])
                self.context_color[:, 1] = torch.where(new, second_color, self.context_color[:, 1])
            if level >= 2:
                fresh_shape = (self.rand(self.batch, new_n) * level).long()
                fresh_color = (self.rand(self.batch, new_n) * self.params["color_count"]).long()
                target_shape = (self.rand(self.batch) * level).long()
                target_color = (self.rand(self.batch) * self.params["color_count"]).long()
                context = (self.rand(self.batch) > 0.5).long()
                self.food_shape[:, :new_n] = torch.where(new[:, None], fresh_shape, self.food_shape[:, :new_n])
                self.patch_color[:, :new_n] = torch.where(new[:, None], fresh_color, self.patch_color[:, :new_n])
                self.food_shape[:, 0] = torch.where(new, target_shape, self.food_shape[:, 0])
                self.food_shape[:, 1] = torch.where(new, target_shape, self.food_shape[:, 1])
                self.patch_color[:, 0] = torch.where(new, target_color, self.patch_color[:, 0])
                self.patch_color[:, 1] = torch.where(new, target_color, self.patch_color[:, 1])
                self.target_shape = torch.where(new, target_shape, self.target_shape)
                self.target_color = torch.where(new, target_color, self.target_color)
                self.room_context = torch.where(new, context, self.room_context)
                self.context_required = torch.where(new, context, self.context_required)
                other_color = (target_color + 1 + (self.rand(self.batch) > 0.5).long()) % self.params["color_count"]
                map_zero = torch.where(context == 0, target_color, other_color)
                map_one = torch.where(context == 1, target_color, other_color)
                self.context_color[:, 0] = torch.where(new, map_zero, self.context_color[:, 0])
                self.context_color[:, 1] = torch.where(new, map_one, self.context_color[:, 1])
                self.patch_color[:, 0] = torch.where(new, map_zero, self.patch_color[:, 0])
                self.patch_color[:, 1] = torch.where(new, map_one, self.patch_color[:, 1])
            else:
                target_color = self.context_color.gather(1, self.room_context[:, None])[:, 0]
                self.target_color = torch.where(new, target_color, self.target_color)
            current_color = self.context_color.gather(1, self.room_context[:, None])[:, 0]
            self.food_channel = torch.where(new, current_color, self.food_channel)
            probability = self.params["decoy_probability"][level]
            fresh_decoys = self.rand(self.batch, new_n) < probability
            fresh_decoys[:, 0] = False
            if level < 2:
                fresh_decoys[:, 1] = False
            self.decoy[:, :new_n] = torch.where(new[:, None], fresh_decoys, self.decoy[:, :new_n])
        self.room = torch.where(advance, self.room + 1, self.room)
        if bool(advance.any()) and bool((self.room >= self.ROOMS).any()):
            bad = self.room[self.room >= self.ROOMS].detach().cpu().tolist()
            raise RuntimeError(f"room transition exceeded {self.ROOMS} rooms: {bad[:8]}")
        self.mastered_colors = torch.where(advance[:, None], torch.zeros_like(self.mastered_colors), self.mastered_colors)
        self.room_age = torch.where(advance, torch.zeros_like(self.room_age), self.room_age)
        side = self._side()
        self.pos = torch.maximum(torch.minimum(self.pos, side[:, None] / 2), -side[:, None] / 2)
        dead = (self.energy <= 0) & active
        self.alive &= ~dead
        self.energy.clamp_(min=0)
        self.room_age += active.long()
        if self.t % window == window - 1:
            self.energy_window.zero_()
            self.window_n.zero_()
        self.t += 1
        self.last_gain = gain
        self.last_bite = bite
        return gain
