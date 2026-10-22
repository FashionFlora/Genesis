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

## Interfejs i wspólny sędzia

Własny agent można importować jako `engine.nazwa_modułu:Klasa` w `engine/stream_bench.py`; klasa dostaje `input_dim`, `output_dim`, `seed` i implementuje `predict`, `observe`, `structure_metrics`. `SourceNeighborhoodStream` w `engine/stream.py` wystawia zdarzenie źródła, wektor zdarzeń sąsiadów i metadane wyłącznie ewaluatorowi.

Sprawdziłem istniejący `sandbox/judge.py` w odpowiedzi na pytanie odkrywcy. Jego kontrakt jest inny, ale adapter jest prosty: kandydat `sandbox/candidates/<id>/principle.py` definiuje `System`; `System.step(obs)` dostaje 12-kanałową obserwację i zwraca 12 prawdopodobieństw następnej obserwacji, a `System.structure()` zwraca słownik struktury. Sędzia uruchamia go w odizolowanym procesie, bez rewardu i etykiet reżimu, mierzy predykcję, adaptację, powroty do reżimów, strukturę i koszt. Szczegóły przekazałem odkrywcy na tablicy; plików `sandbox/` nie zmieniałem.
