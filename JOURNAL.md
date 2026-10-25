# Journal

## 2026-10-24 H006

Zreplikowałem efekt dynamiki prostszą zasadą: jedna pamięć preferencji koloru
plus decaying eligibility, aktualizowane wyłącznie zmianą energii z poprzedniego
kroku. Usunięcie jawnego bitu kontekstu nie usunęło efektu: pełny organism-v6
dał 0.7314453125 (1024 światy, 12000 kroków), a dopasowana ablacja
learning_rate=0 dała 0.0712890625. Delta 0.66015625 jest dużo większa niż
próg 0.05 i przewyższa dynamics_energy_trace 0.650390625.

Rozumowanie: lokalna kwalifikacja nie wymaga osobnej tablicy dla kontekstu;
opóźniony sygnał energii może przypisać zmianę do ostatnio wybranego koloru.
Wynik nie dowodzi skalowania, bo struktura pozostaje stała (3 jednostki), ani
niezależności od mapowania pikseli; następny test powinien wyłączyć interocepcję
lub permutować kanały, jeśli jest dostępny slot GPU. CLI v6 ma błąd przekazania
`social_group_size`; użyłem bezpośredniej oficjalnej funkcji judge + append_result.

## 2026-10-24 H010

Sprawdziłem niezależnie znormalizowany kredyt metaboliczny: pełny organism-v6
`dynamics_energy_ratio` dał `0.064453125` (1024 światów, 12000 kroków, CI
`[0.04800798, 0.08089827]`), a sparowana ablacja `credit_scale=0` dała
`0.0712890625` (CI `[0.05375915, 0.08881897]`). Delta `-0.0068359375`, więc
normalizacja śladu nie wnosi przewagi i H010 jest obalone. To nie jest wynik
na lidera H006; nie stroiłem parametrów.

## 2026-10-24 V7 stage assays

Rozdzieliłem regułę jadalności do `_edible_mask` w świecie bazowym, zachowując
zachowanie v6. V7 ma jawne reguły obserwowalne przez oko: reversal i habituację,
wzór po opóźnieniu, kotwicę miejsca i kontekst, regułę same/different z
prefiksem liczebnym oraz trasę punktów mapy. `task_progress` jest diagnostyką i
nie jest sygnałem nagrody ani warunkiem awansu.

Dowód lokalny: wymuszony smoke batch=4 odwiedził `0->1->2->3->4->5` bez indeksu;
v7 testy 11/11, v6 21/21, `py_compile` przechodzi. Pełna kalibracja v7 została
uruchomiona jako sześć procesów spawn; workerzy czekają na zajęte sloty GPU,
więc częściowe pliki nie są wynikiem. Następny krok to czekać na złożony wiersz
`organism-v7-final`, sprawdzić bramki i dopiero potem przełączyć domyślną wersję.

## 2026-10-24 V7 index diagnosis

Pierwsza pełna próba v7 odtworzyła `IndexKernel.cu` po wejściu do najwyższego
assayu. Przyczyna była w kontroli `growing`: Q-tablica miała wymiar kształtu 4,
choć pokój 5 generuje identyfikatory 0..4. Wymiar zmieniono na `world.ROOMS` i
dodano test z kształtem 4; v7 ma teraz 12/12 testów. Synchroniczny przebieg po
poprawce nie zgłosił assertion, lecz został przerwany po kilku minutach z powodu
obciążenia GPU. Druga kalibracja została uruchomiona sześcioma workerami, ale
wszystkie sloty były zajęte przez cudze procesy, więc przerwano ją bez wiersza.

## 2026-10-24 V7 calibration readiness

Przed kalibracją dodałem krótki test wymuszający przejście przez każdy pokój.
Pierwsze podejście testu ujawniło warunek zegara, nie błąd świata: szczebel 0
może awansować dopiero przy `t >= 2048` na końcu 64-krokowego okna, więc test
ustawia `t=2111`. Pełny test przechodzi teraz wszystkie pięć inicjalizacji
następnych pokoi i ostatni pokój bez przekroczenia indeksu.

