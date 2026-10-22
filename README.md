# GENESIS

Eksperyment: zespół agentów AI szuka **jednej fundamentalnej zasady**, z której sama wynika cyfrowa biointeligencja.
Chodzi o system, który rośnie, przycina się, uczy, pamięta i bada świat, **bez nagrody zewnętrznej i bez
backpropagation**. Zamiast dokładać osobne mechanizmy (tu pamięć, tam eksplorację) szukamy prawa, z którego one wynikają,
tak jak w fizyce jedno prawo tłumaczy wiele zjawisk. Biologia mózgu jest źródłem inspiracji.

Cel pomiarowy na końcu drogi: Crafter w trybie bez nagrody. Realistyczny pierwszy kamień milowy to wynik powyżej
2,1% (Plan2Explore z artykułu Crafter) bez nagrody i bez backpropu.

## Jak to działa

Agenci to modele językowe w Codex CLI, sterowane przez nadzorcę (`agents/supervisor_v3.py`). Każda tura to świeża sesja,
a pamięć między turami jest w plikach (`HANDOFF.md`).

| Agent | Rola |
|---|---|
| `odkrywca_life` | szuka zasady wychodząc od życia: zasoby, metabolizm, podział, śmierć |
| `odkrywca_axioms` | szuka zasady wychodząc od warunków, jakie musi spełniać każdy samobudujący się system |
| `krytyk` | zakłada, że „nowy” pomysł już istnieje i że wynik może być artefaktem, dopóki nie wykaże inaczej |
| `eksperymentator` | niezależnie replikuje wyniki i przenosi zasady do formatu sędziego |
| (wcześniej) `biolog` | wydobywa zasady z neuronauki i biologii rozwoju (`biology/PRINCIPLES.md`) |

Komunikują się przez wspólną tablicę (`shared/board.jsonl`). Hipotezy przechodzą cykl
proposed → critiqued → testing → supported / refuted (`shared/hypotheses.json`).

## Sędzia (`sandbox/`)

Kotwicą jest deterministyczny kod, a nie ocena modelu językowego. Kandydat to jeden plik `candidates/<nazwa>/principle.py`.

- **Świat:** strumienie sygnałów, w których reżimy zmieniają się i wracają, a złożoność rośnie i maleje.
  Dalej trudniejsze strumienie, Snake bez nagrody i Crafter bez nagrody, zaliczane po kolei.
- **Pomiary:** przewidywanie, adaptacja po zmianie, pamięć po powrocie, czy struktura śledzi złożoność świata, koszt.
- **Elegancja:** kara za każdą ukrytą stałą i warunek w kodzie.
- **Odporność:** parametry w `PARAMS` są dozwolone, ale sędzia losowo je zmienia (×0,5–2) i sprawdza, czy zjawiska
  nadal występują.
- **Wymóg uczenia się:** gotowa strategia nie może zaliczyć szczebla.
- W budowie: test grokowania (czy zasada potrafi długo nic, a potem nagle zrozumieć regułę), długi tor na GPU
  i test skalowania.

## Co wyszło do tej pory

- **H003–H005 (przepływ zasobów):** jedno prawo bilansu masy: komórka ginie, gdy masa spada do zera, i dzieli się,
  gdy się podwoi. Daje wzrost, przycinanie i selekcję połączeń. W małym świecie wyraźnie wygrywa z kontrolami
  (np. 90% vs 37% komórek na właściwym sygnale, 20/20 seedów). W większym świecie przegrywa z prostą regułą Hebba.
- **H001 (kiełkowanie połączeń):** potwierdzona przy 8 kanałach, słabnie przy 16.
- **H002 (najkrótszy opis), H006, H008:** obalone.
- **Trzy próby obejścia sędziego** (wpisana trasa w Snake, ukryte stałe, ręczny BFS) zostały wykryte i
  zdyskwalifikowane. Zostały w repozytorium jako przykład (`sandbox/disqualified.tsv`).

Uczciwie: na razie to warianty znanych idei (dobór darwinowski, MDL, znaczniki synaptyczne) w zabawkowych światach,
a nie nowy paradygmat. Pełne krytyki są w `audit/`.

## Struktura

```
theory/      teorie, dzienniki i symulacje odkrywców
audit/       krytyki, prior art, turniej
biology/     zasady biologiczne
sandbox/     sędzia, tablica wyników, dyskwalifikacje
candidates/  kandydaci do oceny (także baseline'y i oszuści testowi)
shared/      tablica, rejestr hipotez, bank pomysłów, narzędzie literaturowe
engine/      testy strumieniowe i harness Craftera
agents/      nadzorcy i prompty agentów
registry/    katalog literatury z pierwszej fazy (pamięć przeciw powtórkom)
```
