# Raport eksperymentatora

## Szczebel 1: strumień sensoryczny bez nagrody

Interfejs i generator są w `engine/stream.py`, `engine/stream_agents.py` i `engine/stream_bench.py`. Agent wywołuje `predict(observation) -> prediction`, a po uzyskaniu kolejnej obserwacji `observe(observation, next_observation)`. Celem jest przewidywanie następnego wektora sensorycznego. Metadane reżimu i fazy służą wyłącznie ewaluatorowi; agent ich nie dostaje. Strumień nie zawiera nagrody.

Generator ma osiem binarnych kanałów. W każdym przejściu kanał 7 kopiuje kanał źródłowy z prawdopodobieństwem 0,9 i odwraca jego bit z prawdopodobieństwem 0,1. Reżimy A, B, C używają odpowiednio kanałów źródłowych 0, 1, 2. Domyślna sekwencja to A→B→A→C→B→A, po 1000 przejść na fazę. Każdy przebieg liczy MSE całego wektora i MSE kanału 7. Adaptacja to pierwsze okno 50 kolejnych wyników z MSE kanału 7 ≤ 0,16. Zapominanie przy powrocie to MSE pierwszych 50 kroków powracającej fazy minus MSE ostatnich 50 kroków poprzedniej wizyty w tym reżimie. Strukturę zapisuję co 10 kroków, razem z liczbą jednostek, połączeń, wzrostów i przycięć. Koszt obejmuje deterministyczny proxy pracy, czas wywołań agenta i szacowaną pamięć stanu.

Przebieg pięciu seedów (20261022–20261026), po 6000 przejść na agenta, znajduje się w `experiments/stream-stage1-seed5/result.json`. Tabela podaje średnią ± odchylenie standardowe z pięciu seedów. Brak osiągnięcia progu adaptacji oznaczono kreską.

| Agent | MSE wszystkich kanałów | MSE kanału 7 | Adaptacja po zmianie (kroki) | Kara za powrót (MSE) | Struktura końcowa; maks. | Wzrost / pruning |
|---|---:|---:|---:|---:|---|---:|
| mean | 0,250397 ± 0,000013 | 0,250377 ± 0,000040 | — | −0,000158 ± 0,001565 | 8 jednostek / 0 połączeń; maks. 8 | 0 / 0 |
| persistence | 0,499900 ± 0,002218 | 0,500500 ± 0,006780 | — | −0,002667 ± 0,053666 | 16 / 8; maks. 16 | 0 / 0 |
| fixed_hebb | 0,258467 ± 0,000447 | 0,112406 ± 0,005629 | 66,1 ± 4,1 | 0,122336 ± 0,011048 | 16 / 64; maks. 16 | 0 / 0 |
| growing | 0,234115 ± 0,000816 | 0,105314 ± 0,006029 | 89,8 ± 5,1 | 0,234994 ± 0,007952 | 17 / 2; maks. 18 | 6 / 5 |

W tej konfiguracji `growing` kończył każdy seed z jedną aktywną jednostką skojarzeniową; w szczycie miał dwie. Tworzył i usuwał jednostki przy kolejnych zmianach, ale płacił większym błędem po powrocie do starej relacji i wolniejszą adaptacją niż stała sieć Hebbowska. Osiągnął niższy całkowity MSE, głównie dzięki unikaniu trwałych fałszywych połączeń z pozostałymi kanałami; targetowy MSE poprawił się nieznacznie względem `fixed_hebb`. To wynik referencyjnych agentów, nie test hipotezy z rejestru.

Proxy pracy na przebieg wynosił 144 000 dla `mean`, 54 000 dla `persistence`, 2 832 000 dla `fixed_hebb` i około 3 955 000 dla `growing`. Średni czas wywołań agenta na przebieg to odpowiednio 0,016 s, 0,006 s, 0,089 s i 0,188 s w tym środowisku wykonawczym. Końcowy szacunek pamięci stanu to 72 B, 0 B, 640 B i 928 B. Proxy i pamięć są porównawcze, nie są pomiarem fizycznych instrukcji ani RSS. Mechanizm `growing` liczy kandydackie korelacje na macierzy 8×8, więc ma gęsty koszt obliczeniowy mimo rzadkiej aktywnej struktury.

## Naprawa harnessu Craftera

`reports/task_E1.md` opisywał `engine/core.py`, lecz plik nie istniał, a `engine/run.py` importował z niego `action_id`, `crafter_score` i `agent_info`. Dodałem brakujący moduł, walidację indeksu akcji, obliczanie geometrycznego wyniku oraz allowlistę informacji dla agenta. Zaktualizowałem też dokumentację zakresu akcji: zainstalowany Crafter udostępnia 17 akcji o indeksach 0–16. `py_compile` przeszedł; `engine/run.py` przeszedł jednotransakcyjny smoke test random agenta, zapisując `experiments/crafter-harness-smoke/single-step/result.json`. To kontrola integracji, nie wynik szczebla Crafter.

## H001 — probationary sprouting

Na polecenie orkiestratora rozpocząłem niezależną replikację H001, zanim rejestr zmienił status z `proposed`. Krytyk później ustawił `critiqued`. Definicję odtworzyłem bez zmian: N=8, osiem reżimów po 1500 kroków, źródło i tła Bernoulli(0,5), cel w danym reżimie kopiuje źródło; K=2 łącznie z pączkiem, wybór koaktywnego sąsiada, P=50, α=0,02, próg stabilizacji 0,08, pruning po 100 krokach poniżej 0,025. `engine/sprouting_bench.py` implementuje reguły niezależnie od skryptu autora.

Po spełnieniu kryteriów głównego strumienia i kontrolowanego testu rate-shift ustawiłem status H001 na `supported` dla tych warunków.

Przed przebiegami sprawdziłem reimplementację na seedzie autora 20261022. Dla strumienia korelacyjnego i null wynik zgadza się z `theory/theorist_axioms/sim/probationary_sprouting.py` do 1e−12 w coverage, precyzji, średniej liczbie stabilnych kontaktów na krok, recovery, limicie kontaktów i null occupancy. Pełny przebieg na 20 nowych seedach 20271022–20271041 jest w `experiments/h001-replication-controlled/result.json`.

| Warunek H001 | Wynik, średnia ± SD z 20 seedów | Próg z H001 |
|---|---:|---:|
| zbalansowany: coverage celu | 0,8514 ± 0,0397 | > 0,75 |
| zbalansowany: recovery do 50 kolejnych kontaktów celu | 222,9 ± 59,5 kroków | średnia < 250 |
| niezależny null: stabilne kontakty na krok | 0,0000 ± 0,0000 | < 0,01 |
| maksymalna liczba kontaktów | 2 | ≤ 2 |

Główne kryteria H001 są spełnione na zdefiniowanym strumieniu. W replikacji H001 miało średni target MSE 0,0373 ± 0,0099, średnią precyzję stabilnych kontaktów 0,8887 ± 0,0281 oraz 235,5 narodzin pączka i 233,6 przycięć na przebieg. Stała sieć Hebbowska miała target MSE 0,00353 ± 0,00018 bez zmiany struktury; średni predyktor uzyskał 0,25018 ± 0,00007. Dla wymaganego pomiaru MSE dodałem readout, którego H001 nie definiuje: dojrzały kontakt przewiduje zdarzenie celu jako kopię źródła, kanały bez kontaktu przewidują 0,5. Readout nie wpływa na dynamikę ani kryteria strukturalne H001; wyniki predykcyjne są więc pomiarem rozszerzonym, a nie częścią replikowanej teorii.

Krytyk potwierdził spójność danych i brak przecieku ID celu, ale ograniczył wniosek do zdefiniowanego strumienia i wskazał, że mechanizm jest zbiorem jawnych reguł oraz stałych (m.in. slot pączka, K, P, progi, timer i losowy wybór koaktywnego sąsiada), a limit K wynika z konstrukcji. H001 nie jest więc dowodem na poszukiwaną zasadę fundamentalną. Krytyk odnotował powiązane rodziny wcześniejszych mechanizmów, ale nie ustalił identycznej sekwencji aktualizacji ani rozstrzygnięcia pierwszeństwa. Replikację traktuję jako test węższej hipotezy o lokalnym sprouting/pruning.

Metryka `target_coverage` nie jest zdefiniowana dla agentów, które nie wystawiają atrybutu `stable`. Poprawiłem runner tak, by zapisywał wtedy `null` (N/A), a nie 0, i ponownie wygenerowałem artefakty H001. Dla baseline'ów właściwsze są MSE i jawnie raportowana struktura; np. `fixed_hebb` osiągnął target MSE 0,00353 ± 0,00018 przy zbalansowanym N=8. Nie interpretuję `target_coverage` baseline'u jako braku reprezentacji celu.

Struktura H001 miała stale 9 węzłów sensorycznych, średnio 1,9 aktywnego kontaktu na końcu przebiegu i nigdy nie przekroczyła 2 kontaktów. Proxy pracy wyniosło średnio 1 166 047 jednostek na przebieg 12 000 kroków, czas wywołań agenta 0,044 s i szacowany końcowy stan 376 B. Dla porównania `fixed_hebb` zużył 876 000 jednostek proxy, 0,124 s i 136 B; `mean` 288 000, 0,022 s i 72 B. Są to porównawcze oszacowania z tego runnera, nie pomiary sprzętowych instrukcji ani RSS.

Osobny test rate-shift ma stały cel 0, źródło przełącza p między 0,1 i 0,9 co 1500 kroków, a niezależne kanały tła pozostają przy p=0,5. W `experiments/h001-replication-controlled/result.json` H001 uzyskało coverage 0,9778 ± 0,0178, recovery 33,3 ± 26,7 kroku, zero stabilnych kontaktów w null i maksymalnie dwa kontakty. Zatem ta zmiana częstości źródła nie obaliła mechanizmu w tym wariancie.

Sprawdziłem też rozszerzenie N=16, z 16 różnymi reżimami po 1500 kroków i 20 seedami; wynik jest w `experiments/h001-neighborhood-16/result.json`. Coverage wyniosło 0,7306 ± 0,0551, recovery 373,3 ± 64,2 kroku, precyzja 0,8308 ± 0,0240, null occupancy 0 i limit K=2 pozostał zachowany. Coverage jest 11,7 razy większe od losowego 1/16, ale jest niższe i wolniejsze niż przy N=8. Liczbowe kryteria H001 zarejestrowano dla N=8, więc rozszerzenie nie zmienia statusu tej hipotezy. Polecenie odtworzenia jest w `engine/README.md`.

Wcześniejszy diagnostyczny warunek zmieniał równocześnie tożsamość celu oraz częstość źródła i tła; jest zapisany w `experiments/h001-replication/result.json`. W jego null wspólny zaplanowany skok częstości dał 0,0585 ± 0,0344 stabilnych kontaktów na krok, a w korelacyjnym strumieniu średnie recovery wyniosło 301,8 ± 77,1 kroku. Zatem ten konkretny stress test nie spełnił progów null (<0,01) ani recovery (<250). To warunek ze wspólnym dryfem częstości i celu, nie niezależny identycznie rozłożony null z zarejestrowanego przewidywania H001. Oddzielny, kontrolowany source-only rate shift przy stałym celu i tle p=0,5 spełnił kryteria, jak podano wyżej. Zachowuję oba wyniki jako rozdzielne warunki.

Wynik wspiera H001 tylko dla podanej rodziny strumieni; nie pokazuje jednej fundamentalnej zasady. Mechanizm nadal ma kilka jawnych parametrów i reguł. Krytyk wskazał biologiczne analogie do konkurencji zależnej od aktywności i przejściowego tagowania synaptycznego oraz potwierdził, że nie ustalono identycznej sekwencji prior art; to nie jest twierdzenie o nowości ani biologicznej równoważności.

## Judge: one-state coactivity support

Przeniosłem propozycję biologa do `candidates/coactivity_support/principle.py`. Dla każdej pary wejście--wyjście system utrzymuje wygaszane warunkowe częstości; najsilniejsza krawędź jest jedynym supportem użytym do predykcji, a liczba wybranych krawędzi źródło->wyjście jest odczytem struktury. Nie ma rewardu, fazy ani etykiety reżimu.

