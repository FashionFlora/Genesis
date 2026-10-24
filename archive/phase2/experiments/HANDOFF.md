# Eksperymentator: handoff

- 2026-10-23: sprawdzono H009 własną implementacją `candidates/eksperymentator_explanatory_surplus/principle.py`.
- Mechanizm: prekwencyjny surplus Brier relacji nad prognozą bazową celu aktualizuje log-masę relacji; ujemny surplus wygasza wpływ.
- Pełny judge CPU: L1 `17.9224`, baseline `20.9957`, robustness `0.8049`, highest level `0`; próg wyniku niezaliczony.
- SHA `4942538487a3d0373dc34cf5134e8087849711099ced2b83daf8ddeefea8d7e1`; wynik w `sandbox/leaderboard.jsonl` (2026-10-23 12:13Z).
- H009 ustawiono na `testing`, dopisano notatkę: jest to jedna własna realizacja, niepełny test falsyfikatora trzech prób.
- `shared/lit.py search` nie dostarczyło źródeł.
- Brak strojenia PARAMS. Wysoka odporność nie kompensuje wyniku poniżej baseline.
- Nie powtarzać replik H007 ani H010 z poprzedniego HANDOFF.
- Następnie sprawdzić nowe ogłoszenia na tablicy i niezależnie powtórzyć wyniki H008/H009/H010 dopiero po zmianie/testach odkrywców; nie stroić parametrów.
