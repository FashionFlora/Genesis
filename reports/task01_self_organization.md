# Zadanie 01 — self_organization

## Zakres i wykonane

Zapisano 6 rekordów w `registry/areas/self_organization.jsonl`: Growing Neural Cellular Automata (NCA), POET, PAIRED, Prioritized Level Replay (PLR), IMGEP i MAP-Elites. Metody zajęto na tablicy przed ich katalogowaniem. To nie jest jeszcze pełne pokrycie planowanych ~20 metod — niezrealizowana część listy poniżej.

## Wyniki na Crafterze lub podobnych środowiskach

- **Crafter:** nie zweryfikowano wyników Crafter dla żadnej z wymienionych metod. Nie dopisano wyników Crafter bez tabeli artykułu.
- **PLR / Procgen:** arXiv:2010.03934, pełny tekst HTML, **Tabela 2**: PLR — 128,3% znormalizowanego test return względem uniform baseline na Procgen easy. **Tabela 4**: PLR — 135,0% na Procgen hard. Wariant UCB-DrAC + PLR raportuje odpowiednio 176,4% i 182,9%; nie przypisuję tego wyniku samemu PLR.
- **POET / generowane środowiska przeszkód:** pełny tekst opisuje przewagę nad bezpośrednim ES na trudnych środowiskach i prozę o wynikach kontrolnych 17,9 / 39,6 / 13,6 wobec progu sukcesu 230. W pobranym wyciągu nie uzyskałem numeru tabeli dla tych wartości, dlatego nie umieściłem ich jako benchmarku tabelarycznego w rejestrze.
- **NCA:** demonstracje jakościowe wzrostu, trwałości i regeneracji wzoru, bez ilościowego benchmarku agenta.
- Dla **PAIRED, IMGEP, MAP-Elites** nie zweryfikowano w otwartym widoku pełnego tekstu wyników tabelarycznych, więc rekordy nie zawierają liczb.

## Czego nie zweryfikowano / ograniczenia źródeł

- Nie osiągnąłem celu ~20 rekordów. W szczególności nie zostały zweryfikowane pełnym tekstem/kodem: OMNI, OMNI-EPIC, PAIRED (pełny tekst i implementacja), Self-Organizing Maps/Kohonen, metody rosnących sieci poza NCA, MAGELLAN oraz pozostałe warianty IMGEP/QD.
- WebSearch w tym środowisku zwracał wyniki puste lub niewystarczające dla części zapytań; nie uzupełniałem luk z pamięci modelu. Nie pobierano PDF-ów do `registry/sources/` — treści artykułów weryfikowano przez WebFetch.
- Kod oficjalny potwierdzono tylko dla NCA (repo wskazane w otwartym artykule Distill) i PLR (repo wskazane w pełnym tekście). Dla pozostałych rekordów brak zweryfikowanego URL kodu; nie zgadywałem repozytoriów.
- IMGEP i PAIRED są rodzinami/frameworkami, nie pojedynczymi regułami optymalizacji; wykorzystanie backpropu zależy od implementacji agenta. PAIRED korzysta z zwrotów protagonisty/antagonisty do regret; PLR uzależnia GAE od nagrody i stosuje gradientowo uczone PPO w eksperymentach.
- NCA nie wymaga nagrody RL, ale uczy się przez BPTT z zewnętrznie zadanym celem obrazu; to nie jest brak sygnału nadzorującego.

## Obserwacje dla celu GENESIS

1. **Samoorganizacja nie gwarantuje braku nagrody.** POET, PAIRED i PLR kształtują trudność/kurikulum, ale są zakotwiczone w zewnętrznych zwrotach zadaniowych (PLR dodatkowo używa GAE).
2. **Brak backpropu i brak nagrody to niezależne osie.** POET i MAP-Elites mogą korzystać z ewolucyjnej optymalizacji bez backpropu, ale jakość rozwiązań zwykle mierzy się wynikiem zadania; nie spełnia to samo przez się kryterium reward-free.
3. **NCA jest interesującą wskazówką mechanistyczną, nie gotowym agentem.** Współdzielona lokalna dynamika, samonaprawa i rozwój ze stanu początkowego mogą inspirować architekturę, lecz oryginalne uczenie jest BPTT na obrazie docelowym.
4. **Rozdzielenie generatora zadań od reguły uczenia jest użyteczne.** Można eksperymentować z kurikulum/rozwojem zdolności niezależnie od aktualizatora parametrów; dla GENESIS kluczowe będzie zastąpienie reward-dependent kryterium postępem/kompetencją wewnętrzną, bez ukrycia nagrody środowiska.
5. **Konieczna jest precyzyjna etykieta sygnału.** Intrinsic reward, regret między politykami i supervised target nie są tym samym co brak sygnału; w przyszłym katalogu warto odróżniać zewnętrzną nagrodę od wszelkiego nadzoru.

## Tablica współpracy

- Początkowy `read self_organization`: brak nowych wiadomości.
- Późniejszy odczyt: otrzymano od `no_backprop` informację, że Forward-Forward (Hinton 2022, arXiv:2212.13345) deklaruje eliminację backpropu, ale brak potwierdzenia Craftera w abstrakcie i sygnału nagrody zewnętrznej w algorytmie. Metoda należy do `no_backprop`; nie katalogowałem jej.
- Otrzymano od `orchestrator` komunikat o `experiment_engine`: przy publicznym kodzie łatwym do szybkiego testu reward-free na Crafterze należy przekazać nazwę/repo/użycie backpropu.
- Przekazano `all`: informację, że wyniki/repo dla części metod nie są jeszcze weryfikowalne z dostępnego WebFetch; brak niezweryfikowanych liczb i repo.
- Przekazano `experiment_engine`: POET ma ES bez backpropu, ale używa nagrody zadaniowej; NCA ma potwierdzone repo `https://github.com/google-research/self-organising-systems`, lecz BPTT i nadzorowany target obrazu, więc nie jest gotowym reward-free Crafter learnerem. Nie wskazano jeszcze metody plug-and-play spełniającej oba kryteria.
- MAP-Elites, PAIRED, PLR, IMGEP, `growing_neural_ca`, `som_kohonen` i inne próby dodatkowych claimów wykonano zgodnie z wynikiem `claim`; jeden `go_explore` claim był już zajęty przez `intrinsic_motivation` i został pominięty.
- Przed końcem zadania wykonano końcowy `read self_organization`; brak nowych wiadomości.

## Źródła otwarte

- NCA: [Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/) — pełny artykuł/wyciąg.
- POET: [arXiv:1901.01753](https://arxiv.org/abs/1901.01753) oraz [pełny HTML](https://arxiv.org/html/1901.01753).
- PAIRED: [arXiv:2012.02096](https://arxiv.org/abs/2012.02096) — abstrakt.
- PLR: [arXiv:2010.03934](https://arxiv.org/abs/2010.03934) oraz [pełny HTML v4](https://arxiv.org/html/2010.03934v4).
- IMGEP: [arXiv:1708.02190](https://arxiv.org/abs/1708.02190) — abstrakt.
- MAP-Elites: [arXiv:1504.04909](https://arxiv.org/abs/1504.04909) — abstrakt.

## Następny krok

Dokończyć bibliografię i weryfikację OMNI/OMNI-EPIC, SOM, MAGELLAN oraz pozostałych automatycznych kurikulum; dla PAIRED/IMGEP/MAP-Elites sprawdzić PDF/full text i kod; dodać tylko faktycznie otwarte źródła i tabelaryczne wyniki.
