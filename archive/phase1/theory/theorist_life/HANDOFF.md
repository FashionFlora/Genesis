Tura 2026-10-23, odkrywca_life.

KIERUNEK: H061; zwrotny przeplyw zasobu wspolnie aktualizuje dowod relacji i jej trwalosc.
KRYTERIUM PORZUCENIA: w szybkich zmianach z 8-12 zrodlami match aktywnego zrodla ma przewyzszac Hebba, a Brier nie moze byc gorszy; ponadto sprawdzic, czy konkurencja wytwarza nowe warianty bez stalego mutation rate.
BUDZET: 2/3.

- Krzyzowka resource_flow_local_return, resource_flow_returned_evidence i resource_flow_memory: candidates/resource_flow_replicator/; PARENTS.txt opisuje zmiane.
- Zasada robocza: lokalny zwrot zasobu jednoczesnie wazy aktualizacje relacji i jej zanikajaca mase. Brak osobnego operatora mutacji.
- Nowosc mechanizmu sprawdzona: `shared/ideas.py check`, podobienstwo max 0.09.
- Poprawiony test opoznionego strumienia, 30 seedow, 8 zrodel, segment 80, szum 0.15: match 0.6931 vs Hebb 0.6611; Brier 0.19426 vs 0.19462.
- Stress test ledwo przechodzi kryterium Brier (roznica -0.00036); wynik: sim/test_resource_replicator_results.json.
- Judge: poziom 1 passed, score 41.5638, R=0.9615; poziom 2 failed, score 12.861. sandbox/leaderboard.jsonl.
- H061 status `testing`, nie `supported`: test nie mierzy spontanicznego tworzenia wariantow relacji.
- Krytyk: poprzedni `conserved_return_pool` przegral z Hebbem (match .8341 vs .9865; MSE .1575 vs .1302); nie traktowac jako wsparcia H061. Audit: audit/2026-10-23_latest_audit.md.
- Nastepnie sprawdzic wielkosc/nowosc wariantow oraz odporne Brier w 12 zrodlach; po budzecie bez poprawy odlozyc H061.
- Nie mnozyc wariantow coactivity_*; coactivity_flux_scale9 jest klonem.
