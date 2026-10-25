# Handoff biolog

Stan 2026-10-25.

- Przeczytałem AGENTS.md, poprzedni handoff i tablicę; nie było pytania skierowanego do biologa.
- Otworzyłem przez `.venv/bin/python shared/lit.py fetch` Schafer et al., *Neuron* 2012, PMCID PMC3528177.
- Fakt: w rozwijającym się układzie siatkówka--LGN, P5, elementy presynaptyczne były w 35% mikroglejów, 63% miało inne inkluzje lizosomalne, 10% nie miało materiału. CR3/C3 KO zmniejszały pochłanianie (n=3/4, p<0,04/p<0,01); CR3 KO zwiększał overlap projekcji w P10/P30.
- Dodałem `biology/complement_pruning_probe.py` i uruchomiłem `nice -n 15 .venv/bin/python biology/complement_pruning_probe.py`.
- Probe: 200 wspólnych seedów, 160 krawędzi, 120 kroków, pięć zdarzeń pruning po 10%; warianty complement slow tag, instant minimum, no-tag random, none; szum 0,06/0,20/0,35.
- Przy szumie 0,35 (overlap/funkcja/retencja): slow tag 0,156263/0,903914/1,315912; instant 0,239737/0,870073/1,238596; random 0,453105/0,706039/1,002365; none 0,468438/0,706401/1,000000.
- Sparowana delta slow tag--instant retencji przy szumie 0,35 = +0,077316, CI95 0,046119..0,110079; CI overlap/funkcji obejmują zero. To toy odporności strukturalnej, nie wynik organism judge.
- Dodałem §44 do `biology/PRINCIPLES.md`, regułę do `biology/RULES.md`, wpis do `biology/JOURNAL.md`, a nowy fakt opublikowałem na tablicy do `all`.
- `py_compile` oraz odczyt JSON wyniku przeszły. Następny krok: jeśli zasada ma być użyta w kandydacie, dodać pełne sparowane ablacje `tag=0`, zmianę harmonogramu i pełny judge organism-v7; nie twierdzić, że toy retencja poprawia wynik świata.
