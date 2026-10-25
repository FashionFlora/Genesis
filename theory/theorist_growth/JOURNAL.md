## 2026-10-24: growth_trace_island

Przeniosłem regułę śladu energii do `candidates/growth_trace_island/`. Pełny domyślny organism-v6 (1024 światy, 12000 kroków, limit 302) dał score `0.00683594`, rooms CI95 `[0.001106, 0.012566]`, survival `0.98047`. Aktywna struktura wzrosła z 2 do maksimum 2.68066 jednostek / 3.36133 połączeń, a skończyła na 2.66699 / 3.33398. Przebieg trwał 1359.22 s.

Odczyt wcześniejszego pełnego wpisu w `sandbox/leaderboard.jsonl` pokazuje ten sam wynik i krzywą przy limitach 302, 1000 i 10000. Limit jest więc tylko pojemnością, a zasada przechowuje trzy ślady RGB, nie rośnie ze złożonością świata. Pełna ablacja `growth_trace_static_structure` ma identyczny wynik zachowania; struktura aktywnych śladów nie poprawiła funkcji w tym protokole. To refutuje wkład aktualnej metryki wzrostu w wynik, ale 1 seed v6 nie zamyka szerszej hipotezy o rzadkim wzroście przy dużej skali lub dłuższym uczeniu.

v6 nie mierzy jakości predykcji ani bajtów pamięci, więc nie przypisuję jej tych wyników. Obecny kod trzyma stały bufor śladów RGB i nie dowodzi oszczędności przez rzadką alokację. Następny kandydat musi jawnie alokować rzadkie asocjacje i udostępniać koszt stanu; test powinien mierzyć predykcję, strukturę, pamięć oraz dynamiczną-vs-statyczną ablacją na 8 seedach i kilku limitach.
## 2026-10-24: growth_local_eligibility

Utworzono mutację `candidates/growth_local_eligibility/` z rodzicem `growth_trace_island`. Bank pomysłów uznał mechanizm pixel-local energy eligibility za nowy (podobieństwo maks. 0.05). Lokalny ślad kwalifikuje sensoryczne piki piksel–kolor poprzedzające ugryzienie, aktualizuje je przez późniejszą zmianę energii i wygasza bez osobnego harmonogramu przycinania. Powinien zmieniać zarówno kierunek ruchu, jak i obserwowaną aktywną strukturę.

Pełny organism-v7 (1 seed, batch 1024, 50000 kroków, skale 302/1000/10000/100000, perturbacje x0.7/x1.4) zapisał się w `sandbox/leaderboard.jsonl`; wall `8375.21 s`. Score/rooms_reached `0.00683594` (CI95 `[0.001106, 0.012566]`), survival `0.771484` (CI95 `[0.745754, 0.797214]`). Wszystkie skale miały identyczny wynik. Struktura start: 2 jednostki/2 połączenia; maksimum średnio: 9.2002/11.8428; koniec kroku 50000: 7.4941/9.5537. Sam większy limit `n_units` nie zwiększył używanej struktury.

Perturbacje: x0.7 score `0.00390625`, survival `0.833008`; x1.4 score `0.02734375`, survival `0.603516`. Nie wykonano behawioralnej ablacji `association_gain=0`, więc nie przypisuję mutacji skutku dla wyniku. Jeden seed nie potwierdza ani nie refutuje zasady.

Sędzia nie mierzy accuracy predykcji. Osobny pomiar `measure_memory.py` -> `memory_measurement.json` wykazał 392 B stanu/organizm + 64 B współdzielone, 401472 B dla batch 1024 przy każdym limicie. Tensor jest gęsto zarezerwowany; aktywne krawędzie nie oznaczają rzadkiej alokacji. Następna iteracja powinna dodać jawny pomiar predykcji, kontrolę bez association_gain i faktyczne przydzielanie pamięci po dowodzie.
## 2026-10-24: sparse allocation probe

Zastąpiłem trwały tensor `batch x pixel x color` dynamicznymi kolumnami w
`candidates/growth_local_eligibility/principle_organism.py`. Kolumna powstaje
dopiero, gdy poprzedni bodziec był ugryzieniem, wartość pikselowa była dodatnia
i nastąpiła niezerowa zmiana energii; wszystkie kolumny wygaszają się tym samym
zanikiem i są usuwane poniżej progu. `pruning_probe.result.json`: po 80 krokach
losowych struktura miała 18 jednostek/32 połączenia/1052 B, po 1000 krokach
zerowego oka 2/2/476 B i 0 kluczy.

`growth_sparse_probe.result.json` to smoke v7 (512 kroków, 1024 światy): dla
limitów 302, 1000 i 100000 krzywe były identyczne; nominalny gain 0.8 osiągnął
2 -> 18 jednostek i średnio 2 -> 4.748 połączeń (koniec 4.376), ablacja gain=0
2 -> 18 i 2 -> 4.532 (koniec 4.124). Wszystkie miały rooms=0, więc nie ma
twierdzenia o poprawie zachowania ani o pełnym judge. Stream probe dał MSE
0.5416/0.2440/0.2413 i pamięć 1024/12480/48000 B dla 4/16/32 kanałów.

`shared/ideas.py check` zwrócił NOWY (max 0.08), ale eligibility ma znaną
literaturę; nowość dotyczy lokalnej alokacji i wspólnego zaniku. Level-1 smoke
dał score 15.6708 (baseline 20.9957), więc kierunek nie jest jeszcze wynikiem.

## 2026-10-25: growth_metabolic_sparse

Utworzono nową mutację `candidates/growth_metabolic_sparse/` jako krzyżówkę
`growth_local_eligibility` x `life_metabolic_context`. `shared/ideas.py check`
zwrócił NOWY, maksymalne podobieństwo 0.09. Zmiana: opóźniona zmiana energii
wzmacnia lokalny ślad przez bieżącą rezerwę energii, a narodziny i zanik
połączenia pozostają jedną regułą aktywności.

Pierwszy pełny v7 odrzucono po około 2 h przez kontrolę kontraktu: wspólna
lista dynamicznych kluczy sprzęgała batch. Naprawiłem to przez per-organism
sloty piksel-kolor i maskę `active`; każdy wiersz ma niezależną topologię.
Kontrola `load_independent_brain` przeszła.

Pełny v7 (1 seed, 50000 kroków, limity 302/1000/10000/100000, perturbacje)
zakończony pomyślnie, rekord w `sandbox/leaderboard.jsonl`, wall 12813.95 s,
hash `50e7379638c8ce12477bed81ad3a1146477196abdc7722c39b1ae8b887f00892`.
Score `0.0068359375`, rooms CI95 `[0.00110624, 0.01256564]`, survival
`0.7685546875`. Wszystkie cztery limity miały identyczny score i krzywą.
Struktura: start 2/2; maksimum 5.760742 jednostek/6.540039 połączeń; koniec
4.613281/5.15625. Perturbacje score: x0.7 `0.0`, x1.4 `0.0244141`.
Wynik identyczny z rodzicem i bez poprawy lidera; nie przypisuję mutacji efektu
behawioralnego.

`metabolic_sparse_probe.result.json`: przy limitach 302..100000 stan startowy
92 B; 80 kroków syntetycznych 530 B; 1000 cichych kroków 92 B, 0 aktywnych
kluczy. To potwierdza lokalny wzrost/zanik, ale nie predykcję ani użyteczność.
Ablacja `association_gain=0` nie została jeszcze uruchomiona na pełnym v7.
