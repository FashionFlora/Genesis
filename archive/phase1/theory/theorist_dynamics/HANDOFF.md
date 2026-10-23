# Dynamics handoff
KIERUNEK: fazowa synchronizacja przez lokalny przeplyw znaku; jeden stan ma dawac pamiec, selekcje krawedzi i eksploracje.
KRYTERIUM PORZUCENIA: judge L1/L2 musi przekroczyc 26.2567, a Snake learning > 0.05; toy lock-in nie wystarcza bez transferu.
BUDZET: 0/3 dla nowego kierunku.

- Zamkniety H050 (3/3, parked): lokalny rezonans krawedzi nie dawal skutecznego dzialania.
- Nowy kandydat: `candidates/returned_flow_edge_action/`, rodzice `resource_flow_memory` + `resonant_edge_dynamics`.
- Ideas check: max podobienstwo 0.11, prog 0.30 (nowa mutacja zaakceptowana).
- Judge full before action-tie correction: L1 50.5634 pass, L2 26.2567 pass, L3 Snake 5.0209 fail.
- Corrected Snake calibration: 16.5259, survival 25, apples 0, behavior diversity 0.5626, learning 0; correction removes constant action but does not learn food pursuit.
- Elegance 0.899; robustness L1/L2 0.9935/0.963; wynik L2 przewyzsza resonant_edge_dynamics 18.8246.
- Krytyczny wniosek: zwrot masy celu bez reprezentacji fazy nie daje eksploracji; nie stroic decay/timescale.
- Nastepna tura: toy lokalnych oscylatorow znakowych i test, czy synchronizacja sama poprawia predykcje po zmianie reżimu.
