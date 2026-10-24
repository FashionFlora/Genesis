KIERUNEK: sprawdzić, czy adaptacyjna retencja śladu metabolicznego poprawia eksplorację względem stałej retencji.
KRYTERIUM PORZUCENIA: po maks. 2 kolejnych turach bez rooms_reached > 0.3125 lub gdy ablacja nie zmienia wyniku, odłożyć kierunek.
BUDŻET: 1/2; mutacja adaptacyjnej retencji dała rooms_reached=0.0117, score=0.0117, survival=0.

Krzyżówka kandydatów: axiom_homeostasis + axiom_instant_flow, nowy candidates/axiom_metabolic_retention/.
ideas.py: NOWY, max podobieństwo 0.15. Metabolizm sterował czasem życia śladu; wynik nie wspiera tej zasady.
Organism-v2 judge: cztery skale 302–100000, wszędzie rooms_reached=0.01171875; wynik zapisany w sandbox/leaderboard.jsonl.
Porównanie: axiom_instant_flow=0.3125, action_directional_credit=0.3671875 w ostatnich widocznych wpisach; lider aksjomatów zgłoszony na tablicy=0.5.
Poprzednia relaksacja kierunku miała 0.1211, ablacja natychmiastowego przepływu 0.3125; brak przewagi pamięci kierunku.
Następnie: abluj adaptacyjne sterowanie retencją względem tego samego kandydata ze stałym decay; zamknij po budżecie, jeśli brak poprawy.
