# Raport zadania N1 — Novelty Auditor

Data: 2026-10-22

## Zakres i wyniki
- Przeczytano `CLAUDE.md`, schemat rejestru i tablicę agentów.
- Skontrolowano wszystkie dostępne pliki `registry/areas/*.jsonl`: katalog `registry/areas/` nie zawiera jeszcze żadnych plików. Nie było więc rekordów do próbkowania; brak wyników nie oznacza poprawności rejestru.
- Ogłoszenie Forward-Forward od `no_backprop` sprawdzono przez otwarcie strony abstraktu oraz pełnego HTML arXiv: `https://arxiv.org/abs/2212.13345` i `https://arxiv.org/html/2212.13345`.
- Zapisano 4 wpisy w `audit/claims.jsonl`: dwa dotyczące mechanizmu/nowości Forward-Forward (werdykty `partial`, `partial`), jeden ograniczony werdykt `not_found` odnoszący się do raportu experiment_engine, oraz weryfikację tabeli Crafter zgłoszonej przez `intrinsic_motivation` (`known`). Ostatni wpis odzwierciedla wyłącznie zgłoszoną listę kandydatów, nie niezależne przeszukanie.
- Brak potwierdzonych błędów rekordów; `audit/registry_check.jsonl` jest pusty z powodu braku rekordów.

## Najważniejsze ustalenie
Pełny tekst opisuje dwa przejścia forward i warstwowe kryterium goodness (np. suma kwadratów aktywacji ReLU) z dodatnimi i ujemnymi danymi. W opisanym ustawieniu supervised MNIST poprawna/błędna etykieta jest częścią odpowiednio dodatniego/ujemnego przykładu. Artykuł opisuje unikanie propagacji pochodnych między warstwami, ale to nie oznacza braku nadzoru. W otwartym tekście nie znaleziono Craftera. Autor nazywa FF nową procedurą i omawia inspiracje/prace pokrewne; to nie wystarcza, by stwierdzić ani pierwszeństwo absolutne, ani identyczne wcześniejsze disclosure. Dokładne pierwszeństwo wymaga porównania równań z cytowanymi pracami.

Wyniki WebFetch nie były kompletne/bezbłędne przy zapytaniu o precyzyjne porównanie; dlatego nie wpisano niezweryfikowanych tytułów ani szczegółów bibliograficznych poprzedników jako odrębnych rekordów. Wpis źródłowy odsyła do otwartego tekstu.

## Narzędzia
- `audit/PROCEDURE.md`: procedura porównywania równań, sygnałów, kodu i testów kontrolnych; checklista ogłoszenia nowości.
- `audit/search.py`: deterministyczne cosine TF-IDF w standardowej bibliotece Pythona, teksty zważone dla `principle` i `learning_rule`, uwzględnia też `learning_signals`; sortowanie remisów po ID. Skrypt kompiluje się i obsługuje brak rejestru bez wyjątku. Obecnie rejestr wejściowy jeszcze nie istnieje, więc nie mogę zweryfikować rankingów na danych rzeczywistych.
- Odpowiedź audytowa z korektą zakresu twierdzenia została wysłana do `no_backprop`; ustalenie o nadzorze wysłano również do `all`. Wyniki Plan2Explore/RND/Random z Tabeli 1 zostały niezależnie sprawdzone i przekazane do `all`; nie rozstrzygają kryterium no-backprop.

## Ograniczenia / dalsze kroki
Dalszy audyt należy wznowić po pojawieniu się plików w `registry/areas/` i nowych twierdzeń na tablicy; należy pobrać/przeczytać źródła pierwotne każdego sprawdzanego rekordu oraz uzupełnić audyt rejestru bez edycji cudzych plików. Narzędzie rankujące jest wyłącznie pomocą do odkrywania podobnych wpisów, nie dowodem nowości.
