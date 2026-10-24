# Replikacja: dwufazowa homeostaza synaptyczna

Hipoteza H002 opiera się na poście biologa z 2026-10-24, odsyłającym do Lu et al. (eLife 2025). Sam opis literatury nie jest tu traktowany jako źródło wyniku; cyfrowa replikacja sprawdza tylko mechanizm.

Kandydat `candidates/biphasic_homeostasis/principle_organism.py` reguluje wolną skalę wag odchyleniem aktywności od celu, rekrutuje krawędzie przy niskiej aktywności i usuwa długo nieużywane słabe krawędzie. Uczy preferencję koloru przez własną zmianę energii po gryzieniu. Nie używa nagrody świata ani dostępu do stanu świata.

Przewidywanie: mechanizm poprawi przejście pokoi względem losowego ruchu; efekt wkładu homeostazy/wzrostu wymaga porównania z ablacją (`scaling_rate=0`, `growth_rate=0`) na tych samych seedach.

Uruchomienie pełne: `nice -n 15 .venv/bin/python sandbox/judge.py candidates/biphasic_homeostasis --organism --organism-seeds 8 --author eksperymentator`. Wynik po zakończeniu należy brać wyłącznie z `sandbox/leaderboard.jsonl`.

## Wynik

Oczekuje na ukończenie uruchomienia. Pierwsze uruchomienie bez `--organism-seeds 8` zostało odrzucone przez walidację i nie jest pomiarem.

## Ablacja

Nie wykonana w tej turze. Bez niej wynik kandydata nie potwierdza mechanistycznego wkładu dwufazowości.
