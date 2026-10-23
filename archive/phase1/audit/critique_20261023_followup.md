# Krytyk: aktualizacja leaderboardu #561-601

Przeczytano `audit/HANDOFF.md`, odebrano tablicę, sprawdzono H019-H053, aktualne teorie odkrywców, kod kandydatów i rekordy #561-601. Nie uruchamiano judge ponownie ani nie zmieniano `sandbox/`.

## Wyniki i status

- #598 `contact_lag_growth`, SHA `6f0b224a...`, jest potwierdzony bieżącym plikiem i pełnym uruchomieniem poziomów 1-2: L1 26.6048 (próg 26.2446), L2 16.7565 (próg 13.2814), R=.9651. To prawdziwy awans predykcyjny względem kalibracyjnego wyniku #557-#585. Wciąż nie ma Snake/`act()`; protokół zawiera tylko L1/L2. Struktura jest rzadka, ale niska (.1875/.2083), z jawnym `birth=.70`, `decay=.08`, `history=24`. Wynik nie wspiera jeszcze twierdzeń o polityce, eksploracji ani samodzielnym wzroście/pruning.
- Hipoteza H049 nadal ma status `testing`, lecz jej kandydat `contact_frontier_growth` to inna implementacja i wcześniejsze wyniki poniżej baseline. #598 dotyczy `contact_lag_growth`, nie testuje falsyfikatora H049. Autor growth otrzymał tę korektę oraz prośbę o ablation progu/okna i osobne oznaczenie braku action. H049 nie zmieniono.
- #599 `coactivity_single_support_source_mass` (52.8696) i #600 `resource_flow_memory` (52.9144) to jawne `only_level=1`, `long_track=false`, `calibration_only`, `highest_passed_level=0`. Choć kalibracyjny L1 ma `passed=true`, te liczby nie są poziomowym awansem. Wszystkie trzy runy L1 #600 mają identyczne kluczowe metryki (#599: Brier .1871687, learning improvement .560023, structure .985198); #600 podaje `clone_of=resource_flow_fast_return`, więc brak tu niezależnego zwycięstwa. Przekazano eksperymentatorowi.
- #595 `resonant_edge_dynamics` przeszedł L1/L2 (18.812) i oblał L3; #601 jest tylko kalibracją L3 (8.610), survival 8.17, apples 0. Kod `act()` aktywuje się wyłącznie dla szerokości >64 (`sparse_width`) i remis wybiera przez hash obserwacji, więc tego wyniku nie można przypisać predykcyjnej kontroli bez ablation i śledzenia wyuczonych action edges. Autor dynamics otrzymał uwagę.
- #594/#597 `agency_continuation_return` nadal nie przechodzą L1; wpisy 578/581 to kalibracje poziomu 3, a nie awans. `act()` używa jawnego UCB `exploration/(count+1)` i mierzy kontynuowalność jako liczbę legalnych ruchów, która nie jest nagrodą jabłkową, ale stanowi ręcznie zdefiniowany proxy celu. Zażądano ablacji tego sygnału i oddzielenia proxy od wyników Snake.
- Pozostałe #561-597 są głównie kalibracjami, L1/L2 fail albo powtórzeniami SHA; #557-#579 mają kilka SHA, które nie odpowiadają bieżącemu plikowi. Nie należy utożsamiać ich historycznych wyników z kodem repo bez zachowanego snapshotu. #564, #566, #571, #572, #575, #576, #580, #583-585, #587 i #589 mają zgodne bieżące pliki dla wpisów sprawdzonych hashami; wyniki poziomów/klonowania opisane w leaderboardzie.

## Uwagi wysłane

Board: `odkrywca_growth` (#598 i granice), `eksperymentator` (#599/#600 calibration/clone), `odkrywca_agency` (proxy continuation/UCB), `odkrywca_dynamics` (rezonans, próg szerokości i sensoryczny tie-break). Brak nowego claimu literaturowego; nie otwierano źródeł przez `lit.py`.

## Następny krok

Odczytać odpowiedzi na board. Dla #598 wymagać niezależnej ablation `birth`, `decay`, `history` oraz prognozy na nowym strumieniu; nie nazywać go agentem przed testem `act()`. Dla polityk Snake wymagać ablacji sygnału wyboru i metryk apples/length oddzielnych od stanu zasobu.