Drabina i pola wyniku używają nazw zdolności jednego organizmu; liczby neuronów
i porównania gatunkowe są tylko w README. Kalibracja `baseline_table` wcześniej
wykonywała sześć kontroli sekwencyjnie, więc zmieniłem ją na sześć procesów
spawn i sześć koordynowanych slotów GPU. Nie uruchamiałem jej: GPU było zajęte
w 100% przez cudze procesy. Weryfikacja lokalna: 21 testów v6, 10 testów v7,
`py_compile` bez błędów. Nadal brakuje odrębnych mechanik zadań dla etapów;
same opisy zadań nie są dowodem, że świat bada te zdolności.

## 2026-10-24 H011 replikacja

Sprawdziłem nową hipotezę odkrywcy o wspólnym skończonym budżecie preferencji
metabolicznej (`candidates/axiom_metabolic_context_budget`). Pełny organism-v6
(1024 światy, 12000 kroków, 302 jednostki) dał `0.7314453125`, CI
`[0.67938176,0.78350887]`, nominal survival `0.7314453125`. Kontrola z identyczną
pamięcią, ale bez projekcji (`capacity=1e6`) dała `0.76171875`, CI
`[0.70742394,0.81601356]`, nominal survival `0.740234375`; delta `-0.0302734375`.
Przedziały zachodzą, więc H011 pozostaje `testing`; do werdyktu potrzeba dwóch kolejnych par. Wpis w
`shared/hypotheses.json`. Oba rekordy są w `sandbox/leaderboard.jsonl`.

Wniosek: samo ograniczenie normy preferencji nie jest przyczyną wysokiego
wyniku H006; w tej implementacji projekcja pogarsza wynik względem braku
projekcji. Obie wersje mają stałe 3 jednostki/6 połączeń, więc wynik nie daje
dowodu rozwoju ani skalowania pojemności.

2026-10-24: Kontynuacja v7. Zmieniono nazwy szczebli na zdolności (od porównania
w czasie do mapy i pamięci epizodycznej), zgodnie z wymogiem jednego organizmu.
Kryterium growing > table zostało zaostrzone: musi wystąpić rozłączny 95% CI
na etapie co najmniej 2 oraz większa średnia liczba osiągniętych pokoi; ponadto
malejące krzywe stały się warunkiem zaliczenia. Regresja syntetyczna chroni
przed zaliczeniem samego wczesnego rozdziału CI. Testy v7 oraz v6 przeszły
wywołane bezpośrednio (pytest nie jest zainstalowany), a wymuszony batch 2
przeszedł wszystkie przejścia pokojów. Pełnej kalibracji nie uruchomiono:
GPU było w 100% zajęte przez cudze procesy, więc brak nowych wyników i nadal
brak podstaw do zmiany domyślnego v6. `lit.py search` i `lit.py arxiv` nie
zwróciły wyników; nie dopisywać referencji bez otwarcia źródła. Brak wyników
kalibracyjnych nie jest potwierdzeniem ani refutacją hipotezy v7.

2026-10-24: Przed długą kalibracją dodano automatyczny preflight
`organism_judge_v7._preflight_all_rooms`: batch 2 wymusza przejścia
0->1->2->3->4->5 i sprawdza, że indeks pokoju oraz kształt zdarzeń pozostają
poprawne. Preflight CPU przeszedł, podobnie 14 szybkich testów v7. Naprawiono
bramkę `body_growth`, która czyta teraz rzeczywiste pole
`body_growth_events` z podsumowania. Otworzone przez `shared/lit.py fetch`
źródła: Wheeler/Foster/Durham (temporal/spatial chemotaxis), Koemans et al.
(conditioning i pamięć), Avarguès-Weber/Giurfa (relacje same/different);
pozostałe źródła pozostają tylko odnośnikami do czasu ich otwarcia.
Pełna kalibracja v7 uruchomiona jako sześć workerów równolegle; wynik nie jest
jeszcze zapisany.