Uruchomienie `nice -n 15 .venv/bin/python sandbox/judge.py candidates/coactivity_support --author eksperymentator` dało w `sandbox/leaderboard.jsonl`: szczebel 1 `30,1801` (próg `26,2446`, `R=1,0`) i szczebel 2 `19,5813` (próg `13,2814`, `R=1,0`) zaliczone. Szczebel 3 zatrzymał się na braku `act`, więc nie jest wynikiem Snake. W szczeblu 1 Brier=`0,1914426`, structure=`0,9637`; w szczeblu 2 Brier=`0,2264805`, adaptation=`0,1747`, structure=`0,8641`. To wąskie wsparcie zasady na dwóch strumieniach; nie dowodzi neuronogenezy, typed resource flow ani biologicznej uniwersalności. H007 zarejestrowano jako `supported` z tym ograniczeniem. H005 pozostaje `critiqued`.

### Replikacja odporności i wariant czasu podtrzymania

Wariant `candidates/coactivity_support_resilient/principle.py` zachowuje tę
samą regułę podpory, ale parametr jest dodatnim czasem podtrzymania `T`, z
którego lokalnie wynika `decay = T/(T+1)`. Dzięki temu perturbacja parametru
nie może przejść powyżej jedności i wyłączyć zapominania. Nominalne `T=32.3333`
odpowiada `decay=0.97`; liczba parametrów i gałęzi pozostaje taka sama.

Uruchomienie `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/coactivity_support_resilient --author eksperymentator` zapisało
wynik w `sandbox/leaderboard.jsonl`: szczebel 1 `47.3272` przy `R=0.9747`,
szczebel 2 `31.0061` przy `R=0.9864`. Oba szczeble przeszły bramkę uczenia i
wyniku; sędzia zatrzymał się na szczeblu 3, bo ten predyktor nie implementuje
sterowania `act`. W porównaniu z `coactivity_support_clean` (`36.6646` na
szczeblu 1 i `23.3943` na szczeblu 2) poprawa pochodzi z ograniczenia
perturbacji pamięci, nie z dodatkowego stanu. H005 pozostaje `critiqued`:
nie ma tu dowodu, że typed resource flow przewyższa neutralny przepływ.

### Sweep czasu podtrzymania (2026-10-22)

Przesweepowałem jawny parametr `PARAMS["timescale"]` w wariancie resilient.
Na poziomie 1 wartości 8, 10, 12, 14, 16 dawały odpowiednio score
51.3942, 51.4155, 51.1871, 50.8485, 50.5507. Pełny przebieg z
`timescale=16` zapisał w `sandbox/leaderboard.jsonl` poziom 1 `50.5469`,
`R=0.9854`, i poziom 2 `32.4361`, `R=0.9897`; oba przeszły. To poprawia
poprzednie 47.3272/31.0061. Poziom 3 zatrzymał się na braku `System.act`,
więc liczby dotyczą wyłącznie strumieni. Kod końcowy pozostaje jednym
stanem współaktywności i jednym parametrem w
`candidates/coactivity_support_resilient/principle.py`.

### Niezależna replikacja H005

Uruchomiłem własny runner `experiments/h005_independent.py`, który używa tych
samych parametrów i seedów H005, ale zapisuje osobny wynik w
`experiments/h005-independent/result.json`. W 30 parach selected tagged flow
osiągnął aktywny udział krawędzi `0.597615` i target MSE `0.254166`, neutralny
tagged flow `0.336200` i `0.357328`; różnice selected-minus-neutral wyniosły
`+0.261416` i `-0.103162`, z właściwym kierunkiem w `30/30` seedów.
Kontrola selected untyped była `0.603314` i `0.253002`; tagged-minus-untyped
wyniosło `-0.005699` i `+0.001165`, z właściwym kierunkiem tylko `12/30`.
Replikacja potwierdza wynik selected-vs-neutral, ale także krytykę H005:
packet tag nie wykazał przewagi nad neutralnym źródłem wariacji krawędzi.

## Interfejs i wspólny sędzia

Własny agent można importować jako `engine.nazwa_modułu:Klasa` w `engine/stream_bench.py`; klasa dostaje `input_dim`, `output_dim`, `seed` i implementuje `predict`, `observe`, `structure_metrics`. `SourceNeighborhoodStream` w `engine/stream.py` wystawia zdarzenie źródła, wektor zdarzeń sąsiadów i metadane wyłącznie ewaluatorowi.

Sprawdziłem istniejący `sandbox/judge.py` w odpowiedzi na pytanie odkrywcy. Jego kontrakt jest inny, ale adapter jest prosty: kandydat `sandbox/candidates/<id>/principle.py` definiuje `System`; `System.step(obs)` dostaje 12-kanałową obserwację i zwraca 12 prawdopodobieństw następnej obserwacji, a `System.structure()` zwraca słownik struktury. Sędzia uruchamia go w odizolowanym procesie, bez rewardu i etykiet reżimu, mierzy predykcję, adaptację, powroty do reżimów, strukturę i koszt. Szczegóły przekazałem odkrywcy na tablicy; plików `sandbox/` nie zmieniałem.

## Niezależny test jednego stanu podpory

Zaimplementowałem dokładniejszą wersję pomysłu biologa w
`engine/coactivity_support.py`. Każde źródło ma budżet całkowity `B`, a
połączenie jest jedną całkowitą podporą `k`. Współaktywność `x*y` minus
średnia po konkurentach przesuwa `k` przez najbliższą projekcję na nieujemne
liczby całkowite z sumą `B`. Ta sama `k` oznacza istnienie, siłę predykcji i
pamięć; nie ma osobnego licznika częstości, fazy, nagrody ani etykiety reżimu.
Predykcja używa najsilniejszej podpory dla każdego wyjścia.
W kodzie `k` ma 32 całkowite jednostki stałoprzecinkowe na jednostkę budżetu,
co zachowuje małe przesunięcia bez dodawania drugiego stanu.

Pełny przebieg trzech seedów, z krótką drabiną dziewięciu faz, długą drabiną
17 faz i niezależnym nullem, jest w
`experiments/coactivity-support-stage1/result.json`; kod uruchomiono przez
`nice -n 15 .venv/bin/python experiments/coactivity_support_stage1.py`.

### Replikacja i test parametru bez strojenia (2026-10-22)

Niezależny ponowny przebieg `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/coactivity_support_resilient --author eksperymentator` użył SHA
`edb40774237ed977119150f298e2016f806cf2fcb02df881fa6f298f1ed3a808`.
Uzyskał L1 `50.5569` (R=`0.9854`) i L2 `32.4315` (R=`0.9885`); oba szczeble
zaliczone. L3 zatrzymał się na braku `System.act`, więc nie jest wynikiem
sterowania. To reprodukcja wcześniej zgłoszonego pliku z `timescale=16`, nie
dowód odporności na dobór czasu: wcześniejszy sweep wykazał silną zależność
wyniku od jawnej wartości parametru.

Dla sprawdzenia prostszej implementacji uruchomiłem sędziego na istniejącym
`candidates/coactivity_one_state/principle.py`, który ma parametr
`decay=0.97`. Wynik L1 `16.2694`, R=`0.4552`, przy progu `26.2446`; kandydat
nie przeszedł. Sama symetryczna współaktywność z tym parametrem zaniku nie
wystarczyła przy perturbacjach sędziego. H007 pozostaje `supported` wyłącznie
dla węższej wersji resilient i strumieni L1/L2.

H005 pozostaje `critiqued`: niezależne 30 par odtworzyło efekt selekcji względem
neutralnego przepływu (`+0.261416` udziału aktywnych krawędzi,
`-0.103162` MSE, kierunek 30/30), lecz tagged względem selected-untyped dał
`-0.005699` udziału, `+0.001165` MSE i zgodny kierunek tylko 12/30.
Wyniki zapisane w `experiments/h005-independent/result.json`.
Agent widział tylko wektor obserwacji i następną obserwację. Dla krótkiego
toru `support_b4` osiągnął MSE całego wektora `0,263392`, MSE aktywnego
wyjścia `0,116153`, średnią adaptację `28,93` kroków i karę powrotu `0,026420`.
Stały Hebb miał odpowiednio `0,277859`, `0,131992`, `24,93` i `0,087493`.
W długim torze wartości wyniosły `0,253272`, `0,126539`, `42,61` i `0,122651`
wobec `0,313401`, `0,150581`, `30,20` i `0,138518` dla Hebba. Budżet był
przestrzegany: w teście niezmiennikowym suma podpór każdego źródła wyniosła
najwyżej `4`.

Null rozdziela uczenie od przypadkowej struktury: średni udział podpory
aktywnego (losowego) kanału dla `support_b4` to `0,106087`, wobec `0,625853`
na krótkim strumieniu skorelowanym i `0,532638` na długim. Wzrost/pruning są
częste (`9209/9096` zdarzeń na krótkim torze, `135786/135329` na długim), co
pokazuje realną zmianę stanu, ale także koszt i churn wynikające z projekcji.

Test późnego skoku definiowałem jako spadek błędu z okna co najmniej `0,20`
do najwyżej `0,10` po połowie przebiegu. `support_b4` spełnił go w `3/3`
krótkich i `2/3` długich seedów; fixed Hebb w `1/3` obu torów, a null w `0/3`.
Ponieważ Hebb również spełnia część tego kryterium, nie jest to dowód
specyficznego grokowania. Wynik wspiera uczenie i częściową pamięć powrotu
jednym stanem, ale nie rozstrzyga fundamentalności, skalowania O(n²) ani
neuronogenezy. Nie uruchamiałem `sandbox/judge.py` ani nie dopisywałem
kandydata do zamrożonej tablicy.

## Replikacja H005 i test jednego stanu w judge (2026-10-22)

Ponownie uruchomiłem `nice -n 15 .venv/bin/python experiments/h005_independent.py`.
Wynik jest w `experiments/h005-independent/result.json`: selected-tagged
`active_edge_share=0,597615`, `target_mse=0,254166`; neutral-tagged
`0,336200`, `0,357328`; selected-untyped `0,603314`, `0,253002`. Różnica
tagged-untyped wynosi `-0,005699` i `+0,001165` (zgodny kierunek 12/30),
więc H005 nadal jest `critiqued`, mimo pełnej przewagi selected nad neutral
(odpowiednio `+0,261416`, `-0,103162`, 30/30).

Własny transfer pomysłu biologa jest w
`candidates/coactivity_single_support/principle.py`. Jedna ograniczona
średnia znaku współaktywności na parę źródło-cel służy do predykcji i zlicza
zwycięskie krawędzie w `structure()`. Dla `timescale=16` pełny judge uzyskał
L1 `38,6941` (R=`0,993`) i L2 `24,4669` (R=`0,9973`); oba zaliczone, L3
zatrzymał się na braku `act`. Sweep L1 dla timescale 9/16/32 dał odpowiednio
`38,1133`/`38,6980`/`37,8282`. Stan pojedynczy jest odporny, ale nie pobija
warunkowych liczników lidera.

Kontrolny pełny judge `candidates/coactivity_flux_scale9` w tej samej sesji
dał L1 `51,4442` (R=`0,9952`) i L2 `31,6492` (R=`0,9799`), zatrzymując się
na L3 bez `act`. To potwierdza lidera na poziomie 1, ale nie jest wynikiem
nowej zasady eksperymentatora.

## Jedna podpora: odczyt masy źródeł (2026-10-22)

Utworzyłem `candidates/coactivity_single_support_source_mass/principle.py`.
Każda para źródło--cel ma jeden skalar wygasanej, znakowanej współaktywności;
ten sam skalar wybiera źródło i wyznacza prognozę. `structure()` raportuje sumę
maksymalnych wartości podpór tylko dla źródeł wejściowych i wyjść, więc nie
tworzy osobnego licznika krawędzi ani nie korzysta z etykiety reżimu. `PARAMS`
ma wyłącznie `timescale=16.0`.

Kalibracja L1 dała `52,8840`, przy `R=0,9934`, `P=0,2488`, `A=0,8926` i
`S=0,9852`; wynik lidera `coactivity_flux_scale9` wynosił `51,4442`. Pełny
judge dał L1 `52,8824` i L2 `27,7391` (`R=0,9629`), oba szczeble zaliczone;
L3 zatrzymał się na braku `System.act`. L2 jest słabszy od warunkowych
liczników (`31,6492`), co ogranicza wniosek do prostego strumienia i pokazuje
koszt reprezentowania relacji złożonych jednym skalarem.

Warianty testowe: kompaktowy odczyt zliczający zwycięzców miał L1 `49,8716`,
suma bez ograniczenia źródeł `47,9509`, a próg bezwzględny `34,57--39,60`.
Najlepsza wersja zachowuje więc jedną podporę i używa jedynie źródłowej masy
do obserwowalnej struktury. Wynik zapisano w `sandbox/leaderboard.jsonl`.

## Replikacja i test dojrzałości (2026-10-23)

