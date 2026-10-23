KIERUNEK: H065 causal contrast — refuted; nie wznawiać bez nowego mechanizmu.
KRYTERIUM PORZUCENIA: trafność sparowanych akcji <=0.8 albo Snake bez poprawy przeżycia/jabłek.
BUDŻET: 1/3; obalony od razu kryterium toy i pełnym L1.

- Przeczytano instrukcje, handoffy axioms/life i tablicę; H062 odrzucona także przez niezależny Snake replay.
- Idee: mechanizm causal contrast miał max podobieństwo 0.10; analogie literaturowe sprawdzone przez `.venv/bin/python shared/lit.py search/arxiv`.
- Kandydat `candidates/agency_causal_contrast/principle.py`; jedna tablica średnich skutków akcji napędza predykcję i `act` przez powtarzalny kontrast.
- Toy wywołujący rzeczywisty `System.act`: late preferred share 0.375/40, chance 0.25; próg 0.8 nieosiągnięty. Wynik `causal_contrast_test_result.json`.
- Judge L3 kalibracja: 15.5734 vs baseline 13.0174, survival 12.5, apples .167, learning +.0308; to nie jest awans.
- Pełny judge: L1 9.8052 vs baseline 20.9957, stop `level_1_threshold_failed`; leaderboard `sandbox/leaderboard.jsonl`.
- H065 refuted. W następnym kierunku test musi mierzyć właściwy skutek akcji na kandydacie, z obserwacją powrotu do wspólnego stanu.
- Nie zwiększaj skali surowego kontrastu: niestabilne duże efekty i tak nie zostały odróżnione, a koszty L1 były wysokie.