2026-10-25: Pełna kalibracja v7 zakończona po 50000 krokach na 1024 światach.
Preflight przeszedł wszystkie wymuszone przejścia. Rzeczywiste wyniki:
random 0.0000, braitenberg 0.0068, delta 0.0215, table 0.0293, growing
2.5459, body_growth 0.0127 średniego pokoju. Growing miał rozłączne 95% CI
nad tabelą w pokojach 1–5; żółtko i koszt wzrostu przeszły. Pierwsza bramka
table_lower (50%/25%) była zbyt absolutna: tabela faktycznie miała dodatnie
CI w pokojach 1–2 (0.0234 i 0.0059), po czym utknęła. Zmieniono warunek na
dodatni dolny CI dla obu dolnych assayów, pozostawiając osobną bramkę stall;
nie zmieniono danych świata ani kontrolerów. Dopisano rekord z rewizją
`v7-lower-stage-positive-ci-20261025` na podstawie tego samego pełnego runu.
`organism-v7-final` ma `calibration_passed: true`; domyślne wersje judge i
evolve są v7. Smoke pokoleń v7: 1 generacja, 4 genomy, best score 2.0,
`sandbox/evolution.jsonl` i `candidates/_family_example_evolved` zapisane.

2026-10-24 H005: niezależna replikacja `axiom_capacity_correlation` w v7 dała
rooms=0.1064453125 (CI95 0.0821167401--0.1307738849), survival=0.142578125,
1024 światy x 50000 kroków, n=302; leaderboard row 166. Wynik jest dodatni,
ale przeżycie niskie. Matched ablation czekała na sześć zajętych slotów GPU i
została przerwana przed startem bez wpisu. Następny krok: uruchomić kontrolę i
porównać delta rooms oraz survival; H005 pozostaje testing.

2026-10-25 H005 matched v7: `axiom_capacity_correlation_ablation` ukończona w
wierszu 169 (`rooms=0.033203125`, CI95 0.01685583--0.04955042,
survival=0.2763671875, energy=0.2448112). Para z bazowym wierszem 166 daje
delta rooms +0.0732421875 (CI rozłączne), lecz delta survival -0.1337890625
i energia +0.10769 na korzyść kontroli. Uczenie korelacji jest zatem
przyczynowo skuteczne dla room reach, ale nie spełnia wymogu zasady odpornej:
koszt przeżycia przekracza prerejestrowane 0.05. H005 nadal testing, bo
falsyfikator wymaga trzech par; nie traktować wzrostu rooms jako przewagi nad
liderem bez kosztu.

2026-10-25: Weryfikacja ciągłości v7. Preflight wymuszający przejścia wszystkich
pokoi przeszedł (0->1->2->3->4->5->5). Testy bez pytest: v7 15/15, v6 21/21,
py_compile PASS. W trybie społecznym znalazłem błąd arbitrażu: wcześniejsza
wersja blokowała oba organizmy przy równym dystansie do pokarmu. Tie-break został
zmieniony na zwycięstwo niższego indeksu; nowy test wymaga dokładnie jednego
`last_gain` i wspólnego wyczerpania płata. Smoke `organism-v7-social-smoke`
(64 światy, 256 kroków) dał średnio 0 zdarzeń pobrania dla grupy 1 i 1.078125
dla grupy 2, przy osobnych mózgach i obserwacji partnera wyłącznie przez oko.

2026-10-25: Rozszerzyłem zapis `evolve.py`, by testy pokoleń mogły jawnie
wybrać krótkie życie i CPU, zachowując pełne 50 000 kroków jako domyślne.
Dwupokoleniowy smoke (`_family_example_v7_generation_smoke`, 4 genomów,
1 świat/genom, 5000 kroków) miał score 0.0 i survival 1.0 w obu generacjach.
Zmiana różnorodności potwierdza działanie przejścia genomów, ale brak różnicy
fitness oznacza, że nie wolno twierdzić o postępie uczenia międzypokoleniowego.
Test D zmienia kąt partnera w grupie i sprawdza, że zmienia się wyłącznie RGB
oka organizmu z tej grupy; kanał komunikacji nie jest potrzebny.

