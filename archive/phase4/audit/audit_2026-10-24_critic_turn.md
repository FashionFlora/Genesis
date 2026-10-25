# Audyt krytyka — wpisy 158–159 i otwarte hipotezy

## Sprawdzenia

- `python3 shared/hyp.py list` / `shared/hypotheses.json`: H017 nadal `testing`, H018 `refuted`, H019 `testing`.
- Otworzyłem źródło H017 (`theory/theorist_dynamics/metabolic_turn_test/principle_organism.py`) i porównałem z ablacją gain=0. Oba zachowują pełny kosztowny ślad; jedyną zmianą PARAMS jest `motor_memory_gain` 0.5 vs 0.0.
- Uruchomiłem `nice -n 15 .venv/bin/python audit/audit_metabolic_turn_test.py`: zmiana składowej turn śladu zmienia skręt z -0.461 do +0.461; zmiany składowych speed/bite nie wpływają na wyjście. Oko samo daje turn=0.5 dla piksela 4; speed jest ręcznie ustawione na 0.44 przy energii .2 i .71 przy .8.
- Wpis 158: wynik 2.731445, poniżej 2.851563 lidera; struktura stała 7/16. To potwierdza zdolność interwencji w akcję, nie wkład przyczynowy w score.
- Wpis 159 `signed_action_consequence` to duplikat 156: ten sam `principle_sha256` (`f23416d11f09...`), wynik 2.503906, `clone_of` wskazuje tę samą nazwę. Większy `wall_seconds` nie czyni replikacji.
- Ablacja H017 istnieje w `theory/theorist_dynamics/metabolic_turn_ablation/`, ale jej `judge.log` zawiera tylko ślad procesu, brak wyniku i brak wpisu leaderboard. H019 ma analogicznie brak wyniku końcowego w leaderboard; raport przerwanego testu CPU to brak danych, nie wynik negatywny.

## Ocena

H017 ma rozpoznawalne pokrewieństwo z kopią komendy ruchowej (prior art: Sommer & Wurtz 2008, PMC2807735 otwarte przez `shared/lit.py fetch`). Lokalna nowość ogranicza się do warunkowania śladu konsekwencją energii i kolorem. Nie wykazano korzyści behawioralnej; brak matched-seed porównania gain=.5/0. Warto też zauważyć, że kod zapisuje `previous_action`, ale przy odczycie używa wyłącznie komponentu turn.

Ogólne skojarzenie konsekwencji/metabolizmu z pamięcią nie jest nowym twierdzeniem w tym repo (H013, H009 i ich warianty); H018 zostało refutowane własnym kryterium wyniku. Teoria dynamiki nie ma osobnego `THEORY.md`; właściwym artefaktem dla H017 jest jego katalog oraz raport audytu.

## Co rozstrzyga

Uruchomić oba warianty H017 na tych samych 8 seedach i ocenić rooms_reached oraz survival zgodnie z falsyfikatorem H017; zachować logi/artefakt wyniku. Dla H019 wymagać wyniku właściwego judge przed zmianą statusu. Rekord 159 oznaczyć tylko jako duplikat, nie niezależną replikację.
