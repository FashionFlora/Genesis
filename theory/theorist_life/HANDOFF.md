KIERUNEK: życie i zasoby — zbadać, czy lokalna pamięć metaboliczna poprawia
eksplorację kosztem przeżycia, oraz jaka reguła alokuje zasoby między pamięć,
żerowanie i utrzymanie organizmu. Adaptacyjna normalizacja skali nie ma przewagi
w dotychczasowym sparowanym v7; następna tura wyspy to ewolucja tego kierunku,
zaczynając od `life_metabolic_fixed_scale_budget` i jawnego kosztu survival.

KRYTERIUM PORZUCENIA: nie porzucać efektu pamięci metabolicznej bez pełnego
sparowanego v7 i ablacji. Dla nowej reguły alokacji: wymagać >=1024 wspólnych
światów, 50k kroków, istotnego sparowanego zysku `rooms_reached` (95% CI ponad
zero, delta >=0.05) bez spadku survival większego niż 0.02; próg mierzy
praktyczną korzyść netto, nie samą eksplorację. Słaby efekt w smoke nie rozstrzyga.

WYNIK 2026-10-25:
- Pełne v7: adaptacyjny 0.287109 rooms (CI [0.252028, 0.322190]), survival
  0.812500; stały 0.382812 (CI [0.344420, 0.421205]), survival 0.771484.
- Sparowane fixed-minus-adaptive, n=1024: rooms +0.095703, CI
  [+0.052685, +0.138721]; survival -0.041016, CI [-0.069308, -0.012723].
  Efekt statystycznie wspiera stałą skalę dla pokojów, ale nie spełnia progu
  korzyści netto z powodu kosztu życia. Szczegóły: `metabolic_scale_paired_assay.md`.
- Kontrola różni się tylko normalizatorem delta energii; wspólne seedy (7),
  zgodne rodziny światów. Parametry fixed w judge są niestabilne (rooms 0.319336
  przy factor 0.7; 0.487305 przy 1.4). Leader dynamics nadal 0.8.
- Limit n_units=302 nie wywołał wzrostu: organizm pozostawał przy 3 jednostkach;
  skalowanie 1e3..1e5 nie zostało ocenione.

NASTĘPNIE:
1. W turze ewolucji szukać reguły metabolizmu, która zachowuje aktywność pamięci
   przy niskiej rezerwie, ale ogranicza koszt przeżycia; zmieniać jeden mechanizm.
2. Każdy zwycięski wariant przeprowadzić przez pełny v7 oraz matched ablation;
   zapisać rooms i survival z CI, w tym perturbacje PARAMS.
3. Przed GPU sprawdzić nvidia-smi; nie przekraczać 40 GB ani limitów CPU/RAM.
