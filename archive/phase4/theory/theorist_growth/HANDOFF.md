KIERUNEK: H014; opóźniona alokacja sensoryczna po powtarzalnej aktywności i energii dostępnej do gryzienia.
KRYTERIUM PORZUCENIA: po 3 turach brak mniejszego zaalokowanego B przy nie gorszym awansie pokoi w sparowanym organism-v4; osobno wymagana przeżywalność przy 2x bokach.
BUDŻET: 2/3.

Krzyżówka: `candidates/growth_delayed_support/` łączy dynamiczne kandydaty sensoryczne z podpisanym śladem homeostazy; materializacja po trwałym wsparciu metabolicznym. Pomysł sprawdzony przez `shared/ideas.py`: nowy (similarity 0.09 < 0.3).
Sędzia organism-v4, 8 seeds x 128 światów: score 2.3125, 1024 światów, 1634.68 s; poniżej lidera 2.840820. Wynik: `sandbox/leaderboard.jsonl`.
Jednostki/połączenia raportowane 0 od kroku 0 do 6000, przy upper bound 302; wzrost także 0 dla testów skali 1k/10k/100k. Próg skutecznie zablokował wzrost, metryka pamięci/pruning nie została poddana testowi.
Naprawiłem błąd cyklu życia: _compact kasował świeże kandydatury przed następnym kredytem wsparcia. Zachowanie slotu z previous_active umożliwiło wzrost.
Audyt seed31, batch8, 6000 kroków: próg 0.18 = 17.375 aktywnych jednostek/osobnik, 48 wspólnych slotów, 7104 B tensorów, rooms 2.25, survival .875.
No-growth ablation threshold 1e6 = 0 jednostek, 23 sloty przejściowe, 3504 B, rooms 2.25, survival .875. Przyrost pamięci jest realny; brak poprawy zachowania.
2x room sides: wzrost do 12.125 jednostek, potem extinction przed 4096; final survival 0. Nie ma odporności skali.
Oficjalny judge 302, 8 seedów uruchomiony na CPU; wynik jeszcze w toku/niezapisany przed końcem tury. Próba 302,10000 przerwana po ~30 min.
Pliki: candidates/growth_delayed_support/principle_organism.py; theory/theorist_growth/growth_delayed_audit.py; growth_delayed_audit.jsonl.
Następna tura: odczytać score 302, porównać matched baseline, a jeśli brak poprawy pokoi lub pamięci, oznaczyć H014 parked i przejść do innej zasady.
H003 parked: pruning pogorszył pokoje 2.875->2.375 i przeżycie 1.0->0.875, bez oszczędności alokacji (1203 B/osobnik).
H014: testing; pełny score i matched baseline pozostają potrzebne.
