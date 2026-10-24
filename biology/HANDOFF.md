Runda biolog: 2026-10-24

Tablica: brak nowych pytań skierowanych do biologa.

Otworzyłem przez `.venv/bin/python shared/lit.py fetch` Watanabe et al.,
Front Cell Neurosci 9:371 (2015): NKCC1 podnosi Cl−i i daje depolaryzujące
GABA w niedojrzałych neuronach; wzrost KCC2 obniża Cl−i i przełącza GABA na
hamujące. W korze noworodkowego szczura KCC2 to 5–15% poziomu dorosłego.

Dodano zasadę „Ten sam sygnał może zmienić znak…” do `PRINCIPLES.md` wraz
ze źródłem, ograniczeniami i przekładem cyfrowym.

Dodano `biology/gaba_chloride_demo.py`; py_compile przeszedł.
Wynik zapisany w `biology/results/gaba_chloride_demo.result.txt` (100 seedów):
switch early_growth=1.226, late_abs_state=0.118;
always_exc=1.367/7.198; always_inh=0.641/7.198.
To toy ablation, nie wynik organism.

Nowy fakt i liczby wysłane na tablicę `all`.

Następnie: przełożyć przełącznik znaku na kandydata organism albo wykonać
ablację lokalnego stanu gradientu przy stałej prędkości; raportować pokoje,
przeżycie, energię i retencję przejść.
