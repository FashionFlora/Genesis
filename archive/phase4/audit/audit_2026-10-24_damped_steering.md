# Audyt krytyka: damped_steering_homeostat — 2026-10-24

## Wynik

- Nowy rekord `damped_steering_homeostat` ma organism-v4 score **2.7587890625**.
- Rodzic/lider `axiom_causal_homeostasis` ma score **2.8515625** w tym samym protokole; różnica to -0.0927734375.
- Oba rekordy mają 6000 kroków, 1024 światy, `batches=8` i interocepcję. Wpis kandydata ma `baseline=null`, `clone_of=null` i nie zawiera agregacji po ośmiu seedach organizmu. `batches=8` nie jest dowodem testu 8-seed matched.
- Rekord skali uruchamia tylko smoke test 64 kroków dla 1000/10000/100000 jednostek; nie mierzy tam zachowania ani osiągania pokoi.

## Zgodność z hipotezą

- H012 przewiduje lokalny stan relaksacji, który łączy bearing wzrokowy z pamięcią kierunku metabolicznego. Kod ma `turn_state`, ale aktualizuje go wyłącznie z `desired_turn` obliczonego z bieżącego obrazu (`principle_organism.py:53-57`). Ślad energii wybiera kolor (`:49-53`), lecz nie zapisuje ani nie dodaje kierunku działania.
- Różnicę względem rodzica stanowią parametr `turn_relaxation`, jeden skalar `turn_state` i zamiana natychmiastowego `turn` na filtr pierwszego rzędu. `trace`, speed, bite i wybór celu pozostają te same.
- Test jednostkowy z identycznym obrazem i energiami `[0.5]*5` oraz `[0.1,0.9,0.1,0.9,0.1]` dał identyczne wartości `turn` (0.225, 0.34875, 0.4168125, ...), a zmienił tylko speed (0.575 vs 0.395/0.755). To obala tezę, że energia jest pamięcią kierunku w nowym module.

## Prior art i wniosek

- Otwarty przez `shared/lit.py` artykuł Zhao et al., *Walking is like slithering* (PNAS 2022, PMC9477242), opisuje ciągłe modele kinematyczne locomocji; nie stanowi dowodu dla reward-free homeostazy Genesis, ale pokazuje, że samo wygładzanie/ciągła kinematyka nie jest nową zasadą biologiczną.
- Wynik jest niższy od lidera, więc nie ma dowodu poprawy rooms/survival. H012 pozostaje niezweryfikowana; do rozstrzygnięcia potrzebny jest matched parent vs candidate na tych samych ośmiu seedach oraz ablation `turn_relaxation=1`/brak `turn_state`, z osobnym raportem rooms i survival.
