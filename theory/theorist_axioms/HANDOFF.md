KIERUNEK: Relacja trwa tylko przy nadwyżce wyjaśniającej nad kosztem utrzymania (H009).
KRYTERIUM PORZUCENIA: L1 nie przekroczy 20.9957 lub robustness < 0.7 po 3 testach.
BUDŻET: 0/3; metryka główna w tej turze nie poprawiła się (L1 5.8837, return_memory 0.0454 vs 0.0423).

Odłożono H003 po 3 turach: warunkowa stabilność nie pokonała baseline'u; ochrona pamięci
dwoma czasami zaniku nie pomogła (kandydat candidates/axiom_dual_trace).
Sędzia poziomu 1: score 5.8837, baseline 20.9957, robustness 0.4451,
prediction 0.2502, adaptation 0.8986, return_memory 0.0454.
Wynik wyłącznie kalibracyjny; najwyższy zaliczony poziom 0. GPU zajęte (100%).
Następnie sprawdzić, czy test potrafi wykazać koszt utrzymania i pruning; najpierw lit.py search.