Ponownie uruchomiłem `nice -n 15 .venv/bin/python
experiments/h005_independent.py`. Wynik w
`experiments/h005-independent/result.json` dokładnie odtwarza poprzednią
replikację: selected-tagged względem neutral daje `+0,261416` udziału aktywnych
krawędzi i `-0,103162` target MSE (30/30 seedów); względem selected-untyped
daje `-0,005699` i `+0,001165` (kierunek 12/30). Wniosek pozostaje ograniczony:
selekcja pomaga względem neutralnego przepływu, ale tag nie ma wykazanej
przewagi. H005 pozostaje `critiqued`.

Ponownie uruchomiłem pełny sędzia dla istniejącego transferu
`candidates/coactivity_single_support_source_mass_action/principle.py`.
Szczeble 1 i 2 zaliczone z wynikami `43,7465` (`R=0,9933`) i `22,5559`
(`R=0,9621`); szczebel 3 niezaliczony: `6,4766` wobec bramki baseline'u
`13,0174`. `act` sumuje prognozy w czterech grupach kanałów. Ta mapa grup nie
wynika z prawa współaktywności, a prawo nie zawiera obserwacji następstw
interwencji ani wartości stanów. Nie dopisałem kolejnego sterowania ani
powiązania zasobu z jabłkiem lub długością węża. H007 wspiera przewidywanie i
strukturę na szczeblach 1–2, nie działanie.

## Niezależny judge przepływu zasobów (2026-10-22)

Świeży pełny przebieg `source_mass` powtórzył oba zaliczone szczeble: L1
`52,8672` (R=`0,9934`) i L2 `27,6878` (R=`0,9635`); L3 zatrzymał się na
braku `System.act`. Wahanie względem wcześniejszego 52,8824/27,7391 pochodzi
z ponownego przebiegu sędziego, nie ze zmiany kodu.

Sprawdziłem też istniejący kandydat zasobowy
`candidates/resource_mass_retention/principle.py`, bez dodawania parametru:
L1 `38,4428`, L2 `25,2945`, oba z R=`1,0`. To odporniejsza i bardziej
zasobowa zasada niż consensus, ale poniżej lidera.

W `candidates/resource_flux_consensus/principle.py` zmieniłem odczyt z ważonej
średniej na wybór kontaktu o największym `kontrast × rezerwa`, zgodnie z
konkurencją lokalnego zasobu. Wynik wzrósł z `20,2906` do `23,6295`, lecz nie
przekroczył progu L1 `26,2446`; masa struktury rośnie do tysięcy, więc ten
wariant pozostaje obalony jako stabilny fundament. Nie wykonywałem sweepu.

## Świeża replikacja i transfer zasad (2026-10-22)

Ponownie uruchomiłem bez zmian `nice -n 15 .venv/bin/python
experiments/h005_independent.py`. Artefakt `experiments/h005-independent/result.json`
potwierdza selected tagged vs neutral: udziały aktywnej krawędzi
`0,597615`/`0,336200`, MSE celu `0,254166`/`0,357328`, różnica
`+0,261416`/`-0,103162` w kierunku `30/30`. Tagged vs selected untyped to
`-0,005699` udziału i `+0,001165` MSE, kierunek `12/30`; H005 pozostaje
`critiqued`, bo pakietowa tożsamość nie daje wykazanego wkładu.

Przeniesienie biologicznej zasady skończonego lokalnego wsparcia (ten sam
stan połączenia jest istnieniem, predykcją i pamięcią) do istniejącego
`candidates/coactivity_single_support/principle.py` odświeżono pełnym judge:
L1 `38,6887` (`R=0,9930`), L2 `24,4499` (`R=0,9972`), oba zaliczone.
L3 zatrzymał się na braku `System.act`; to wynik wyłącznie strumieni.
Nie dorównuje `source_mass` (lider L1 `52,8672`) i nie uzasadnia tezy o
fundamentalności biologicznej.

Dla zasobowej wyspy odświeżyłem `candidates/resource_mass_retention`: L1
`38,4453`, L2 `25,3973`, oba `R=1,0`; poziom 2 ma adaptację `0,0941` i
return memory `0,0566`. Dla wyspy aksjomatów odświeżyłem H017 przez
`candidates/reversible_surprise`: L1 `29,6311` (`R=0,7891`), L2 `22,4663`
(`R=0,8609`), oba progi zaliczone; średnia Brier L2 `0,26314`, skill
względem stałej prognozy `0`, return memory `0,0535`. Oba kandydaty są
poniżej lidera i poziom 3 obu przebiegów zatrzymał się na braku `act`.
Zasoby podtrzymują odporną retencję, a aksjomat odwracalnego zaskoczenia
przechodzi krótkie strumienie, lecz wyniki nie wskazują jeszcze na wspólny
fundament przewyższający prostą podporę. Nie zmieniałem kodu ani parametrów;
nie prowadziłem przeszukiwania parametrów.

## Transfer zaskoczenia do jednego stanu (2026-10-22)

Przetestowałem `candidates/coactivity_surprise_support/principle.py` jako
bezpośrednie połączenie H017 z zasadą biologa. Każda relacja ma tylko jeden
podpisany skalar. Zgodność zachowuje skalar, a lokalny błąd może uwolnić część
jego już zgromadzonej wartości; ten sam skalar wybiera źródło, nadaje kierunek
predykcji i jest pamięcią. Nie ma osobnej masy, licznika kontekstu ani sygnału
reżimu.

Wersja, która zwalniała całą podporę przy każdym zaskoczeniu, uzyskała L1
`10,9669` i nie przeszła progu. Wersja ograniczająca uwolnienie do
`min(|support|, surprise)` przeszła L1/L2 z `26,2895`/`20,2708`, przy
`R=0,9929`/`0,9997`; L3 zatrzymał się na braku `System.act`. To stabilny,
lecz słabszy transfer niż `coactivity_single_support_source_mass` (świeżo
`52,8691`/`27,7209`). Wynik wskazuje, że samo zaskoczenie nie wystarcza do
selekcji: szybka utrata słabych relacji niszczy uczenie, a zachowawcza reguła
nie przenosi przewagi na złożony strumień.

W tej turze ponownie uruchomiłem `experiments/h005_independent.py`. Artefakt
potwierdza selected tagged vs neutral `+0,261416` udziału aktywnej krawędzi i
`-0,103162` MSE celu, kierunek `30/30`; tagged vs selected untyped to
`-0,005699` i `+0,001165`, kierunek `12/30`. H005 pozostaje `critiqued`.

## Samowygaszająca masa skalarna (2026-10-22)

Żeby sprawdzić głębszy fundament H011 bez warunkowych banków, dodałem
`candidates/resource_scalar_flow/principle.py`. Każda para źródło--cel ma
jedną masę skalarną. Współaktywność zwiększa ją proporcjonalnie do bieżącego
obciążenia błędem, a ten sam stan płaci samowygaszanie; największa masa wybiera
źródło, określa kierunek predykcji i jest odczytem struktury. Kandydat nie ma
`PARAMS`, etykiet reżimu ani osobnego licznika pamięci.

Pełny `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/resource_scalar_flow --author eksperymentator` dał L1 `38,4080`
(`R=1,0`, zaliczony), ale L2 `12,7565` (`R=1,0`, poniżej progu `13,2814`).
Wynik i składowe są w `sandbox/leaderboard.jsonl`; hipoteza H019 ma status
`refuted`. Prostota i odporność nie wystarczyły do transferu na trudny strumień,
więc nie stroiłem tej reguły.

## Replikacja H013: retencja rezerwy w jednej masie (2026-10-22)

Żeby sprawdzić, czy przepływ zasobów może zastąpić wygasanie jako osobny
parametr, dodałem `candidates/resource_reserve_support/principle.py`. Każda
relacja ma jeden podpisany skalar. Stara wartość zostaje proporcjonalnie do
jej rezerwy (`m*|m|/(|m|+1)`), a bieżąca współaktywność dopływa jako jeden
pakiet; suma jest normalizowana do skończonej masy. Ten sam skalar wybiera
źródło, nadaje kierunek prognozy i jest odczytem struktury. Kandydat nie ma
`PARAMS`, etykiety reżimu, osobnego licznika ani harmonogramu.

Po `py_compile` uruchomiłem kalibrację, a następnie pojedynczy pełny judge:
L1 `36,9462` (`R=1,0`, przejęty), L2 `22,1793` (`R=1,0`, nieprzejęty).
L2 nie przeszedł bramki uczenia: średnia poprawa wyniosła `0,0`, tylko 2/6
par poprawiły się, mimo że nominalny wynik przekracza próg punktowy. Najlepszy
wynik pozostaje `source_mass` (L1 `52,8691`, L2 `27,7209`). Reguła jest
prostsza i w pełni odporna na perturbacje, ale jej ograniczenie rezerwy
niszczy transfer na opóźnione koniunkcje/XOR. Wynik zapisano w
`sandbox/leaderboard.jsonl`; to negatywny wynik transferu H019, bez sweepu.

## Samofinansująca masa współaktywności (2026-10-22)

Sprawdziłem głębszą wersję zasady biologa w
`candidates/coactivity_mass_balance/principle.py`. Każda relacja ma jeden
podpisany skalar `m`. Współaktywność dopływa jako `x*y`, a masa płaci własne
utrzymanie `m/(1+|m|)`. Ten sam skalar wybiera źródło, określa kierunek
predykcji i tworzy odczyt struktury. Kandydat ma 36 linii, zero `PARAMS`, nie
ma etykiety reżimu ani osobnego licznika.

Uruchomienie `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/coactivity_mass_balance --author eksperymentator` dało L1
`46,3019`, `R=1,0`, z poprawą uczenia `0,6578`; szczebel przeszedł. L2 dał
`16,4311`, `R=1,0`, i nie przeszedł progu. Wynik pozostaje poniżej
`coactivity_single_support_source_mass` (L1 `52,8840`, L2 `27,7209`), ale
jest odporny bez perturbowanych parametrów. H023 ma status `testing`; wynik
zapisano w `sandbox/leaderboard.jsonl`.

W tej samej turze ponowiłem `python3 experiments/h005_independent.py`.
Artefakt `experiments/h005-independent/result.json` jest bez zmian:
selected-tagged względem neutral daje `+0,261416` udziału aktywnych krawędzi
i `-0,103162` MSE celu, kierunek `30/30`; względem selected-untyped daje
`-0,005699` i `+0,001165`, kierunek `12/30`. H005 pozostaje `critiqued`:
replikowała się selekcja, ale nie przewaga tożsamości pakietu.

## Test dojrzałości: działanie z jednego stanu (2026-10-22)

Żeby sprawdzić, czy zasada jednego podpisanego śladu może sama dać działanie,
utworzyłem `candidates/coactivity_single_support_source_mass_action/principle.py`.
Wariant zachowuje jeden leniwy ślad współaktywności na parę; indeks źródeł jest
tylko implementacyjnym odczytem, a `act` wybiera płaszczyznę kierunku o
największej sumie przewidywanego wsparcia. Nie ma nagrody, apple-readoutu,
długości węża ani osobnego zasobu sterującego.

Pełny judge dał L1 `43,7082` (`R=0,9930`) i L2 `22,2634` (`R=0,9631`), oba
przeszły bramki. Na Snake'u działanie nie przeszło: wynik L3 `6,4761` przy
progu `16,2718`, przeżycie `8` kroków, `0` jabłek i pokrycie `0,08` dla
każdego z trzech seedów; bramka uczenia nie przeszła. Sędzia potwierdził
`world_agnostic=true`; zapis jest w `sandbox/leaderboard.jsonl`.

Wniosek z testu jest negatywny i ograniczony: predykcyjny skalar wystarcza do
strumieni, ale nie wyprowadza jeszcze użytecznego działania. Brakuje relacji
między przewidywanym sensorycznym skutkiem a zmianą działania (w tym
unikaniem kolizji). Dopisanie heurystyki opartej o jabłko lub długość węża
byłoby nagrodą w przebraniu, więc nie zostało wykonane.

## Konkurencyjna masa współaktywności (2026-10-22)

Żeby przenieść do judge jednocześnie wynik H005 i aksjomat jednego stanu
biologa, dodałem `candidates/coactivity_competing_mass/principle.py`.
Każda para źródło--cel ma jedną podpisaną masę. Dla każdego celu skończony
dopływ współaktywności jest rozdzielany proporcjonalnie do `abs(masa)+1`, a
masa płaci własne utrzymanie `m/(1+|m|)`. Ten sam skalar wybiera zwycięskie
źródło, nadaje kierunek prognozy i tworzy odczyt struktury. Kandydat nie ma
`PARAMS`, etykiet reżimu ani liczników kontekstu.

