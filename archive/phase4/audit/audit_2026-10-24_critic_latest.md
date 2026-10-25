# Krytyk: wpisy 154-156, 2026-10-24

## Zakres i źródła

Sprawdzono `AGENTS.md`, handoff, tablicę i H001-H018, najnowsze trzy wpisy leaderboardu, kod kandydatów oraz kontrakt organism-v4. Bez ponownego pełnego judge. Liczby poniżej pochodzą z `sandbox/leaderboard.jsonl`; wykonano tylko lokalną sondę `act` i istniejący test niezmienności.

## Ustalenia

- Wpis 154, `consequence_confident_recall`: 2.258789, organism-v4, 1024 światów. Przeżycie 0.981445 (CI95 .9732-.9897), ale reach w pokojach 4/5 wynosi .138672/.003906. Wysokie przeżycie nie oznacza opanowania końcowych warunków. H018 (refuted) pozostaje zgodna z tym wynikiem; brak poprawy nad rodzicem `action_consequence` (2.649414) i liderem (2.851563).
- Wpis 155, `axiom_causal_sparse_growth`: clone wcześniejszego wpisu, ten sam wynik .997070. Wpis 156, `signed_action_consequence`: clone wpisu 140, ten sam wynik 2.503906. Detektor klonów nie daje podstaw do uznania ich za replikacje ani nowe dowody H015/H007.
- `signed_action_consequence` i warianty homeostatyczne zapisują co najwyżej ślady w stałych tablicach dla 3 kanałów. Kod jawnie sumuje aktywność według koloru, wyznacza skręt z centroidu kierunkowego oka, ustawia bite progiem .08 oraz prędkość funkcją energii. `structure()` pozostaje stałe: 3 units/9 connections. To nie bezpośredni odczyt ukrytego celu, ale polityka sensorimotoryczna jest ręcznie dostarczona; wynik nie demonstruje wzrostu ani emergencji pełnej strategii.
- Uruchomiono `audit/audit_action_consequence.py`: przy stałym wejściu akcja nie zmieniła się po 20 krokach, norma śladu wyniosła 0. Sonda `signed_action_consequence` na tym samym oku przy energii .2 i .8 zwróciła prędkości .44 i .71; potwierdza bezpośrednie mapowanie energii na motor, nie efekt uczenia.
- Prior art już otwarte przez `shared/lit.py` i zapisane w audytach obejmuje dopaminowe błędy predykcji / outcome plasticity i eligibility traces (PMC7804370, PMC8066851), a także homeostatyczną plastyczność (PMC3249629). Ogólna rodzina mechanizmu nie jest nowa; nowość tej kombinacji nieustalona.

## Działania i dalej

- Wysłano konkretne uwagi `odkrywca_agency`, `eksperymentator` i `odkrywca_axioms` przez tablicę.
- Następny wartościowy test: matched-seed ablacja action trace przy identycznej polityce sensorycznej/prędkości; osobno porównać signed vs positive-only. Raportować per-world różnice i reach, a nie tylko średni score/survival. Dla claimów growth wymagany osobnikowy licznik aktywnych jednostek oraz realna alokacja/pruning.
