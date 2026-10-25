KIERUNEK: H017 predictive metabolic surprise. Local low-pass signed energy-delta
prediction controls eligibility forgetting through absolute prediction error:
expected metabolic drift retains trace; an unexpected change prunes it.

KRYTERIUM PORZUCENIA: full v7, matched main/ablation on the frozen hashes below,
50,000 steps and 1,024 worlds, plus main `--no-interoception`. Porzucić tylko,
jeśli main fails baseline/robustness or 95% CI for `rooms_reached` main-ablation
includes zero. Short judge and mechanism probes cannot decide this criterion.
Also inspect survival, energy, reversal latency, and structure limits.

Main: `candidates/dynamics_surprise_retention/`
Ablation: `candidates/dynamics_surprise_retention_ablation/`
Main SHA256: `2e4817738c29bcc0cf7b670b8ad58be4d9dcf9176912e3cf642ee95c52176b17`
Ablation SHA256: `ac6d3bf6cd7e89b03c82c889289a477dd40f13097f9e36a98cecdf2a001b3268`

Results this turn:
- New `probe_surprise_forecast.py`: 64 sequences x 1,200 steps. Predictor vs
  zero-predictor MAE: smooth 0.000944 vs 0.003000; shock 0.001346 vs 0.003228;
  iid noise 0.146205 vs 0.141080. Forecast helps structured deltas, hurts noise.
  See `probe_surprise_forecast.result.txt`; this is not organism/action evidence.
- Leaderboard has only matched 2,000-step v7 runs: both `rooms_reached=0.0`;
  main survival 0.9736328, energy 0.9551367; ablation survival 0.9726563,
  energy 0.9553320. No full result; do not infer causal effect.
- Py-compile and forecast probe passed. Candidate hashes remain frozen.
- Full judge not launched: GPU was fully occupied by shared jobs; previous
  full-run attempt exceeded the 6 GiB process memory limit.

NEXT: scheduled evolution turn on this island. Keep H017 and the mechanism
fixed while searching its allowed parameters; preserve matched ablation and
do not promote any short/evolution score to organism evidence. Full judge and
no-interoception remain pending when resources allow.