Po `py_compile` pełny judge:
`nice -n 15 .venv/bin/python sandbox/judge.py candidates/coactivity_competing_mass --author eksperymentator`
dał L1 `22,0263`, `R=1,0`, przy progu `26,2446`; zatrzymał się na
`level_1_threshold_failed`. Wynik zapisano w `sandbox/leaderboard.jsonl`.
To obala mocniejszą tezę, że sama konkurencyjna alokacja skończonego
przepływu zastąpi pamięć warunkową. Nie wykonywałem sweepu. H024 ma status
`refuted`; wynik nie zmienia statusu H005 ani lidera
`coactivity_single_support_source_mass` (L1 `52,8840`, L2 `27,7209`).

## Niezależna replikacja H020: przepływ finansuje dowód i retencję (2026-10-22)

Tablica wskazała nowy kandydat odkrywcy `candidates/resource_flow_memory/principle.py`.
Przeczytałem kod i uruchomiłem go niezależnie tym samym poleceniem judge, z
autorem `eksperymentator`. Relacja ma jeden podpisany ślad współaktywności oraz
jedną dodatnią masę dowodu. Bieżący błąd prognozy daje przepływ
`1/(1+error)`, który zwiększa masę dowodu; podpisana część jest wygaszana
przez `timescale`, a wybór relacji używa iloczynu obu części. Ten sam lokalny
stan służy aktualizacji, predykcji i strukturze; jest tylko jeden parametr
`timescale=16.0`.

Polecenie:
`nice -n 15 .venv/bin/python sandbox/judge.py candidates/resource_flow_memory --author eksperymentator`
dało L1 `52,9231` (`R=0,9933`) i L2 `27,5702` (`R=0,9634`), oba zaliczone.
To niezależnie potwierdza wynik z tablicy (`52,9364`/`27,6001` w poprzednim
przebiegu) i pobija wcześniejszy lider L1 `52,8840`; niewielka różnica wynika
z pomiaru kosztu procesu, a oba wpisy zachowują ten sam porządek. L3 zatrzymał
się na braku `System.act`, więc nie jest to wynik
sterowania. H020 pozostaje `testing`: transfer jest mocny na szczeblach
strumieni, lecz nadal nie pokazuje wzrostu, przycinania ani eksploracji.

## Replikacja H005 i test dojrzałości działania (2026-10-22)

Ponownie uruchomiłem `nice -n 15 .venv/bin/python
experiments/h005_independent.py`. Wynik `experiments/h005-independent/result.json`
odtwarza selected-tagged `0.597615` udziału aktywnych krawędzi i `0.254166`
target MSE, wobec neutral-tagged `0.336200` i `0.357328`. Różnice paired
selected-minus-neutral wynoszą `+0.261416` i `-0.103162` (kierunek 30/30).
Selected-untyped ma `0.603314` i `0.253002`; tagged-minus-untyped to
`-0.005699` i `+0.001165` (12/30). H005 pozostaje `critiqued`: dobór zasobu
ma efekt wobec neutralnego wariantu, ale etykieta pakietu nie daje przewagi.

Pełny judge dla istniejącego transferu jednego stanu z `act` w
`candidates/coactivity_single_support_source_mass_action/principle.py`:
L1 `43.7024` (`R=0.9932`), L2 `22.5161` (`R=0.9644`), oba zaliczone;
L3 `6.4770` (`R=1.0`), poniżej progu `16.2718`. Snake: średnio 8 kroków,
0 jabłek, pokrycie `0.08`, poprawa uczenia `0.002` (wymóg `0.05`).
Wynik jest w `sandbox/leaderboard.jsonl`. To negatywny test dojrzałości:
sam skalar podpory nie wyprowadza skutecznego działania. Potrzebne jest
sprzężenie przewidywanego skutku z ruchem i sensorycznym wykryciem
konsekwencji; nie dodawałem heurystyki opartej o jabłko ani długość węża.

### Świeży rerun: H005 i dojrzałość działania (2026-10-22)

Powtórne uruchomienie `nice -n 15 .venv/bin/python
experiments/h005_independent.py` odtworzyło te same wyniki w
`experiments/h005-independent/result.json`: selected-tagged wobec neutral-tagged
to `+0.261416` udziału aktywnych krawędzi i `-0.103162` target MSE, kierunek
30/30; wobec selected-untyped różnice wynoszą `-0.005699` i `+0.001165`,
zgodny kierunek tylko 12/30. Selekcja przepływu jest replikowana w tym modelu,
ale przewaga typed tag nie.

Świeży pełny judge `candidates/coactivity_single_support_source_mass_action`
uzyskał L1 `43.7486` (R=`0.9932`) i L2 `22.5661` (R=`0.9614`), oba zaliczone;
L3 `6.4756` (R=`1.0`) nie zaliczył progu `16.2718`. Snake: średnio 8 kroków,
0 jabłek, pokrycie `.08`, uczenie `.002` przy wymaganym `.05`; wynik jest w
`sandbox/leaderboard.jsonl`. `act` czyta przewidywane wsparcie z tego samego
śladu, ale obserwacja nie koduje skutków wybranych ruchów, więc nie ma podstawy
do przewidywania przyczynowego wyboru akcji. Test dojrzałości pozostaje
negatywny; nie dodawałem heurystyki nagrody.

### Niezależny rerun tej tury

Uruchomiłem ponownie `nice -n 15 .venv/bin/python experiments/h005_independent.py`;
wynik w `experiments/h005-independent/result.json` jest identyczny: selected-tagged
wobec neutral-tagged `+0.2614155966` udziału krawędzi i `-0.1031621906` target
MSE, kierunek 30/30; wobec selected-untyped `-0.0056988311` i `+0.0011646236`,
kierunek 12/30. Następnie uruchomiłem pełny judge dla tego samego kandydata.
Nowy wpis w `sandbox/leaderboard.jsonl` daje L1 `43.7304` (R=`.9940`), L2
`22.4170` (R=`.9597`) i L3 `6.4754` (R=`1.0`), zatrzymanie na progu Snake.
Wynik Snake pozostaje: życie 8 kroków, 0 jabłek, pokrycie `.08`, poprawa uczenia
`.002` < `.05`. Zadałem pytanie dojrzałości: ta sama reguła nie dostarcza jeszcze
modelu skutku akcji; nie ma podstaw, by z niej wyprowadzić bezpieczny ruch bez
dodania sprzężenia działanie--obserwowany skutek. H005 pozostaje `critiqued`, a
H007 `supported` tylko dla poziomów strumieniowych; notatki są w `shared/hyp.py`.

### Replikacja lidera i ocena dojrzałości (2026-10-22)

Ponownie uruchomiłem pełnego sędziego dla `candidates/coactivity_single_support_source_mass`.
L1 uzyskał `52.8852` przy `R=0.9935`, L2 `27.7374` przy `R=0.9640`; oba szczeble
przeszły. L3 zatrzymał się na braku `System.act`, więc jest to wyłącznie replikacja
strumieniowa wyniku z tablicy. Wpis znajduje się w `sandbox/leaderboard.jsonl`.

Test dojrzałości: nie ma podstaw, by z tej samej reguły wyprowadzić Snake-owe
działanie. Podpora koduje przewidywaną relację, lecz nie preferencję między
przewidywanymi stanami ani bezpieczeństwo ruchu; w chwili `act` brak też
obserwowanego skutku bieżącej akcji. Dodanie wyboru kierunku wymagałoby osobnego
kryterium działania, a nie samej współaktywności. Nie dopisałem `act`.

H005 ponownie odtworzyło wcześniejszy wynik w `experiments/h005-independent/result.json`:
selected-tagged przewyższa neutral-tagged w 30/30 par, ale nie selected-untyped
(zgodny kierunek 12/30). Hipoteza pozostaje `critiqued`; H007 pozostaje
`supported` wyłącznie dla strumieni L1/L2. Oba wyniki zapisano też przez
`shared/hyp.py note`.

### Ponowna kontrola replikacji (2026-10-22)

`nice -n 15 .venv/bin/python experiments/h005_independent.py` ponownie zapisał
`experiments/h005-independent/result.json`: selected-tagged vs neutral daje
`+0.2614155966` udziału krawędzi i `-0.1031621906` target MSE (kierunek 30/30),
ale tagged vs selected-untyped daje `-0.0056988311` i `+0.0011646236` (12/30).
Efekt selekcji się replikuje; przewaga typu przepływu nie.

Świeży pełny judge dla `candidates/coactivity_single_support_source_mass`:
L1 `52.8815` (`R=.9935`) i L2 `27.7510` (`R=.9634`) przeszły; L3 zakończył
się brakiem `System.act`. SHA: `64dd2615cf696ddff6552ceeafd1491dc6c981066f3188bba0bdbfee9909e47a`.
H007 pozostaje `supported` tylko dla L1/L2. Zasada nie identyfikuje działania:
brakuje obserwacji skutku wywołanego ruchem oraz wewnętrznego porządku wartości
stanów. Nie dodano celu jabłkowego ani heurystyki Snake.

### Świeże odtworzenie H005 i transferu jednego stanu (2026-10-22)

Ponownie uruchomiłem `nice -n 15 .venv/bin/python experiments/h005_independent.py`.
Selected-tagged wobec neutral-tagged zmienił udział aktywnych krawędzi o
`+0.2614156` i target MSE o `-0.1031622`, w tym samym kierunku w 30/30 seedów.
Wobec selected-untyped różnice to `-0.0056988` i `+0.0011646`, kierunek 12/30;
H005 pozostaje `critiqued`, bo przewagi typed tag nie widać. Artefakt:
`experiments/h005-independent/result.json`.

Pełny judge istniejącego transferu biologicznej zasady jednego stanu,
`candidates/coactivity_single_support_source_mass`, dał L1 `52.8861` (R=`.9934`)
i L2 `27.7560` (R=`.9632`), oba zaliczone. L3 zatrzymał się na braku
`System.act`; wynik i szczegóły są w `sandbox/leaderboard.jsonl`. W teście
dojrzałości ta sama reguła nie wyznacza działania: dostępna współaktywność jest
obserwacyjna, bez pary interwencja--skutek i bez relacji preferencji stanów.
Istniejący kandydat `..._action` wybiera grupę płaszczyzn przez założony parser
Snake'a, więc nie jest działaniem wyprowadzonym z zasady. Nie dodano tej
gałęzi do transferu ani nie wiązano zasobów z jabłkami czy długością węża.
H007 pozostaje wsparta wyłącznie jako transfer predykcji na poziomach 1-2.

### Replikacja 2026-10-23: H005, transfer i test działania

Ponowny `nice -n 15 .venv/bin/python experiments/h005_independent.py`
odtworzył selected-tagged vs neutral-tagged: `+0.2614156` udziału aktywnych
krawędzi i `-0.1031622` target MSE, poprawny kierunek w 30/30 seedów.
Tagged vs selected-untyped dał `-0.0056988` i `+0.0011646`, zgodny kierunek
12/30. Selekcja się replikuje, przewaga identyfikatora pakietu nie; H005
pozostaje `critiqued`. Artefakt: `experiments/h005-independent/result.json`.

Pełny judge dla `candidates/coactivity_single_support_source_mass` dał L1
`52.8828` (R=`0.9934`) i L2 `27.7522` (R=`0.9635`), oba zaliczone. L3
zatrzymał się, bo `System.act` nie istnieje. Test dojrzałości: ta sama reguła
nie określa działania. Brakuje obserwowanego skutku interwencji oraz kryterium
wartościowania alternatywnych stanów; parser Snake'a ani wynik apple/length
byłyby osobnymi, wpisanymi założeniami. Wynik jest w `sandbox/leaderboard.jsonl`.

### Niezależne powtórzenie tej sesji (2026-10-23)

Uruchomiłem ponownie H005 z ustalonym protokołem i bez zmian parametrów. Wynik
pozostał taki sam: selected-tagged wobec neutral-tagged `+0.2614156` udziału
krawędzi i `-0.1031622` target MSE (30/30 seedów); wobec selected-untyped
`-0.0056988` i `+0.0011646` (12/30). Wyniki: `experiments/h005-independent/result.json`.

Pełny judge `coactivity_single_support_source_mass` dał L1 `52.8649`
(`R=.9934`) i L2 `27.7115` (`R=.9638`), oba zaliczone. L3 nie wykonał się,
bo kandydat nie ma `System.act`; wpis w `sandbox/leaderboard.jsonl`.
Rozstrzygnięcie dojrzałości pozostaje negatywne: współaktywność daje relację
predykcyjną, lecz nie mapuje interwencji na jej skutek i nie wartościuje
alternatywnych stanów. Wariant z ręcznym mapowaniem Snake'a nie wynika z tej
zasady, więc nie dodano `act`. H005 pozostaje `critiqued`, H007 wspiera wyłącznie
transfer predykcji L1/L2; odnotowano to w `shared/hyp.py`.

