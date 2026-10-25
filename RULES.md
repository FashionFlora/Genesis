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
- `_family_example` GA (16 genomów, 4 światy/genom, 5 pokoleń) osiągnęła najlepsze 2.75 pokoju vs 1.75
  w losowej populacji; CI po 4 światach nachodzą, więc to kontrola działania narzędzia, nie dowód przewagi.
- Identyczny wynik kopii `metabolic_gate` (2.4023 pokoju, 0.9033 survival; 8 seedów) potwierdza powtarzalność
  implementacji w judge, ale bez ablacji nie potwierdza wkładu poszczególnych bramek.
- `organism-v6`: kontekst musi być widoczny w oku od pokoju 1, a jadalność nie może używać stałej wartości koloru;
  testy 21/21 potwierdzają zgodność obserwacji, koniunkcji kolor×kontekst, pamięci growing i niezależności batcha.
- Pełna kalibracja v6 (8x128, 6000) została przerwana po 81 minutach w `world.step` bez wiersza wyniku;
  koszt kontrolera growing z pamięcią miejsc jest za duży dla obecnego obciążenia GPU. Nie zapisano liczb jako wyniku.
- Diagnostyka v6 (jeden batch 1024, 12000 kroków): growing przeżył 93.7% światów, średnia energia końcowa 0.897,
  lecz po odwróceniach miał średnio 36.4 ugryzień i 20.5 poprawnych (selectivity 0.55-0.58); awanse, które zaszły,
  miały 0.80-0.94. Próba progu 0.60 dała growing 47.95%, ale tabelę 11.23% (kryterium było zbyt łatwe), więc
  próg 0.80 pozostaje. Growing po dodatniej nagrodzie blokuje teraz nieprzetestowane kolory w bieżącym kontekście,
  aby uczciwie wykorzystać naukę kolor×kontekst zamiast wybierać patch wyłącznie po odległości.
- Korekta kontrolera: `last_bite_index` wskazywał pierwszy dotknięty patch, niekoniecznie ten z nagrodą; growing używa
  teraz `last_patch` dla dodatniego feedbacku i zapamiętuje nagrodzony kolor w kontekście. Jedna kontrola po tej
  korekcie: pokoje 1-4 = 93.07%, 56.45%, 14.55%, 0.49% (logs/calib_v6/growing_final3.json).
- Wersja z opcjonalnym rozwojem ciała potrzebuje stałego tensorowego obwiedni obserwacji,
  jawnych aktywnych liczników sensorów/mięśni i osobnego rachunku energii za budowę oraz utrzymanie.
- Kontrolę rozwoju ciała należy raportować osobno od kontroli uczenia; sam wzrost nie jest nagrodą ani dowodem
  poprawy zdolności.
- `growth_trace` (organism-v6) osiągnął score 0.00684 vs random 0.0055, lecz struktura zmieniła się tylko
  2.00 -> 2.68 -> 2.67, identycznie dla limitów 302/1000/10000. Nie utożsamiać metryki aktywnych śladów z
  oszczędnością pamięci: bufor nadal kosztuje 44 B/świat i wymaga ablacji stałej struktury.
- Pełny retest growth_trace_island i ablacja stałej struktury dały identyczne rooms_reached=0.00683594 (CI95
  0.001106-0.012566); widoczny wzrost kilku aktywnych RGB śladów sam nie wnosi wykrywalnej poprawy funkcji.
- organism-v7 starts one life with a finite `yolk_energy` reserve that pays only ordinary metabolism; construction and upkeep still reduce usable energy, and depletion is reported separately.
- v7 rooms are developmental tasks of one organism. Advancement checks the active body envelope (`PIXELS_BY_ROOM`, `MOTORS_BY_ROOM`) as well as feeding selectivity, while legacy brains receive a fixed full envelope.
- World families are sampled per row and a fourth held-out family is evaluated separately; social rows share food state and see partners through RGB rendering, with no inter-brain channel.
- H006: jedna pamięć preferencji koloru z lokalnym eligibility trace i opóźnioną zmianą energii dała 0.73145 w pełnym v6, a identyczna ablacja bez uczenia 0.07129. Efekt jest rzeczywisty w tym protokole, ale nie jest jeszcze dowodem skalowania ani odporności na permutację kanałów.
- Dwupokoleniowy v7 smoke (`evolution.jsonl`, 4 genomy, 1 świat/genom, 5000 kroków) dał score 0.0 w obu generacjach; zmiana genomów bez wariancji fitness sprawdza mechanikę, ale nie dowodzi postępu selekcji. Pełne twierdzenie wymaga pełnej długości życia i wielu światów na genom.
- Pełny test grupy dwuosobowej (50 000 kroków, 512 wspólnych światów) miał wynik 2.5371 pokoju vs 2.5459 dla grupy jednoosobowej; obserwacja partnera i współzawodnictwo działają, ale wynik nie wykazuje korzyści społecznego uczenia.
- Pełne dwa pokolenia v7 (4 genomy x 4 światy, 50 000 kroków, wspólny seed 1925141753) zwiększyły średnią fitness 0.000375 -> 0.000500 przez przeżycie; najlepszy wynik pokoi pozostał 0.0, więc to nie jest dowód rozwoju zdolności.
