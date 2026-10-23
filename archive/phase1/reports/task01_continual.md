# Zadanie 01 — continual

## Zakres i wykonanie

Zarezerwowane na tablicy: EWC, SI, MAS, LwF, GEM, A-GEM, Progressive Nets, replay, generative replay, PackNet, CLEAR, continual backprop, shrink-and-perturb, loss of plasticity; claims sprawdzane indywidualnie przez `shared/board.py`. Wpisano rekordy do `registry/areas/continual.jsonl` zgodnie ze schematem. Pełny tekst zweryfikowano dla EWC, GEM i Progressive Nets; pozostałe źródła to w większości abstrakty albo oczekują weryfikacji. Pomyłki WebFetch/arXiv (niepowiązane artykuły) są odnotowane przy rekordach, nie uzupełniano ich na podstawie tych błędnych stron.

## Metody ujęte

EWC; Synaptic Intelligence; Memory Aware Synapses; Learning without Forgetting; GEM; A-GEM; Progressive Neural Networks; experience replay; generative replay; PackNet; CLEAR; continual backprop; shrink-and-perturb; loss of plasticity.

## Crafter i podobne środowiska

Nie znaleziono w otwartych źródłach wyników na Crafterze dla powyższych metod; nie wpisano takich wyników. EWC — Atari 2600: full text opisuje Figure 3 jako sumę wyników human-normalized z 10 gier (10 zestawów, 4 seedy); podano jakościowo, że plain SGD pozostaje poniżej 1, a EWC uczy się wielu gier. Nie odczytano punktów z wykresu i nie podano wartości liczbowej. Źródło: arXiv:1612.00796, Figure 3; Table 2 to hiperparametry, nie rezultat. Progressive Nets: abstrakt/full text potwierdzają Atari i 3D Labyrinth oraz przewagę nad baseline'ami, ale brak zweryfikowanej tabeli/liczby w tej sesji.

GEM ma zweryfikowane porównawcze wyniki na zadaniach klasyfikacyjnych, nie Crafterze: Appendix B arXiv:1706.08840 podaje final accuracy Permuted MNIST 0.8260, Rotated MNIST 0.8607 i incremental CIFAR-100 0.6783. To nie wyniki RL ani Crafter.

## Niezweryfikowane / wymagające uzupełnienia

- SI, MAS, LwF, A-GEM: szczegółowe reguły, pełne teksty, tabelaryczne wartości oraz publiczne repozytoria.
- PackNet, CLEAR, generative replay, continual backprop, shrink-and-perturb i loss of plasticity: właściwe źródła pierwotne, pełne teksty, kod i benchmarki. W niektórych wyszukiwaniach WebFetch zwrócił niepowiązane prace; są oznaczone w `notes`, a nie użyte jako dowód.
- Z wyjątkiem GEM nie pozyskano zweryfikowanych URL-i repozytoriów kodu. Brak URL nie oznacza, że repo nie istnieje.
- Brak źródłowych tabel Crafter dla ujętych metod.

## Obserwacje dla GENESIS

1. Większość metod continual learning odpowiada na problem interferencji/retencji, nie dostarcza motywacji do eksploracji. Sama nie zastępuje intrinsic signal przy uczeniu Craftera bez reward.
2. EWC, SI, MAS, LwF, GEM/A-GEM i typowe replay są gradientowe; nie spełniają kryterium no-backprop w standardowej postaci.
3. Warianty RL (np. EWC na Atari, Progressive Nets z A3C, CLEAR) wykorzystują zewnętrzną reward i backprop. W tym projekcie trzeba traktować oddzielnie mechanizm retencji i źródło sygnału zadania.
4. Replay i generative replay mogą ograniczyć zapominanie, lecz ich użyteczność dla reward-free Crafter zależy od tego, jakie cele/etykiety lub sygnał samonadzorowany są replayowane.
5. Architektoniczne zamrażanie/rozbudowa Progressive Nets ogranicza zapominanie bez penalty, ale zwiększa model wraz z liczbą zadań i wymaga identyfikacji zadania; nie stanowi samo w sobie metody bez reward/backprop.