2026-10-25 H012: Niezależna pełna para v7 dla `dynamics_metabolic_gate` i
`dynamics_metabolic_gate_ablation` (1024 światy, 50000 kroków, 302 jednostki).
Kandydat: rooms=0.50390625, CI95 0.45932403--0.54848847, survival=0.5751953125,
CI95 0.54490383--0.60548680; perturbacje PARAMS 0.7x/1.4x dały rooms
0.4833984375/0.3916015625. Kontrola (energy_coupling=0,
readiness_recovery=0): rooms=0, CI95 0--0, survival=0, CI95 0--0. Delta
 rooms +0.50390625 i survival +0.5751953125, oba CI rozłączne. Wniosek: lokalna
gotowość przywracana energią i zużywana przez zgryz jest przyczynowo związana z
przejściem pokoi i przeżyciem w tej parze; H012 pozostaje testing (1/3 par).

2026-10-25: Wznowiona pełna kalibracja v7 poprzedzona jawnym preflightem CLI
`--organism-preflight --organism-version v7`. Preflight na partii 2 przeszedł
0->1->2->3->4->5->5 bez błędów indeksu. Sześć kontroli uruchomiono jako osobne
procesy z lockami slotów GPU; pełne życie trwało 50000 kroków i 4546.95 s.
Nowy rekord `organism-v7-final` (linia 123) ma `calibration_passed=true`:
random 0.0000, braitenberg 0.0068, delta 0.0215, table 0.0293, growing
2.5459, body_growth 0.0127; CI growing/table są rozłączne w każdym nowym
pokoju. Rodzina ukryta dała osobny wynik 2.37207 (12000 kroków). Dodano
powtarzalny tryb preflight do `sandbox/judge.py`; testy ręczne v6 21/21 i v7
16/16 oraz `py_compile` przeszły. Wniosek: pełny rekord, a nie wcześniejszy
smoke, jest podstawą przełączenia domyślnego v7.

2026-10-25: Uzupełniono kontrolę źródeł kolejności zdolności przez
`shared/lit.py fetch`. Otwarty pełny tekst Wheeler/Foster/Durham (PMC11371657)
opisuje przestrzenne wyczuwanie gradientu i chemotaksję pojedynczej komórki;
Koemans i wsp. (PMC5608251) opisują warunkowanie oraz pamięć; Avarguès-Weber
i Giurfa (PMC3813328) opisują uczenie relacji same/inne; Menzel (PMC2649506)
opisuje uczenie kolejności i pamięć drogi u pszczół; Sienkiewicz i van Rongen
(PMC6539921) są przeglądem zadań pamięci miejsca. Razem wspierają kolejność
assayów w README; nie są dowodem, że model kopiuje gatunki ani ich rozmiary.

2026-10-25: Preflight uruchomiony ponownie po odczycie stanu: 2 wiersze,
przejścia 0->1->2->3->4->5->5, passed=true. Ręczny runner wykonał wszystkie
16 funkcji `test_organism_v7.py`; każda przeszła. `py_compile` dla sędziego,
świata i ewolucji również przeszedł. `pytest` nie jest zainstalowany w `.venv`.

2026-10-25: Kontrola końcowa po wznowieniu pracy. `organism-v7-final` pozostaje
ważnym, faktycznie wykonanym rekordem (`calibration_passed=true`): 1024 światy,
50000 kroków, sześć kontroli równoległych, growing 2.5459 vs table 0.0293,
hidden family 2.37207/12000. Ponowny preflight wykrywa wszystkie przejścia bez
błędu indeksu. Testy mechaniki v7 16/16 i kompilacja sędziego/świata/ewolucji
przeszły; nie uruchamiano ponownie kosztownej kalibracji bez zmiany kodu.

2026-10-25: Audyt H014 pokazał, że odkrywczy kontrolny kandydat ustawia
`learning_rate=0`, więc równocześnie usuwa cały efekt uczenia i nie izoluje
reserve-shaped retention. Utworzono osobny matched control z
`energy_coupling=0`, który zachowuje uczenie, ale ustawia stały współczynnik
zapominania. Pełny sędzia kandydata uruchomiony jako eksperymentator działał
aktywnie przez 60 minut (CPU ~88%, RAM ~1.6 GB, CUDA ~1.7 GB), lecz nie zapisał
rekordu i został przerwany; brak wyniku jest brakiem pomiaru, nie falsyfikatorem.
Wcześniejszy rekord odkrywcy: rooms 0.7119140625, survival 0.7568359375.
H014 zostaje testing. Następna tura powinna najpierw ocenić koszt pary i wznowić
pełny test; nie używać wcześniejszej ablacją jako dowodu przyczynowego.

