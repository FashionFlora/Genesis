KIERUNEK: H019 — H009 (metabolic scarcity pruning) z napędem stałym 0.575; energia steruje pamięcią/pruningiem, nie prędkością.
KRYTERIUM PORZUCENIA: score organism <= 2.3242 albo survival spada bez wzrostu rooms_reached.
BUDZET: 2/3; ta tura bez pełnego wyniku (CPU test przerwany po 49 min, brak wpisu leaderboard).

Kandydat: candidates/metabolic_scarcity_fixed_speed/principle_organism.py
Pojedyncza ablacja względem H009 to linia speed; PARAMS i pruning pozostają identyczne.
H009 v4: score 2.3242, survival 0.90625, rooms_reached 2.3242.
Wcześniejsza ablacja interocepcji metabolic_gate_optional_intero: 2.8379 z energią vs 2.3721 bez; survival 0.8906 vs 0.9141.
Próba judge GPU wykazała błąd torch dla bezindeksowego cuda; CPU uruchomiono, ale przerwano po 49 min.

Następna tura: uruchomić kandydata przez wrapper ustawiający torch.device('cuda:0') albo po zwolnieniu GPU; zapisać pełne 8-seed v4.
