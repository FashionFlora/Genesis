# Eksperymentator: replikacje hipotez

## H001 — Wybór przez ślad metaboliczny

Świeży przebieg oficjalnego sędziego (`author=eksperymentator`, 2 światy/rozmiar) odtworzył `score=0.01171875`, zgodnie z wcześniejszym wpisem. Wyniki po skali: 302, 1k i 10k miały `rooms_reached=0`; skala 100k miała `rooms_reached=0.046875` i `room_reach_fraction(room 2)=0.0234375`. Średni wynik jest więc skutkiem sukcesu wyłącznie w największym mózgu, a nie szerokiej poprawy.

Ablacja `rate=0` na tych samych seedach i protokole (pełne 4 skale, 2 światy) dała `score=0` i `room2_fraction=0` na każdej skali. Wyniki ablacją zapisane w `experiments/H001_rate0_result.json`. Wspieram H001 w ograniczonym sensie: ślad metaboliczny współwystępuje z przejściami w tej próbie, ale n=2 seedów/rozmiar nie pozwala potwierdzić stabilności efektu. Status `supported` dotyczy tej implementacji i tego protokołu.

## H002 — Homeostatyczna selekcja śladów sensoromotorycznych

Świeża oficjalna replikacja dała `score=0` dla 302, 1k, 10k i 100k; wszystkie 256 światów na skalę pozostały w pokoju 1, bez przeżycia do końca. To spełnia zapisany falsyfikator `rooms_reached <= 0.0055` dla tej implementacji i bieżącego protokołu. Rejestr pozostaje `testing`, ponieważ odkrywca odnotował wcześniejszy wynik `0.46875` w innym wariancie protokołu; wyników nie należy łączyć bez zgodności wersji.

## H003 — Działanie wzmacnia kierunek

Świeża oficjalna replikacja `candidates/action_credit` dała `score=0` i `room2_fraction=0` dla 302, 1k, 10k i 100k (2 światy/rozmiar). Hipoteza nie przekroczyła losowego progu `0.0055`; status `refuted` dla tej implementacji.

## H002 — bounded eligibility (nowa replika)

Niezależna replika nowego kandydata odkrywcy `candidates/axiom_bounded_eligibility` w `organism-v2` (`author=eksperymentator`, 2 światy/rozmiar) dała `score=0.0` na 302, 1k, 10k i 100k. Średni wiek wyniósł `60.203125`, średnie żerowanie między patchami `1.32421875`, a wszystkie światy zakończyły w pokoju 1 z energią `0.0`; wynik jest zapisany w `sandbox/leaderboard.jsonl`.

Ablacja `--no-interoception` również dała `score=0.0` we wszystkich skalach; średni wiek `60.9609375`, żerowanie `1.39453125`, energia końcowa `0.0` (ten sam plik wyników). Obie próby kończą się przed pierwszym odwróceniem barwy przy kroku 768, więc nie testują adaptacji do odwrócenia. Replika nie wspiera bounded eligibility ani zależności od interocepcji w tym protokole; status H002 pozostawiam `testing` z powodu wcześniejszego, nieporównywalnego wariantu 3-pokojowego.

## H004 — Direct sensory-motor flow (nowa replika)

Niezależny przebieg `candidates/axiom_sensorimotor_flow` (`organism-v2`, 2 światy/rozmiar) dał `score=0.0469` na każdej skali. Średni wiek wyniósł `307.43359375`, żerowanie `7.3359375`, a pokój 2 osiągnęło `0.046875` światów; pokój 3+ nie został osiągnięty. Wynik znajduje się w `sandbox/leaderboard.jsonl`.

Ablacja `--no-interoception` dała `score=0.0664` na każdej skali, średni wiek `255.44140625`, żerowanie `6.875`, pokój 2 `0.05859375` i pokój 3 `0.0078125`. To przewyższa próg losowy `0.0055` i pokazuje, że efekt nie wymaga wejścia energii, choć żaden organizm nie przeżył do końca 6000 kroków. Replika wspiera H004 w tym protokole; rozdzielenie wpływu skrętu i gryzienia pozostaje otwarte.

## Następny krok

Zwiększyć liczbę niezależnych światów dla H001 i sprawdzić, czy efekt utrzymuje się poza pojedynczym sukcesem przy 100k. Nie stroić wartości parametrów pod wynik.

## H006 — Oscylacyjny rezerwuar homeostatyczny

Niezależna replika `candidates/eksperymentator_dynamics_oscillator` w `organism-v2` (2 seedy na skalę) dała `score=0` dla 302, 1k, 10k i 100k. Średni wiek wyniósł `66.1953125`, średnia energia końcowa `0`, a `room2_fraction=0` na każdej skali; wszystkie organizmy zakończyły w pokoju 1 przed odwróceniem barwy.

Ablacja `rate=0` na tych samych seedach również dała `score=0`, `room2_fraction=0`, survival `0` i średni wiek `66.83984375` (zapis: `experiments/H006_rate0_result.json`). Brak różnicy w przejściach i brak dłuższego życia obala predykcję H006 w tym protokole; wynik nominalny jest w `sandbox/leaderboard.jsonl`.

## H007 — Habituacja obrazu uwalnia eksplorację

Niezależna implementacja lokalnej habituacji sensorycznej (`candidates/eksperymentator_habituation`) w `organism-v2`, 2 seedy/skalę, 302–100k, uzyskała score `0.1796875`, room2 `0.06640625`, średni wiek `165.20703125`, żerowanie między patchami `3.16796875` i survival `0`. Sparowana ablacja `habituation_gain=0` dała odpowiednio `0.171875`, `0.05859375`, `155.42578125`, `3.24609375` i `0`. Przedziały ufności wyników room reach nakładają się; nominalna reguła nie podniosła żerowania między patchami, więc przewidywany mechanizm nie jest potwierdzony. To jedna replika, nie końcowy falsyfikator. Zachowuję H007 jako `testing`; szczegóły: `experiments/H007_result.json`, pełne przebiegi: `sandbox/leaderboard.jsonl`.
