# Raport eksperymentatora — 2026-10-23

## H002: Krawędzie jako skutek nieprzewidzianej współzmienności

Uruchomiłem standardową drabinę CPU sędziego dla istniejącej implementacji `candidates/growth_nucleation`; zakończyła się po niezaliczonym poziomie 1. Wynik punktowany to `1.056`, wynik przed karą elegancji `21.1191`, baseline `_baseline_online` `20.9957`, próg `26.2446`. Uczenie przeszło (przyrost `0.0546`), struktura dostała `0.4930`, a pamięć powrotu `0.0359`.

Obecny zapis nie jest odporny na perturbacje `PARAMS`: robustness `0.5` wobec wymaganego `0.7`; dla `decay=1.7133` sędzia odrzucił niefinitywną lub spoza zakresu predykcję. Kara AST daje mnożnik elegancji `0.1` przy 60 literałach liczbowych. To wskazuje na słabą reprezentację i odporność tej wersji, a nie rozstrzyga jeszcze przewidywań H002 o skalowaniu struktury i powrocie reżimów.

Wynik zapisano w `sandbox/leaderboard.jsonl` (SHA testowanej wersji `a3821b1c`). Podczas pracy odkrywca równolegle zmienił współdzielony plik: jego bieżący SHA to `35d38b45`, więc wynik nie opisuje obecnej wersji. H002 pozostaje `testing`. `shared/lit.py search` nie zwróciło cytowań, a zapytanie arXiv zakończyło się HTTP 429; nie otwarto źródeł.

Odkrywca ogłosił test GPU, lecz obecny kandydat nie ma `principle_gpu.py`. GPU był zajęty przez obce procesy (93–100%, 13.9 GiB pamięci zajęte), więc nie uruchomiłem niezgodnego adaptera ani nie zmieniałem współdzielonego kandydata.

Następny krok: niezależnie replikować GPU po udostępnieniu adaptera i wolnego slotu; nie traktować wyniku tej starszej wersji jako oceny aktualnego kodu.

## Niezależne repliki H006 i H003

Uruchomiłem standardowego sędziego CPU dla dwóch nowych pomiarów odkrywców. `dynamics_predictive_competition` (SHA `3cd699ec`) uzyskał L1 `15.0289` wobec baseline `20.9957`, robustness `0.8698`; `axiom_conditional_stability` (SHA `c0c52686`) uzyskał L1 `12.2672`, robustness `0.5679`. Oba przebiegi zakończyły się na poziomie 1 z powodu nieosiągnięcia progu. Wyniki odtwarzają opublikowane liczby w granicach zaokrąglenia, ale żaden kandydat nie przechodzi drabiny. H003 i H006 pozostają `testing`, z notatkami o replikacji. Źródło: `sandbox/leaderboard.jsonl`.

## H007: Budżet metaboliczny relacji

Niezależny pełny przebieg CPU dla `candidates/life_metabolism` (SHA `560633e5`) zaliczył L1: `28.458` wobec baseline `20.9957`, robustness `0.7808`; zaliczył także L2: `16.8482`, robustness `0.7165`. Drabina zatrzymała się na L3, bo kandydat nie implementuje `System.act`; przewidywanie Snake i poprawa drugiego epizodu pozostają nieprzetestowane. Wynik końcowy sędziego to poziom 2, `16.8482`; pomiar jest zgodny z kalibracją L1 odkrywcy `28.4509` w granicach wahań kosztu CPU. H007 pozostaje `testing` jako częściowa replikacja. `shared/lit.py search` zwróciło HTTP 403, więc nie otwarto źródeł. Pełny wynik: `sandbox/leaderboard.jsonl` (2026-10-23 12:06Z).

## H010: Niezależna replika

Uruchomiłem pełnego sędziego CPU dla `candidates/axiom_evidence_competition` (SHA `b5b8caab`). L1 uzyskał `4.9322`, robustness `0.6018`, highest level `0`; wynik odkrywcy to `4.9281`/`0.6016`. Replika jest zgodna, a hipoteza H010 pozostaje `testing` z notatką o wyniku. Szczegóły w `sandbox/leaderboard.jsonl`.

Test dojrzałości H007: nie da się wyprowadzić `act` z obecnej zasady metabolicznej bez dodania mechanizmu. Energia ocenia trafność predykcji obserwacji, lecz zasada nie modeluje skutków warunkowych względem ruchu ani nie porównuje możliwych działań. Nie dodawałem ręcznej strategii; brakującym fundamentem jest endogeniczne powiązanie wyboru działania z przewidywaniem/niepewnością.

## H009: surplus wyjaśniający

H009 nie miał kandydata do replikacji, więc zaimplementowałem osobną, minimalną interpretację: log-masa każdej relacji zmienia się według różnicy prekwencyjnego błędu Brier względem prognozy bazowej celu, a relacje mieszają prognozę z prior-em. `candidates/eksperymentator_explanatory_surplus` uzyskał L1 `17.9224` wobec baseline `20.9957`, robustness `0.8049`; nie zaliczył progu wyniku i zakończył na poziomie 0. SHA: `4942538487a3d0373dc34cf5134e8087849711099ced2b83daf8ddeefea8d7e1`. Pełne szczegóły i liczby w `sandbox/leaderboard.jsonl`. To jedna niezależna realizacja H009, nie pełna replikacja kodu odkrywcy ani obalenie formalnego falsyfikatora po trzech testach. Hipoteza pozostaje `testing`. `shared/lit.py search` nie zwróciło źródeł.
