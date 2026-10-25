# Krytyk: follow-up leaderboardu, 2026-10-24

## Zakres

- Przeczytano `AGENTS.md`, `audit/HANDOFF.md`, tablicę, rejestr hipotez, wpisy leaderboardu 137-144 oraz kod świeżych kandydatów.
- Wpisy po poprzednim raporcie: `axiom_gain_only` 2.805664; druga ocena `growth_signed_trace` 2.307617; `signed_action_consequence_positive_ablation` 2.384766; ponowna ocena `growth_metabolic_graph` 0.047852.
- Nie uruchamiano sędziego. Wartości i CI pochodzą z `sandbox/leaderboard.jsonl`; nie edytowano `sandbox/`.

## Audyt wyników i mechanizmów

- `axiom_gain_only` i rodzic `axiom_causal_homeostasis` mają odpowiednio 2.805664 (CI95 rooms 2.7043-2.9071) i 2.851563 (2.7517-2.9514), oba organism-v4, 1024 światów. To lokalny kontrast obcinania strat, nie dowód przewagi signed trace; przedziały marginalne zachodzą na siebie. Oba raportują stałe 3 jednostki od początku do końca.
- `signed_action_consequence` 2.503906 (CI 2.4016-2.6062) i positive-only 2.384766 (2.2777-2.4918) nie pobijają rodzica `action_consequence` 2.649414. H007 jest wsparta tylko dla wąskiego porównania signed kontra obcięcie do zera; brak per-world różnic lub wielu matched seedów ogranicza pewność. Nie traktować tego jako poprawy całej polityki.
- Wzrostowy wpis `growth_metabolic_graph` powtórzył słaby score 0.047852 (CI 0.0266-0.0691, survival 0.123). Kod `_grow` tworzy współdzieloną pulę kluczy kolor-piksel dla batcha, zaś `structure()` sumuje maskę `[batch, features]`: raport końcowy 486.625 i maksimum 2339.375 nie są liczbą jednostek mózgu na organizm i przekraczają limit 302 przez agregację. Krzywa nie dowodzi lokalnego wzrostu/przycinania ani oszczędności pamięci.
- Kandydaci o najlepszych wynikach nadal stosują ręcznie zadane trzy kategorie koloru, argmax ważony energią, geometrię oka dla skrętu oraz próg gryzienia. To jawnie zakodowany sensorimotor controller ze śladem, nie emergentne wyprowadzenie całej strategii z zasady. Nie znaleziono dowodu na bezpośredni odczyt ukrytego celu świata w przeglądanym kodzie.
- Prior art sprawdzono w otwartych źródłach odnotowanych w `audit/tournament.jsonl` i `theory/theorist_growth/THEORY.md`: m.in. dopaminowe błędy predykcji (PMC7804370), plastyczność homeostatyczna i aktywnościowe przycinanie. Ogólne związki metabolizmu, uczenia i pruning nie są nowością; nowość specyficznej implementacji nieustalona.

## Działania

- Uwagi o niepoprawnej mierze struktury wysłano `odkrywca_growth`.
- Uwagi o wąskim efekcie ablacji i stałej, ręcznie zdefiniowanej polityce wysłano `eksperymentator`, `odkrywca_agency` i `odkrywca_axioms`.
- Następny audyt: wymagać licznika globalnych slotów i per-organism occupancy w growth oraz matched per-world kontrastów dla znaków trace. H003 pozostaje zaparkowana; H014 jest dopiero proponowana.
