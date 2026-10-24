KIERUNEK: rzadka sieć kolor–piksel wzmacniana zmianą energii i zanikająca przy nieużyciu.
KRYTERIUM PORZUCENIA: do końca budżetu score organism < 0.0055 albo brak wzrostu score ponad random.
BUDŻET: 2/3 tur.
Ta tura: uruchomiono wymagany sędzia: `nice -n 15 .venv/bin/python sandbox/judge.py candidates/growth_metabolic_graph --organism --organism-seeds 8 --author odkrywca_growth`.
Wynik sędziego (organism-v3, 8 seedów, 1024 światy, 6000 kroków): score 0.046875,
survival 0.12695, średnia liczba pokojów 0.046875; wzrost końcowy 491.625 jednostek/krawędzi.
Próba poprawności limitów 302/1k/10k/100k zaliczona. Losowy baseline 0.0055; lider 2.4.
Pomiar struktury (measure.py, 1 seed, 8 światów, 1500 kroków, batch 8):
302/1k/10k/100k limitu dały tę samą strukturę; z przycinaniem 83→137→106 węzłów,
bez 83→153→229; szczyt estymowanego stanu 9.5 KB vs limit mózgu.
Przycinanie poprawiło metrykę rzadkości (229→106 aktywnych po 1500 krokach),
ale jeszcze nie testowano jego wpływu na score w tym samym pełnym protokole.
Świat pozostał w pokoju 0 w obu wariantach. Połączenia == węzły w implementacji,
więc ich pomiar nie jest niezależny; predykcja nie była mierzona.
Score przewyższył random, lecz daleko mu do lidera; kontynuuj ostatnią turę budżetu:
pełna ablacja przycinania + sensowna metryka predykcji/niezależnych krawędzi albo porzuć.
Test 1500 kroków nie wykazał jakości uczenia; jakości predykcji nadal nie mierzono.
