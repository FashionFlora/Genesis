# Wynik wstępny

Na razie wiernie przeniesiono i zmierzono jedną odrębną regułę: `inertial_channel_dynamics`. GPU zgadza się z implementacją CPU (maksymalny błąd `0.0`). Przy 10 tys. kroków jakość to `0.9528`, `0.9994`, `0.9298` dla `1e3`, `1e4`, `1e5`; nachylenie po rozmiarze wynosi `-0.003459`, a stan rośnie liniowo. Mechanizm nie wykazuje poprawy jakości wraz ze skalą.

Baseline `_baseline_gpu_online`, uruchomiony w tych samych ustawieniach, osiągnął `0.9422`, `0.0000`, `0.0000` i nachylenie `-0.141808`. To mocny spadek baseline'u, ale nie dowód, że mechanizm bezwładny zyskuje przy największej skali.

**Wniosek jest niepełny.** Pozostałych rodzin z `families.tsv` jeszcze nie pogrupowano ani nie zmierzono; nie można stwierdzić, że mała skala niczego niesłusznie nie zabiła. `HANDOFF.md` opisuje stan dalszej pracy. Wszystkie liczby pochodzą z faktycznych przebiegów sędziego w tym katalogu.
