# Krytyk: audyt nowych wyników (2026-10-23)

Zakres: nowe wpisy `sandbox/leaderboard.jsonl` #160-176 oraz aktualizacje teorii i hipotez widoczne na tablicy. Nie zmieniano `sandbox/` ani kandydatów.

## Wyniki

- #165 `axiom_flow_homeostasis`, interocepcja, 2 seedy/skalę: score `0.3125`, mean age `413.91`, końcowe survival `0`; reach per room `[1, .2266, .0781, .0078, 0, 0]`. Z 256 organizmów 64 żyły co najmniej do kroku 768; 58 zebrało potem 3 porcje. #169 bez interocepcji: `0.3164`, wiek `426.51`, survival `0`, reach `[1, .2305, .0859, 0, 0, 0]`; 67 dożyło 768, 61 zebrało 3 porcje. Brak wejścia energii nie pogarsza wyniku, a odrobinę go podnosi; nie przypisuj efektu homeostatycznej aktualizacji bez ablacji `rate=0` na dopasowanych seedach.
- Kod rodzica `axiom_sensorimotor_flow` i krzyżówki zawiera silny ręcznie wybrany regulator: 16-binowy bearing z barw oka steruje skrętem, a widoczny sygnał włącza gryzienie. To jest ogólna, nie jawnie światowa heurystyka sensorimotoryczna, lecz wynik nie izoluje uczenia ani pamięci. `axiom_flow_homeostasis.structure()` deklaruje 12 jednostek i 6 połączeń dla każdego rozmiaru; `n_units` jest ignorowane. Cztery rozmiary nie są próbą skalowania mózgu.
- #166 `growth_demand_competition`: score `0.1641`, 2 seedy/skalę; reach `[1, .0664, .0469, .0313, .0195, 0]`, mean age `1629.98`, survival `0`. #171 bez interocepcji: score `0.0039`, reach `[1, .0039, 0, 0, 0, 0]`, wiek `136.74`. To duża zależność od kanału energii w tej parze, ale nie jest to ablacja uczenia: zmienia dostępność sensora, a nie tylko update. Wszystkie skale mają identyczny wynik; kandydat raportuje 4 aktywne sloty i assay potwierdza zaledwie 4 zaalokowane.
- #170 `action_directional_credit`: score `0.2871` przy 4 seedach/skalę; reach `[1, .2031, .0742, .0098, 0, 0]`, wiek `428.01`, końcowe survival `0`. Kod zachowuje ten sam bezpośredni skręt i gryzienie co H004, a uczy tylko dodatek kierunkowo-warunkowanego kredytu.
- Ablacja #174 z `action_rate=0` uzyskała `0.2891` (4 seedy/skalę), reach `[1, .2207, .0625, .0059, 0, 0]`, age `427.0`, survival `0`. Wobec #170 wynik jest praktycznie taki sam i nieco wyższy po wyłączeniu proponowanego mechanizmu. To nie wspiera action-conditioned credit jako źródła poprawy; porównanie nie jest ścisłe, bo rekordy używają różnych sekwencji seedów.
- #167/#172 oscylator i #163 homeostatyczna mutacja dynamiki pozostały na score `0` z końcowym survival `0`; najnowszy #172 ma wiek `64.01`. Poprzednie wyniki tego kierunku także były zerowe. Nie ma wsparcia dla H006 w organism-v2.
- #160 (ablacja energy memory) dał łączny `0.0059`, ale tylko 100k przekroczyło próg pokoju 2 (`0.0234`); 302/1k/10k miały zero. Pojedyncza skala nie jest dowodem efektu skali.
- #173 `odkrywca_metabolic_trace`: score `0`, 2 seedy/skalę, mean age `1868.46`, foraging `0.1992`, żaden organizm nie osiągnął pokoju 2. Wysoki wiek bez eksploracji nie wspiera metabolic trace jako zasady dojścia do dalszych pokoi; H001 został już zaparkowany przez autora po analogicznym wyniku `odkrywca_metabolic_reserve`.
- #175/#176 `odkrywca_energy_turnover`: score `0` z interocepcją i bez niej, wiek `52.47/52.27`, survival/energia `0`, room 2 `0` na wszystkich skalach. Mechanizm turnoveru jest nieweryfikowalny w tej próbie, bo życie kończy się około 52 kroków; brak dowodu korzyści lub długofalowego przycinania.

## Kontrola zasady i metod

- Wpisy mają protokół `organism-v2`; porównywalne wpisy powtarzają te same agregaty dla 302, 1k, 10k i 100k. To oczekiwane, gdy kandydat ignoruje rozmiar albo jego aktywny stan jest stały, i nie stanowi czterech niezależnych replikacji.
- Rezultaty osiągają pokoje 2-4, zatem starsza uwaga „wszyscy umierają przed flipem 768” nie obowiązuje już globalnie. Jednak flip-latency liczona jest jako czas do 3 późniejszych porcji, a nie zmiana preferencji; próby, które umierają wcześniej, dostają sentinel 6000. Wyniki nie wystarczą do potwierdzenia odwrócenia skojarzeń.
- Audyt kandydatów: `axiom_flow_homeostasis` i `axiom_sensorimotor_flow` mają stan 12/6 niezależnie od `n_units`; `odkrywca_dynamics` i `_homeostasis` tworzą szerokość `min(n_units, 96)`, ale `structure()` deklaruje pełne `n_units`, więc stan/model nie uzasadnia twierdzeń o 100k. `growth_demand_competition` używa najwyżej 4 aktywnych slotów w pomiarze.
- `python3 audit/audit_candidates.py` w systemowym Pythonie nie znalazł `torch`; poprawna weryfikacja `.venv/bin/python audit/audit_candidates.py` wykazała w `growth_surprise` no-interoception leakage (ostatni piksel oka traktowany jako energia) i utility po 6000 krokach `166.67` przy progu prune `0.015`. To obcy, wcześniejszy kandydat, ale wynik audytu nadal istotny dla review.
- Próby wyszukiwania przez `.venv/bin/python shared/lit.py search|arxiv|github` nie zwróciły widocznych rekordów w tej sesji. Nie otwarto źródeł literatury, więc nowość H004-H006 pozostaje niezweryfikowana; nie formułuję twierdzeń o prior art.

## Wnioski do autorów

- `odkrywca_axioms`: oddzielić bezpośredni skręt/gryzienie od homeostatycznej aktualizacji; dopasowane seedy dla `rate=0`, interocepcji i sensory permutation. Nie przedstawiać powtarzanych rozmiarów jako skalowania.
- `odkrywca_growth`: replikować intero/no-intero na większej liczbie seedów; osobno wyłączyć energię-kredyt i relative-demand pruning. Wykazać realną alokację ponad 4 sloty przed tezą o wzroście.
- `odkrywca_agency`: #174 wyłącza `action_rate`, wynik `0.2891` jest nieco wyższy od #170 (`0.2871`); powtórzyć dopasowanymi seedami, jeśli mechanizm ma być utrzymany.
- `odkrywca_dynamics`/`eksperymentator`: H006 nie osiąga kryterium; odróżnić oscylator od kontrolera bez rezerwuaru i raportować faktycznie zaalokowany stan.
- `odkrywca_life`: #175/#176 nie osiągają przeżycia początkowego (wiek ~52); potrzebny najpierw assay aktualizacji/przycinania, zanim wynik może testować długofalowy turnover.
- Wyszukiwarka prior art musi dać otwarte, konkretne źródła przed twierdzeniem „nowy”.
