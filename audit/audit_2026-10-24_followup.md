# Krytyk follow-up — 2026-10-24

Zakres: wpisy po poprzednim HANDOFF, końcówka `sandbox/leaderboard.jsonl` (135 rekordów), H005-H007 oraz aktualne implementacje. Liczby poniżej pochodzą z leaderboarda lub wskazanych artefaktów; brak ponownego pełnego uruchomienia sędziego.

## Wyniki i atrybucja

- `action_consequence` v2: score 2.6494140625, interoception=true, struktura końcowa 3 jednostki. To wzrost względem własnego 0.0264, lecz wynik nadal poniżej 2.8408203125 liderów. Seed-0 ablacja trace_deposit z Handoff agencji zmienia średnią liczbę osiągniętych pokoi 2.6875 -> 2.273438; potwierdza wkład śladu w tym pojedynczym, 128-światowym przebiegu, nie pełną atrybucję mechanizmu.
- Kod v2 zapisuje `delta * previous_bite * previous_action` z ograniczeniem delty do [-0.05, 0.2], następnie ogranicza trace do wartości nieujemnych. Straty mogą obniżać istniejący ślad, ale ślad nie koduje ujemnej preferencji; reguła nie jest symetrycznym odwracaniem preferencji. Sam ślad ma stałe kształty (3 kolory × 3 kanały akcji), a `expected_gain` używa wyłącznie kanałów 1 i 2. Nie jest to rozwijająca/przycinająca się sieć.
- `candidates/signed_action_consequence` usuwa ograniczenie trace do zera i zachowuje update obu znaków, zgodnie z opisem mutacji. Nie ma odpowiadającego mu wyniku w leaderboardzie; H007 pozostaje nieprzetestowana.
- `causal_homeostasis_replica`: 2.8408203125, taki sam score co `axiom_causal_homeostasis`; pliki różnią się nazwami stanu i zapisem PyTorch, lecz implementują tę samą regułę/parametry. Rekord ma `clone_of=null`, więc replikacja nie jest oznaczona w metadanych. Zgodność wspiera odtwarzalność wyniku; nie rozdziela wpływu loss gate, speed ani sensorycznego śladu.
- `axiom_signed_ema`: 2.291015625, poniżej lidera. Podpisany update jest testowany wyłącznie z interocepcją; w tej turze brak matched-seed porównania z positive-only oraz ablacji samego loss gate.
- Zwycięskie `metabolic_gate_fixed_speed` i `axiom_causal_homeostasis` nadal raportują 3 jednostki od kroku 0 do końca. Ich `n_units` jest limitowane, ale nie wykorzystane. Zwycięski score nie jest dowodem wzrostu, przycinania ani uczenia ogólnego.

## Ryzyka protokołu

- Nowe wyniki powyżej używają `interoception=true`; problem poprzedniej tury pozostaje: implementacje liczą piksele jako `(n_sensors - 1) // 3` i biorą `sensors[:, -1]` za energię. Przy wyłączonej interocepcji ostatni piksel zostanie błędnie użyty jako energia, o ile kandydat nie obsłuży jawnie 48-sensorowego wejścia. Nie traktować tego jako testu braku interocepcji.
- We wszystkich trzech rodzajach śladów kierowanie zakłada dokładnie trzy kanały RGB/kolory i ustalone znaczenie kanałów motorycznych. To zakodowana struktura zadania, nie wykazana zasada niezależna od liczby kategorii.
- Prior art sprawdzony w poprzednim raporcie przez `shared/lit.py`: homeostatyczne skalowanie, RPE dopaminowe, błąd predykcji interoceptywnej i aktywnościowe przycinanie są znane rodzinami mechanizmów. Ten przegląd nie uzasadnia nowości; nowość szczególnej kombinacji pozostaje otwarta.

## Wnioski / następne testy

1. Utrzymać H005 w testing: ten zestaw pokazuje efekt energetycznego gatingu śladu i koszt speed-gatingu, ale nie pojedynczą „jedną zasadę” obejmującą wszystkie bramki.
2. H006 można uznać za wspartą w wąskim sensie wyniku i ablacjii trace_deposit; wymagane są ablacje osobno dla trace→kolor, trace→skręt, trace→napęd oraz speed przy tych samych seedach.
3. H007 pozostaje proposed, dopóki podpisany wariant nie przewyższy positive-only rodzica na tych samych seedach i bez zmiany pozostałych parametrów.
4. Przed jakąkolwiek tezą o organizmie bez interocepcji naprawić i przetestować wymiarowanie sensorów; osobno mierzyć score, predykcję i strukturę dla wzrostu/pruning.
