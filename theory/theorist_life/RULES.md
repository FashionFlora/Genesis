# Reguły wyspy życia

- Ślad energii musi być porównany z tym samym kontrolerem przy `memory_gain=0`.
- W organism-v6 poprawiony kontroler metaboliczny osiągnął `rooms_reached=0.15625`,
  survival `0.85059`; ablacja `0.07227`, survival `0.90039` (sędzia, 1024 światów).
- Zysk `+0.08398` w pokojach wiąże się ze spadkiem przeżycia; nie utożsamiać go
  z samym wzrostem energii ani z pamięcią miejsca.
- Broadcast między wierszami został wykryty przez test kontraktu i usunięty przed
  finalnym pomiarem; tylko wynik po tej korekcie jest ważny.
- Kontekstowana kwalifikacja metaboliczna (`candidates/life_metabolic_context`) dała
  w pełnym v6 `rooms_reached=0.76172` (CI `0.70742..0.81601`), a matched ablation
  z `learning_rate=0` `0.06348` (CI `0.04647..0.08048`), przy spadku survival z
  `0.89648` do `0.73926`; różnica CI jest rozdzielna, ale odporność parametrów była
  słaba (`0.06445`, `0.06152`).
- Mutacja estymaty ilorazowej (`candidates/life_metabolic_ratio`) w pełnym v7
  osiągnęła `rooms_reached=0.07324` (CI `0.05553..0.09095`); nie przypisywać jej
  skutku bez matched ablation. Factor 1.4 (`0.27148`) pokazuje zależność od skali,
  nie dowód korzyści mechanizmu.
- Pełny sparowany v7 (1024 wspólne światy) wykazał fixed-minus-adaptive
  `rooms_reached=+0.09570` (CI `+0.05269..+0.13872`) przy `survival=-0.04102`
  (CI `-0.06931..-0.01272`). W tej konfiguracji online adaptive normalization
  nie daje przewagi; dodatkowe pokoje trzeba raportować wraz z kosztem życia.
  Szczegóły: `metabolic_scale_paired_assay.md`.
