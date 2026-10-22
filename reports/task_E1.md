# Raport zadania E1 — Experimental Engine

## Zakres i stan

Zaimplementowano `engine/core.py`, `engine/agents.py`, `engine/run.py` oraz instrukcję `engine/README.md`. Instalacja lokalnego `.venv` ma Crafter 1.8.3 oraz PyTorch 2.14.1 (CUDA 13.0 build); CUDA jest widoczna, ale oba benchmarki są CPU, z limitem 3 rdzeni.

## Metryki źródłowe

Otwarty tekst HTML artykułu Crafter, arXiv:2109.06780, sekcja 3.3 „Score” podaje: `S = exp((1/N) sum_i log(1+s_i)) - 1`, gdzie N=22, a `s_i` jest achievement success rate w procentach. Ocena sukcesu to odsetek epizodów odblokowujących każdy achievement. W tabeli 1 („Crafter benchmark scores”) Random ma score 1.6% i return 2.1 ± 1.3. Harness oblicza score z 22 achievement rates, ale nie liczy ani nie przekazuje return/reward agentowi.

Źródło: https://arxiv.org/html/2109.06780 (sekcja 3.3 i tabela 1; dostęp przez WebFetch). Wynik z pojedynczego epizodu jest bardzo zgrubny i nie można go bezpośrednio uznać za porównywalny z raportem publikacyjnym.

## Przebiegi

`random-smoke` było pierwszym testem i ujawniło błąd metodologiczny: użycie 100k kroków jako jednego epizodu nie jest zgodne z domyślnym horyzontem Craftera (10k); reset powoduje ponowne rozpoczęcie epizodu. Wynik tego przebiegu nie jest porównywalny i został zachowany do śladu audytowego. Harness poprawiono tak, by rozliczać epizody 10k, resetować po śmierci/horyzoncie i liczyć success rate per episode.

- Wstępny random 100k: `experiments/random-smoke/result.json` — score 0.2334044671%, jeden epizod do śmierci (160 kroków), tylko wake_up; błędna agregacja per-episode, nie porównywać.
- Wstępny pixel novelty 100k: `experiments/pixel-novelty-smoke/result.json` — do odczytu po zakończeniu; błędna agregacja, nie porównywać.
- Random 100k poprawiony, 10 epizodów: `experiments/random-smoke-final/result.json` — w trakcie.
- Pixel novelty 100k poprawiony, 10 epizodów: `experiments/pixel-novelty-smoke-final/result.json` — w trakcie.

Rozbieżność wstępnego random score (0.2334% vs artykuł 1.6%, tabela 1) pochodzi z błędnego traktowania 100k kroków jako jednego epizodu i śmierci przy 160 krokach. Stąd zamiast wyniku 10 epizodów liczono tylko jeden; poprawiona implementacja przeprowadzi wiele niezależnych epizodów po 10k budżetu z resetami.

## Kontrola reward-free i backprop

`crafter.Env(reward=False)` zeruje zwracany reward; warstwa runnera przekazuje do `observe` tylko allowlistę (`inventory`, `discount`, `semantic`, `player_pos`), nigdy reward/achievements. Achievements odczytywane są osobno przez ewaluator do metryk. Deklaracja `uses_backprop` jest zapisywana. Dodatkowo funkcja `audit_tensors` skanuje osiągalny stan agenta pod kątem tensorów `requires_grad`; `install_backward_audit` opakowuje `Tensor.backward` i zwraca licznik oraz restore callback. Runner obecnie nie instaluje wrappera automatycznie; `backward_calls` jest więc jawnie null. Luki: `torch.autograd.backward` / `autograd.grad`, nieosiągalne tensory, custom/native gradienty, wywołania w innych procesach i agent celowo wprowadzający harness w błąd. To audyt heurystyczny, nie formalny dowód braku backprop.

## Dalsze przebiegi

1M kroków jest standardowym horyzontem benchmarku Crafter (domyślny epizod to 10k kroków, wiele epizodów składa się na budżet 1M); należy uruchomić wyłącznie dla losowego agenta, jeśli uprzedni 100k random mieści się w limicie 30 min. Wstępna próba była bardzo szybka, ale po poprawieniu obsługi resetu wymagany jest nowy pomiar; jeśli 1M nie zmieści się w 30 minut, zaplanować osobne uruchomienie i nie uruchamiać tutaj. Nie uruchamiać 1M curiosity baseline w tym zadaniu. Dla wiarygodnych success rates przeprowadzić później wiele seedów/epizodów, uwzględniając koszt czasu.

## Kolejka metod z tablicy

Na ostatnim odczycie tablicy przed zakończeniem należy sprawdzić ewentualne zgłoszenia do szybkiego testu.
