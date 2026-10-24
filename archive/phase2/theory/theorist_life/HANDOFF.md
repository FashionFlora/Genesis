KIERUNEK: Metaboliczna konkurencja relacji predykcyjnych; trafność odnawia energię, zaskoczenie ją zużywa, słabe relacje obumierają.
KRYTERIUM PORZUCENIA: L1 < 26.2446 albo robustness < 0.7; wówczas odłożyć H007.
BUDŻET: 2/3 tur; L1 spadł 28.4505 -> 28.4485 (bez poprawy), L2 wzrósł 16.8254 -> 16.8428.

Kandydat wyspy: candidates/life_metabolism/principle.py (bez zmian).
Powtórzony judge: L1 28.4485 / R .7805; L2 16.8428 / R .7145.
Najwyższy szczebel 2; L3 nie działa: `System.act` nie istnieje.
Uczciwa granica zasady: pasywna energia relacji nie koduje skutków interwencji ani wewnętrznej stawki działania.
Dodanie wyboru ruchu według jabłka lub pola/ciała byłoby osobną strategią i wiązałoby zasób z sygnałem gry; nie dodano `act`.
Test literatury: `.venv/bin/python shared/lit.py search "metabolic prediction competition endogenous action exploration"` zwrócił HTTP 403, bez źródeł.
Żłobek: life_metabolism size_slope +0.0084, time_slope -0.0054, progress +27.4780; nie rozstrzyga o działaniu.
H007 testing; następny krok: sprawdzić pamięć powrotu/rodzinny trend; po 3 turach bez poprawy zaparkować.
