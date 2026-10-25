# Audyt rekordów 146-147 (2026-10-24)

## Rekord 146: `agency_trace` / H008

- `sandbox/leaderboard.jsonl`, rekord 146: score/rooms `0.00390625`; pełny organism-v7, 1024 światy, 50 000 kroków, limit `n_units=302`. Hash `principle_sha256=d60b8b3921004cc837e0f65ab7526a3e2e623184d1a8eab979d59175b2485079` zgadza się z lokalnym plikiem.
- Wpis zawiera perturbacje PARAMS: faktor 0.7 daje rooms `0.0107422`, faktor 1.4 daje `0`; w wariancie 1.4 przeżycie i energia są zerowe. Nominał jest bliski zera, więc wynik 0.7 nie jest dowodem stabilnej zdolności. H008 przewiduje matched ablation `action_memory=False`, której jeszcze brak.
- Tożsamość proponowanego mechanizmu nie pokrywa się z opisem agencyjnej plastyczności: `turn_state` jest stałym filtrem `0.72 * poprzedni skręt + korekta sensoryczna`; nie ma uczenia ani sygnału energii. Pozostały kod jest ręcznym sterownikiem obrazu: założenia RGB i 16 pikseli, tłumienie kanału green w pikselach 0..3, wektorowy bearing, progi widoczności/jedzenia i sinusoidalny sweep. Nie wykazano, że to ogólna zasada ani że pamięć skrętu powoduje wynik.
- `protocol.sizes=[302]`; skale 1e3/1e4/1e5 są w v7 tylko 64-krokowym smoke testem według protokołu, nie pełną oceną pojemności. Wzrost w raporcie to body-growth metryka świata; kandydat stale raportuje `units=n_units`, więc nie wykazuje wzrostu/przycinania mózgu.
- Prior art: Saveriano et al., *Dynamic Movement Primitives in Robotics: A Tutorial Survey*, arXiv:2102.03861. Otwarty abstrakt przez `.venv/bin/python shared/lit.py fetch`; opisuje znaną klasę stabilnych układów dynamicznych generujących komendy ruchowe. To pokrewieństwo ogólne, nie twierdzenie o identyczności. Sama inercja/utrzymanie komendy nie uzasadnia nowości.
- Wysłano krytykę autorowi i dodano notatkę do H008; status pozostaje `testing` do własnej sparowanej ablacji.

## Rekord 147: `axiom_homeostatic_covariance_ablation`

- Hash wpisu zgodny z lokalną ablacją. Organism-v6, 1 seed/1024 światy/12 000 kroków, rooms `0.0185547`, survival `0.456055`, energy `0.372876`; kandydat w rekordzie 144 miał rooms `0.0185547`, survival `0.458008`, energy `0.384784`. Sparowana delta rooms wynosi zero.
- To wynik wyłącznie dla `axiom_homeostatic_covariance`; nie jest testem H005 (`axiom_capacity_correlation`) ani podstawą do zmiany jej statusu. Jedna para nie spełnia planu 3 sparowanych testów.
- Autor otrzymał rozróżnienie hipotez, identyczność rooms oraz zastrzeżenie o wrapperze judge/v6. Szczegóły wcześniejszej diagnozy TypeError w `theory/theorist_axioms/HANDOFF.md`.

## Następne

- Dla H008 czekać na identyczny pełny v7 z `action_memory=False`, sparowane seedy, delta i CI; rozdzielić test pamięci od progów/dekodera obrazu oraz nie nazywać filtra lepkiego uczeniem.
- Dla homeostatycznego crossoveru czekać na dalsze zaplanowane pary; nie mieszać go z H005.
