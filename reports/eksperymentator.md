# Eksperymentator

## H001: aktywny ślad jako wzrost i przycinanie

Pełny `organism-v6` sędziego dla `candidates/growth_trace` (1 batch, 1024 światy,
12000 kroków, 302 jednostki) dał score `0.0068359375` i przejście pokoju 1 w
`0.005859375` światów; wpis jest w `sandbox/leaderboard.jsonl` (autor
`eksperymentator`). Struktura proxy zmieniła się: jednostki `2.0 -> 2.680664`
(maks.) -> `2.666992` (koniec), połączenia `2.0 -> 3.361328 -> 3.333984`.

Ablacja `candidates/growth_trace_static_structure` zachowała identyczny mózg i
politykę, ale zwracała stałą strukturę `2/2`. Wynik był identyczny:
`0.0068359375`, z tą samą krzywą pokoi i przeżyciem; wpis jest w leaderboardzie.
Perturbacje parametrów bazowego kandydata dały score `0.0` dla czynnika `0.7`
i `0.0009765625` dla `1.4`.

Wniosek: próg wyniku H001 jest spełniony, lecz wzrost/przycinanie jako raportowana
struktura nie wyjaśnia wyniku. Właściwy wkład trwałości śladu pozostaje
nierozstrzygnięty; próba `trace_decay=0` nie dostała slotu GPU i została przerwana
bez wyniku (nie liczyć jako rezultat).

## H006: pojedynczy ślad energii bez kontekstu

Hipoteza przewidywała, że jedna tablica preferencji koloru, aktualizowana
opóźnioną zmianą energii i poprzedzona zanikiem śladu kwalifikacji, zachowa
większość efektu `dynamics_energy_trace` bez drugiego wymiaru kontekstu. Kandydat
`candidates/energy_trace_simple/principle_organism.py` przeszedł pełny oficjalny
`organism-v6` (1 batch, 1024 światów, 12000 kroków, 302 jednostki) z wynikiem
`0.7314453125`; wpis autora `eksperymentator` jest rekordem 148 w
`sandbox/leaderboard.jsonl` i przewyższa lidera `dynamics_energy_trace`
(`0.650390625`). Średnie przeżycie wyniosło `0.7734375`, a room reach miał
95% CI `[0.67731, 0.78558]`. Wariant z mnożnikiem parametrów `0.7` osiągnął
`0.6337890625` (CI room reach `[0.58357, 0.68401]`).

Dopasowana ablacja `candidates/energy_trace_simple_ablation` z identycznym
ruchem i `learning_rate=0` uzyskała `0.0712890625` (przeżycie `0.8896484375`,
CI room reach `[0.05376, 0.08882]`), czyli delta room reach `+0.66015625`.
To izoluje wpływ aktualizacji śladu w pełnym sędzim; rekord ablacji jest 149.
Hipoteza H006 została oznaczona `supported` w `shared/hypotheses.json`.

Ograniczenia: mózg raportuje stałe 3 jednostki niezależnie od `n_units`; nie
wykonano jeszcze permutacji pikseli ani testu `no_interoception`, więc nie ma
wniosku o skalowaniu ani o niezależności od kolejności kanałów. CLI `judge.py
--organism` ma niespójność v6 (`social_group_size`), dlatego wynik zapisano
bezpośrednim wywołaniem oficjalnego `sandbox/organism_judge.py` i jego
`append_result`, bez modyfikacji sandbox.

## H010: znormalizowany kredyt metaboliczny

Niezależna para dla H010 użyła oficjalnego organism-v6 (1 batch = 1024
światy, 12000 kroków, 302 jednostki). `candidates/dynamics_energy_ratio`
osiągnął `rooms_reached=0.064453125`, 95% CI `[0.04800798, 0.08089827]`.
Dopasowana ablacja `candidates/dynamics_energy_ratio_ablation`, z
`credit_scale=0`, osiągnęła `0.0712890625`, CI `[0.05375915, 0.08881897]`.
Delta wyniosła `-0.0068359375`; przedziały zachodzą na siebie, a wariant z
normalizowanym kredytem wypadł gorzej. H010 oznaczono `refuted`; oba rekordy
mają autora `eksperymentator` w `sandbox/leaderboard.jsonl`.

## H011: wspólny budżet pamięci kontekstowej

Niezależna, sparowana replikacja H011 użyła pełnego organism-v6: 1 batchu
(1024 światów), 12000 kroków i 302 jednostek. Kandydat
`candidates/axiom_metabolic_context_budget` z projekcją preferencji do wspólnego
budżetu `capacity=1` osiągnął `rooms_reached=0.7314453125`, 95% CI
`[0.67938176, 0.78350887]`, nominal survival `0.7314453125`. Dopasowana kontrola
`candidates/axiom_metabolic_context_budget_ablation` (ta sama pamięć, projekcja
wyłączona przez `capacity=1e6`) osiągnęła `0.76171875`, CI
`[0.70742394, 0.81601356]`, nominal survival `0.740234375`. Delta kandydata względem
kontroli wynosi `-0.0302734375`, a przedziały ufności zachodzą.

Pierwsza para nie wspiera H011: skończony wspólny budżet nie poprawił room reach
ani przeżycia. H011 pozostaje `testing`, bo prerejestr wymaga trzech par; do
werdyktu potrzeba jeszcze dwóch. Oba przebiegi są zapisane w
`sandbox/leaderboard.jsonl` z autorem `eksperymentator`; sędzia raportuje stałe
3 jednostki i 6 połączeń przez całe życie. Pełne wyniki nominalne i perturbacje
PARAMS wykonano bez strojenia.

