KIERUNEK: H010 - relacja trwa tylko przy nadwyżce wyjaśniającej względem prioru.
KRYTERIUM PORZUCENIA: po 3 oficjalnych testach score L1 < 6.9 lub robustness < 0.7; bramka uczenia musi przejść.
BUDŻET: 2/3; główna metryka nie poprawiła się.

Ta tura: sprawdzone dwie projekcje H010 w symulacji A-B-A, 4 seedy.
Stara mieszanina: Brier 0.2608-0.2671; korekta prioru: 0.2900-0.2971;
bezpośrednia relacja: 0.3833-0.3970. Test obalił te projekcje, nie cały H010.
Nie zapisano nowego kandydata, bo żadna projekcja nie przeszła symulacji.
Następny test powinien ważyć relację przewidywaną poprawą straty względem prioru.
Literatura: `shared/lit.py search` dla conditional evidence / continual learning -> HTTP 403.
Poprzedni wynik oficjalny axiom_evidence_competition: L1 4.9281, R 0.6016,
bramka uczenia nie przeszła (improvement 0.0195), kandydat w candidates/axiom_evidence_competition/.
