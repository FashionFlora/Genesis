# Schemat rekordu (`algorithms.jsonl`, jedna linia = jeden obiekt)

```json
{
  "id": "rnd",
  "name": "Random Network Distillation",
  "area": "intrinsic_motivation",
  "family": "prediction-error curiosity",
  "year": 2018,
  "sources": [{"title": "...", "arxiv": "1810.12894", "url": "https://arxiv.org/abs/1810.12894"}],
  "principle": "1-3 zdania: na czym polega",
  "learning_rule": "równanie / pseudokod reguły aktualizacji (LaTeX dozwolony)",
  "learning_signals": ["intrinsic: błąd predykcji losowej sieci", "..."],
  "uses_extrinsic_reward": "no | optional | yes",
  "uses_backprop": "yes | partial | no",
  "backprop_notes": "co dokładnie jest uczone gradientem, a co nie",
  "benchmarks": [{"env": "Crafter", "metric": "score %", "value": 0.0, "source": "arXiv ... Tabela N"}],
  "limitations": ["..."],
  "code": [{"url": "https://github.com/...", "official": true}],
  "related": ["icm", "ngu"],
  "meets_genesis_criteria": "both | no_reward_only | no_backprop_only | neither",
  "self_building": "czy architektura sama rośnie/zmienia strukturę (neurony, połączenia, moduły) w trakcie uczenia: yes | partial | no",
  "brain_relevance": "1-2 zdania: co z tej metody przydaje się do ciągłej, samobudującej się architektury mózgopodobnej",
  "verified_from": "abstract | full_text | repo | pamięć_modelu",
  "notes": ""
}
```

Obszary (`area`):
1. `intrinsic_motivation` — uczenie bez nagrody zewnętrznej (RND, ICM, Plan2Explore, …)
2. `no_backprop` — reguły lokalne, hebbowskie, ewolucyjne, forward-forward, predictive coding, …
3. `continual` — uczenie ciągłe, zapominanie, transfer
4. `memory_exploration` — pamięć, ciekawość, eksploracja (episodic, count-based, …)
5. `algorithm_discovery` — AutoML-Zero, odkrywane reguły RL/uczenia, meta-learned rules
6. `self_organization` — samoorganizacja, rozwój zdolności, open-endedness
7. `world_models` — modele świata, przewidywanie konsekwencji (Dreamer, JEPA, …)
8. `neuro_learning` — jak uczy się mózg: plastyczność, neuromodulacja, konsolidacja/sen, active inference, kora/hipokamp
9. `neuro_development` — jak mózg się BUDUJE: neurogeneza, synaptogeneza i pruning, plastyczność strukturalna, rozwój, programy rozwojowe sieci
