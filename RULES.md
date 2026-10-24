# Rules

- An energy-only gate lets lucky reflexes advance; require sustained feeding
  after a color reversal and a complete non-overlapping energy window.
- Random colors, visible decoys with a bite cost, depletion/regrowth, and new
  patch locations make the initial room depend on learning and persistence.
- PPO reached room 2 in 64.1% of 128 worlds (95% CI 55.7-72.4); random in
  1.6% (0-3.7; two lucky worlds), Braitenberg in 0.8% (0-2.3), delta in 0%.
- PPO without interoception reached room 2 in 57.8% (49.2-66.4).
- The 302/1e3/1e4/1e5 PPO curve is flat; this control does not demonstrate a
  brain-size effect.
- Gdy baseline bez uczenia (losowy, odruch) wypada podejrzanie dobrze, najpierw szukaj przecieku lub błędu świata
  (np. obserwacja niezgodna ze stanem świata), dopiero potem stroj progi.
- Świat ma mieć testy spójności: to, co widzi oko, musi zgadzać się ze stanem świata (np. niewidoczne zasoby
  wyczerpane), maski akcji zgodne z obserwacją.
- `organism-v3`: maskuj nieaktywne sloty także w oku; inaczej odruch dostaje losowe cele mimo poprawnej maski ugryzienia.
- Atrapy muszą wyczerpywać się po ugryzieniu; stała atrapa tworzy sztuczną pułapkę energii.
- organism-v3 control (8x128 światów, 6000 kroków) osiągnęła pokoje 1-6: 1.000/0.768/0.696/0.618/0.291/0.034.
- organism-v3 losuje nowy, różny od poprzedniego kolor celu przy każdym odwróceniu; pierwszy pokój wymaga dwóch
  różnych opanowanych kolorów, a następne pokoje po jednej nowej zmianie, więc pojedynczy kanał odruchu nie wystarcza.
- Losowość kontrolera kalibracyjnego ma osobny generator; nie zmienia rozmieszczenia zasobów ani zdarzeń świata.
- Rutyna jest obserwacją: entropia akcji i pozycji jest liczona w kolejnych oknach czasu dla każdego pokoju i nie
  uczestniczy w energii, awansie ani wyniku.
- W pomiarze `growth_metabolic_graph` przycinanie zmniejszyło aktywne węzły po 1500 krokach (229 do 106),
  ale świat pozostał w pokoju 0; ten horyzont nie dowodzi poprawy uczenia ani eksploracji. Węzły i krawędzie
  muszą mieć niezależne definicje, zanim ich liczniki będą odrębnym wynikiem.
- W organism-v4 symetryczny losowy napęd (cofanie i jazda naprzód) utrzymywał organizm przy początkowym skupisku
  pokarmu i dawał około 26% przejścia do pokoju 1; to efekt błądzenia, nie poprawa uczenia. Losowy baseline zachowuje
  dodatni napęd v3, a świat nadal przyjmuje ujemny napęd kandydatów.
- Pełny organism-v3 (`growth_metabolic_graph`, 8 seedów, 1024 światy) dał score 0.046875 i survival 0.12695,
  ponad random 0.0055, ale daleko od metabolic_gate 2.4. Wynik całego kandydata nie izoluje wpływu wzrostu;
  potrzebna ablacja przycinania w tym samym protokole.
- Identyczny wynik kopii `metabolic_gate` (2.4023 pokoju, 0.9033 survival; 8 seedów) potwierdza powtarzalność
  implementacji w judge, ale bez ablacji nie potwierdza wkładu poszczególnych bramek.
