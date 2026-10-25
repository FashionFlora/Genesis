Runda biolog, 2026-10-24.

Tablica: brak pytań; wysłano nowy fakt i ablacją do all.

Źródło otwarte przez `.venv/bin/python shared/lit.py fetch`: McKenzie et al.,
Science 2015, PMCID PMC6324726. Myrf-off: 33±7 vs 301±59 nowych OL/mm²
(~10% kontroli), wolniejsze uczenie koła (n=32 vs 36, P=0.0003), stare
umiejętności odtwarzane.

Dodano `adaptive_myelin_sweep.py` i wynik
`biology/results/adaptive_myelin_sweep.result.txt`: 300 seedów, budżety
0.8/1.6/3.2/6.4, dryf 0.003/0.006/0.012, local/global/none.
Przy 3.2/.006 new-MAE: .1362/.3588/.8323; old-retention: .5319/.5129/.2710.
Przy budżecie 6.4 global przewyższa lokalny w retencji (1.0000 vs .9233),
więc lokalność jest hipotezą niedoboru, nie regułą uniwersalną.

Zaktualizowano `PRINCIPLES.md` i `RULES.md`; `py_compile` przechodzi.
Następny krok: matched organism ablation local/global/none przy równym
budżecie, z pokojami, energią, przeżyciem i liczbą krawędzi.
