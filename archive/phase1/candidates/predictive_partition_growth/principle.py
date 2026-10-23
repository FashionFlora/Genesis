"""A predictive distinction creates a context split; lost distinction merges it."""

PARAMS = {"window": 64.0, "probe": 4.0, "split": 0.04}


class System:
    def __init__(self):
        self.width = 0
        self.previous = None
        self.history = []
        self.splits = {}
        self.tick = 0

    @staticmethod
    def _pack(values):
        packed = bytearray((len(values) + 7) // 8)
        for index, value in enumerate(values):
            packed[index // 8] |= int(value) << (index % 8)
        return bytes(packed)

    @staticmethod
    def _bit(packed, index):
        return (packed[index // 8] >> (index % 8)) & 1

    @staticmethod
    def _prob(rows, feature, target, state):
        count = 0
        ones = 0.0
        for before, after in rows:
            if System._bit(before, feature) == state:
                count += 1
                ones += System._bit(after, target)
        return (ones + 1.0) / (count + 2.0)

    @staticmethod
    def _validated_loss(training, evaluation, feature, target):
        counts = [[0, 0.0], [0, 0.0]]
        for before, after in training:
            state = System._bit(before, feature)
            counts[state][0] += 1
            counts[state][1] += System._bit(after, target)
        total = 0.0
        for before, after in evaluation:
            count, ones = counts[System._bit(before, feature)]
            p = (ones + 1.0) / (count + 2.0)
            total += (System._bit(after, target) - p) ** 2
        return total / max(1, len(evaluation))

    def _rebuild(self):
        rows = self.history
        if len(rows) < 4:
            return
        boundary = len(rows) // 2
        training, evaluation = rows[:boundary], rows[boundary:]
        updated = {}
        for target in range(self.width):
            parent_train = self._validated_loss(training, training, target, target)
            best = None
            for source in range(self.width):
                if source == target:
                    continue
                fit_loss = self._validated_loss(training, training, source, target)
                gain = parent_train - fit_loss
                if best is None or gain > best[0]:
                    best = (gain, source)
            if best is not None:
                parent_test = self._validated_loss(training, evaluation, target, target)
                split_test = self._validated_loss(training, evaluation, best[1], target)
                if parent_test - split_test > PARAMS["split"]:
                    updated[target] = best[1]
        self.splits = updated

    def step(self, obs):
        if self.previous is None:
            self.width = len(obs)
            self.previous = list(obs)
            return [0.5] * self.width

        old = self.previous
        self.history.append((self._pack(old), self._pack(obs)))
        self.history = self.history[-max(1, int(PARAMS["window"])):]
        self.tick += 1
        if self.tick % max(1, int(PARAMS["probe"])) == 0:
            self._rebuild()

        prediction = []
        for target in range(self.width):
            source = self.splits.get(target, target)
            state = int(old[source])
            prediction.append(self._prob(self.history, source, target, state))
        self.previous = list(obs)
        return prediction

    def structure(self):
        splits = len(self.splits)
        return {"units": self.width + 2 * splits, "connections": 2 * splits,
                "memory_bytes": self.width * 8
                + len(self.history) * 2 * ((self.width + 7) // 8)
                + splits * 16}
