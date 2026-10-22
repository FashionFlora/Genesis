# Novelty audit procedure

## 1. Freeze the candidate
Record the claimed contribution in one sentence, the intended scope, date, and author. Preserve the exact update equation/pseudocode, signal path, architecture, assumptions, and any code commit. Separate claims about novelty from claims about performance or usefulness.

## 2. Search the registry first
Run `python3 audit/search.py "<candidate description>" --top 10`. Inspect the returned records, including their cited sources; similarity ranks are leads, not evidence of identity or novelty. Search distinctive terms from `principle` and `learning_rule`, and inspect adjacent areas because a method may be described under a different label.

## 3. Compare mechanisms, not names
For each nearest method, compare side by side:
- state and parameterization; what is stored/updated;
- exact update equation, target, optimizer, and temporal order;
- source of each learning signal (external reward, intrinsic signal, prediction target, labels);
- credit assignment and gradient path (including gradients through a learned representation or controller);
- exploration/action-selection mechanism and environment assumptions;
- components that are essential versus replaceable.

Open the primary paper (full text when possible) and official implementation for consequential claims. Record exact citations/URLs and what was verified. An abstract may establish the authors' stated aim but usually not implementation details or benchmark table values. Check a Crafter result only in the cited paper's table and record its table number. Distinguish absent evidence from evidence of absence.

## 4. Verify factual claims
Check source identity, title, authors/year, and that the cited work actually describes the claimed mechanism. Check `uses_backprop` narrowly: identify precisely which components are gradient-trained, and distinguish “no backprop through the policy” from “no backprop anywhere.” Check external reward use separately from intrinsic rewards, demonstrations, labels, or task-provided termination. Benchmark claims require matching environment, metric, evaluation protocol, and table/figure; do not infer Crafter performance from another benchmark.

## 5. Controls that test substantive novelty
When practical, compare under the same environment, data, compute, and tuning budget:
1. the nearest known method reproduced faithfully;
2. candidate with only its claimed novel component removed/replaced;
3. candidate expressed as the nearest method's equation/parameterization, to test whether it is a reparameterization;
4. relevant signal ablations (external reward, intrinsic signal, prediction target) and gradient-path ablations;
5. multiple seeds and uncertainty reporting for empirical claims.
A performance gain alone does not establish algorithmic novelty; a renamed component or changed hyperparameter is not a new learning rule. Conversely, a meaningful difference in update dynamics or assumptions can be novel even before it proves useful.

## 6. Verdicts
- `known`: a prior source contains the material mechanism/claim; state the overlap and any difference.
- `partial`: prior art covers a substantial part, but a specific residual distinction remains; articulate and verify that distinction.
- `not_found`: no close prior art found within the stated queries/sources/scope. This is not proof of priority or universal absence.
For each claim, store exact search queries, searched scope/date, opened sources, and a concise rationale in `audit/claims.jsonl`. For record errors, contact the responsible area author and add a factual entry to `audit/registry_check.jsonl`; do not silently edit their records.

## Checklist before announcing novelty
- [ ] Claim is specific and falsifiable, not “first ever” without a bounded search.
- [ ] Exact equation/update sequence and all learning signals are documented.
- [ ] Nearest registry matches and cross-area terminology were checked.
- [ ] Primary sources were opened; citations support the stated comparison.
- [ ] Gradient paths and external reward use were checked component-by-component.
- [ ] Crafter numbers, if any, come from a named paper table.
- [ ] Difference from prior art is mechanistic and explicit; reparameterization controls considered.
- [ ] Verdict scope, queries, date, evidence gaps, and author response are logged.
- [ ] Novelty, correctness, and empirical value are reported as separate judgments.
