# Audyt krytyka: metabolic_scarcity_prune — 2026-10-24

## Zakres i dowody

- Odczytano `AGENTS.md`, `audit/HANDOFF.md`, tablicę, rejestr H009/H014, teorię wzrostu i `sandbox/leaderboard.jsonl`.
- Najnowszy rekord organism-v4 `metabolic_scarcity_prune`: score 2.32421875, 6000 kroków, 1024 światy, 302 jednostki kalibracyjne; maksimum occupancy 34.4434, końcowa 32.9795. Źródło liczb: rekord leaderboardu.
- Nie ma rekordu `metabolic_scarcity_prune_ablation` ani innego wpisu z `scarcity_prune=0`; plik `candidates/metabolic_scarcity_prune_ablation/principle_organism.py` istnieje, ale sam kod ablation nie jest wynikiem.

## Ustalenia

- H009 przewiduje wynik ponad `growth_signed_trace` 2.3076 na 8 seedach oraz mniejszą maksymalną liczbę żywych łączy. Pojedyncze 2.3242 nie sprawdza tej predykcji i daje tylko +0.0166 względem opisanego punktu odniesienia, bez matched seedów ani CI porównawczego.
- Energia wpływa na kilka kanałów naraz: szybkość w `principle_organism.py:127`, wybór koloru/eksplorację w liniach 107–108 i wykładnik zaniku użycia w liniach 86–87. Wpływ wyniku na pruning nie jest zidentyfikowany bez porównania z `scarcity_prune=0` przy reszcie zachowania stałej.
- `keys`, `weights`, `use` i `exists` są wspólne jako pule indeksów dla batcha, natomiast `structure()` zwraca `exists.sum(dim=1)`. Liczba w leaderboardzie jest uśrednioną occupancy organizmów, nie liczbą globalnie zaalokowanych slotów; nie mierzy pamięci na organizm ani wzrostu niezależnych sieci.
- Ręcznie ustalone trzy kolory, wybór `argmax`, geometryczne skręcanie i próg gryzienia pozostają częścią kontrolera. Efekt nie stanowi dowodu, że ogólna zasada sama wyprowadza strategię organizmu.
- Nowość ogólnej idei przycinania zależnego od użycia jest nieustalona jako nowość; wcześniejszy otwarty przegląd w `theory/theorist_growth/THEORY.md` wskazuje znaną literaturę activity-dependent pruning (Faust, Gunner i Schafer 2021, PMC8541743). Nie twierdzę, że otwarto nowe źródła w tej turze.

## Następny test

Uruchomić matched-seed parent/mutant z jedyną zmianą `scarcity_prune`, a osobno raportować wynik per-world, occupancy per-organism oraz globalną liczbę zaalokowanych kluczy/slotów. Skala powyżej 302 pozostaje smoke testem 64 kroków według komunikatu orchestratora, nie pełnym testem organizmu.

## Działanie

Wysłano krytyczne uwagi odkrywca_life przez `shared/board.py`; H009 pozostawiono bez zmiany statusu, bo prerejestrowane 8-seedowe porównanie nie zostało wykonane.
