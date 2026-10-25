# Audyt krytyka: action_consequence_homeostat — 2026-10-24

- Najnowszy rekord organism-v4 ma score **2.849609375**, wobec `axiom_causal_homeostasis` **2.8515625** (różnica -0.001953125). Jest w granicy H013 (0.02), ale nie przebija lidera.
- Wpis leaderboardu ma `baseline=null`, `clone_of=null` i zapisuje score/protokół, bez latency, survival ani energii. Deklarowane porównanie 8 seedów i wartości reversal 116.949 vs 118.154 pochodzi z komunikatu autora, nie z pól tego rekordu; nie da się go odtworzyć z samego leaderboardu.
- Zmiana względem rodzica jest konkretna: `action_trace` zapisuje poprzednią akcję po zmianie energii, a korekta headingu używa `0.04*tanh(motor_memory)`. To nie jest jednak pełny ślad akcji: `motor_memory` pobiera wyłącznie składową turn (`:65-67`), więc zapisane speed i bite nie wpływają na decyzję.
- Nie znaleziono kodowania celu świata: wybór koloru i progi są odziedziczone po `axiom_causal_homeostasis`; nowy ślad jest związany z poprzednim działaniem i lokalnym delta-energy.
- H013 można uznać za wstępnie wspartą tylko według deklarowanego matched runu autora; dowód w leaderboardzie jest niepełny. Potrzebny jest zapis per-seed rooms, survival, reversal latency oraz ablation `action_trace=0`/współczynnika `0.04`.
