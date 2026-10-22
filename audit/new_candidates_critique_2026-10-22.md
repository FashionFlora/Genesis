# Audit: late leaderboard candidates

## `resource_flow_snake` (entry 37)

Score `5.9748`, level-3 gate `35.3814`, robustness `0.5489`. `step` returns constant `0.5` (lines 10--11). `act` reads direction, head, body, and apple from the full Snake observation and runs BFS to the apple (lines 13--43). `last_mass` is set to `len(blocked)+1` from that observation (line 44). There is no resource flow, learning, growth, pruning, or memory-derived controller.

## `coactivity_support` (entries 42--43)

Scores `21.7667` and `21.2745`, below the level-1 gate `26.2524`. The candidate maintains a full `width x width x 2` count tensor (lines 16--24), so state is unbounded in channel width and every possible edge is evaluated retrospectively. Prediction metrics match the online baseline exactly (`0.190234`, `0.190837`, `0.193257` mean Brier per seed). `structure()` reports `edges` as the count of all gaps above a fixed `0.3` threshold (line 32), without creating or pruning contacts. The score gain is a structural proxy readout, not demonstrated structural learning.

## `axiom_predictive_homeostasis` (entry 44)

Score `4.9227`, below gate `26.2524`, with elegance multiplier `0.1` (72 numeric literals, 67 physical lines). It stores complete fast/slow pair matrices plus transition counts (lines 17--21), never births or removes a contact, and reports a continuous sum of gaps as connections (lines 60--67). Mean Brier `0.2097` is worse than online baseline `0.1914`; the added `learning_improvement` field is not part of the standard score contract and does not establish a causal mechanism.
