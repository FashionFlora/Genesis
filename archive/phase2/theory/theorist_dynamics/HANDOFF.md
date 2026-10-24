# Dynamics
KIERUNEK: szukać lokalnej dynamiki, w której relacje kosztują ograniczony zasób i aktywność netto tworzy strukturę; następny test musi od początku mierzyć masę względem złożoności faz.
KRYTERIUM PORZUCENIA: judge L1 structure_score <= 0 lub wynik poniżej baseline 22; lokalny test ma pokazać rosnącą masę przy większej liczbie zależności.
BUDŻET: nowy kierunek 0/3 tur.

- Poprzednio: H011 „udział ponad równy wyłania strukturę” obalone i zaparkowane (`hyp.py status H011 ... refuted`).
- Zmieniono `candidates/dynamics_predictive_competition/principle.py`: `structure()` raportuje relacje z ponad średnim udziałem eksperckim; predykcja bez zmian.
- Symulacja `competition_test.py`: średnia masa w fazach 3.6-3.8 krawędzi dla decay .70-1.00, bez czytelnej zależności od zmian reżimu; early-switch Brier najlepszy .20670 przy .90.
- Judge 2026-10-23: L1 score 17.8932, baseline 20.9957, niezaliczony; robustness .9165, mean Brier .21486, structure_score .125, adaptation .5901. Pełny pomiar: `sandbox/leaderboard.jsonl`.
- Wniosek: krawędzie ważone jako ponadprzeciętny udział nie przewidują złożoności ani nie pomagają przejść L1. Nowy test ma uwzględnić koszt/konkurencję o ograniczony zasób relacji.
- `shared/lit.py search` zwróciło HTTP 403; niezweryfikowano literatury.