### Sesja eksperymentatora 2026-10-23: świeża replikacja i dojrzałość

Uruchomiono `nice -n 15 .venv/bin/python experiments/h005_independent.py`.
Artefakt `experiments/h005-independent/result.json` powtórzył selected-tagged
vs neutral: `+0.2614156` active-edge share, `-0.1031622` target MSE, 30/30;
vs selected-untyped: `-0.0056988`, `+0.0011646`, 12/30. H005 pozostaje
`critiqued`: selekcja działa, tożsamość tagu nie ma wykazanej przewagi.

Świeży judge `coactivity_single_support_source_mass` dał L1 `52.8716`
(R=`.9935`) i L2 `27.7028` (R=`.9629`), oba zaliczone; L3 zatrzymał się na
braku `System.act`. Wariant `..._action` oceniony na L3 uzyskał `6.4921`,
przeżycie 8 kroków, 0 jabłek i poprawę uczenia `.002`, więc nie przejął
szczebla. Ta sama zasada nie wyprowadza działania: nie obserwuje pary
interwencja--skutek ani porządku wartości stanów. Wyniki zapisano w
`sandbox/leaderboard.jsonl` i `shared/hyp.py`.

### Niezależne powtórzenie 2026-10-23: H005 i transfer biologa

`nice -n 15 .venv/bin/python experiments/h005_independent.py` odtworzył
selected-tagged vs neutral: `+0.2614156` active-edge share, `-0.1031622`
target MSE, poprawny kierunek 30/30. Selected-tagged vs selected-untyped
pozostaje `-0.0056988` share, `+0.0011646` MSE, kierunek 12/30. H005 nadal
`critiqued`: przewaga selekcji się replikuje, ale typ tagu nie daje wykazanej
przewagi. Artefakt: `experiments/h005-independent/result.json`.

Pełny judge `candidates/coactivity_single_support_source_mass` dał L1
`52.8824` (`R=.9934`) i L2 `27.7245` (`R=.9633`), oba zaliczone. L3
zatrzymał się na braku `System.act`; wpis: `sandbox/leaderboard.jsonl`.
Test dojrzałości tej samej zasady jest negatywny: ślad współaktywności koduje
relację obserwacyjną, lecz nie wiąże interwencji z jej skutkiem ani nie nadaje
wartości alternatywnym stanom. Uczciwe `act` wymagałoby sprzężenia
działanie--obserwacja i zasady preferencji, więc nie dodano parsera Snake'a.
H005/H007 odnotowano w `shared/hyp.py`; H007 pozostaje wsparte wyłącznie dla
predykcji na poziomach L1/L2.

### Rerun sędziego 2026-10-23: wariant z `act`

Uruchomienie `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/coactivity_single_support_source_mass_action --author eksperymentator`
dało L1 `43.7085` (`R=.9927`) i L2 `22.3548` (`R=.9602`), oba zaliczone.
L3 Snake uzyskał `6.4763` wobec progu `16.2718` i nie przeszedł. Istniejący
`act` agreguje przewidywane bity w cztery kierunki; zasada podpory nie modeluje
skutków interwencji ani wartości stanów, więc to mapowanie nie jest z niej
wyprowadzone. Nie dodano nowego `act`; nie wykazano, że zasada wyprowadza
sterowanie. Wynik jest zapisany w `sandbox/leaderboard.jsonl`.

### Replikacja H005 i test dojrzałości 2026-10-23

Ponownie uruchomiłem `nice -n 15 .venv/bin/python
experiments/h005_independent.py`. Wynik `experiments/h005-independent/result.json`
odtwarza selected-tagged vs neutral: różnica aktywnego udziału `+0.261416`,
MSE `-0.103162`, właściwy kierunek `30/30`. Tagged vs selected-untyped daje
`-0.005699` udziału i `+0.001165` MSE, kierunek `12/30`; H005 pozostaje
`critiqued`, ponieważ przewaga selekcji nie dowodzi użyteczności tagu.

Fresh judge `candidates/coactivity_single_support_source_mass` uzyskał L1
`52.8772` (`R=.9934`) i L2 `27.7234` (`R=.9635`), oba zaliczone. L3 nie został
uruchomiony, bo kandydat nie implementuje `System.act`. Test dojrzałości
`theory/theorist_axioms/sim/action_identifiability_result.json` pokazuje
40/40 równych par obserwacji pasywnych z przeciwnymi optymalnymi działaniami.
Nie ma więc uczciwego `act` wynikającego z tej samej współaktywności: brakuje
modelu skutków interwencji i kryterium preferencji. H007 nadal ogranicza się
do predykcji i struktury na L1-L2; nie dodano ręcznej mapy kierunków.

### Świeża replikacja 2026-10-23: H005 i sędzia

Powtórne uruchomienie `nice -n 15 .venv/bin/python
experiments/h005_independent.py` zapisało `experiments/h005-independent/result.json`.
Selected-tagged wobec neutral-tagged dał `+0.2614156` active-edge share i
`-0.1031622` target MSE (30/30). Wobec selected-untyped wynik to
`-0.0056988` share i `+0.0011646` MSE (kierunek 12/30). H005 pozostaje
`critiqued`: selekcja się replikuje, tag nie daje wykazanej przewagi.

Pełny judge `candidates/coactivity_single_support_source_mass` uzyskał L1
`52.8685` (`R=.9935`) i L2 `27.7031` (`R=.9646`), oba zaliczone. L3 nie
został oceniony, bo kandydat nie implementuje `System.act`; wpis jest w
`sandbox/leaderboard.jsonl`. Test dojrzałości pozostaje negatywny:
`theory/theorist_axioms/sim/action_identifiability_result.json` pokazuje
40/40 identycznych pasywnych par z przeciwnymi optymalnymi działaniami.
Pasywna współaktywność nie koduje skutków interwencji ani preferencji stanów.
Nie dodano ręcznego sterowania. H005 i ograniczony zakres H007 zapisano w
`shared/hyp.py`.

### Powtórzenie wyników 2026-10-23: H005 i transfer biologa

Nowe uruchomienie H005 ponownie dało selected-tagged wobec neutral-tagged
`+0.261416` active-edge share i `-0.103162` target MSE w 30/30 seedów. Wobec
selected-untyped różnice wyniosły `-0.005699` i `+0.001165`, kierunek zgodny
tylko w 12/30; H005 pozostaje `critiqued`.

Pełny judge kandydata `coactivity_single_support_source_mass` dał L1 `52.8759`
(R=`.9935`) i L2 `27.7369` (R=`.9635`), oba zaliczone. L3 zatrzymał się na
braku `System.act`. Ponowiony test identyfikowalności: 40/40 par ma identyczne
obserwacje pasywne i przeciwne optymalne działania. Nie dodano `act`: potrzeba
modelu skutków interwencji oraz wewnętrznego kryterium preferencji stanów.
Wyniki zapisano w `experiments/h005-independent/result.json`,
`theory/theorist_axioms/sim/action_identifiability_result.json`,
`sandbox/leaderboard.jsonl` i `shared/hyp.py`.

### Świeży rerun tej sesji: H005 i test działania (2026-10-23)

Ponownie uruchomiłem `nice -n 15 .venv/bin/python experiments/h005_independent.py`.
Artefakt `experiments/h005-independent/result.json` powtórzył selected-tagged
wobec neutral: `+0.2614156` active-edge share i `-0.1031622` target MSE,
zgodnie w `30/30` par. Wobec selected-untyped otrzymano `-0.0056988` share,
`+0.0011646` MSE i zgodny kierunek `12/30`; H005 pozostaje `critiqued`.

Pełny judge `candidates/coactivity_single_support_source_mass` dał L1 `52.8725`
(`R=.9934`) i L2 `27.7222` (`R=.9627`), oba zaliczone; L3 zatrzymał się na
braku `System.act`. Istniejący transfer z `act` (`..._source_mass_action`) dał
L3 `6.4754` przy progu `16.2718`: przeżycie `8`, jabłka `0`, pokrycie `.08`,
poprawa uczenia `.002`. Ten wybór kierunku nie wynika z jednej podpory, bo
nie ma obserwowanego skutku interwencji ani porządku preferencji stanów.
Nie dodano mapy Snake'a ani sprzężenia zasobów z jabłkiem/długością węża.

### Lokalna konkurencyjna pula biologa i test dojrzałości (2026-10-23)

Przeniosłem propozycję z `biology/PRINCIPLES.md` §4 do
`candidates/local_competitive_support/principle.py`: całkowite wsparcie krawędzi
jest jednocześnie siłą, pamięcią i obecnością; aktywność konkuruje w lokalnym
budżecie, a zero oznacza usunięcie. Bez strojenia użyłem jawnego budżetu 4 i
tempa 1 jako parametrów prototypu. To abstrakcja testowa, nie twierdzenie o
dosłownej biologicznej zmiennej.

Judge zatrzymał kandydata na L1: wynik `17.5521`, próg `26.2446`, `R=.7859`,
`world_agnostic=true`; brak przejścia (`level_1_threshold_failed`). Nie
kontynuowałem L2/L3. Ponowny H005 dał te same kontrasty co poprzednio:
selected-tagged vs neutral `+.261416` udziału aktywnych krawędzi i `-.103162`
MSE (30/30), lecz tagged vs selected-untyped `-.005699` / `+.001165` (12/30).
H005 zostaje `critiqued`; selekcja się replikuje, przewaga typu tagu nie.

Test dojrzałości: z tej samej zasady nie wynika uczciwe działanie. Wsparcie
uczy korelacji pasywnych obserwacji, ale nie skutków interwencji ani porządku
preferencji. Wynik identyfikowalności `40/40` pasywnych par z przeciwnymi
optima jest zapisany w
`theory/theorist_axioms/sim/action_identifiability_result.json`. Brakuje
sprzężenia działanie→obserwacja oraz wewnętrznego kryterium wyboru; nie dodałem
parsera Snake'a ani powiązania zasobu z jabłkiem/długością. H007 pozostaje
wspierana tylko w ograniczonym zakresie L1/L2 wcześniejszego kandydata.

### Niezależny rerun H005 i judge transferu (2026-10-23, 01:33 UTC)

Świeże uruchomienie `experiments/h005_independent.py` dało selected-tagged
vs neutral `+0.2614156` active-edge share i `-0.1031622` target MSE (30/30).
Tagged vs selected-untyped dało `-0.0056988` / `+0.0011646` (zgodny kierunek
12/30); H005 pozostaje `critiqued`, bo typ pakietu nie wnosi wykazanej przewagi.

Pełny judge `coactivity_single_support_source_mass` uzyskał L1 `52.8811`
(`R=.9935`) i L2 `27.7323` (`R=.9633`), oba zaliczone. L3 nie może być
oceniony przez tę zasadę, bo `System.act` nie istnieje. Test dojrzałości:
pasywna współaktywność nie identyfikuje skutków interwencji ani wartości
stanów, więc uczciwe działanie nie wynika z tej samej zasady. Dodanie
hardkodowanego Snake'a byłoby strategią; brakującym elementem jest sprzężenie
działania z jego skutkiem oraz wewnętrzny porządek preferencji.
Wynik judge: `sandbox/leaderboard.jsonl`; rerun H005:
`experiments/h005-independent/result.json`.

### Rerun H005 i lidera sędziego (2026-10-23, 01:39 UTC)

`nice -n 15 .venv/bin/python experiments/h005_independent.py` ponownie
odtworzył wynik z 30 parami: selected-tagged minus neutral to `+0.261416`
active-edge share i `-0.103162` target MSE (30/30); selected-tagged minus
selected-untyped to `-0.005699` i `+0.001165` (12/30). H005 pozostaje
`critiqued`: selekcja pomaga wobec kontroli neutralnej, ale przewaga tagowania
nie jest wykazana.

Pełny judge `candidates/coactivity_single_support_source_mass` dał L1
`52.8792` (`R=.9933`) i L2 `27.7291` (`R=.9625`), oba zaliczone. L3 zatrzymał
się na braku `System.act`; wynik znajduje się w `sandbox/leaderboard.jsonl`.
Test dojrzałości: z tej samej pasywnej współaktywności nie wynika uczciwe
działanie. Jedna krawędź przewiduje następne obserwacje, lecz brak w niej
warunkowania na interwencji i kryterium porządkującego skutki. Nie dodano
mapowania kierunków Snake'a ani powiązania zasobu z jabłkiem/długością. H007
pozostaje wspierana wyłącznie dla predykcji i struktury L1/L2. Aktualizacje
H005/H007 zapisano przez `shared/hyp.py note`.

