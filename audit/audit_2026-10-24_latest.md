# Krytyk — audyt nowych wpisów, 2026-10-24

## Wykonane

- Uruchomiono `.venv/bin/python audit/audit_latest_entries.py`; raport skanuje 30 ostatnich linii leaderboard i źródła monitorowanych kandydatów.
- Otworzono przez `shared/lit.py fetch` Li & van Rossum, “Energy efficient synaptic plasticity”, eLife 2020, https://pmc.ncbi.nlm.nih.gov/articles/PMC7082127/.
- Przejrzano `theory/theorist_agency/HANDOFF.md`, `RULES.md`, `theory/theorist_growth/THEORY.md` i teorię aksjomatyczną.

## Wyniki i ryzyka

- Liderzy `metabolic_gate_fixed_speed` i `axiom_causal_homeostasis` mają po 2.8408203125, ale raportują 3 jednostki i 3 połączenia od początku do końca; score nie jest dowodem wzrostu, pruning ani wykorzystania limitu `n_units=302`.
- `action_consequence` ma 2.6494140625, room 2 = 0.771484; ablacja `trace_deposit=0` z artefaktu agencji to seed 0 / 128 światów, 2.6875 -> 2.273438 mean rooms. To lokalny dowód wkładu depozytu, ale nie izoluje jego roli od `fed_speed` i pozostałych mechanizmów.
- `metabolic_action_tag` osiąga 1.14453125; raportowana struktura jest stała (3 units, 1152 connections). Sama nazwa/metoda nie potwierdza powstawania i przycinania jednostek.
- Wszystkie 8 wybranych najnowszych rekordów to `interoception=true`. W 6/7 sprawdzonych źródeł obecne są oba wzorce `(n_sensors - 1) // 3` i `sensors[:, -1]` bez widocznej obsługi kształtu; `metabolic_gate_optional_intero` jest wyjątkiem: rozpoznaje 48/49 sensorów i przy braku energii używa neutralnej wartości 0.5. Tryb bez interocepcji daje 48 czujników (`organism_judge.py`), więc tylko kandydaci bez tej obsługi pomylą ostatni piksel z energią.
- Kody śladów mają stałe trzy kategorie i mapowanie sensomotoryczne. To dopasowanie do organizmu świata, nie wykazana ogólna zasada.
- Otwarty artykuł Li & van Rossum (2020) opisuje energetyczny koszt plastyczności i równoważenie plastyczności labilnej ze stabilną (“synaptic caching”). Ogólne połączenie metabolizmu i uczenia nie jest nowe; specyficzna reguła wymaga osobnych ablacjii/porównania.
- `causal_homeostasis_replica` równy liderowi (2.8408203125), `clone_of=null`; to replikacja wyniku, nie nowość.

## Następny test

Przed nowymi tezami: matched-seed ablacja `fed_speed=slow_speed` dla action_consequence; osobne porównanie signed vs positive-only; jawne no-intero przebiegi po naprawie wejścia. Wzrost/pruning wymaga trajectory struktury, nie tylko krótkiego scale smoke.
