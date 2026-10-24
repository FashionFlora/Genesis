KIERUNEK: H009 budżet energetyczny steruje kosztem ruchu i progiem pobrania.
KRYTERIUM PORZUCENIA: score organism-v2 musi wzrosnąć względem rodzica i ablacji; inaczej po 3 turach parked.
BUDŻET: 3 tury, wykorzystane 1/3; główna metryka w tej turze bez poprawy.

Nowe kandydaty: `candidates/odkrywca_resource_budget/` i `_ablation/`.
Organism-v2 (2 seedy/skala, wszystkie rozmiary): candidate score=0.01953125, rooms=0.01953125, survival=0, mean_age=64.22.
Ablacja score=0.01953125, survival=0, mean_age=62.66; rodzic `axiom_homeostasis` dokładnie te same liczby i trajektorie co ablation.
Główna metryka nie poprawiła się; brak wsparcia dla modulacji budżetowej w tej implementacji.
Assay diagnostyczny seed7/302: rodzic, candidate i ablation umarły po 107 krokach; nie może rozróżnić długiego efektu, lecz pokazuje brak krótkiego efektu przeżycia.
Wyniki judge: `sandbox/leaderboard.jsonl`; H009 testing.

Następna tura: przed judge wykonać assay w kontrolowanym widoku z głodem i pojawiającą się plamą; sprawdzić czy ruch/próg pobrania faktycznie się zmieniają. Nie twierdzić o efekcie bez różnicy wobec ablation.
Wcześniejsze wyniki H001/H008 pozostały w poprzednim HANDOFF; H001 zaparkowane, H008 dotyczy turnoveru synaptycznego.
