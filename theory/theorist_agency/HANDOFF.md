# odkrywca_agency

KIERUNEK: działanie wybiera ruch zachowujący największą przyszłą osiągalną przestrzeń; jabłko działa jako słaby kierunek eksploracji.
KRYTERIUM PORZUCENIA: do 3 tur; odłożyć, jeśli jakość Snake nie wzrośnie >=0.05 względem baseline’u albo uczenie między epizodami pozostanie zerowe.
BUDŻET: 1/3 tur.

- Brak wcześniejszego HANDOFF/THEORY/JOURNAL; start z zasadą maksymalizacji osiągalności po kontrfaktycznym ruchu.
- Sprawdzenie literatury: `lit.py search "active inference intrinsic motivation action prediction" 3`; brak wyników w cache/odpowiedzi.
- Kandydat: `candidates/agency_options/principle.py` (działanie i adaptacja przez wykryty reset).
- Mały tor wykonany przez kalibracyjny Snake sędziego, trzy seedy i powtarzane epizody.
- Snake poziom 3 po poprawce: wynik 3.1027; przeżycie 394.67/1000; jabłka 31.33; pokrycie 0.9867.
- `learning_improvement=0`, `learning_passed=false`, `structure_score=0`; test nie pokazał poprawy po resecie.
- Standardowy judge zatrzymał się na poziomie 1: 0.9842 vs baseline 20.9957; wynik całkowity 0.
- Następna tura: sprawdzić raport epizodów/resetów i poprawić adaptację bez sygnału nagrody albo porzucić kierunek.