## Tablica współpracy

- Początkowy `read continual`: brak nowych wiadomości.
- `no_backprop` poinformował o Forward-Forward: bez backprop, ale jego MNIST używa poprawnych/błędnych etykiet; nie jest dowodem na Crafter.
- `orchestrator` polecił zgłaszać kandydatów do szybkiego testu `experiment_engine`.
- `experiment_engine` przekazał: POET to ES bez backprop, lecz optymalizuje reward; NCA ma supervised target/BPTT. Nie wskazano czystego plug-and-play rozwiązania spełniającego jednocześnie oba kryteria.
- Wysłano do `experiment_engine`: brak zweryfikowanego prostego kandydata continual do reward-free Crafter bez backprop; wymieniono Progressive Nets jako wymagające dalszej weryfikacji.
- `novelty_auditor` przypomniał, by nie utożsamiać no-backprop z brakiem etykiet/nagrody; odnotowano tę zasadę w analizie.
- Przed końcem wykonano ostatni `read continual`.

## Aktualizacja: samobudowanie i neuroobszary

Po aktualizacji SCHEMA dodano `self_building` i `brain_relevance` do wszystkich 14 rekordów. Progressive Nets, PackNet i continual backprop oznaczone jako częściowo strukturalne (rozbudowa kolumn / pruning / wymiana jednostek), ale tylko Progressive Nets i PackNet mają zweryfikowany abstrakt/tekst w tej sesji; continual backprop jest jawnym wpisem wymagającym źródłowej weryfikacji. Informację o SI i MAS jako biologicznie inspirowanych mechanizmach synaptycznej konsolidacji przekazano `neuro_learning`; ostrożnie, bez twierdzeń o lokalności pełnej metody. Powiązanie wymiany jednostek z neurogenezą przekazano `neuro_development` jako hipotezę do sprawdzenia. Końcowy `read` przyniósł też potwierdzenie, że Crafter Plan2Explore/RND wynikiem są reward-free, lecz nic to nie mówi o braku backprop; przypisano źródło arXiv:2109.06780v2 Table 1.

## Uzupełnienie po przeglądzie orkiestratora

Dodano 15. metodę: **Progress & Compress** (arXiv:1805.06370). Otworzono abstrakt oraz pełny tekst HTML. Metoda naprzemiennie uczy aktywną kolumnę nowego zadania (progression), a następnie destyluje jej wiedzę do bazy (compression) chronionej online EWC. Pełny tekst podaje gradientowe SGD/RMSProp actor-critic i zewnętrzne nagrody w Atari/nawigacji, więc kryteriów GENESIS nie spełnia. Wyniki z tabel: Atari positive forward transfer, Table 1 (P&C z reinitializacją 127, 129, 125, 129, 128 dla 1–5 poprzednich zadań; bez reinitializacji 131, 127, 114, 106, 101); Omniglot test accuracy po pięciu przebiegach 82.84% ± 1.4, Table 2. Nie są to Crafter wyniki. Repozytorium kodu niezweryfikowane.

Tablica: na początku ponownie odczytano (brak nowych wiadomości), sprawdzono claims (Progress & Compress wolne) i zajęto `progress_compress`. Przed dopisaniem rekordu wykonano kolejny `read` (brak nowych wiadomości). Katalog zawiera teraz 15 poprawnych rekordów JSONL; wszystkie mają pola `self_building` i `brain_relevance`.

Dodatkowa wiadomość przy końcowym odczycie: dołączyli `theorist_axioms` i `theorist_life`; ich kandydaci mają priorytet testów równy metodom literaturowym. Nie zawierała pytania ani nowego kandydata z obszaru continual. `intrinsic_motivation` potwierdził zaktualizowanie pól self-building/brain-relevance w swoich rekordach i zaznaczył, że modulowanie wzrostu architektury sygnałem intrinsic byłoby nową kombinacją, a nie właściwością tych metod.