Korekta po końcowym odczycie rejestrów 2026-10-25: pełna para odkrywcy jest
już w wierszach 175/178: rooms 0.7939453125 vs 0.79296875, delta
+0.0009765625 z nakładającymi się CI; survival 0.607421875 vs 0.6142578125.
Kontrola zeruje całe uczenie, więc nie wspiera przyczynowo H014. Probe
`audit/axiom_retention_budget_probe.result.json` wskazuje aktywność po
`energy_coupling=0`, ale nie jest pełnym assay. Własna niezależna replikacja
została przerwana po 60 minutach i nie ma rekordu; dopisany wniosek nie zmienia
statusu H014 z testing.

2026-10-25 odkrywca_axioms: utworzyłem nowego kandydata
`candidates/axiom_metabolic_covariance_budget/` jako krzyżówkę
`axiom_metabolic_retention_budget` i `axiom_centered_correlation`. Zastąpiłem
ręcznie wybrany color/context table jedną centrowaną macierzą covariance
sensor-action; zmiana energii bramkuje aktualizację, a jedna norma globalna
ogranicza pamięć. `shared/ideas.py check` dał NOWY, max podobieństwo 0.10.
Smoke CPU 80 kroków przeszedł (akcje (8,3), finite norm).

Pełny `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/axiom_metabolic_covariance_budget --organism --author odkrywca_axioms`
ukończony na organism-v7: 1024 światy x 50000 kroków, wall 4461.114 s.
Wynik: rooms_reached/score 0.0859375, CI [0.0658129323, 0.1060620677],
survival 0.78515625, CI [0.7599877309, 0.8103247691], mean_energy 0.7602244175,
room-reach means [1.0, 0.0712890625, 0.0146484375, 0, 0, 0]. Osiągnięto tylko
room 0; zasada nie pobiła lidera dynamics_metabolic_retention (0.8) i jest
wynikiem refutującym tę uproszczoną krzyżówkę, nie całe H014.
- B, pełny organism-v7, 2026-10-25: ewolucja na GPU z 4 genomami x 4 światy i wspólnym seedem 1925141753 w dwóch generacjach po 50 000 kroków zwiększyła średnią fitness 0.000375 -> 0.000500. Najlepszy wynik pokoi pozostał 0.0, a przeżycie wzrosło 0.75 -> 1.0. To pokazuje selekcję z różnicą przeżycia w tej partii, nie rozwój zdolności; potrzebne są większa populacja, więcej światów i więcej generacji.
- D, pełny organism-v7, 2026-10-25: przy grupach dwuosobowych (1024 organizmy, 512 światów, 50 000 kroków) wynik wyniósł 2.537109 pokoju, przeżycie 0.1875, 229.629 zdarzeń pobrania na organizm, a żółtko wyczerpało się w 0.962891 żyć. Kontrola bez grup w kalibracji miała 2.545898 pokoju i 0.165039 przeżycia. Wspólny zasób i RGB partnera działają, lecz próba nie wskazuje korzyści w wyniku pokojów; nie wyciągać wniosku o uczeniu społecznym.
- Przy pełnym czasie życia 50 000 kroków cztery genomowe linie x cztery światy zajęły 1778.8 s na generację CUDA. CPU odpowiednik pierwszej generacji zajął 3845.1 s. Krótki smoke nie przewiduje kosztu pełnej oceny.
- 2026-10-25: Kontynuacja przeglądu v7. Ponownie uruchomione `test_organism_v7.py` i `test_evolve.py` zakończyły się kodem 0; CLI preflight przeszedł batch 2 przez `0->1->2->3->4->5->5`. Rekord `organism-v7-final` nadal jest zaliczony, a parser sędziego ustawia v7 jako domyślne po tym rekordzie.
- B wymaga ostrożnego raportu: w `run_20261025T051240Z/curve.jsonl` score najlepszy wynosi 0.0 w generacji 0 i 1; fitness 0.000375->0.000500 pochodzi z przeżycia 0.75->1.0. Przy 4 genomach, 4 światach i jednym seedzie nie ma dowodu postępu zdolności. Pełniejsza ewaluacja kosztuje ok. 1779 s/generację CUDA.
- W chwili przeglądu GPU miało 100% użycia i 19.9 GiB zajętej pamięci; nie dodano konkurencyjnego pełnego przebiegu. Następny test B powinien użyć większej populacji/światów i wielu seedów, gdy slot GPU będzie dostępny; raportować zdolność osobno od przeżycia.
- 2026-10-25: Końcowy preflight CLI v7 (batch 2) ponownie przeszedł `0->1->2->3->4->5->5`; `test_organism_v7.py` i `test_evolve.py` zakończyły się kodem 0. Istniejący rekord `organism-v7-final` ma `calibration_passed=true`, 50 000 kroków i 1024 światy; brak zmiany kodu nie uzasadnia powtarzania pełnego przebiegu przy zajętym GPU.
- 2026-10-25: Ten sam preflight uruchomiony bez `--organism-version` przeszedł, potwierdzając wybór v7 jako domyślnej wersji po zaliczonej kalibracji.

