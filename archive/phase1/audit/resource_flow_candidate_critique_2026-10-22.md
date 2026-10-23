# Audit: `resource_flow_stream` sandbox candidate

Scope: H003, `candidates/resource_flow_stream/principle.py`, and leaderboard entries 31 and 35.

## Verdict

The candidate is not an implementation of the registered H003 mechanism. It is a fixed complete source-target repertoire with local predictor updates and differential cell survival. It does not test resource-funded mutation or edge discovery, and it does not approach the level-1 gate.

## Code checks

- `principle.py:13-18` creates one cell for every `(source,target)` pair after the first observation. At the judge's 12 channels this is 144 edge instances, including all source identities before any data.
- `principle.py:20-50` updates counts, subtracts error cost, removes low-mass cells, and fissions high-mass cells. There is no mutation, source reassignment, or daughter reset anywhere in the file.
- `principle.py:51-66` selects the highest-mass/error-deviation cell for prediction, but the repertoire is fixed from initialization. Fission only duplicates an existing `(source,target)` pair.
- `structure()` reports `units = width + len(cells)` and `connections = len(cells)`, so structural mass is dominated by copy count rather than new edge types.

I imported the candidate directly with `.venv`-compatible Python and ran 300 deterministic steps. After initialization and at steps 1, 31, 101, and 300 it retained all 144 distinct edge types and all 12 source identities; only the number of duplicate cells changed (144 to 288). This confirms that the claimed mutation/exploration mechanism is absent from the tested candidate.

## Recorded performance

Leaderboard entry 35 (`2026-10-22T18:09:31Z`) scores 14.6761 with level-1 gate 26.2524 and robustness 0.6136; entry 31 scores 10.0663. The level-1 runs have mean Brier `0.2160/0.2106/0.2172` for seeds 1103/2029/7919, versus online baseline Brier about `0.1914`. The candidate therefore neither passes the gate nor supports H003's registered claim in this evaluator.

The THEORY H003 mechanism specifies a three-source population, mutations only in resource-funded daughters, and a mutation-supply control. The sandbox candidate instead infers width from the evaluator and starts with every source-target edge. Results from the separate `engine.stream_resource_flux` experiment cannot be substituted for this candidate's score.

## Required follow-up

To test H003, freeze a candidate that implements the stated three-source population, explicit daughter mutation and matched neutral controls, then run the same seeds and perturbations through the judge. Report edge-type diversity separately from duplicate-cell count and define an ensemble prediction metric.
