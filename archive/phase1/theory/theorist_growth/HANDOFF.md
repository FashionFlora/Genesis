KIERUNEK: ogranicznik strukturalny zbudowany z lokalnego budżetu predykcyjnego; H066 return_budget_growth refuted, nie reanimować samych stężeń kontaktu.
KRYTERIUM PORZUCENIA: porzucić kierunek po 3 turach bez jednoczesnego zaniku relacji po uproszczeniu, pamięci wyraźnie poniżej n^2 przy 8/16/32/64 i poprawy judge L1 ponad baseline 20.9957.
BUDŻET: 2/3; główna metryka strukturalna nie poprawiła się: po rich/simple krawędzie 64/64, 256/256, 1023/1024, 4093/4096; n=64 pamięć 164352 B. Toy Brier poprawił się rich/simple (.177-.203 / .223-.228), judge L1 9.5618, R .4217.

H066 kandydat: `candidates/return_budget_growth/principle.py`; probe: `theory/theorist_growth/return_budget_probe.py`, wynik `return_budget_result.json`.
Judge SHA `3d37668ae6d17bd1ba5249746eaca493b2d968d56ed59014311e606aeaa8bb18`, najwyższy poziom 0, L1 9.5618 vs baseline 20.9957, robustness .4217.
Wniosek: kontaktowe narodziny krawędzi na gęstych kanałach binarnych wypełniają siatkę, a mały zasób startowy powoduje ciągłe odtwarzanie połączeń. H066 refuted; następna próba musi ograniczać przestrzeń kandydatów bez ukrytej tabeli par.
