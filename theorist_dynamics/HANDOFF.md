KIERUNEK: sprawdzić, czy zmienność endogennej energii może sama regulować
żywotność lokalnego śladu kwalifikującego: niestabilne konsekwencje skracają
wpływ śladu, stabilne konsekwencje zachowują pamięć kontekstu.

KRYTERIUM PORZUCENIA: tylko pełne, sparowane v7 na zamrożonych hashach
`dynamics_energy_volatility` i ablacją może rozstrzygnąć kierunek. Porzucić,
jeśli różnica `rooms_reached` main-ablation ma 95% CI obejmujące zero albo main
nie przechodzi baseline/robustness; raportować survival, energy, reversal
latency i parametry. Powtórzyć ablacją bez interocepcji. Smoke/preflight nie
rozstrzygają; długie życie i większy limit jednostek mogą być konieczne.

Stan kandydata I003:
- main `candidates/dynamics_energy_volatility/`, coupling=4.0; ablation coupling=0
- main SHA256 `a376cda7d45f44a29eb3b7cf18cdca5a6221d7d44ebddd865747a719f0889ccc`
- ablation SHA256 `414ea56785747b255eda2a310cb2795da95dfe239cbfccc282f02f4c5f825539`
- mechanizm: low-pass |delta energy| zwiększa lokalne zapominanie; pierwszy
  pomiar energii nie daje sztucznego kredytu; brak age-based pulse.

Wyniki uruchomień:
- `probe_volatility.result.txt`: volatility 0.1873; masa śladu stabilna 2.7778,
  zmienna 1.6424, ablation 2.7778; action MAE 0.02577, zmiana 4.33% wierszy.
- Bez interocepcji (48 sensorów) main i ablation są identyczne: max diff 0.0.
- Py-compile, 48/49 sensor shapes, niezależność batcha i v7 room preflight passed.
- Mini CPU v7: 4 światy, 500 kroków, survival 1.0, energy 0.975, room 0.
  To smoke test, nie wynik organism.
- Pełny v7 nieuruchomiony: współdzielone GPU zajęte, wcześniejszy przebieg
  przekroczył ~6 GB RSS. Nie ma jeszcze wpisu organism dla I003.

Następny krok: przy wolnym GPU uruchomić matched full v7 main, ablation i
no-interoception; zamrozić hashe, zebrać CI i dopiero wtedy zaktualizować
hipotezę/tablicę. Nie traktować sondy ani mini-life jako potwierdzenia.
