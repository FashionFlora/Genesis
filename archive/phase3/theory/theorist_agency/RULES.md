# Zasady z pomiarów

- `action_credit`: rooms_reached=0.0 po dwóch wcześniejszych pomiarach; kredyt ograniczony do ugryzienia nie wystarczył.
- `action_flux`: pierwszy pomiar z 2 seedami/skalę dał rooms_reached=0.0 z interocepcją; średni wiek 95.4.
- `action_flux` replika: 4 seedy/skalę (512 organizmów), rooms_reached=0.0 z interocepcją i bez niej na 302–100k; mean_age odpowiednio 105.70 i 61.82. Interocepcja wspiera przeżycie, ale jej kredyt działania nie przekłada się na przejście pokoju; większa skala nie zmieniła wyniku.
- Wcześniejsze `--no-interoception` (2 seedy/skalę) miało score=0.00390625 i jedno przejście do pokoju 2/256; 4-seed replika nie odtworzyła efektu.
- `action_directional_credit`, mutacja `axiom_sensorimotor_flow` z kredytem znaku poprzedniego skrętu, osiągnęła `rooms_reached=0.2871` na 512 światach; ablacją `action_rate=0` było `0.2891`. Żerowanie (11.78 vs 11.90) i wiek (428.0 vs 427.0) były niemal takie same: wynik należy przypisać przepływowi bazowemu, nie kredytowi skrętu.
- Test syntetyczny potwierdził, że dodatni przyrost energii zwiększa wyuczony skręt `0.70 -> 0.71`, lecz nie przekłada się to na poprawę w świecie organizmów. H005 zaparkowana po trzech turach bez potwierdzenia efektu.
- Mały świat kierunkowy (120 kroków, energia tylko ze zmniejszenia odległości do źródła): kredyt skrętu dał końcową odległość `0.00215`, ablacja `0.01096`; oba doszły do energii około `1.0`. Mały lokalny efekt nie odtworzył poprawy w organizerze.
# Wyniki odkrywcy_agency

- `action_rate` nie wniósł wykrywalnej korzyści w poprzedniej ablacji (0.2871 vs 0.2891); H005 parked.
- W organism-v2 wyłączenie interocepcji podniosło action_directional_credit z 0.2871 do 0.3672 (4 seedy/skala); obecne porównanie nie oddziela uczenia preferencji od kredytu skrętu.
- Homeostatyczny przepływ axiom_flow osiągnął 0.3398 z energią i 0.3672 bez niej; w obu warunkach survival=0. Wynik rooms_reached nie oznacza pełnego przeżycia.
- Judge jest wrażliwy na wejście interoceptywne; test no-interoception może wykryć efekt, bo wyłącza aktualizację sensorycznej wartości energią.
