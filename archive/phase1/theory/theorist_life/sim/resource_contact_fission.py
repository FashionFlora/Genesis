"""Test whether local source-outcome contact can seed resource-funded variants."""
import json
import random
from pathlib import Path
from statistics import mean

from resource_flux_tagged_fission import Cell, observe, poisson, run as random_tag_run


def run(seed, *, steps=4000, segment_length=800, schedule=(0, 3, 7, 11, 0),
        source_count=12, initial_population=90, initial_sources=(0, 1, 2),
        substrate_inflow=7.7625, maintenance=0.10, error_cost=0.25,
        flip_probability=0.08):
    env = random.Random(seed ^ 0xE17A)
    ecology = random.Random(seed ^ 0xC011)
    inflow = random.Random(seed ^ 0xF10A)
    routing = random.Random(seed ^ 0xA110)
    cells = [Cell(initial_sources[i % len(initial_sources)])
             for i in range(initial_population)]
    ecology.shuffle(cells)
    trace = []
    for t in range(steps):
        phase = min(t // segment_length, len(schedule) - 1)
        active = schedule[phase]
        x, y = observe(env, source_count, active, flip_probability)
        errors = [float(x[cell.source] != y) for cell in cells]
        n = len(cells)
        count = poisson(inflow, substrate_inflow) if n else 0
        intake = [0] * n
        labels = [None] * n
        contacts = [s for s, bit in enumerate(x) if bit == y]
        for _ in range(count):
            idx = int(routing.random() * n)
            intake[idx] += 1
            if contacts:
                labels[idx] = contacts[routing.randrange(len(contacts))]
        survivors = []
        for i, cell in enumerate(cells):
            mass = cell.mass + intake[i] - maintenance - error_cost * errors[i]
            if mass <= 0:
                continue
            lineage = [Cell(cell.source, mass)]
            for parent in lineage:
                while parent.mass >= 2:
                    parent.mass /= 2
                    lineage.append(Cell(labels[i] if labels[i] is not None else parent.source,
                                        parent.mass))
            survivors.extend(lineage)
        cells = survivors
        if t % 20 == 19 or t == steps - 1:
            counts = [sum(cell.source == s for cell in cells)
                      for s in range(source_count)]
            trace.append({"step": t + 1, "phase": phase, "active": active,
                          "match": counts[active] / len(cells) if cells else 0,
                          "mse": mean(errors) if errors else 0.5})
    return trace


def score(trace, phase, segment_length=800):
    return mean(row["match"] for row in trace
                if row["phase"] == phase and phase * segment_length + 100
                <= row["step"] <= phase * segment_length + 300)


def main():
    from compare_h005_hebb import hebb, window
    schedule = (0, 3, 7, 11, 0)
    paired = []
    for seed in range(10):
        contacted = run(seed, schedule=schedule)
        random_tagged = random_tag_run(
            seed, "selected_tagged_fission", steps=4000, segment_length=800,
            schedule=schedule, source_count=12, initial_population=90,
            initial_sources=(0, 1, 2), substrate_inflow=7.7625,
            maintenance=0.10, error_cost=0.25, flip_probability=0.08)
        hb = hebb(seed, 4000, 800, schedule, 12, 0.08)
        for phase in range(1, len(schedule)):
            start = phase * 800
            hb_window = [row["correct"] for row in window(hb, phase, 800)]
            paired.append({"seed": seed, "phase": phase,
                           "contact_flow_match": score(contacted, phase),
                           "random_tag_flow_match": mean(
                               item["matching_source_fraction"]
                               for item in random_tagged["trace"]
                               if item["phase"] == phase and start + 100 <= item["step"] <= start + 300),
                           "hebb_match": mean(hb_window)})
    summary = {key: mean(row[key] for row in paired) for key in paired[0]
               if key not in {"seed", "phase"}}
    result = {"world": {"sources": 12, "schedule": list(schedule),
                        "segment_length": 800, "seeds": 10},
              "summary": summary, "paired": paired}
    path = Path(__file__).with_name("resource_contact_fission_results.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
