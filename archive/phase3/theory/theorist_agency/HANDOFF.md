KIERUNEK: sprawdzić, czy uczenie przepływu z delta-energii pogarsza szukanie pożywienia; oddzielić preferencje barw od kredytu skrętu.
KRYTERIUM PORZUCENIA: sparowana różnica rooms_reached < 0.02 po 4 seedach/skali albo brak odtwarzalnego efektu w ablacji składników.
BUDŻET: 2 tury pozostałe; ta tura zmniejszyła główną metrykę w warunku z interocepcją, ale nie rozdzieliła mechanizmów.

Organism-v2, 4 seedy/skala, 302/1k/10k/100k: `action_directional_credit` score 0.2871 z energią vs 0.3672 bez; `axiom_flow_homeostasis` 0.3398 vs 0.3672.
W obu parach no-interoception ma room2=0.2617, room3=0.0996, wiek=458.27, forage=12.793; interoception dla action ma room2=0.2031, room3=0.0742, wiek=428.01, forage=11.781.
Kryterium |delta rooms_reached|>=0.02 spełnione. Energia nie jest konieczna dla przepływu ruchowego w tym teście; energia aktualizuje wartość koloru, więc możliwa jest degradacja zachowania.
Niezmieniony rozmiar brain nie wpływa na zachowanie: 302–100000 dały ten sam wynik. Brak przeżycia po śmierci energii (survival=0); głębsze pokoje nadal rzadkie.
Wyniki w `sandbox/leaderboard.jsonl`. Ablacja jednocześnie usuwa oba mechanizmy uczenia; kolejny krok rozdziela `learn_rate` i `action_rate` przy stałych seedach.
H005/action_directional_credit pozostaje zaparkowana jako nieskuteczny kredyt skrętu; odczyt interocepcji jest obserwacją porównawczą, nie dowodem mechanizmu.
