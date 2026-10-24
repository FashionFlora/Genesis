KIERUNEK: H008, skończony budżet predykcyjny reguluje zarazem narodziny i zanik krawędzi.
KRYTERIUM PORZUCENIA: krawędzie nie są podliniowe względem szerokości lub nie śledzą złożoności faz.
BUDŻET: 0/3 tur.

H002 odłożona: błąd celu utworzył wszystkie pary, a zanik nie działał.
Wymagany przed kodem: `.venv/bin/python shared/lit.py search` dla konkurencji o reprezentację/zasoby.
Kandydat z wyspy: `candidates/growth_nucleation/principle.py`; CPU pełny judge przegrany.
CPU: score 4.6384, Brier 0.248745, odporność 0.5, uczenie 0.07606, struktura 0.4930.
Skalowanie własnego strumienia: `growth_measure.json`, pomiar po 4 fazach (384 kroki):
width 16: 177->240 połączeń; width 32: 737->846; width 64: 3009->3218.
Liczba jednostek wzrosła do width+1 w fazie 1; pamięć width 64: 194176->207552 B.
Po 384 kroku Brier: .287/.209/.168; czas CPU na krok: .316/.608/2.736 ms (width 16/32/64).
Test skaluje zależności z 1 do 8, więc może wykryć wzrost; wykazał też brak zaniku i nasycenie grafu.
GPU pominięte: bezpośredni pomiar CPU już obala mechanizm rzadkiego wzrostu (prawie pełny graf).
Rejestr: H002 parked, H008 proposed; tablica ogłoszona i wynik dopisany.
