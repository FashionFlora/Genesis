KIERUNEK: rozpoznawanie opcjonalnej energii i zachowanie całego oka; metabolizm bez jawnego interoceptora.
KRYTERIUM PORZUCENIA: score no-interoception < 2.64 albo standardowy spadnie > 0.10 względem 2.8408.
BUDŻET: 1/3; standard 2.8379 (bez poprawy vs 2.8408), no-intero 2.3721 (poniżej progu).
Kandydat candidates/metabolic_gate_optional_intero: obsługa 49/48 kanałów; kod korzysta z wszystkich pikseli RGB.
Ocena organism 8 seedów: standard rooms 2.8379, survival 0.8906, room5 0.0967; no-intero rooms 2.3721, survival 0.9141, room5 0.0361.
Wniosek: kontrakt no-intero naprawiony, lecz stały fallback energii nie zachowuje wyniku. Test nie bada wzrostu mózgu; struktura stoi na 3 jednostkach.
Wyniki źródłowe: sandbox/leaderboard.jsonl; kod i PARENTS: candidates/metabolic_gate_optional_intero/.
Poprzedni kierunek metabolic_gate: budżet 3/3; 2.8379 nie pobił 2.8408, więc nie stroić dalej tej reguły.
Następnie: zbadać lokalny metabolizm wyprowadzany z konsekwencji działania, bez kanału energii; wymagać ablacji i pełnej oceny organism.
