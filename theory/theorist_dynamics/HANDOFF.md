# Dynamics
KIERUNEK: lokalna konkurencja predyktorów relacji; możliwe odzyskiwanie wpływu po zmianie reżimu przez wygaszanie log-wag.
KRYTERIUM PORZUCENIA: po 3 turach bez syntetycznego early-switch Brier < 0.15661 i sędziowskiego score >= 27.5 odłożyć H006.
BUDŻET: 2/3 tury dla H006.

- H006: `candidates/dynamics_predictive_competition/`; sądzone score: 15.0288 (.98, poprzednia tura), 15.3955 (.98), 14.9900 (.90). Ostatnia mean Brier .21486, robustness .7893.
- Symulacja w `theory/theorist_dynamics/competition_test.py`, 5 seedów, opóźnione źródła przełączane co 300; Brier w pierwszych 60 krokach: .24747 bez wygaszania, .20670 przy .90 (najlepszy z testowanych .98/.95/.90/.80/.70).
- Postęp metryki: poprawa w specjalnie skonstruowanym oknie przełączenia, ale brak poprawy w głównej metryce sędziego; wynik syntetyczny nie przenosi się na benchmark.
- H006 pozostaje testing; kryteria (Brier < .15661, judge score >= 27.5) nieosiągnięte. Następna tura: jedna próba łączenia lokalnej konkurencji z retencją powracających kontekstów; po niej zaparkować, jeśli próg nadal nieosiągnięty.
