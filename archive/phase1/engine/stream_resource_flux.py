"""H003 population agents for the shared reward-free sensory stream."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp
import random
import sys


SOURCE_COUNT = 3
TARGET_CHANNEL = 7
MAINTENANCE = 0.10
ERROR_COST = 0.25
BASE_INFLOW = 7.3125
BASE_MUTATION_RATE = 0.05


@dataclass
class Cell:
    source: int
    positive: list[int]
    seen: list[int]
    mass: float = 1.0

    def predict(self, source_value: int) -> float:
        return (self.positive[source_value] + 1.0) / (self.seen[source_value] + 2.0)

    def observe(self, source_value: int, target_value: int) -> None:
        self.seen[source_value] += 1
        self.positive[source_value] += target_value

    def offspring(self, rng: random.Random, mutation_rate: float, daughter_mass: float):
        source = self.source
        positive = self.positive.copy()
        seen = self.seen.copy()
        if rng.random() < mutation_rate:
            alternatives = [candidate for candidate in range(SOURCE_COUNT)
                            if candidate != source]
            source = rng.choice(alternatives)
            positive = [0, 0]
            seen = [0, 0]
        return Cell(source, positive, seen, daughter_mass), source != self.source


def _poisson(rng: random.Random, rate: float) -> int:
    """Knuth's exact Poisson sampler for the small resource inflows here."""
    if rate <= 0.0:
        return 0
    limit = exp(-rate)
    product = 1.0
    count = 0
    while product > limit:
        count += 1
        product *= rng.random()
    return count - 1


