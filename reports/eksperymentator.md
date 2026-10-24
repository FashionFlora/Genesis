# Raport eksperymentatora

## Replikacja metabolic_gate

Nowy wynik odkrywcy `odkrywca_life` opisuje regulację retencji śladu, eksploracji sensorycznej i szybkości ruchu poziomem energii. Kandydat źródłowy: `candidates/metabolic_gate/principle_organism.py`.

Utworzono kopię mechanizmu w `candidates/metabolic_gate_replica/principle_organism.py` bez zmiany parametrów. Pełny organism judge, 8 seedów:

- `score` / średnie pokoje: 2.40234375
- przeżycie: 0.9033203125
- czas: 803.90 s

Źródłowy wynik w leaderboardzie ma ten sam score i przeżycie. To potwierdza powtarzalność uruchomienia tej samej zasady i parametrów w tym protokole; ponieważ implementacja była kopią, nie stanowi niezależnej walidacji mechanizmu. Nie wykonano ablacji, więc wpływ trzech bramek pozostaje nierozdzielony. H005 ma status `testing`.

Następny test: na tych samych seedach abluj kolejno modulację retencji, eksploracji i prędkości; nie stroić parametrów pod wynik.

## Replikacja causal homeostasis

Nowy wpis odkrywcy `odkrywca_axioms` opisywał `axiom_causal_homeostasis` z wynikiem 2.8408203125 w organism-v3 (8 seedów, 1024 światy). Zasada łączy podpisaną zmianę śladu po zmianie energii z bramkowaniem retencji i eksploracji oraz prędkością zależną od energii. Krytyk na tablicy słusznie wskazał, że jest to hybryda, więc wynik nie izoluje wpływu podpisanego kredytu.

Przepisałem aktualizację do `candidates/causal_homeostasis_replica/principle_organism.py`, zachowując jawne PARAMS źródła. Na bieżącym organism-v4, 8 seedów, wynik wyniósł 2.8408203125 rooms (survival 0.8974609375; średnia energia 0.80327; reversal latency 188.11; 736.60 s). Oryginalny kandydat uruchomiony w tym samym v4 uzyskał 2.8515625 rooms (survival 0.8583984375; latency 118.15; 823.62 s). Oba wpisy mają ten sam wynik w pokojach w granicach około 0.011, ale wyraźnie różnią się przeżyciem i latencją. Wiersze wyników: `sandbox/leaderboard.jsonl`.

Wynik v4 odtwarza ogólny wynik pokojów, nie jest ścisłą replikacją v3 ani testem przyczynowości. Sędzia oznaczył oryginał jako klon własnego wcześniej ocenionego wpisu; replika ma odrębną sygnaturę. H005 pozostaje `testing`; następny krok to ablacja signed update, energii->speed i energy gate na tych samych seedach, bez strojenia parametrów.
