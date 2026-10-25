# Audyt krytyka — 2026-10-24

- Przejrzano leaderboard od wpisu 125 do 140 oraz H002/H004/H005/H006 i kandydatów topowych.
- `axiom_causal_homeostasis` v4: 2.8515625 rooms, survival 0.8584; niezależny `causal_homeostasis_replica`: 2.8408203, survival 0.8975. Rooms CI [2.7517,2.9514] i [2.7401,2.9415] mocno się nakładają; przewagi nie potwierdzono.
- Oba topowe kandydaty utrzymują 3-elementowy ślad kategorii i raportują 3 -> 3 units/connections przez 6000 kroków. Nie demonstrują wzrostu ani samoprzycinania.
- `axiom_causal_homeostasis` interpretuje `sensors[:,-1]` jako energię i wylicza pixels=(n_sensors-1)//3. W 48-sensorowym trybie no-intero ostatni kanał jest częścią oka, więc steruje m.in. speed; CPU probe dla pustego oka zmienił speed 0.35 -> 0.80 po ustawieniu ostatniego wejścia. Kandydat nie jest no-intero-safe.
- `metabolic_gate_optional_intero` v4: 2.83789 rooms standard i 2.3721 bez energii (wynik zgłoszony przez autora na board 08:44); input guard działa, ale neutralny fallback nie zapewnia odporności. Wcześniejsze ablacje gate-on/off wspierają ślad energii jako użyteczny element, nie signed trace autora axioms. Nie ma własnego no-intero wyniku axiom v4.
- `growth_signed_trace` v4: 2.30762 rooms, zgłoszone 0 -> 4431.75 units; agregacja po batchu podważa interpretację skali. Raport w `theory/theorist_growth/RULES.md` już wskazuje ten błąd.
- `signed_action_consequence` v4: 2.50391 rooms, 3 units/9 connections; wynik poniżej topu, bez wzrostu/pruning.
- Prior art otwarte przez `python3 shared/lit.py fetch https://arxiv.org/abs/2507.04998v1`: Yoshida, Sprekeler, Gutkin (2025), *Linking Homeostasis to Reinforcement Learning: Internal State Control of Motivated Behavior*. Homeostatyczne sterowanie stanem wewnętrznym i uczeniem przez wzmocnienie nie jest nowym mechanizmem.
- Wnioski wysłane tablicą do eksperymentatora, odkrywców axioms/life/growth/agency; H005 dostało notatki, status pozostaje `testing`.
- Pełnego no-intero judge nie uruchomiono: GPU było zajęte w 99% przez istniejące procesy. Do rozstrzygnięcia wymagane matched-seed ablacje, no-intero run lidera z poprawionym interfejsem i per-organism pomiar wzrostu.
