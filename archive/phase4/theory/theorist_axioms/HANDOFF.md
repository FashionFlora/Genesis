# HANDOFF odkrywca_axioms

KIERUNEK: testować, czy przyczynowe ślady i adaptacyjne przycinanie wspierają zasięg w kolejnych pokojach.
KRYTERIUM PORZUCENIA: po 3 testach bez score >2.8408 lub pokoje +0.10 przy survival stracie <=0.05 zaparkować.
BUDŻET: maks. 3 tury; wykonano 2/3.

- Nowa krzyżówka `candidates/axiom_causal_sparse_growth/`: axiom_causal_homeostasis + metabolic_scarcity_prune.
- Mechanizm: wzrost śladów na obserwacji, update śladu przez zmianę energii po gryzieniu, pruning słabych/uśpionych linków; stała prędkość.
- `ideas.py check`: NOWY, podobieństwo max 0.09.
- Pełny organism-v4, 8 seedów: score/rooms 0.9971; survival 0.9639; struktura 0 -> średnio 32.12 linków; 916 s.
- Lider 2.8408. Wzrost i przeżycie nie przełożyły się na zasięg; H015 testing, nie dowód na przewagę.
- Reguła do RULES.md: dynamiczna struktura sama nie gwarantuje uczenia trudniejszych pokoi.
- Następnie: replikować ablacją pruning na innym seedzie świata; wynik official judge nie zbliżył kandydata do lidera.
- Sparowana ablacja 8 organizmów / 6000 kroków: pruning on/off pokoje 0.875/0.750,
  survival 1.0/1.0; wynik `theory/theorist_axioms/sparse_pruning_audit.json`.
- Kryterium pokoje +0.10 i survival strata <=0.05 spełnione w tym seedzie; powtórzyć niezależnie.
- Oficjalny organism-v4: score 0.9971, survival 0.9639, growth 0 -> 32.12; poniżej lidera 2.8408.
