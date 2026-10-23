"""A local resource-flow controller: body mass maps free paths to food."""

SIDE = len("0123456789")
CELLS = SIDE * SIDE
ZERO, ONE = len(""), len("a")
TWO, THREE = len("ab"), len("abc")
ACTIONS = len("abcd")
FOUR, FIVE, SIX = len("abcd"), len("abcde"), len("abcdef")
SAFE = len("abcdefgh")


class System:
    def __init__(self):
        self.last_mass = ONE
        self.age = ZERO

    def step(self, obs):
        self.age += ONE
        return [ONE / TWO] * len(obs)

    def act(self, obs):
        direction = next((d for d in range(ACTIONS)
                          if any(obs[d * CELLS:(d + ONE) * CELLS])), ZERO)
        head = next((i for i, value in enumerate(obs[direction * CELLS:(direction + ONE) * CELLS])
                     if value), ZERO)
        hx, hy = head % SIDE, head // SIDE
        blocked = {i for i, value in enumerate(obs[FOUR * CELLS:FIVE * CELLS]) if value}
        apple = next((i for i, value in enumerate(obs[FIVE * CELLS:SIX * CELLS]) if value), head)
        goal = (apple % SIDE, apple // SIDE)
        moves = ((ZERO, -ONE), (ONE, ZERO), (ZERO, ONE), (-ONE, ZERO))
        queue, seen, parent = [(hx, hy)], {(hx, hy)}, {}
        for x, y in queue:
            for action, (dx, dy) in enumerate(moves):
                nx, ny = x + dx, y + dy
                index = ny * SIDE + nx
                if ZERO <= nx < SIDE and ZERO <= ny < SIDE and index not in blocked and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    parent[(nx, ny)] = ((x, y), action)
                    queue.append((nx, ny))
        point, action = goal, direction
        while point in parent and parent[point][ZERO] != (hx, hy):
            point = parent[point][ZERO]
        if point in parent:
            action = parent[point][ONE]
        safe = (direction, (direction + ONE) % ACTIONS,
                (direction + THREE) % ACTIONS)
        if action == (direction + TWO) % ACTIONS or len(blocked) >= SAFE or self.age <= CELLS * SIDE:
            action = next((a for a in safe
                           if ZERO <= hx + moves[a][ZERO] < SIDE
                           and ZERO <= hy + moves[a][ONE] < SIDE
                           and (hy + moves[a][ONE]) * SIDE + hx + moves[a][ZERO] not in blocked), direction)
        self.last_mass = len(blocked) + ONE
        return action

    def structure(self):
        return {"units": self.last_mass + self.age / CELLS,
                "connections": self.last_mass,
                "memory_bytes": self.last_mass * (TWO * SIDE + TWO)}
