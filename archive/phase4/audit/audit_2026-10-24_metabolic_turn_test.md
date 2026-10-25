# Krytyk: `metabolic_turn_test`, wpis 158 (2026-10-24)

## Wynik i kontekst

- Rekord organism-v4: score/rooms **2.7314453**, 1024 światów, 6000 kroków;
  CI95 rooms [2.6290, 2.8339], survival 0.8955078 [0.8768, 0.9143].
- W obu rozmiarach (302 i 10 000) wynik jest identyczny. Raportowana struktura
  pozostaje stała: 7 units / 16 connections od kroku 0 do 6000. To nie jest
  dowód wzrostu ani adaptacji liczby jednostek.
- Score jest poniżej `axiom_causal_homeostasis` 2.8515625 o 0.1201. Przedziały
  ufności zachodzą na siebie; brak podstaw do tezy o przewadze albo porażce
  statystycznej na tym porównaniu.

## Mechanizm i sonda

Uruchomiono `nice -n 15 .venv/bin/python audit/audit_metabolic_turn_test.py`.
Ślad `turn` -2 i +2 zmienił wyjściowy skręt z -0.461 na +0.461 przy tym samym
oku; zmiana zapisanych komponentów speed/bite przy stałym turn nie zmieniła
wyjścia. Kod odczytuje `action_trace[..., 0]`, a pozostałe dwa wymiary wektora
akcji ignoruje. Skręt bazowy jest ręcznie obliczany z centroidu kierunkowego oka,
gryzienie progiem 0.08, a szybkość bezpośrednio jako 0.35 + 0.45 * energy;
sonda potwierdziła szybkość 0.44 przy energii .2 oraz .71 przy .8.

Sonda dowodzi wpływu lokalnej pamięci na skręt, nie użyteczności tej pamięci w
organism ani przyczynowego wzrostu wyniku. H017 wymaga 8-seed porównania z
`motor_memory_gain=0`; wpis 158 zawiera tylko wariant gain=.5. W repo istnieje
`theory/theorist_dynamics/metabolic_turn_ablation/`, ale nie znalazłem jego
wyniku w leaderboardzie. Do rozstrzygnięcia potrzebny sparowany test z tymi
samymi seedami i raportem reach/survival; obecne `action_trace` to osobny
bufor dla 3 kolorów, nie ogólna kopia całego wektora sterowania.

## Prior art

Otwarty tekst Sommer & Wurtz (2008), *Visual Perception and Corollary Discharge*,
PMC2807735, opisuje kopię komendy sakadycznej używaną do planowania kolejnych
ruchów i interpretacji reafferencji. To wcześniejsza rodzina mechanizmu
kopii komendy, nie dowód nowości ani równoważności z cyfrowym śladem energii.
W zespole H013 już dotyczy energetycznej konsekwencji wyboru akcji; H017 jest
wąskim wariantem, który wiąże następny skręt z przypomnianym kolorem.

## Wniosek

H017 pozostaje nierozstrzygnięta do czasu wskazanej ablacji. Wartościowy claim
ogranicza się do tego, że zaimplementowany ślad może zmienić następną składową
turn. Brak dowodu, że wynik pochodzi z tej reguły, a nie z geometrii oka,
energetycznej eksploracji i ręcznej funkcji szybkości.
