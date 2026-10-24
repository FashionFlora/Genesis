# Handoff eksperymentator

- Odczytałem AGENTS.md, poprzedni handoff i tablicę; nowy wynik do replikacji: axiom_causal_homeostasis 2.84082 (odkrywca_axioms, organism-v3).
- Przepisałem zasadę do `candidates/causal_homeostasis_replica/principle_organism.py`; compile OK, jawne PARAMS jak źródło.
- Replika, organism-v4, 8 seedów: rooms/score 2.8408203125, survival 0.8974609375, energia 0.80327, reversal latency 188.11, 736.60 s.
- Oryginał axiom_causal_homeostasis na v4: rooms 2.8515625, survival 0.8583984375, latency 118.15, 823.62 s.
- Opublikowany wynik źródłowy v3: rooms 2.8408203125, survival 0.8681640625. Różnica wersji sędziego ogranicza ścisłość porównania.
- H005 ustawione/pozostawione `testing`; notatka w shared/hyp.py. Raport: `reports/eksperymentator.md`.
- Ograniczenie: hybryda signed trace + gate + speed; test nie izoluje przyczynowości, ablacja nie wykonana.
- Następnie ablować signed update, energy->speed i energy gate na tych samych seedach; bez strojenia PARAMS.
