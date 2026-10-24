KIERUNEK: lokalny tag konsekwencji: zmiana energii zapisuje wektor poprzedniego działania przy kolorze bodźca.
KRYTERIUM PORZUCENIA: pełny sędzia nie poprawia rooms_reached ponad 2.84082 lidera ani survival ponad 0.85; brak poprawy po 3 turach oznacza odłożenie.
BUDŻET: 1/3 tur; action-tag kierunek odłożony po pełnym teście (survival poniżej progu), poprzedni signed-trace też odłożony.
Poprzedni pełny wynik: candidates/metabolic_relaxation rooms_reached 0.61914, survival 0.86523, reversal_latency 793.38; energy_association 0.01758 / 5321.73.
Naprawa kontraktu: kod rozpoznaje wejście bez interocepcji (`n_sensors=48`) zamiast czytać niebieski kanał jako energię; prędkość jest jawnie zależna od energii.
Ablacja lokalna, 128 światów, 6000 kroków, seed 7: metabolic_relaxation z energią 0.9062 pokoi, survival 0.9219, latency 523.5; bez energii (stały stan) 2.2891, 0.8984, 37.8.
Kontrole tego samego batcha: metabolic_gate 2.6719 / 0.9219 / 172.0; ungated_trace 2.0391 / 0.9609 / 50.3; fixed_speed 2.6641 / 0.8906 / 189.5.
Wniosek: signed trace nie przewiduje wyniku; lepszy wynik pochodzi z bramkowania eksploracji/prędkości, a kanał energii może pogarszać adaptację. Nie twierdzę o pamięci trace.
Następne: status H001 zmienić na critiqued/refuted i przejść do nowej dynamiki; nie uruchamiać pełnego sędziego dla tego kierunku.
Nowy kandydat: candidates/metabolic_action_tag (rodzice metabolic_relaxation + action_consequence).
Wynik sędziego 8 seedów: score/rooms 1.14453125, survival 0.556640625, reversal_latency 703.5078125.
Wniosek: tag działania zwiększa wynik względem 0.61914, ale nie jest odporny; pamięć wektora nie pobiła metabolic_gate_fixed_speed 2.84082.
Następne: rozpocząć nową lokalną dynamikę bez signed trace; nie rozwijać H008.
