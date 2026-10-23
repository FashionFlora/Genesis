# Raport eksperymentatora — 2026-10-23

## H002: Krawędzie jako skutek nieprzewidzianej współzmienności

Uruchomiłem standardową drabinę CPU sędziego dla istniejącej implementacji `candidates/growth_nucleation`; zakończyła się po niezaliczonym poziomie 1. Wynik punktowany to `1.056`, wynik przed karą elegancji `21.1191`, baseline `_baseline_online` `20.9957`, próg `26.2446`. Uczenie przeszło (przyrost `0.0546`), struktura dostała `0.4930`, a pamięć powrotu `0.0359`.

Obecny zapis nie jest odporny na perturbacje `PARAMS`: robustness `0.5` wobec wymaganego `0.7`; dla `decay=1.7133` sędzia odrzucił niefinitywną lub spoza zakresu predykcję. Kara AST daje mnożnik elegancji `0.1` przy 60 literałach liczbowych. To wskazuje na słabą reprezentację i odporność tej wersji, a nie rozstrzyga jeszcze przewidywań H002 o skalowaniu struktury i powrocie reżimów.

Wynik zapisano w `sandbox/leaderboard.jsonl` (SHA testowanej wersji `a3821b1c`). Podczas pracy odkrywca równolegle zmienił współdzielony plik: jego bieżący SHA to `35d38b45`, więc wynik nie opisuje obecnej wersji. H002 pozostaje `testing`. `shared/lit.py search` nie zwróciło cytowań, a zapytanie arXiv zakończyło się HTTP 429; nie otwarto źródeł.

Odkrywca ogłosił test GPU, lecz obecny kandydat nie ma `principle_gpu.py`. GPU był zajęty przez obce procesy (93–100%, 13.9 GiB pamięci zajęte), więc nie uruchomiłem niezgodnego adaptera ani nie zmieniałem współdzielonego kandydata.

Następny krok: niezależnie replikować GPU po udostępnieniu adaptera i wolnego slotu; nie traktować wyniku tej starszej wersji jako oceny aktualnego kodu.

## Niezależne repliki H006 i H003

Uruchomiłem standardowego sędziego CPU dla dwóch nowych pomiarów odkrywców. `dynamics_predictive_competition` (SHA `3cd699ec`) uzyskał L1 `15.0289` wobec baseline `20.9957`, robustness `0.8698`; `axiom_conditional_stability` (SHA `c0c52686`) uzyskał L1 `12.2672`, robustness `0.5679`. Oba przebiegi zakończyły się na poziomie 1 z powodu nieosiągnięcia progu. Wyniki odtwarzają opublikowane liczby w granicach zaokrąglenia, ale żaden kandydat nie przechodzi drabiny. H003 i H006 pozostają `testing`, z notatkami o replikacji. Źródło: `sandbox/leaderboard.jsonl`.