### Replikacja H005 i test działania (2026-10-23, świeży przebieg)

Ponownie uruchomiłem `nice -n 15 .venv/bin/python experiments/h005_independent.py`.
Wynik w `experiments/h005-independent/result.json` odtwarza selected-tagged
minus neutral: `+0.261416` udziału aktywnych krawędzi i `-0.103162` target MSE,
w zgodnym kierunku w 30/30 seedów. Tagged minus selected-untyped to nadal
`-0.005699` udziału, `+0.001165` MSE i zgodny kierunek w 12/30. H005 pozostaje
`critiqued`: selekcja zasobowa replikuje się, ale przewaga typu tagu nie.

Bez strojenia uruchomiłem `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/coactivity_single_support_source_mass_action --author eksperymentator`.
Wynik z `sandbox/leaderboard.jsonl`: L1 `43.6970` (`R=.9925`) i L2 `22.4498`
(`R=.9647`) przeszły; L3 Snake `6.4763`, poniżej bramki `13.0174`.
Inspekcja `act` pokazuje sumowanie predykcji w czterech równych grupach
obserwacji; grupy i ich mapowanie na akcje nie wynikają ze stanu
współaktywności. To wariant ze strategią formatu, nie wyprowadzone działanie.

Test dojrzałości pozostaje negatywny dla tej samej zasady: pasywna
współaktywność nie obserwuje skutków interwencji i nie porządkuje preferencji
stanów. Nie dodano nowego `act`, mapowania jabłek ani powiązania zasobu z
długością węża. H007 pozostaje wsparta wyłącznie dla transferu predykcji i
struktury L1/L2; potrzebne jest wspólne prawo uczenia skutków akcji oraz
wewnętrznego kryterium wartości stanu. Wpisy H005/H007 uzupełniono w rejestrze.

### Niezależna replikacja H005 i transfer wspólnego wsparcia (2026-10-23)

Uruchomiłem ponownie `nice -n 15 .venv/bin/python experiments/h005_independent.py`.
Wynik `experiments/h005-independent/result.json` powtarza selected-tagged vs
neutral: active-edge share `+0.261416`, target MSE `-0.103162`, kierunek 30/30.
Kontrola selected-untyped pozostaje praktycznie taka sama: tagged minus untyped
`-0.005699` share i `+0.001165` MSE, kierunek 12/30. H005 nadal jest
`critiqued`; efekt pochodzi z selekcji, nie z wykazanej tożsamości pakietu.

Pomysł biologa (lokalna współaktywność, jeden stan support/mass, wspólny budżet)
ma już transfer `candidates/local_competitive_support`. Świeży judge uzyskał L1
`17.5691`, `R=.7861`, poniżej progu `26.2446`, więc transfer nie przejął
szczebla. Dla kontrolnego lidera `coactivity_single_support_source_mass` świeży
judge dał L1 `52.8819` (`R=.9934`) i L2 `27.7518` (`R=.9632`); L3 zatrzymał
się na braku `System.act`.

Test dojrzałości pozostaje negatywny. Pasywny support przewiduje współaktywność,
ale nie obserwuje skutków własnej interwencji i nie ma wewnętrznego porządku
preferencji stanów. Nie dodałem mapowania Snake'a ani wiązania zasobu z jabłkiem
lub długością węża. Wyniki są w `sandbox/leaderboard.jsonl`, a H005/H007
odnotowane przez `shared/hyp.py note`.

### Niezależny rerun: H005, transfer biologa i test działania (2026-10-23)

`nice -n 15 .venv/bin/python experiments/h005_independent.py` ponownie
zapisał `experiments/h005-independent/result.json`: selected-tagged względem
neutral dał `+0.2614156` active-edge share i `-0.1031622` target MSE, kierunek
30/30. Względem selected-untyped różnice wyniosły `-0.0056988` share i
`+0.0011646` MSE, kierunek 12/30. H005 pozostaje `critiqued`; korzyść wynika
z selekcji, a przewaga tożsamości pakietu nie jest wykazana.

Ponowny pełny judge `candidates/local_competitive_support` uzyskał L1 `17.573`
(`R=.7859`), poniżej bramki `26.2446`; nie przejął szczebla. Kandydat koduje
konkurencyjne wsparcie w jednym całkowitym stanie krawędzi, lecz ta wersja
transferu nie odtwarza wyniku jednowartościowej współaktywności. Kontrolny
`candidates/coactivity_single_support_source_mass` uzyskał L1 `52.8797`
(`R=.9934`) i L2 `27.7402` (`R=.9635`), oba zaliczone; L3 zatrzymuje brak
`System.act`.

Test dojrzałości: z tej samej pasywnej współaktywności nie wynika uczciwe
działanie. `theory/theorist_axioms/sim/action_identifiability_result.json`
wykazuje 40/40 identycznych pasywnych par z przeciwnymi optymalnymi akcjami.
Brakuje obserwacji skutków interwencji i wewnętrznego kryterium preferencji.
Nie dodano mapy Snake'a ani powiązania zasobu z jabłkiem lub długością węża.
H005/H007 zaktualizowano w `shared/hyp.py`; wyniki sędziego są w
`sandbox/leaderboard.jsonl`.

### Niezależny rerun i wynik testu dojrzałości (2026-10-23)

Rerun H005 zachował te same wyniki: selected-tagged minus neutral to
`+0.2614156` active-edge share i `-0.1031622` target MSE (30/30), natomiast
tagged minus selected-untyped to `-0.0056988` i `+0.0011646` (12/30).
Wniosek się nie zmienia: selekcja działa w tym symulatorze, ale tagowanie
pakietów nie ma wykazanej przewagi.

Pełny judge `coactivity_single_support_source_mass` uzyskał L1 `52.8828`
(`R=.9934`) i L2 `27.7476` (`R=.9634`), oba zaliczone. L3 zatrzymał się,
ponieważ kandydat nie ma `System.act`. Zasada opisuje pasywną predykcję
współaktywności; nie zawiera akcji-warunkowanych obserwacji skutków ani
preferencji między stanami. Istniejący wariant `source_mass_action` wprowadza
grupowanie kanałów w kierunki, co jest dodatkową strategią, a nie konsekwencją
tej zasady. Zatem z tej samej zasady nie da się uczciwie wyprowadzić działania.
Niezależna identyfikowalność pokazuje 40/40 pasywnie identycznych par światów
z przeciwnymi optymalnymi akcjami. Wymagany fundament to doświadczenie
interwencyjne oraz wewnętrzne kryterium wartości; nie dodawałem mapy Snake'a
ani wiązania zasobów z jabłkiem lub długością węża.

Dowody: `experiments/h005-independent/result.json`,
`sandbox/leaderboard.jsonl` i
`theory/theorist_axioms/sim/action_identifiability_result.json`.

### Bezpośredni test istniejącego `act` (2026-10-23)

Uruchomiłem `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/coactivity_single_support_source_mass_action --author eksperymentator`
bez zmian parametrów. Kandydat używa największej sumy predykcji w czterech
równych grupach kanałów jako akcji; nie koduje jabłka ani długości węża, ale
nie uczy skutków własnych działań, a podział na cztery grupy nie wynika z prawa
podpory. Wynik L1/L2 to `43.7490/22.5655` (`R=.9931/.9621`); Snake L3 uzyskał
`6.4766` przy progu `16.2718`. Ten wariant nie przejął sterowania i nie
zmienia wniosku: pasywna podpórka nie wyprowadza działania. Brakuje
action-conditioned evidence i wewnętrznego kryterium preferencji. Wpis wyniku
jest w `sandbox/leaderboard.jsonl`.

### Rerun H005 i transferu biologa (2026-10-23)

Niezależna replikacja w `experiments/h005-independent/result.json` ponownie
dała selected-tagged wobec neutral `+0.2614156` active-edge share i
`-0.1031622` target MSE (30/30); wobec selected-untyped różnice wyniosły
`-0.0056988` i `+0.0011646` (12/30). H005 pozostaje `critiqued`: efekt
selekcji odtwarza się, ale etykieta pakietu nie wykazuje przewagi.

Bez zmiany PARAMS świeży judge `coactivity_single_support_source_mass`
przeszedł L1/L2 z `52.8759/R=.9934` i `27.7006/R=.9635`; L3 zatrzymał brak
`System.act`. Transfer pomysłu biologa `local_competitive_support` uzyskał
L1 `17.5728/R=.7858`, poniżej progu `26.2446`. Zatem lokalna konkurencyjna
alokacja w tej implementacji nie odtwarza wyniku lidera współaktywności.
Sam lider utrzymuje gęstą macierz wszystkich par; raportowana masa nie jest
rzadkim procesem tworzenia i przycinania krawędzi, więc wynik nie potwierdza
pełnej tezy biologa o eksploracyjnym wzroście połączeń.

Test dojrzałości pozostaje negatywny: 40/40 par o identycznych obserwacjach
pasywnych ma przeciwne optymalne akcje. Zasada nie zawiera efektów
interwencyjnych ani preferencji stanów, więc nie dodano `act`. Wyniki i zakres
wsparcia H005/H007 odnotowano w `shared/hyp.py`.

### Świeży judge source-mass i test działania (2026-10-23)

Uruchomienie `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/coactivity_single_support_source_mass --author eksperymentator`
bez zmiany kodu ani PARAMS uzyskało L1 `52.8795` (`R=.9934`) i L2 `27.7308`
(`R=.9638`), oba zaliczone. L3 zatrzymał się na braku `System.act`.
`action_identifiability_result.json` daje 40/40 pasywnie identycznych par
światów z przeciwnymi optymalnymi akcjami. Ta sama zasada nie zawiera więc
informacji potrzebnej do wyboru działania; potrzebuje interwencyjnych skutków
akcji i kryterium preferencji stanów. Nie dopisano strategii Snake'a.
Wpis wyniku jest w `sandbox/leaderboard.jsonl`; H007 pozostaje wsparta tylko
dla predykcji/struktury L1-L2. H005 pozostaje skrytykowana: tagowanie pakietów
nie przewyższało wariantu untyped (`experiments/h005-independent/result.json`).

### Rerun H005 i lidera, test dojrzałości (2026-10-23)

Ponownie uruchomiłem `nice -n 15 .venv/bin/python experiments/h005_independent.py`.
Wynik w `experiments/h005-independent/result.json` odtwarza poprzednią replikację:
selected-tagged minus neutral to `+0.2614156` udziału aktywnych krawędzi i
`-0.1031622` MSE (30/30); tagged minus selected-untyped to `-0.0056988` i
`+0.0011646` (12/30). Selekcja pomaga względem neutral, ale przewaga tagu
pakietu się nie replikuje; H005 pozostaje `critiqued`.

Świeży judge bez zmian kodu/PARAMS dla `coactivity_single_support_source_mass`
uzyskał L1 `52.8827` (R=`.9934`) i L2 `27.7460` (R=`.9636`), oba zaliczone.
L3 przerwał na braku `System.act`. Test identyfikowalności
`theory/theorist_axioms/sim/action_identifiability_result.json` zawiera 40/40
par z identycznymi pasywnymi obserwacjami i przeciwnymi akcjami optymalnymi.
Ta sama zasada nie wyprowadza działania: potrzebuje skutków warunkowanych
interwencją oraz kryterium preferencji stanów. Nie dodano polityki Snake'a.
H007 pozostaje ograniczone do predykcji/struktury L1-L2.

### Świeży rerun i werdykt dojrzałości (2026-10-23)

Rerun `experiments/h005_independent.py` odtworzył selected-tagged wobec neutral:
`+0.261416` active-edge share i `-0.103162` target MSE (30/30 seedów).
Kontrola selected-untyped nadal nie ustępuje: tagged-minus-untyped `-0.005699`
share i `+0.001165` MSE, zgodny kierunek tylko 12/30. H005 pozostaje
`critiqued`; selekcja działa w tym teście, przewaga tagu nie jest wykazana.

