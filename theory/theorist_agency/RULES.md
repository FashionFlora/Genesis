# Reguły

- Efekt musi być porównany z ablacją tego samego kontrolera bez śladu.
- Liczą się wyłącznie wyniki zapisane przez sędziego.
- W organism-v6 różnica rooms_reached 0.00586 (0.06836 vs 0.06250) nie uzasadnia zasady; próg H002 wynosił 0.05.
- Ablacja musi usuwać tylko wskazany mechanizm, nie zmieniać także wag pozostałych ścieżek. Tu action_memory=False zmieniło również sensoryczny współczynnik korekty; wcześniejsza sparowana delta jest nieważna mimo pełnego sędziego.
- Krótki smoke nie może falsyfikować zasady rozwoju: 600 kroków i 16 światów nie przeszło pokoju dla żadnego wariantu. Liczy się dopiero pełny matched organism-v7 z CI.
- Dla reafferencji kontrola zachowuje predyktor i aktualizację; zerowany jest wyłącznie `reafferent_gain`.
- Action-conditioned zmiana namiaru oka (bearing-Jacobian) nie poprawiła wyniku pełnego v7: rooms=0.0 vs matched ablacją 0.00097656, a x0.7 było 0.00585938 w obu. Nie wnioskuj o sparowanej CI z samych agregatów leaderboardu.
