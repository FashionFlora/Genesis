# Zadanie 01 — no_backprop

## Zakres i wpisy
Wpisano 4 rekordy do `registry/areas/no_backprop.jsonl`: Forward-Forward, Feedback Alignment, Direct Feedback Alignment oraz OpenAI-ES. Lista początkowa nie została zrealizowana w całości: poniższe metody nie mają jeszcze rekordów; nie dopisuję ich na podstawie samej pamięci, ponieważ nie udało się otworzyć w tej sesji wiarygodnych źródeł pierwotnych/pełnych tekstów i zweryfikować reguł oraz kodu: Oja, BCM, STDP, predictive coding, equilibrium propagation, target propagation, CMA-ES, NEAT, neuromodulated STDP, HSIC bottleneck, PEPITA. Odpowiednie claimy zarezerwowałem na tablicy.

## Zweryfikowane źródła i wyniki
- **Forward-Forward (Hinton, 2022), arXiv:2212.13345.** Otworzyłem abstrakt i HTML pełnego tekstu. Bezpośrednie wyniki CIFAR-10 są z **Table 1**: lokalne pola recepcyjne, dwie warstwy ukryte, score every label: 41% test error dla FF vs 37% backprop; trzy warstwy: 41% vs 39%. Artykuł nie bada Craftera. Wpisane w rekordzie wartości ograniczone są do tych wariantów z tabeli.
- **Feedback Alignment, Lillicrap et al., arXiv:1411.0247.** Otworzyłem stronę abstraktu. Abstrakt deklaruje porównywalną szybkość/dokładność na kilku problemach, ale nie wymienia benchmarków/liczb ani tabel; nie dopisuję metryk. Nie znaleziono repo w stronie źródłowej.
- **Direct Feedback Alignment, Nøkland, arXiv:1609.01596.** Otworzyłem abstrakt. Jest wzmianka o MNIST/CIFAR i jakościowych wynikach, bez liczb/tabel w sprawdzonym abstrakcie; brak zweryfikowanego linku do kodu.
- **OpenAI-ES, Salimans et al., arXiv:1703.03864.** Otworzyłem abstrakt: MuJoCo i Atari, black-box ES. ArXiv HTML zwrócił stronę błędu, więc brak liczb i tabel. Reward jest wymagany; metoda spełnia no-backprop, lecz nie no-extrinsic-reward.

## Weryfikacja i luki
- Benchmarki Crafter: brak u wszystkich czterech wpisów; rekordy nie zawierają zastępczych wyników z pamięci lub innych źródeł.
- Kod: brak zweryfikowanego repozytorium w źródłach otwartych dla czterech rekordów; pola `code` pozostają puste.
- Forward-Forward pełny tekst: zweryfikowany. Dla trzech pozostałych rekordów: informacje ograniczone do abstraktów. `uses_backprop` opisuje dokładnie mechanizm, nie samą obecność gradientów: FF i FA/DFA nie propagują standardowego gradientu warstwowego, ale nadal optymalizują wagi sygnałem gradientowym (FA/DFA mają też wsteczny sygnał błędu); nie oznacza to całkowicie bezgradientowego uczenia.
- Przeszukano źródła dla Oja/BCM/STDP i PEPITA, ale wyniki były nieadekwatne lub brakowało wiarygodnej strony pierwotnej; nie przypisałem im niezweryfikowanych URL-i ani kodu.

## Obserwacje dla celu GENESIS
1. „Bez backprop” nie znaczy „bez sygnału zadania”: nadzorowane FF koduje etykietę jako positive/negative, a FA/DFA potrzebują błędu względem targetu. Są kandydatami do ograniczenia mechanizmu gradientowego, nie automatycznie do uczenia reward-free.
2. OpenAI-ES usuwa backprop, ale wymaga return/reward środowiska; zatem kryterium GENESIS nie spełnia.
3. FF wymaga rozróżnienia między brakującym backpropagation *między warstwami* a użyciem lokalnego gradientu goodness względem wag. Nie powinien być opisany jako całkowicie bezgradientowy.
4. Publiczne wyniki dla klasyfikacji nie stanowią dowodu skuteczności w sterowaniu Crafterem ani uczeniu bez nagrody.
5. Brak repo/pełnego tekstu to luka dowodowa, nie dowód nieistnienia kodu lub braku wyników.

## Tablica współpracy
- Początek pracy: `read no_backprop` — brak nowych wiadomości.
- Orkiestrator polecił raportować łatwe kandydaty do testów Crafter agentowi `experiment_engine`; przekazałem FF jako możliwy kandydat, zaznaczając brak zweryfikowanego oficjalnego repo i brak testu Crafter w artykule.
- `experiment_engine` przekazał: POET używa ES bez backprop, ale task reward, więc nie spełnia no-reward; NCA repo `https://github.com/google-research/self-organising-systems` wskazano jako oficjalne, lecz jest target-supervised BPTT i nie jest kandydatem bez nagrody/backpropu. Przekazałem to dalej do `all`.
- `novelty_auditor` przypomniał, że FF nie może być ogłaszany jako nowy paradygmat bez węższego twierdzenia i audytu prior art; źródła arXiv full text potwierdzają positive/negative label supervision dla supervised MNIST. Uwzględniono w zasadach interpretacji wyżej.
- Ostatni odczyt tablicy wykonano przed zakończeniem; brak dodatkowych pytań do mnie w otrzymanych wiadomościach.

## Źródła otwarte
- [Forward-Forward abstract](https://arxiv.org/abs/2212.13345), [pełny tekst](https://arxiv.org/html/2212.13345v1)
- [Feedback Alignment abstract](https://arxiv.org/abs/1411.0247)
- [Direct Feedback Alignment abstract](https://arxiv.org/abs/1609.01596)
- [OpenAI-ES abstract](https://arxiv.org/abs/1703.03864)
