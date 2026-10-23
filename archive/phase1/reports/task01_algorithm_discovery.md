# Task 01 — algorithm_discovery

## Zakres i wynik
Do katalogu `/opt/dlami/nvme/genesis/registry/areas/algorithm_discovery.jsonl` dodano dwa rekordy źródłowo zweryfikowane: AutoML-Zero i VeLO. Oba są w obszarze odkrywania/uczenia reguł optymalizacji. Nie utworzono wpisów pamięciowych dla pozostałych kandydatów, gdyż wyszukiwanie/otwieranie źródeł nie dało wiarygodnych, pełnych danych do zgodnego ze schematem rekordu.

## Metody i dowody
- **AutoML-Zero** — arXiv:2003.03384, abstrakt i HTML full text otwarte; sekcje 3.1–3.2, 4.1–4.2, Fig. 1–5 i materiały uzupełniające. Ewoluuje programy Setup/Predict/Learn z prostych operacji, selekcjonując po wynikach zadaniowych. Artykuł opisuje ponowne odkrycie sieci uczonej backpropem, więc algorytm poszukiwania jest gradient-free, lecz nie wszystkie znalezione programy spełniają no-backprop. Kod wskazany i sprawdzony jako oficjalny Google Research: https://github.com/google-research/google-research/tree/master/automl_zero. Crafter: żadnego wyniku/tabeli nie znaleziono.
- **VeLO** — arXiv:2211.09760, abstrakt i HTML full text otwarte (Sections 2–3, 4.4.4); artykuł wskazuje https://github.com/google/learned_optimization. Uczy optimizer przez meta-optymalizację ES nad końcowym training loss, ale jego inner loop używa gradientów z zadania. Stąd outer loop nie backpropaguje przez optymalizację, lecz całość nie jest metodą no-backprop. Crafter: brak odnalezionego wyniku/tabeli. Nie podano szczegółowych wyników RL, bo przy paginacji tekstu ich tabela/źródło nie zostały wiarygodnie potwierdzone.

## Crafter
Brak wyników Crafter do wpisu z tych dwóch artykułów. Nie twierdzę, że są wyniki ani nie podaję żadnych liczb bez tabeli źródłowej.

## Niezweryfikowane / brak
Próbowano szukać LPG/learned policy gradient, DiscoRL/discovered RL rules, OPEN, FunSearch, AlphaEvolve, learned plasticity rules и других кандидатов. По ряду запросов WebSearch/WebFetch вернул нерелевантные страницы или неверные соответствия; поэтому ни ссылку, ни год, ни код этих работ в реестр не добавлял. В частности, произвольное совпадение по FunSearch привело к страницам не о FunSearch — они не использованы как доказательство. Требуется отдельный повторный поиск для расширения каталога и обнаружения точных источников. Никакого вывода об отсутствии этих работ не делается.

## Наблюдения для GENESIS
1. Эволюционный outer loop может исключать backpropagation при поиске, но это не означает, что найденная обучающая процедура не использует backprop: AutoML-Zero явно восстанавливает такой алгоритм.
2. VeLO демонстрирует другую границу: ES во внешнем meta-loop не устраняет потребность inner learner в градиентах задачи; критерий no-backprop следует применять к полной цепочке.
3. Оптимизация validation/training loss — внешний целевой сигнал отбора, но не награда среды. В полях о награде это важно отличать от RL reward.
4. Ни один из двух проверенных источников не подтвердил Crafter eval, так что их нельзя считать эмпирическим доказательством работы в целевой среде.

## Источники
- https://arxiv.org/abs/2003.03384 и https://arxiv.org/html/2003.03384
- https://github.com/google-research/google-research/tree/master/automl_zero
- https://arxiv.org/abs/2211.09760 и https://arxiv.org/html/2211.09760
- https://github.com/google/learned_optimization