## H005: korelacja przy skończonej pojemności

Niezależna replikacja `candidates/axiom_capacity_correlation` oficjalnym
`organism-v7` (1024 światy, 50000 kroków, 302 jednostki) dała
`rooms_reached=0.1064453125`, CI95 `[0.0821167401, 0.1307738849]`, survival
`0.142578125`; rekord autora `eksperymentator` jest wierszem 166
`sandbox/leaderboard.jsonl`.

Matched ablation `axiom_capacity_correlation_ablation` ukończona tym samym
organism-v7 (wiersz 169): `rooms_reached=0.033203125`, CI95
`[0.01685583,0.04955042]`, survival `0.2763671875`, mean energy
`0.2448112`. Wobec bazowego wiersza 166 (`0.1064453125`, survival
`0.142578125`) delta rooms wynosi `+0.0732421875`, a delta survival
`-0.1337890625`; CI rooms są rozłączne. Korelacja poprawia przejście pokoi
kosztem przeżycia ponad prerejestrowany próg `0.05`, więc nie jest prostą
zasadą dominującą lidera. H005 pozostaje `testing` (wymagane trzy pary), z
praktycznie obalonym wariantem bez kosztu przeżycia.

## H014: retencja zależna od rezerwy

Wybrano H014 po audycie: istniejąca kontrola odkrywcy zeruje `learning_rate`,
więc usuwa całe uczenie i nie izoluje zależności retencji od rezerwy. Dodano
`candidates/life_metabolic_adaptive_retention_constant`, który ustawia
`energy_coupling=0` i pozostawia resztę uczenia bez zmian. Pełny sędzia
kandydata uruchomiono z domyślnym protokołem, ale po 60 minutach bez zapisu
wyniku przerwano aktywny proces. Nie uruchomiono kontroli, więc brak własnej
pary pomiarowej i brak wniosku przyczynowego.

Odkrywca ma nowszą pełną parę v7 (wiersze 175/178 leaderboard): rooms
`0.7939453125` vs `0.79296875`, delta `+0.0009765625` z nakładającymi się CI;
survival `0.607421875` vs `0.6142578125` na korzyść kontroli. Kontrola z
`learning_rate=0` wyłącza całe uczenie, więc ta para nie izoluje retencji.
Probe `audit/axiom_retention_budget_probe.result.json` pokazuje, że
`energy_coupling=0` zmienia odpowiedź, ale to nie zastępuje pełnej ablacji.

Moja własna pełna ocena kandydata została przerwana po 60 minutach bez wpisu;
kontrola stałego zapominania nie została uruchomiona. Nie ma własnego wyniku ani
wniosku przyczynowego. H014 pozostaje `testing`; następna próba wymaga
ukończenia obu przebiegów w tej samej turze.

## H012: brama gotowości metabolicznej

Niezależna para H012 użyła pełnego `organism-v7` (1024 światy, 50000 kroków,
302 jednostki) bez strojenia `PARAMS`. Kandydat
`candidates/dynamics_metabolic_gate` osiągnął `rooms_reached=0.50390625`, CI95
`[0.45932403, 0.54848847]`, survival `0.5751953125`, CI95
`[0.54490383, 0.60548680]`; rekord jest w `sandbox/leaderboard.jsonl`.

Matched ablation `candidates/dynamics_metabolic_gate_ablation` wyzerowała tylko
`energy_coupling` i `readiness_recovery`, zachowując resztę kontrolera. Osiągnęła
`rooms_reached=0.0`, CI95 `[0.0, 0.0]`, survival `0.0`, CI95 `[0.0, 0.0]`.
Delta kandydat-kontrola wynosi `+0.50390625` dla pokoi i `+0.5751953125` dla
przeżycia; przedziały są rozłączne. Perturbacje kandydata 0.7x/1.4x dały
odpowiednio rooms `0.4833984375` i `0.3916015625`, więc efekt jest dodatni,
choć maleje przy 1.4x.

To wspiera mechanizm H012 w tej jednej parze: energia przywraca gotowość, a
wysiłek zgryzu ją zużywa. H012 pozostaje `testing`, bo prerejestr wymaga trzech
par; nie jest to jeszcze dowód odporności między światami. Ograniczenie
interpretacji: kontrola wyłącza `energy_coupling` i `readiness_recovery` razem,
więc nie rozdziela ich wkładów; nie wykonano też wariantu `no_interoception`.

## H021: retencja śladu zależna od trendu energii

Podjęto niezależną replikację kandydata
`candidates/eksperymentator_energy_trend_retention` i jego matched ablation,
która zeruje tylko `trend_coupling`. Pełny judge organism-v7 wystartował, ale
został przerwany po około 10 minutach przy GPU obciążonym przez równoległe
przebiegi. Nie powstał wpis leaderboard, a kontrola nie została uruchomiona.

Lokalny CPU probe przy energii 0.5 -> 0.7 dał masę śladu 1.967 dla kandydata i
1.931 dla kontroli. To potwierdza jedynie, że parametr zmienia retencję w
przewidzianym kierunku; nie jest testem skuteczności organizmu. H021 pozostaje
`testing`, bez wniosku. Potrzebna jest pełna sparowana ocena v7, a do decyzji
zgodnej z prerejestracją trzy pełne pary.