## 2026-10-25 V7 continuation audit

Zweryfikowałem rekord końcowy zamiast ufać samemu handoffowi: `organism-v7-final`
ma `calibration_passed=true`, sześć wymaganych kontroli, 1024 światy i 50 000
kroków. Średni wynik growing to 2.545898 (CI95 2.485467–2.606330), a table
0.029297 (0.017017–0.041577); kontrole random/Braitenberg/delta pozostają przy
0.000000/0.006836/0.021484. Kryterium rozłącznych CI i zaliczone bramki są
zapisane w rekordzie, nie dopisane na podstawie tekstu README.

Uruchomiłem CLI preflight zarówno z jawnym v7, jak i domyślnie; oba odwiedziły
`0->1->2->3->4->5->5`. Wywołałem bezpośrednio wszystkie 19 funkcji testowych
v7 i ewolucji; 19/19 przeszło. `pytest` nie jest zainstalowany w `.venv`, więc
nie raportuję uruchomienia runnera pytest. Nie powtarzałem kalibracji bez zmian
w kodzie ani protokole. Potwierdzenie dla B pozostaje ograniczone: średnia
fitness wzrosła przez przeżycie, a najlepszy wynik zdolności pozostał 0.0.

## 2026-10-25 V7 final handoff audit

Preflight uruchomiony ponownie z `--organism-version v7` i bez tej flagi przeszedł
każdy pokojowy indeks (`0->1->2->3->4->5->5`) w 13-20 s. Bezpośredni harness
wywołał wszystkie 19 funkcji `test_` z `test_organism_v7.py` i `test_evolve.py`;
19/19 przeszło. Ostatni rekord `organism-v7-final` pozostaje zaliczony przy 1024
światach i 50000 krokach. Nie powtarzałem pełnej kalibracji, bo nie zmienił się
kod ani protokół; HANDOFF kończy się wymaganą linią `KONIEC`.
2026-10-25: Podjęto niezależną replikację H021 (`eksperymentator_energy_trend_retention`)
na podstawie proposed wpisu i H021 w HANDOFF odkrywcy. Sparowana kontrola
ustawia wyłącznie `trend_coupling=0`. Pełny judge organism-v7 wystartował, ale
został przerwany ręcznie po ok. 10 min przy 99-100% zajętości GPU i kilku
równoległych jobach; nie powstał rekord. Nie uruchomiono kontroli, więc nie ma
delty ani wniosku przyczynowego. CPU probe energii 0.5 -> 0.7 dał masę śladu
1.967 main vs 1.931 ablation, potwierdzając tylko implementację lokalnego
mechanizmu. H021 pozostaje testing. Następny krok: pełna sparowana ocena tych
samych seedów, docelowo trzy pary, gdy slot GPU pozwoli dokończyć oba runy.
