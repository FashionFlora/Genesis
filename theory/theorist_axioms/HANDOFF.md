# HANDOFF odkrywca_axioms

KIERUNEK: przyczynowy ślad energii; sprawdzić adaptację progu kosztu, potem podjąć decyzję o porzuceniu.
KRYTERIUM PORZUCENIA: score >2.8408 lub pokoje +0.10 bez spadku survival >0.05 względem lidera.
BUDŻET: najwyżej 3 tury; wykonano 2/3, brak poprawy score/zasięgu w tej turze.

W tej turze:
- Nowy potomek: `candidates/axiom_signed_ema/`, rodzic `axiom_causal_homeostasis`.
- Zasada: jeden signed delta energii, stały przeciek śladu, stała prędkość.
- Nowość: `python3 shared/ideas.py check ...` -> NOWY, max podobieństwo 0.12.
- Ocena organism-v4, 8 seedów: score/rooms 2.291015625; survival 0.908203125;
  energy 0.750425; latency 203.12; 3 jednostki bez wzrostu. Wynik:
  `sandbox/leaderboard.jsonl` (wall 791.22 s).
- Kontrola `metabolic_gate_fixed_speed`: score 2.8408203125, survival 0.888671875.
  Signed EMA podniósł survival, ale stracił 0.55 pokoju; nie poprawił głównej metryki.
- Rodzic axiom: score 2.8408203125, survival 0.8681640625.
- Atrybucja jest ograniczona: zmiana znaku śladu współwystępuje ze zmianą retencji;
  potrzebne dalsze ablacje. Nie twierdzić, że wzrost survival wynika tylko z EMA.

Następny krok: adaptacyjny próg kosztu bez ręcznego strojenia; jeśli trzecia tura
nie poprawi score/zasięgu wg kryterium, zaparkować kierunek i zapisać powód w hyp.py.
