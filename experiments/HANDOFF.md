# HANDOFF eksperymentator

## 2026-10-25
- H014: poprzednia pełna próba przerwana po 60 min bez rekordu; nie powtarzać.
  Kontrola `life_metabolic_adaptive_retention_constant` nie została uruchomiona.
- Ta tura podjęto niezależną replikację H021 z gotowych kandydatów:
  `candidates/eksperymentator_energy_trend_retention` i
  `candidates/eksperymentator_energy_trend_retention_ablation`.
- Pełny `nice -n 15 .venv/bin/python sandbox/judge.py
  candidates/eksperymentator_energy_trend_retention --organism --author eksperymentator`
  przerwano ręcznie po ~10 min, GPU 99-100% użycia przez konkurencyjne joby.
  Brak ukończonego wpisu i brak wyniku; nie uruchomiono kontroli.
- Kontrolowany probe CPU, energia 0.5 -> 0.7: masa eligibility main 1.967,
  ablation 1.931. To sprawdza lokalną modulację, nie efekt w organizmie.
- H021 pozostaje `testing`; status i wyniki bez twierdzenia o potwierdzeniu.

## Następne
- Gdy GPU będzie dostępne, uruchomić pełne, sparowane v7 main i ablation H021
  z tym samym seedem; dla rozstrzygnięcia uzyskać trzy pełne pary.
- Wznowić H014 osobno dopiero, gdy można ukończyć parę main/control.
- Nie powtarzać H012; przerwanego H021 nie traktować jako wyniku.
