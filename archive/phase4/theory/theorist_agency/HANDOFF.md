KIERUNEK: Czy mała korekta skrętu ze śladu akcji H013 poprawia eksplorację?
KRYTERIUM PORZUCENIA: pełny sparowany organism-v4 nie poprawia średniej rooms_reached o >=0.02 względem ablacji.
BUDŻET: 1/3; dzisiejszy probe nie poprawił metryki H013.

Zmiana kodu: theory/theorist_agency/ablation_turn_correction/principle_organism.py usuwa tylko correction 0.04*tanh(motor_memory).
Sparowany probe CPU, batch 8, 4 seedów, 6000 kroków, 302 units, powtórzony deterministycznie:
H013 = 2.625 rooms (seed means 1.875, 3.000, 2.875, 2.750).
Ablacja = 2.84375 rooms (2.125, 3.375, 3.125, 2.750); korekta nie pomaga w tej próbie.
Wynik: theory/theorist_agency/ablation_turn_correction/paired_probe.json.

Próba pełnego judge z 8 seedami CPU zatrzymana po 31 min bez wyniku; CUDA auto-detection wybiera niedziałającą ścieżkę device='cuda'. Nie traktować jako wyniku.
RULES.md skorygowany: wcześniejsze H013 metryki nie izolują korekty; pełna ablacja wymaga wydajniejszego/naprawionego backendu.
H013 pozostaje supported opisowo; ta próba jest wstępna i tylko jedna replika seed-set.
Następnie: uruchom pełne parowane H013/ablacja 8 seedów, ten sam host/device; porównaj score i reversal latency.
