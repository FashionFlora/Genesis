KIERUNEK: lokalna alokacja i zanik z metabolicznie ważonym śladem.
Połączenie piksel-kolor powstaje dopiero po ugryzieniu, dodatnim oku i
niezerowej zmianie energii; ten sam ślad zanika i usuwa połączenie. Mutacja
`growth_metabolic_sparse` skaluje kredyt przez poprzednią rezerwę energii,
z zachowaniem niezależnej topologii każdego organizmu w batchu.

KRYTERIUM PORZUCENIA: pełny organism-v7 z parowaną ablacją
`association_gain=0`, co najmniej 2 dozwolone seedy i skale
302/1000/10000/100000. Porzucić wkład metabolicznego ważenia, jeśli CI95
parowanej różnicy `rooms_reached(gain=0.8)-rooms_reached(gain=0)` obejmuje zero
na każdej skali oraz krzywe wzrostu nie różnią się poza szumem. Nie używać
liczby tur jako powodu; obecny test 1-seed jest nierozstrzygający.

OSTATNI WYNIK: `growth_metabolic_sparse` full v7 zakończony 2026-10-25.
Score 0.0068359375; rooms CI95 [0.00110624, 0.01256564]; survival 0.7685547;
wall 12813.95 s; hash
50e7379638c8ce12477bed81ad3a1146477196abdc7722c39b1ae8b887f00892.
Wszystkie limity miały identyczny score. Struktura start 2/2, maksimum
5.760742 jednostek/6.540039 połączeń, koniec 4.613281/5.15625.
Perturbacje score: x0.7=0.0, x1.4=0.0244141. Wynik identyczny z rodzicem,
bez poprawy lidera 0.8.

PAMIĘĆ: `metabolic_sparse_probe.result.json` pokazuje 92 B startowo przy
każdym limicie, 530 B po 80 krokach aktywnych, 92 B po 1000 cichych i 0 kluczy.
To jest probe syntetyczny, nie wynik zachowania ani predykcji.

NASTĘPNIE: uruchomić pełną parowaną ablację gain=0 na tych samych seedach i
skalach; dopiero potem rozstrzygać hipotezę. Nie twierdzić, że wzrost poprawia
inteligencję na podstawie tego jednego seeda.
