# Zadanie 01 — intrinsic_motivation (tryb A)

## Zakres i wykonanie
Przeczytano `CLAUDE.md` i `registry/SCHEMA.md`; odczytano tablicę przed pracą, roszczenia metod oraz tablicę ponownie w trakcie. Dodano 6 rekordów: ICM, RND, Plan2Explore, NGU, Agent57, Episodic Curiosity. Każdy użyty identyfikator metody został zgłoszony przez `shared/board.py claim intrinsic_motivation <id>`; roszczenia przyjęte. Nie uzupełniono dalszych metod na podstawie niepewnych lub błędnie rozpoznanych wyników wyszukiwania.

## Potwierdzone metody i wyniki
- **ICM** — arXiv:1705.05363; pełny tekst abstraktu HTML. Wykorzystuje błąd forward-dynamics i stratę inverse-dynamics; gradienty aktualizują sieci ICM i politykę A3C. W eksperymentach metoda łączyła ciekawość z nagrodą środowiska. Tabela 1 raportuje ICM+A3C = 100.0% w zadaniu VizDoom; to wynik z nagrodą zewnętrzną, nie Crafter.
- **RND** — arXiv:1810.12894 i pełny tekst Craftera arXiv:2109.06780v2. W Crafter Table 1: **2.0%** geometrycznego średniego wyniku osiągnięć w trybie bez udostępnianej nagrody. Predictor jest trenowany gradientowo; RND nie spełnia kryterium bez backpropu.
- **Plan2Explore** — arXiv:2005.05960 oraz pełny tekst Craftera arXiv:2109.06780v2. W Crafter Table 1: **2.1%** w tym samym ustawieniu reward-free. Pełny tekst metody opisuje planowanie przez disagreement zespołu modeli i gradientową optymalizację polityki przez wyobrażone rollouty.
- **NGU** — arXiv:2002.06038, pełny tekst. Intrinsic episodic kNN novelty, opcjonalne RND i reward łączony z extrinsic. Atari Table 1: Pitfall! 8.4 (NGU N=32). Nie jest metodą bez nagrody zewnętrznej.
- **Agent57** — arXiv:2003.13350, pełny tekst. Składa się z NGU/RND, osobnych wartości intrinsic/extrinsic i bandytowego wyboru ramienia. Atari Table 1: 57 gier powyżej wyniku ludzkiego; reward zewnętrzny obecny. Nie należy przenosić tego wyniku na Crafter.
- **Episodic Curiosity** — arXiv:1810.02274, pełny tekst. Reachability classifier uczy się gradientowo, a PPO trenuje politykę na nagrodzie zadania plus bonusie. DMLab Table 1: PPO+EC w kolumnie No Reward = 475 (jednostki jak w tabeli). To nie jest wynik Craftera.

## Crafter — tabela i interpretacja
Pełny tekst benchmarku [Crafter, arXiv:2109.06780v2](https://arxiv.org/html/2109.06780v2), Table 1, podaje przy wstrzymanej nagrodzie środowiska: Plan2Explore **2.1%**, RND **2.0%**, random **1.6%** geometrycznego średniego wyniku dla 22 osiągnięć. Appendix Table B.1 podaje wskaźniki osiągnięć; nie przepisywano ich bez potrzeby. Są to niskie wyniki i nie dowodzą uczenia bez backpropu. Artykuł nie podaje w dostępnej metodologii szczegółów gradientów dla tych baseline'ów; backprop dla RND/Plan2Explore oznaczono na podstawie otwartych tekstów ich metod.

## Braki i niepewności
- Nie zweryfikowano pełnych tekstów/rekordów dla empowerment, DIAYN (w pełni), APT, E3B, AMIGo, LEXA, BYOL-Explore ani pełnej listy prac cytujących Craftera; dlatego nie dodano ich jako gotowych rekordów.
- Nie uzyskano zweryfikowanych oficjalnych repozytoriów dla RND, NGU, Agent57 ani Crafter-baseline implementations. ICM project page, Plan2Explore project page oraz Episodic Curiosity GitHub zostały otwarte, ale project page nie jest bezpośrednim URL-em repo.
- Nie pobrano PDF-ów do `registry/sources/`; użyto otwartych abstraktów/HTML przez WebFetch. Nie zapisano faktów wyłącznie z pamięci modelu.
- WebSearch wielokrotnie zwracał pusty blok wyników lub trafienia do niepowiązanych artykułów; przy niezgodnych tytułach źródła odrzucono.

## Obserwacje dla celu GENESIS
1. Sama obecność intrinsic reward nie eliminuje nagrody zewnętrznej: NGU/Agent57 używają jej jawnie, a ICM ma warianty z nagrodą zadania.
2. Praktyczne curiosity/world-model metody zwykle uczą reprezentacje i politykę gradientowo. RND oraz Plan2Explore spełniają w Crafterze warunek braku rewardu, ale nie warunek no-backprop.
3. Rozdzielenie sygnału intrinsic i extrinsic (jak osobne wartości w Agent57) może ułatwić analizę źródeł zachowania, ale nie zmienia zależności od rewardu zewnętrznego ani BP.
4. RND/Plan2Explore osiągają zaledwie ok. 2% geometrycznego wyniku osiągnięć w Crafterze; warto traktować je jako porównawcze baseline'y, nie jako rozwiązanie celu.
5. Dla postępu GENESIS potrzebna byłaby lokalna/nie-gradientowa reguła, która konsumuje intrinsic signal (np. novelty/reachability/disagreement), bez włączenia zewnętrznego rewardu.

## Tablica współpracy
- Otrzymano od `no_backprop` ogłoszenie o Forward-Forward; metoda należy do obszaru no_backprop i nie była katalogowana tutaj.
- `orchestrator` poinformował, że działa `experiment_engine` i prosi o przekazanie kandydatów łatwych do testu Crafter bez rewardu.
- Przekazano do `all`: Plan2Explore 2.1%, RND 2.0%, random 1.6%, źródło Crafter Table 1 / Table B.1.
- Przekazano do `experiment_engine`: RND jako kandydat testu reward-free, z informacją, że predictor używa backpropu; repo baseline niezweryfikowane.
- Ostatni odczyt tablicy wykonano przed zakończeniem; nie było dalszych nowych wiadomości.
