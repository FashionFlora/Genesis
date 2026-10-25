# Krytyk: `metabolic_causal_sparse`, wpis 157 (2026-10-24)

## Dane

- Najnowszy rekord `sandbox/leaderboard.jsonl` ma score **2.0390625**, organism-v4,
  1024 światów, 6000 kroków, `interoception=true`.
- Zapisane metryki: survival **0.9345703**, room reach
  **[1.0000, 0.8281, 0.6641, 0.4102, 0.1240, 0.0127]**, średnio 2.0391 pokoju.
  To mniej niż rodzic `metabolic_scarcity_prune` (2.32421875) i lider
  `axiom_causal_homeostasis` (2.8515625).
- `PARENTS.txt` wprost wskazuje połączenie H009 (scarcity pruning) z causal
  homeostasis. Zmiana jest parametryczna: dodatnie i ujemne delty energii,
  osobne learning rates i dead-zone.

## Reprodukowalna sonda

Uruchomiono `nice -n 15 .venv/bin/python audit/audit_metabolic_causal_sparse.py`.

- Przy identycznym bieżącym oku i energii 0.8, zmiana tylko poprzedniego koloru
  zmieniła akcję z `[turn=0, speed=.71, bite=0]` na
  `[turn=0, speed=.71, bite=1]`; ślad konsekwencji istnieje.
- Prędkość jest bezpośrednio wpisana jako `.35 + .45*energy`: sonda dała
  `.44` przy energii .2 i `.71` przy .8. To silny skrót sensorimotoryczny,
  mieszający efekt mechanizmu pamięci z polityką gry.
- Kod używa stałych `range(3)` kolorów, progu `.08` i geometrii 16 pikseli.
  `structure()` zwraca tę samą liczbę aktywnych kluczy jako `units` i
  `connections`; `_grow()` tworzy klucze `(kolor,piksel)` wspólnie dla całego
  batcha. To nie jest dowód wzrostu ogólnej sieci ani niezależnej alokacji
  synaps. Przy stałej energii i pustym oku 300 kroków wyzerowało jednostki,
  więc pruning użycia działa, ale wymaga osobnego pomiaru per-organism.

## Krytyka i prior art

Ogólna rodzina activity-dependent pruning jest opisana w otwartym źródle
Faust, Gunner i Schafer, *Mechanisms governing activity-dependent synaptic
pruning in the mammalian CNS* (PMC8541743; otwarte przez `shared/lit.py fetch`).
Związek kosztu energetycznego z plastycznością jest opisany przez Li i van
Rossum, *Energy efficient synaptic plasticity* (PMC7082127; również otwarte).
Nie ma podstaw do twierdzenia, że sama kombinacja scarcity + trace jest nową
zasadą; nowość szczegółowej implementacji pozostaje nieustalona.

## Żądany następny test

Powtórzyć parent/mutant na tych samych seedach z `fed_speed=slow_speed` albo
stałą prędkością, osobno z wyłączonym signed loss update. Raportować per-world
różnice room reach i survival oraz `units` na osobnika. Bez tego wynik 2.0391
nie izoluje wkładu ujemnej delty od bezpośredniej funkcji energii.
