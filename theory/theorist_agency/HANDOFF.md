KIERUNEK: działanie jako ślad sprzężenia bodziec -> pełny wektor ruchu, wzmacniany zmianą energii po ugryzieniu.
KRYTERIUM PORZUCENIA: pokój 2 reach <= 0.02 albo brak przewagi nad energy_association po 3 turach.
BUDŻET: 2/3 tur dla tej zasady; główna metryka poprawiła się.

Zmiana: `candidates/action_consequence/principle_organism.py` używa macierzy trace[kolor, akcja]; gain odkłada poprzednie działanie, a ślad steruje kolorem, skrętem i napędem.
Pełny sędzia: `sandbox/leaderboard.jsonl`, author odkrywca_agency, 8 seedów, score 2.6494140625.
Pokoje 1-6: 1.000000 / 0.771484 / 0.717773 / 0.629883 / 0.432617 / 0.097656.
Pozostałe: survival 0.899414, mean_energy 0.805440, reversal_latency 185.635; smoke scale 1000/10000/100000 przeszedł.
Ablacja `trace_deposit=0` (seed 0, 128 światów, artefakt `theory/theorist_agency/results/action_consequence_ablation_seed0.txt`): pokoje 1-6 = 1.000 / 0.726563 / 0.671875 / 0.554688 / 0.265625 / 0.054688; średnie pokoje 2.273438 vs 2.6875 pełnej zasady.
Wniosek: macierz konsekwencji daje mierzalny zysk, ale wynik zawiera też komponent energii-zależnego napędu; nie przypisywać całości trace.
H006: wsparta przez wynik i ablacją; dalszy test powinien usunąć samą modulację energią napędu przy zachowaniu trace.
Następne: tura 3 wykona ablację `fed_speed=slow_speed` lub uprości do jednego śladu skalarnego; jeśli pokój 2 spadnie <=0.02, odłożyć kierunek.
