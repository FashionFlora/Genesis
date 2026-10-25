KIERUNEK: lokalna dynamika skrętu sprzężona z obrazem i śladem energetycznym; kolejny wariant musi celować w progres między pokojami.
KRYTERIUM PORZUCENIA: nie kontynuować, jeśli pełny 8-seed test nie poprawi rooms_reached o >=0.05 względem rodzica bez spadku survival.
BUDŻET: 1/3 tur; test tłumienia skrętu obniżył rooms, więc H012 refuted; pozostałe tury tylko dla nowej, mechanistycznie różnej dynamiki.
Nowy kandydat: candidates/damped_steering_homeostat/; PARENTS.txt opisuje zmianę, ideas.py check podobieństwo 0.02.
Pełny sędzia, 8 seedów, 1024 światy x 6000 kroków. Kandydat: 2.75879 rooms (CI95 2.66022-2.85736), survival 0.87598, reversal_latency 119.496, place_memory 9.06738, mean_energy 0.76915.
Ablacja rodzica axiom_causal_homeostasis na tym samym protokole: 2.85156 rooms (CI95 2.75174-2.95139), survival 0.85840, reversal_latency 118.154, place_memory 9.27441, mean_energy 0.75697.
Wniosek: tłumienie zyskało survival, lecz rooms spadło o 0.09277; brak poprawy głównej metryki. Rezultaty w sandbox/leaderboard.jsonl, hipoteza H012 refuted.
Nowa tura: szukać lokalnego sprzężenia, które zwiększa selektywną eksplorację bez tłumienia skrętów; testować na pełnym horyzoncie.
