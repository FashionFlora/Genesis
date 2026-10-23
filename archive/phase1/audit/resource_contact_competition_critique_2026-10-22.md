# Audit: `resource_contact_competition` (2026-10-22)

The new leaderboard rows 151 and 152 score about 15.307 with level 1
`passed=false` and robustness about 0.642. The candidate is a close
mechanical variant of `resource_flow_competition`, not a new structural law.

`principle.py:15-18` materializes every `(source,target)` pair at first use,
so all `width**2` contact types exist before observations. The fission loop
at lines 42-45 copies the existing source and target labels; there is no
mutation, proposal, or route to create an absent edge type. Mass-dependent
decay (`decay ** (1 / mass)`) changes retention speed, but does not change
the repertoire. The predictor still selects a maximum-scoring existing
contact, and `structure()` reports contact multiplicity rather than distinct
connectivity.

This is an incremental parameter/mechanism combination over the already
critiqued resource-flow family. It should not be presented as evidence for
open-ended edge discovery or a one-principle account. The level-1 failure is
consistent with that limitation. No judge or sandbox file was modified by
this audit.
