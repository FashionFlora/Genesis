# Reguły z wyników

- `axiom_signed_ema`: 8-seed organism-v4 score 2.2910, survival 0.9082, 2.291 pokoju;
  stały speed i podpisany ślad nie wystarczyły do utrzymania zasięgu.
- `metabolic_gate_fixed_speed`: score 2.8408, survival 0.8887. Porównanie sugeruje
  kompromis zasięg/przeżycie, ale zmiany śladu i retencji nie są jeszcze odizolowane.
- W tym świecie 8 seedów mierzy różnicę; wzrost struktury nie pojawił się (3 -> 3).
- `axiom_gain_only`: pełny organism-v4 dał score 2.8057, 2.8057 pokoju,
  survival 0.8535 i energię 0.7573; poniżej lidera 2.8408. Gain-only nie
  poprawił zasięgu ani wyniku mimo krótkiego paired-testu z +0.125 survival.
- Horyzont 1200 kroków nie osiągnął mastery (próg czasu pokoju 0: 2048), więc
  nie mógł zmierzyć wejścia do kolejnego pokoju; używaj pełnych 6000 kroków.
- `axiom_causal_sparse_growth`: organism-v4 score/rooms 0.9971, survival 0.9639,
  połączenia wzrosły 0 -> 32.12. Adaptacyjne ślady zwiększyły przeżycie, ale
  ograniczyły zasięg względem lidera 2.8408; sam wzrost struktury nie wystarcza.
- Sparowana ablacja H015 (8 organizmów, 6000 kroków, seed świata 20261024):
  pruning on/off dał pokoje 0.875/0.750, survival 1.0/1.0, energię
  0.909/0.960 i reversal latency 655.75/657.125. Wstępny dodatni sygnał
  zasięgu, okupiony niższą energią; jeden seed świata nie wystarcza do wniosku.