class ResourceFluxPopulation:
    """Cells persist, split, or die by the same local resource balance."""

    condition_name = "selected"
    inflow_scale = 1.0
    mutation_rate = BASE_MUTATION_RATE

    def __init__(self, input_dim=8, output_dim=8, seed=0):
        if input_dim < SOURCE_COUNT or output_dim <= TARGET_CHANNEL:
            raise ValueError("H003 needs sources 0..2 and target channel 7")
        self.input_dim = int(input_dim)
        self.output_dim = int(output_dim)
        self.inflow = BASE_INFLOW * self.inflow_scale
        self.condition = self.condition_name
        self.ecology_rng = random.Random(int(seed) ^ 0xC011)
        self.resource_rng = random.Random(int(seed) ^ 0xF10A)
        self.cells = [Cell(index % SOURCE_COUNT, [0, 0], [0, 0], 1.0)
                      for index in range(45)]
        self.ecology_rng.shuffle(self.cells)
        self.growth_events = 0
        self.death_events = 0
        self.mutation_events = 0
        self.resource_packets = 0
        self.error_resource_cost = 0.0
        self.cell_error_step_sum = 0.0
        self.cell_error_steps = 0
        self.extinct_at_step = None
        self.samples = 0
        self.work_units = 0

    def predict(self, observation):
        values = [int(float(value) >= 0.5) for value in observation]
        predictions = [0.5] * self.output_dim
        if self.cells:
            predictions[TARGET_CHANNEL] = sum(
                cell.predict(values[cell.source]) for cell in self.cells
            ) / len(self.cells)
        self.work_units += 4 * len(self.cells) + self.output_dim
        return predictions

    def observe(self, observation, next_observation):
        sources = [int(float(value) >= 0.5) for value in observation]
        target = int(float(next_observation[TARGET_CHANNEL]) >= 0.5)
        errors = [
            (cell.predict(sources[cell.source]) - target) ** 2
            for cell in self.cells
        ]
        mean_error = sum(errors) / len(errors) if errors else 0.25
        self.cell_error_step_sum += mean_error
        self.cell_error_steps += 1
        if self.cells:
            packet_count = _poisson(self.resource_rng, self.inflow)
            self.resource_packets += packet_count
            intake = [0] * len(self.cells)
            for _ in range(packet_count):
                intake[self.resource_rng.randrange(len(self.cells))] += 1
            self.error_resource_cost += ERROR_COST * sum(errors)
            for cell in self.cells:
                source_value = sources[cell.source]
                cell.observe(source_value, target)

            survivors = []
            step_births = 0
            step_deaths = 0
            step_mutations = 0
            for index, parent in enumerate(self.cells):
                loss = errors[index] if self.condition == "selected" else mean_error
                new_mass = parent.mass + intake[index] - MAINTENANCE - ERROR_COST * loss
                if new_mass <= 0.0:
                    step_deaths += 1
                    continue
                parent.mass = new_mass
                lineage = [parent]
                lineage_index = 0
                while lineage_index < len(lineage):
                    cell = lineage[lineage_index]
                    if cell.mass >= 2.0:
                        daughter_mass = cell.mass / 2.0
                        cell.mass = daughter_mass
                        child, mutated = cell.offspring(
                            self.ecology_rng, self.mutation_rate, daughter_mass
                        )
                        lineage.append(child)
                        step_births += 1
                        step_mutations += int(mutated)
                    lineage_index += 1
                survivors.extend(lineage)
            self.cells = survivors
            self.growth_events += step_births
            self.death_events += step_deaths
            self.mutation_events += step_mutations
            if not self.cells and self.extinct_at_step is None:
                self.extinct_at_step = self.samples + 1
            self.work_units += 12 * len(errors) + 2 * packet_count + 10 * len(survivors)
        self.samples += 1

    def structure_metrics(self):
        counts = [sum(cell.source == source for cell in self.cells)
                  for source in range(SOURCE_COUNT)]
        source_mass = [sum(cell.mass for cell in self.cells if cell.source == source)
                       for source in range(SOURCE_COUNT)]
        population = len(self.cells)
        mean_mass = sum(cell.mass for cell in self.cells) / population if population else 0.0
        # This is a Python-object estimate, intentionally reported alongside RSS/CPU.
        state_bytes = sys.getsizeof(self.cells)
        for cell in self.cells:
            state_bytes += sys.getsizeof(cell) + sys.getsizeof(cell.positive) + sys.getsizeof(cell.seen)
            state_bytes += sum(sys.getsizeof(value) for value in cell.positive + cell.seen)
            state_bytes += sys.getsizeof(cell.mass) + sys.getsizeof(cell.source)
        return {
            "condition": self.condition,
            "substrate_inflow": self.inflow,
            "mutation_rate": self.mutation_rate,
            "maintenance": MAINTENANCE,
            "error_cost": ERROR_COST,
            "unit_count": self.input_dim + self.output_dim + population,
            "connection_count": population,
            "connection_instances": population,
            "distinct_connections": sum(count > 0 for count in counts),
            "source_edge_counts": counts,
            "source_resource_mass": source_mass,
            "population": population,
            "mean_cell_mass": mean_mass,
            "total_resource_mass": sum(cell.mass for cell in self.cells),
            "growth_events": self.growth_events,
            "pruning_events": self.death_events,
            "births": self.growth_events,
            "deaths": self.death_events,
            "mutations": self.mutation_events,
            "resource_packets": self.resource_packets,
            "error_resource_cost": self.error_resource_cost,
            "mean_cellwise_prediction_mse": (
                self.cell_error_step_sum / self.cell_error_steps
                if self.cell_error_steps else None
            ),
            "extinct_at_step": self.extinct_at_step,
            "work_units": self.work_units,
            "estimated_state_bytes": state_bytes,
        }


class ResourceSelected(ResourceFluxPopulation):
    condition_name = "selected"


class ResourceNeutral(ResourceFluxPopulation):
    condition_name = "neutral_random_mutation"


class ResourceNeutralHighMutation(ResourceFluxPopulation):
    condition_name = "neutral_matched_mutation"
    mutation_rate = 0.15


class ResourceSelectedLowSupply(ResourceSelected):
    inflow_scale = 0.9


class ResourceNeutralLowSupply(ResourceNeutral):
    inflow_scale = 0.9


class ResourceNeutralHighMutationLowSupply(ResourceNeutralHighMutation):
    inflow_scale = 0.9


class ResourceSelectedHighSupply(ResourceSelected):
    inflow_scale = 1.1


class ResourceNeutralHighSupply(ResourceNeutral):
    inflow_scale = 1.1


class ResourceNeutralHighMutationHighSupply(ResourceNeutralHighMutation):
    inflow_scale = 1.1