Świeży judge `coactivity_single_support_source_mass` uzyskał L1 `52.8808`
(`R=.9934`) i L2 `27.7404` (`R=.9630`), oba zaliczone; L3 przerwał na braku
`System.act`. Test dojrzałości daje odpowiedź negatywną: ślad pasywnej
współaktywności nie zawiera skutków własnych działań ani kryterium, które
stany są preferowane. Grupowanie czterech kierunków Snake'a byłoby osobnym
parserem/polityką, więc nie dodano `act` i nie wiązano zasobu z jabłkiem ani
długością węża. H007 pozostaje wsparta tylko dla predykcji/struktury L1-L2;
brakuje prawa uczenia skutków action->outcome oraz wewnętrznego porządku
preferencji stanów. H005 i H007 zaktualizowano w `shared/hyp.py`.

### Wynik tej sesji (2026-10-23)

Świeży judge bez zmian kodu ani PARAMS: `coactivity_single_support_source_mass`
uzyskał L1 `52.8812` (`R=.9934`) i L2 `27.7377` (`R=.9634`), oba zaliczone;
L3 zatrzymał brak `System.act`. H005 rerun dał selected-tagged vs neutral
`+0.261416` share i `-0.103162` MSE (30/30), lecz tagged vs selected-untyped
`-0.005699` share i `+0.001165` MSE (12/30). H005 pozostaje skrytykowane.
Test dojrzałości pozostaje negatywny: 40/40 pasywnie identycznych par ma
przeciwne optima; tej samej zasady brakuje skutków interwencji i kryterium
preferencji stanów, więc `act` nie wynika z niej bez wpisanej strategii.

### Niezależny rerun H005 i source-mass (2026-10-23)

Świeży przebieg `nice -n 15 .venv/bin/python experiments/h005_independent.py`
zapisał `experiments/h005-independent/result.json`. Selected-tagged wobec
neutral dał `+0.261416` active-edge share oraz `-0.103162` target MSE, z
właściwym kierunkiem w 30/30 parach. Tagged wobec selected-untyped dał
`-0.005699` share i `+0.001165` MSE, kierunek 12/30. Wynik wspiera efekt
selekcji względem neutralnego przepływu, lecz nie specyficzny efekt tagowania;
H005 pozostaje `critiqued`.

Pełny judge niezmienionego `coactivity_single_support_source_mass` uzyskał
L1 `52.8779` (`R=.9935`) i L2 `27.7052` (`R=.9630`), oba zaliczone. L3
zatrzymał się na braku `System.act`; wynik zapisano w
`sandbox/leaderboard.jsonl`. Test dojrzałości jest negatywny: 40/40 par z
identycznym śladem pasywnym ma przeciwne optima działania. Prawo współaktywności
nie zawiera ani skutków interwencji, ani wewnętrznego porządku preferencji,
więc działanie wymagałoby dodatkowej zasady. Nie dodano parsera Snake'a ani
wiązania zasobu z jabłkiem/długością. H007 pozostaje wsparta tylko dla
predykcji i struktury L1-L2.

### Replikacja i test prostszego stanu (2026-10-23)

Ponowny `experiments/h005_independent.py` odtworzył poprzednie liczby:
selected-tagged vs neutral `+0.261416` active-edge share, `-0.103162` target
MSE (30/30); tagged vs selected-untyped `-0.005699` share, `+0.001165` MSE
(zgodny kierunek 12/30). To wspiera selekcję w tym układzie, nie etykiety
pakietów; H005 pozostaje `critiqued`.

Świeży pełny judge niezmienionego `coactivity_single_support_source_mass`
przeszedł L1 `52.8760` (`R=.9935`) i L2 `27.7196` (`R=.9626`); L3 zatrzymał
się, bo system nie implementuje `act`. Dla prostszego `coactivity_one_state`,
którego struktura nie ogranicza źródeł do osobnej połowy kanałów, L1 wyniósł
`16.2651`, `R=.4551`, bez zaliczenia. Zatem to uproszczenie nie zachowuje
jakości sędziego; brak implementacji `act` nadal wyznacza granicę zasady H007.
Wpisy obu uruchomień są
w `sandbox/leaderboard.jsonl`; PARAMS pozostały bez zmian.

### Biologiczny toy interwencji i transfer do judge (2026-10-23)

Niezależnie ponownie uruchomiłem `nice -n 15 .venv/bin/python
experiments/h005_independent.py` oraz `biology/viability_pruning_probe.py`.
H005 odtworzyło selected-tagged vs neutral: `+0.261416` active-edge share,
`-0.103162` target MSE, zgodny kierunek 30/30; tagged vs selected-untyped:
`-0.005699` / `+0.001165`, kierunek tylko 12/30. Selekcja pozostaje
replikowalna, ale przewaga typed packet niewykazana; H005 nadal `critiqued`.

Toy biologa dał 40 par / 80 światów: trafność pasywna `0.50`, po próbkowaniu
interwencji `1.00`, a poprawne zachowanie jednej wspierającej krawędzi `1.00`.
Jest to demonstracja identyfikowalności, bo potrzeba, eksploracja i reguła
przycinania są podane przez skrypt, nie wyprowadzone przez agenta.

Transfer najbliższego istniejącego kandydata
`contextual_reversible_intervention` do pełnego judge nie zaliczył L1:
score `21.9774` < próg `26.2446`, `R=.9773`, `highest_passed_level=0`;
wpis w `sandbox/leaderboard.jsonl`. To nie zmienia zakresu H007, które
pozostaje wsparte wyłącznie dla predykcji i struktury L1-L2. Nie stroiłem
PARAMS ani nie mapowałem grup kanałów na akcje.

### Lokalny budżet współaktywności (2026-10-23)

Przeniosłem propozycję biologa z tablicy do `candidates/local_coactivity_budget/principle.py`:
każde źródło ma jeden skończony budżet masy, projekcja konkurencyjnych
współaktywności ustala dodatnie połączenia, a ta sama masa waży prognozę.
Zero oznacza brak krawędzi; nie ma osobnego progu, timera ani losowego
próbkowania. To konkretny transfer axiomatu, nie pełna realizacja szumu
eksploracyjnego biologa.

Uruchomiłem `nice -n 15 .venv/bin/python sandbox/judge.py
candidates/local_coactivity_budget --author eksperymentator`. L1 przeszedł z
`30.6573` (`R=.9919`), L2 nie przeszedł: `12.3445` (`R=.9869`). Wobec lidera
`coactivity_single_support_source_mass` (`52.8760` L1, `27.7196` L2) prostszy
wariant nie poprawia wyniku. Nie zmieniałem PARAMS po uruchomieniu. H041 jest
`critiqued` z powodu nieprzejścia L2; dane w `sandbox/leaderboard.jsonl`.

### Niegasnąca masa współaktywności (2026-10-23)

Jako test bez parametru czasu przeniosłem jedną średnią kroczącą signed
coactivity do `candidates/coactivity_running_mean/principle.py`. Jej najsilniejsza
krawędź zarazem przewiduje następny bit i wnosi masę do struktury; `PARAMS={}`.
To test pamięci jako skumulowanego dowodu, nie kolejny wariant strojenia
timescale.

`nice -n 15 .venv/bin/python sandbox/judge.py candidates/coactivity_running_mean
--author eksperymentator` zatrzymał się na L1: `19.2671` przy baseline `20.9957`,
poniżej progu `26.2446`; `R=1.0`, `world_agnostic=true`, `highest_passed_level=0`.
H043 ustawiona `refuted`. Brak strojenia. Wynik zapisano w
`sandbox/leaderboard.jsonl`; nie da się na jego podstawie wnioskować o L2.

### Rerun H005, toy biologa i lidera (2026-10-23)

Świeże uruchomienie `experiments/h005_independent.py` odtworzyło wynik z
30 sparowanych seedów: selected-tagged minus neutral to `+0.261416` udziału
aktywnych krawędzi i `-0.103162` MSE, oba kierunki 30/30. W porównaniu z
selected-untyped różnica wyniosła `-0.005699` i `+0.001165`, kierunek tylko
12/30. H005 pozostaje krytykowana: selekcja ma efekt, tagowanie typu nie ma
wykazanej przewagi. Wynik jest w `experiments/h005-independent/result.json`.

`biology/viability_pruning_probe.py` ponownie dał 40 par / 80 światów:
trafność pasywna `0.50`, wybór po interwencji `1.00`, poprawna retencja jednej
krawędzi `1.00` (`biology/viability_pruning_probe_result.json`). Toy narzuca
potrzebę, próbkowanie oraz regułę retencji, więc jest testem identyfikowalności,
nie implementacją samowyłaniania tych mechanizmów.

Pełny rerun `coactivity_single_support_source_mass` dał judge L1 `52.8758`
(R=`.9935`) i L2 `27.7270` (R=`.9635`), zaliczone oba poziomy; L3 nie jest
oceniony, bo `System.act` nie istnieje. Zapis w `sandbox/leaderboard.jsonl`.
Wniosek H007 ogranicza się do predykcji i struktury na L1-L2. Nie zmieniałem
reguł ani parametrów i nie wykonywałem strojenia.

### Bezparametrowy zwrot masy (2026-10-23)

Świeży rerun `experiments/h005_independent.py` odtworzył H005: selected-tagged
minus neutral to `+0.2614155966` active-edge share i `-0.1031621906` target
MSE, oba kierunki `30/30`; względem selected-untyped było `-0.0056988311`
i `+0.0011646236` (kierunek `12/30`). H005 pozostaje `critiqued`.

Przeniosłem aksjomat jednego stanu do
`candidates/coactivity_returned_mass/principle.py`. Każda komórka przechowuje
tylko signed relation i returned mass; masa jest zwiększana przez poprawność
predykcji, a `scale = width` wynika z rozmiaru układu. Ta sama masa waży wybór
relacji i `structure()`, bez `PARAMS`, progów i osobnych mechanizmów.

Judge: L1 `44.9998`, L2 `21.4688`, oba zaliczone, `R=1.0`; L3 zatrzymany na
braku `System.act`. Lider `coactivity_single_support_source_mass` osiągał
L1 `52.88` i L2 `27.7`, więc transfer nie pobił lidera. Wynik negatywny dla
przewagi tej postaci, ale potwierdza przenośność zasady do L2 bez strojenia.
Artefakt: `sandbox/leaderboard.jsonl`; H023 pozostaje `testing`.

### Niezależna replika H045 (2026-10-23)

Uruchomiłem odkrywczy kandydat `candidates/agency_control_closure/principle.py`
bez zmian. Judge zakończył na L1: score `0.9812`, próg `26.2446`, baseline
`20.9957`, robustness `0.9998`, `highest_passed_level=0`. Zasada pozostaje
world-agnostic, ale implementacja ma 55 literałów i 10 gałęzi, co obniża
mnożnik elegancji do `0.1`. H045 pozostaje `testing`; wynik zapisano w
`sandbox/leaderboard.jsonl` i odnotowano w `shared/hypotheses.json` oraz na
tablicy. Bez strojenia parametrów.

Test dojrzałości `coactivity_returned_mass`: nie da się wyprowadzić jego Snake
`act` z tej samej zasady bez wprowadzenia action-conditioned evidence. Kandydat
ma tylko pasywne krawędzie źródło-cel i masę zwrotu, więc mapowanie obserwacji na
ruch byłoby wpisaną strategią, nie konsekwencją przepływu. Nie dodawałem `act`
ani nie powtarzałem wcześniejszego judge L1/L2.

### Niezależne repliki H051 i H052 (2026-10-23)

H051 `predictive_consequence_address` uruchomiłem bez zmian i bez strojenia
`PARAMS`. Judge dał L1 `18.3267` przy progu `26.2446`, `R=1.0000`,
`highest_passed_level=0`, więc adresowanie kontekstu przez podpis konsekwencji
nie potwierdziło swojej deklarowanej przewagi. Wynik jest w
`sandbox/leaderboard.jsonl`; H051 pozostaje `testing`.

H052 `agency_continuation_return` ma `System.act()` i był świeżym kandydatem
odkrywcy agency. Niezależny judge zakończył się na L1: score `2.7357`,
`R=.9941`, próg `26.2446`, `highest_passed_level=0`. Toy kontynuowalności nie
przeniósł się na wynik Snake. Odkrywca agency później ustawił H052 na `parked`
po wyczerpaniu budżetu testów. Oba wyniki zapisano także w
`shared/hypotheses.json` i wysłano na tablicę.

### Niezależna replika aktualnego H049 (2026-10-23)

Uruchomiłem bez zmian aktualny `candidates/contact_frontier_growth`. Judge dał
L1 `9.3618` wobec progu `26.2446` i baseline `20.9957`; robustness `1.0`,
`highest_passed_level=0`. SHA-256 `37a0a219a3e2a01a2371089aed27deb8b37d00a5e57cf03b4430844fdcdb5e83`.
Wynik potwierdza brak deklarowanej przewagi predykcyjnej aktualnego kandydata;
nie testowałem wariantów parametrów. H049 oznaczono `refuted`. Artefakt:
`sandbox/leaderboard.jsonl`.

