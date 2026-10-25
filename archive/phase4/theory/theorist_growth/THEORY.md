# Wzrost przez skojarzenie metaboliczne

## Zasada

Twórz sensoryczny węzeł kolor-pozycja tylko po faktycznej aktywacji. Jego krawędź do preferencji koloru wzmacnia się, gdy po ugryzieniu wzrasta własna energia organizmu. Ślad użycia i waga maleją z czasem; węzeł znika, gdy oba są małe. Ten sam sygnał powoduje więc uczenie oraz zanik nieużywanej struktury.

## Stan eksperymentu

Mutant `candidates/growth_signed_trace/principle_organism.py` łączy rzadki ślad metaboliczny z eksploracją i napędem zależnym od energii. Pełny wynik organism-v4: score 2.307617, przeżycie 0.922852, średnio 34.623 aktywne jednostki na organizm przy maksimum 35.746 i limicie 302. To poniżej lidera 2.840820.

Audyt `growth_audit.py` porównuje pruning włączony/wyłączony na jednym seedzie przez 6000 kroków. Bez pruning wynik behawioralny był lepszy (2.875 vs 2.375 średnich pokoi; przeżycie 1.0 vs 0.875), choć utrzymywał 48 zamiast 36.875 aktywnych jednostek/osobnik. Oba warianty alokowały 1203 B/osobnik, bo dense sloty są współdzielone w batchu; logiczne usunięcie jednostki nie zwalnia bufora. Podwojenie boków pokoi spowodowało wymarcie do kroku 4096. To audyt jednego seedu, nie pełny wynik sędziego.

Każdy węzeł ma pojedynczy związek wagowy z kolorem, więc liczba połączeń równa liczbie węzłów nie opisuje odrębnej struktury. Sędzia nie wystawia osobnej straty predykcji; audyt raportuje skumulowaną skuteczność ugryzień po odwróceniu koloru jako proxy zachowania.

## Prior art

Otwarto przegląd Faust, Gunner i Schafer, „Mechanisms governing activity-dependent synaptic pruning in the mammalian CNS” (Nat Rev Neurosci, 2021), przez `shared/lit.py fetch` z PMC8541743. Aktywnościowe przycinanie jest znanym mechanizmem; nie twierdzimy nowości dla tej ogólnej idei. Hipoteza H003 dotyczy połączenia rzadkiego wzrostu węzłów z metabolicznym wzmocnieniem i zanikiem.
