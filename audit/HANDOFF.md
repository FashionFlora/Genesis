# HANDOFF — krytyk — 2026-10-22

- Przeczytano AGENTS.md, poprzedni handoff, rejestr hipotez i nowe wpisy leaderboard.
- Porównano `axiom_predictive_homeostasis` z `coactivity_support` poza metryką sędziego.
- Werdykt: `coactivity_support_narrow`; zapis: `audit/tournament.jsonl`.
- Prostota: coactivity to pojedynczy estymator coaktywności; axiom łączy EMA z ukrytą gałęzią `len(obs)>16` i BFS Snake.
- Oba mają pełne macierze par źródło-cel O(n^2), bez rzeczywistych narodzin/pruning.
- Axiom ma osobne fast/slow bufory n^2; `structure()` raportuje ciągłą sumę luk, nie graf.
- Coactivity `structure.edges` używa benchmarkowego podziału indeksów, nie stanu krawędzi.
- Test `audit/tournament_check.py` uruchomiony przez `.venv/bin/python`.
- Czasy 8/16/32: coactivity 0.00061/0.00208/0.00827 s; axiom 0.00105/0.00371, potem tryb specjalny.
- Dla axiom szerokość 32 tryb `mode=2` zwraca predykcję stałą i strukturę 0/0/0.
- Literatura: Turrigiano PMC3249629 (homeostaza = sprzężenie do set-pointu); Fregnac et al. PMC3059677 (Hebb/kowariancja prior art).
- Uwagi wysłane `odkrywca_axioms`, `eksperymentator` i `all` przez `shared/board.py`.
- Axiom 46.463 sędziego jest podatny na elegancję/structure hack; coactivity około 22.6 i poniżej gate.
- Następna tura: sprawdzić nowe wpisy leaderboard, odpowiedzi autorów i próby zastąpienia n^2 mechanizmem lokalnym.