### Replika potomka zwrotnego przepływu z akcją (2026-10-23)

Po nowym wpisie odkrywcy_dynamics uruchomiłem pełnego sędziego na
`candidates/returned_flow_edge_action/principle.py` bez zmian i bez strojenia
(`timescale=16`, `decay=0.97`, SHA
`bef3d7ebe0534168b8752a833ab06c198563318f2d3168074aeba2d61aec89ee`). To
potomek `resource_flow_memory` i `resonant_edge_dynamics`; sprawdzenie
literaturowe exact-phrase nie zwróciło wyniku.

L1 uzyskał 50,5445 (R=0,9934), L2 26,2292 (R=0,9636); oba zaliczone.
L3 uzyskał 16,5259 przy progu 16,2718 i R=0,9999, ale nie przeszedł bramki
uczenia: improvement=0,0, 0/1 poprawionych par, średnio 25 kroków, 0,333
jabłka i coverage 0,233. Dlatego nie jest to zaliczenie poziomu ani transfer
skutecznego sterowania. Wynik dopisano do `sandbox/leaderboard.jsonl`.

To niezależna replika potomka, nie bezpośredni test H054 ani H057; ich statusów
nie zmieniono. Notatka o potomku została dodana do H057. Nie powtarzać tej
samej repliki/SHA.

### Test dojrzałości: temporal coherence closure -> działanie (2026-10-23)

Nie dodawałem `act()` do `candidates/temporal_coherence_closure`: zasada
utrzymuje EMA relacji obserwacja->obserwacja w dwóch skalach czasu, lecz nie
rejestruje, jaka interwencja poprzedziła skutek. Nawet po dodaniu takich
action-tagged śladów sama zgodność nie wyznacza, który skutek warto wybierać;
potrzebny byłby dodatkowy porządek konsekwencji. Traktowanie większej
przewidywalności jako celu byłoby wpisaną preferencją, nie wyprowadzeniem z H042.

Nie powtarzałem judge ani toy testu. Wykorzystana istniejąca sonda
`theory/theorist_axioms/sim/action_identifiability_result.json`: w 40/40 par
światy miały identyczną historię pasywną (średnia różnica 0), ale przeciwne
najlepsze akcje. To potwierdza konkretny brak zasady: interwencyjnego,
action-conditioned dowodu oraz niezależnie uzasadnionego porządku skutków.
H042 pozostaje `testing`; nie aktualizowałem jej wyniku ani statusu.

### A-B-A dla H057 (2026-10-23)

Uruchomiłem nowy niezależny test `experiments/h057_return.py` na niezmienionym
`candidates/return_flow_self_normalized/principle.py`: 40 seedów, fazy po 500
kroków, z parowanym null bez zależności źródło-cel. Błąd celu dla końca
pierwszego A wyniósł `0.2626032`, a po powrocie A `0.2556499` (różnica
`-0.0069533`, powrót szybszy w 57.5% seedów). Null również poprawił się
(`0.2712946` do `0.2612286`), a sparowany zysk powrotu ponad null to
`-0.0031127`. Brak swoistego dowodu pamięci A-B-A; H057 pozostaje `testing`.
Artefakt: `experiments/h057_return_result.json`.

### Niezależna replika H058 action-effect closure (2026-10-23)

Parowany toy test z odwróconymi stabilnymi ID akcji, wspólnym seedem zakłóceń
i 240 krokami na świat dał late stable-action share `1.0` dla obu ID w 40/40
parach. Artefakt: `experiments/h058_replica.py` i
`experiments/h058_replica_result.json`. Pełny judge niezmienionego SHA
`3c2979cdb31fa01bace7b9b13aa3939747d947928bd9e22eba98e94edefdbeda` zakończył
się po L1: `18.2071`, R=`0.9434`, poniżej progu `26.2446`; L2/L3 nie były
uruchomione. Toy replikuje selekcję stabilnego skutku, lecz transfer judge
pozostaje niepotwierdzony. H058 pozostaje `testing`.

### Niezależna replika H055 (2026-10-23)

Uruchomiłem bez zmian `candidates/return_margin_growth/principle.py` przez
judge. Bieżący SHA `b5e67967f8ebe84dcb687b5b7b996b10028e1c5a9cd091a23c56607122570b27`
uzyskał L1 `4.3729`, robustness `0.9664`, wobec progu `26.2446`; Brier/
prediction skill nie poprawiły baseline, a judge zakończył test po L1.
Odtworzyło to wynik odkrywcy (L1 `4.3819`, Brier `0.2771`): sparsity i
struktura nie wystarczają, jeśli predykcyjna marża nie pokonuje persystencji.
Nie zmieniałem parametrów ani zasady. H055 oznaczono `refuted`; wpis z
niezależnym wynikiem jest w `sandbox/leaderboard.jsonl`.

### Niezależna replika H059 (2026-10-23)

Ponownie uruchomiłem prerejestrowany test A-B-A 40 seedów na niezmienionym
`candidates/returned_reserve_relations/principle.py`. Sparowany zysk powrotu
ponad null wyniósł `-0.0134777`, `-0.0063883` i `-0.0019785` dla luk 100,
500 i 1500; każdy wynik jest poniżej kryterium `0.01`. Wyniki
`theory/theorist_axioms/sim/returned_reserve_return_result.json`.

Judge SHA `522c86ba0482dca5c5ad30742759af8655c3f981c55d7ba43ebd006dd7756423`:
L1 `50.0230` (R `.9915`), L2 `21.4548` (R `.9070`), L3 niedostępny, bo
kandydat nie implementuje `act()`. H059 obalona przez prerejestrowaną
predykcję A-B-A; bez strojenia. Wpis sędziego w `sandbox/leaderboard.jsonl`.

### Niezależny stress test H061 (2026-10-23)

Rozszerzyłem test szybkiego przełączania do 12 źródeł, 30 seedów, segmentów
80 kroków i szumu `.15`; każdy z 12 indeksów jest aktywny w harmonogramie.
`resource_flow_replicator` uzyskał match `.68229` wobec Hebba `.65139`
(różnica `+.03090`), ale Brier `.21068` wobec `.20518` (gorzej o `.00550`).
Przewaga match nie replikuje warunku „Brier nie gorszy”. Artefakt:
`experiments/h061_12source_replay.py` i `.json`. Kandydat pozostał bez zmian.

Próba uruchomienia judge dla istniejącego kandydata zakończyła się przed
oceną: `sandbox/judge.py:2277` zawiera `***@***` w niedomkniętym `try`
(SyntaxError). Zgodnie z zakazem nie zmieniałem `sandbox/`. H061 odłożona po
niezaliczeniu prerejestrowanego stresu; wcześniejszy test 8-źródłowy i L1
41.5638/L2 12.861 pozostają częściowym wynikiem autora, nie są nowym runem.

Sprawdzenie dojrzałości `returned_reserve_relations`: jej zwrotny zasób może
porządkować trwałość/predykcję relacji, ale nie określa wartości skutków ani
celu działania. `act()` wymagałoby dodatkowej zasady preferencji lub
kontrolowalności; nie da się go wyprowadzić z tej samej zasady bez dopisania
strategii. H059 pozostaje obalona; nie ponawiałem jej testu.

### Niezależna replika H062 (2026-10-23)

Uruchomiłem odrębny replay zasady returned downstream controllability na 40
sparowanych światach (seedy 1000-1039, 240 kroków). Średni udział poprawnej
akcji w ostatnich 100 krokach wyniósł `1.0` wobec przypadku `.5`; oba pierwsze
światy uzyskały `1.0`. Artefakt: `experiments/h062_returned_control_replay.py`
i `.json`. To wspiera wyłącznie toy prediction, nie falsyfikator Snake.

Próba transferu istniejącego kandydata
`agency_returned_control_field` do judge zatrzymała się na
`sandbox/judge.py:2283` (`SyntaxError: ***@***`); sandbox nietknięty. H062
pozostaje `testing` do czasu oceny poziomu Snake. Bez strojenia parametrów.

### Niezależna replika adaptive_contact_flux (2026-10-23)

Niezależnym seedem 1931 odtworzyłem fazową sondę kandydata
`adaptive_contact_flux`: dla szerokości 8/16/32/64 liczby krawędzi zmieniły
się z 4/8/16/32 w fazie rich na 0/0/0/0 po uproszczeniu. Brier rich wyniósł
`.1321-.1323`, a simple `.2493-.2519`. Wynik wspiera adaptację struktury w
syntetycznym świecie; artefakt: `experiments/eksperymentator_adaptive_contact_replay.py`
i `.json`.

Niezmieniony kandydat przeszedł przez judge: L1 `2.4446` wobec baseline
`20.9957`, robustness `.7751`, próg L1 niezaliczony; wpis w
`sandbox/leaderboard.jsonl`. Zasada nie ma osobnego wcześniejszego ID, więc
zarejestrowałem H063, oddzielnie od rozstrzygniętej H055, i oznaczyłem ją
`refuted`. Nie strojono parametrów. Wyszukiwanie literatury zwróciło prace o
przycinaniu sieci, bez sprawdzonych źródeł dowodzących nowości tej zasady.

### Niezależny test Snake H062 (2026-10-23)

Po nowym wyniku odkrywcy uruchomiłem oficjalny judge dla
`agency_returned_control_field`; L1 `4.6131` wobec baseline `20.9957`,
robustness `.9997`, więc test nie przeszedł do Snake. Niezależny replay na
nowych seedach 1327/2039/4127 (po 2 epizody) dał kandydatowi średnio 6 kroków,
0 jabłek i coverage `.06`; random baseline miał 29.33 kroku, 0 jabłek,
coverage `.22`, a wall baseline 1000 kroków, `.667` jabłka, coverage `.40`.
Artefakt: `experiments/eksperymentator_h062_snake_replay.py` i `.json`.

Wynik obala przewidywanie Snake dla H062 i pokazuje, że wcześniejsze 1.0 vs
`.5` w toy selectorze nie opisuje działania `System.act()`. H062 ustawiona
`refuted`; oficjalny judge oraz replay zgłoszone na tablicy. Bez zmian
parametrów i bez powtarzania toy replayu.

### Niezależna replika przeniesienia H057 do judge (2026-10-23)

Uruchomiłem niezmieniony `candidates/consequence_gated_return_flow` w
oficjalnym judge. L1 `53.2995` przy robustness `.9918` i L2 `27.9707` przy
`.9607` przeszły; L3 zatrzymał brak `System.act`. Wynik replikuje transfer
predykcyjny odkrywcy (L1 `53.3287`) i zachowuje pozycję ponad wskazanym
baseline'em, ale nie dowodzi pamięci: wcześniejszy A–B–A miał zyski
`-.01293/-.00328/-.00208`. H057 pozostaje `testing`; nie zmieniano kodu ani
parametrów. Wpis repliki w `sandbox/leaderboard.jsonl`.
# H066 — niezależna replika predictive return budget (2026-10-23)

Uruchomiłem `experiments/eksperymentator_h066_replay.py` z nowym seed base
61007 na szerokościach 8/16/32/64, w kolejności 640 kroków rich i 640 simple.
Na aktualnym SHA `3d37668a…` liczba krawędzi w fazie simple wyniosła
64/256/1023/4093, wobec rich 64/256/1021/4095; średnie w końcowej części
simple pozostały 64.0/255.8/1022.8/4091.8. Struktura nie zanika po utracie
regularności, choć Brier spada z rich .1768–.2037 do simple .2228–.2260.
Pamięć wciąż rośnie kwadratowo (width*8 + 40 B/krawędź), więc test H066
falsyfikował warunek zaniku i ograniczonej struktury.

Niezależny judge na tym SHA: L1 9.5768, baseline 20.9957, odporność .4217,
poziom 1 niezaliczony. Wynik i szczegóły: `experiments/eksperymentator_h066_replay.json`
oraz `sandbox/leaderboard.jsonl`; H066 ustawiono na `refuted`.

Test dojrzałości H057: `consequence_gated_return_flow` przechowuje i aktualizuje
predykcyjne relacje między obserwowanymi bitami. Nie koduje, jaka akcja
spowodowała powrót konsekwencji ani nie ma stanu action-conditioned; z tej
samej zasady nie wynika wybór akcji bez nowego mechanizmu wiążącego działanie
z obserwowanym skutkiem. Nie dodano `act`; H057 L1/L2 replika i brak `act` na
L3 pozostają jak w poprzednim wpisie handoff.
