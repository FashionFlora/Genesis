# Wzrost przez skojarzenie metaboliczne

## Zasada

Twórz sensoryczny węzeł kolor-pozycja tylko po faktycznej aktywacji. Jego krawędź do preferencji koloru wzmacnia się, gdy po ugryzieniu wzrasta własna energia organizmu. Ślad użycia i waga maleją z czasem; węzeł znika, gdy oba są małe. Ten sam sygnał powoduje więc uczenie oraz zanik nieużywanej struktury.

## Stan eksperymentu

Pierwszy kandydat to `candidates/growth_metabolic_graph/principle_organism.py`. Jego pełny wynik `organism-v3` jest w toku. Sędzia sprawdza przejścia w ciągłym życiu, ale nie zapisuje predykcji ani szeregów `units`/`connections`; rozmiary mózgu 302, 1k, 10k i 100k są próbą dymną. Potrzebny jest osobny instrumentowany przebieg i ablacją wyłączonego przycinania.

## Prior art

Otwarto przegląd Faust, Gunner i Schafer, „Mechanisms governing activity-dependent synaptic pruning in the mammalian CNS” (Nat Rev Neurosci, 2021), przez `shared/lit.py fetch` z PMC8541743. Aktywnościowe przycinanie jest znanym mechanizmem; nie twierdzimy nowości dla tej ogólnej idei. Hipoteza H003 dotyczy połączenia rzadkiego wzrostu węzłów z metabolicznym wzmocnieniem i zanikiem.
