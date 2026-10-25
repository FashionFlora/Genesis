KIERUNEK: działanie sprzężone z późniejszą zmianą sensoryczną. Badać, czy
organizm może wydobyć lokalny wpływ własnego ruchu z reafferencji, bez nagrody.

KRYTERIUM PORZUCENIA: pełny, sparowany organism-v7, 1024 światy x 50 000
kroków; delta `rooms_reached` (rodzic minus ablacją) >= 0.05 i CI95 delty
powyżej zera. Agregaty z leaderboardu nie wystarczają do CI sparowanej delty.

W TYM PRZEBIEGU:
- Nowy kandydat `candidates/agency_bearing_jacobian/` po
  `agency_reafferent_turn`: EMA zawiniętej zmiany namiaru oka, przypisanej do
  znaku poprzedniego skrętu; różnica śladów kompensuje późniejsze skręty.
- Ablacja `agency_bearing_jacobian_ablation/` zachowuje aktualizacje i stan,
  zeruje tylko `reafferent_gain`. `PARENTS.txt` w obu katalogach.
- `shared/ideas.py check`: NOWY, maks. podobieństwo 0.12 (próg 0.3).
- Preflight organism-v7 obu wariantów oraz `py_compile`: passed.
- Pełny sędzia rodzica: 1024 x 50 000, score=0, rooms=0.0 (CI95 [0,0]),
  survival=0.841796875; x0.7 rooms=0.005859375, x1.4=0.0; wall 4096.07 s.
- Pełna ablacją: score=0.0009765625, rooms=0.0009765625 (CI95
  [-0.0009375, 0.002890625]), survival=0.8515625; x0.7 rooms=0.005859375,
  x1.4=0.0; wall 2925.11 s. Rekordy w `sandbox/leaderboard.jsonl`.
- Punktowa delta rodzic-ablation = -0.0009765625. CI obu agregatów obejmują
  zero; sędzia nie zapisał surowych sparowanych próbek, więc CI delty brak.

WNIOSEK: bearing-Jacobian nie poprawił eksploracji w pełnym świecie; w nominale
ablacja wypadła minimalnie lepiej, a perturbacja x0.7 była identyczna. Nie
uznawać H020 za obaloną: brak CI sparowanej delty i nadal nieprzetestowany pełny
`agency_reafferent_turn`. Następnie uruchomić pełną matched parę reafferent-turn.
