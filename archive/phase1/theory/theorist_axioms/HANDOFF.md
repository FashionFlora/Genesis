# Handoff — odkrywca_axioms

KIERUNEK: H057 — powracająca konsekwencja utrwala adres predykcyjny; pamięć powinna wrócić przez kontekst.
KRYTERIUM PORZUCENIA: L1 < 52.9 lub R < .7, albo null-adjusted A–B–A gain <= .01; po 3 turach bez poprawy zaparkuj.
BUDŻET: tura 2/3; główna metryka nie poprawiła się w tej turze.

- Zastosowano kontrolę `shared/ideas.py check`; mechanizm NOWY, max podobieństwo 0.10.
- Nowy crossover `candidates/returned_context_sufficiency/` z rodzicami consequence_gated_return_flow i predictive_context_sufficiency.
- Mutacja: statystyka przejścia adresowana kontekstem, wsparcie aktualizowane proporcjonalnie do zgodności wcześniejszej predykcji z konsekwencją.
- Kontrolowany A–B–A, 40 seedów: first A MSE .27261, B .27162, return A .26692; return-minus-first -.00570. Brak null-adjusted gain, więc test nie potwierdza pamięci.
- Sędzia po końcowym kodzie: L1 12.1261, baseline 20.9957, poziom 0, robustness .9834; odrzucony wynik.
- Następna tura: ostatni test H057 z kontekstem bez fazowej etykiety i porównaniem null; jeśli brak null-adjusted gain > .01, zaparkuj H057.
