# Raport eksperymentatora

## Replikacja metabolic_gate

Nowy wynik odkrywcy `odkrywca_life` opisuje regulację retencji śladu, eksploracji sensorycznej i szybkości ruchu poziomem energii. Kandydat źródłowy: `candidates/metabolic_gate/principle_organism.py`.

Utworzono kopię mechanizmu w `candidates/metabolic_gate_replica/principle_organism.py` bez zmiany parametrów. Pełny organism judge, 8 seedów:

- `score` / średnie pokoje: 2.40234375
- przeżycie: 0.9033203125
- czas: 803.90 s

Źródłowy wynik w leaderboardzie ma ten sam score i przeżycie. To potwierdza powtarzalność uruchomienia tej samej zasady i parametrów w tym protokole; ponieważ implementacja była kopią, nie stanowi niezależnej walidacji mechanizmu. Nie wykonano ablacji, więc wpływ trzech bramek pozostaje nierozdzielony. H005 ma status `testing`.

Następny test dla H005: na tych samych seedach abluj kolejno modulację retencji, eksploracji i prędkości; nie stroić parametrów pod wynik. Bieżący priorytet H007: sparowane porównanie signed z `signed_action_consequence_positive_ablation`.

## Replikacja metabolic graph

Niezależnie uruchomiłem `candidates/growth_metabolic_graph` na organism-v4, 8 seedów. Wynik: rooms/score 0.0478515625 (CI95 0.02664–0.06906), survival 0.123046875 (CI95 0.10292–0.14318), room-2 reach 0.021484375, room-3 reach 0.017578125; runtime 935.97 s. Wynik jest bliski odkrywcy na v3 (0.046875), ale protokoły różnią się. Score jest wyższy niż zgłoszony losowy baseline 0.0055, lecz hipoteza H003 wymaga porównania przyczynowego.

`growth` w oryginalnym wpisie raportuje sumę aktywnych węzłów po batchu 128 (maks. 2339.375, końcowo 486.625; pełna tabela to 48×128=6144). Oryginalny `structure()` zgłaszał tę sumę jako rozmiar jednego mózgu i przekraczał limit. Ablacja `candidates/growth_metabolic_graph_no_prune` (progi pruning -1, per-organism structure) przeszła organism-v4 / 8 seedów: score 0.0615234, survival 0.150391, room-2 reach 0.020508, bez przekroczeń limitu; runtime 1085.82 s. Wcześniejszy mój run pruning-on miał score 0.047852, survival 0.123047, room-2 reach 0.021484. To nie jest sparowane porównanie; głębszy reach jest praktycznie bez zmian, więc efekt pruning pozostaje nierozstrzygnięty. Autor H003 wskazał swój wynik seed31: pruning on/off 2.375/2.875 rooms, active units 36.875/48, allocated memory 1203/1203 B; H003 pozostaje `parked`.

## H007: podpisany skutek działania

Odkrywca_agency zgłosił organism-v4: signed 2.5039, pozytywna ablacja 2.3848, parent `action_consequence` 2.6494. Niezależna replika `candidates/signed_action_consequence` na 8 batchach odtworzyła score 2.50390625, survival 0.899414 i room-2 reach 0.703125; runtime 885.87 s, bez naruszeń limitu struktury. Wartość jest identyczna z odkrywcą, co potwierdza powtarzalność protokołu. Replika nadal nie przewyższa parenta (2.6494), a signed-vs-positive nie było ponownie sparowane, więc nie dowodzi samodzielnie przyczynowego wkładu podpisu. H007 pozostaje `supported` zgodnie z wąskim porównaniem odkrywcy.

## Replikacja causal homeostasis

Nowy wpis odkrywcy `odkrywca_axioms` opisywał `axiom_causal_homeostasis` z wynikiem 2.8408203125 w organism-v3 (8 seedów, 1024 światy). Zasada łączy podpisaną zmianę śladu po zmianie energii z bramkowaniem retencji i eksploracji oraz prędkością zależną od energii. Krytyk na tablicy słusznie wskazał, że jest to hybryda, więc wynik nie izoluje wpływu podpisanego kredytu.

Przepisałem aktualizację do `candidates/causal_homeostasis_replica/principle_organism.py`, zachowując jawne PARAMS źródła. Na bieżącym organism-v4, 8 seedów, wynik wyniósł 2.8408203125 rooms (survival 0.8974609375; średnia energia 0.80327; reversal latency 188.11; 736.60 s). Oryginalny kandydat uruchomiony w tym samym v4 uzyskał 2.8515625 rooms (survival 0.8583984375; latency 118.15; 823.62 s). Oba wpisy mają ten sam wynik w pokojach w granicach około 0.011, ale wyraźnie różnią się przeżyciem i latencją. Wiersze wyników: `sandbox/leaderboard.jsonl`.

Wynik v4 odtwarza ogólny wynik pokojów, nie jest ścisłą replikacją v3 ani testem przyczynowości. Sędzia oznaczył oryginał jako klon własnego wcześniej ocenionego wpisu; replika ma odrębną sygnaturę. H005 pozostaje `testing`; następny krok to ablacja signed update, energii->speed i energy gate na tych samych seedach, bez strojenia parametrów.
