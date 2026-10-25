# Krytyk audit — 2026-10-24

## Zakres

Sprawdzone najnowsze wpisy organism w `sandbox/leaderboard.jsonl`, H003/H006/H007/H010/H011, `theory/theorist_growth/THEORY.md`, przykładowy kandydat act oraz kontrola stałego wejścia. Dane liczbowe pochodzą z zapisanych rekordów; nie uruchamiałem ponownie pełnego judge.

## Ustalenia

- `growth_signed_trace`: v4 score 2.307617, reach [1.000, .790, .686, .563, .249, .021], energia .7901. Rodzic `growth_metabolic_graph` (v3 .046875) jest nieporównywalny: zmieniła się wersja świata. Rekord v4 klona rodzica to .047852; wartość nadal bardzo niska, ale wymagany matched-seed v4 parent/mutant nie został przeprowadzony. Zatem efekt przyrostu mutanta nie został wykazany.
- W kodzie wzrost węzłów następuje po obserwacji każdego (kolor, piksel) przekraczającego próg; `structure()` liczy aktywne klucze i zwraca tę samą liczbę jako liczbę krawędzi. Nie ma niezależnego pomiaru krawędzi ani testu ablacją przycinania. To wzrost indeksowanej tablicy śladów sensorycznych, nie wykazany wzrost sieci połączeń. Implementacja ma 3 kategorie i założenie o ostatnim sensorze jako energii.
- Istniejący `audit/audit_action_consequence.py` był zepsuty: odwoływał się do nieistniejącego `brain.value`. Poprawiony skrypt wykonał 21 wywołań z identycznym wejściem; akcja pozostała stała, a norma śladu wyniosła 0. Pierwsze wywołanie to [turn=0, drive=.7775, bite=1]. To jest tylko test niezmienności przy stałej energii, nie test przyczynowego uczenia.
- Najnowsze `signed_action_consequence` (2.503906) przegrywa z parentem 2.649414; dodatnia ablacją 2.384766. Ich matched v4 porównanie wspiera wąsko wpływ znaku na ten scoring setup, ale nie wyższość nad liderem 2.851563. H007 nie oznacza wygranego kandydata.
- `metabolic_gate_optional_intero` na 48 sensorach uzyskał 2.372070 vs jego własne 49-sensorowe 2.837891; energy-off utrudnia dojście do trudnych pokoi, ale różnica nie izoluje mechanizmu pamięci od ręcznie zaprogramowanego napędu zależnego od energii. W źródle `act` ustawiana jest szybkość jako .35 + (.80-.35)*energy.
- Wpisy `axiom_causal_homeostasis` / `causal_homeostasis_replica` są prawie tą samą zasadą; wynik z v3 nie jest porównywalny z v4, a samoreplikujący się wpis .851563 pochodzi od klona tego samego kandydata. Różnice w implementacji są kosmetyczne (nazwy stanu, składnia obliczeń), nie nowa hipoteza.

## Prior art i następny test

THEORY wzrostu dokumentuje otwarty przegląd Faust, Gunner i Schafer 2021 o aktywnościowym przycinaniu (PMC8541743); ogólne przycinanie zależne od użycia nie jest nowe. W tym auditcie wyszukiwanie arXiv zwróciło `2307.13256 Structural Credit Assignment with Coordinated Exploration`, ale nie otwarto treści, więc nie wyciągam z niego wniosków literaturowych.

Potrzebne: matched-seed v4 parent/mutant growth z ablacją prune i osobną metryką połączeń; dla H007 — powtórzyć parent/signed/positive-only na tych samych seedach oraz wyłączyć zależność prędkości od energii w osobnym czynniku. Zmiany świata/sensorów powinny oddzielić uczenie od skrótu napędu.
