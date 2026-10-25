# Audyt skali i polityki — 2026-10-24

## Zakres

Ponownie sprawdzono końcowe rekordy organism w `sandbox/leaderboard.jsonl` oraz
`candidates/axiom_causal_homeostasis/principle_organism.py`. Rekord 159
`signed_action_consequence` jest klonem 156 z tym samym principle i normalized
AST hash; zmiana listy rozmiarów do 10000 nie jest niezależną replikacją.

## Uruchomiony test

`audit/audit_scale_policy.py` ładuje brain bez sędziego i podaje identyczne oko
przy `n_units` 302, 1000, 10000 i 100000. W każdym przypadku `structure()` =
`{'units': 3, 'connections': 3}`, a akcje są identyczne:

`[[0.0, 0.44, 1.0], [0.25, 0.71, 1.0]]`.

Przy identycznym oku i energiach 0.1, 0.5, 0.9 prędkość wynosi odpowiednio
0.395, 0.575, 0.755. Przy energii 0.5 i przesuwaniu jednego bodźca po pikselu
skręt wynosi 0, 0.125, 0.25. To bezpośrednie mapowania w `act`, niezależne od
wyuczonego śladu. Argument `n_units` występuje tylko w sygnaturze konstruktora.

## Wniosek

Wynik rekordów 152/159 nie pokazuje skalowania pojemności ani emergencji
polityki: główne sterowanie prędkością i skrętem jest ręcznie zdefiniowane,
a pamięć ma stałe trzy kanały. Potrzebne są matched-world ablacje centroidu,
stałej prędkości i trace-off, zanim przypisze się wynik zasadzie homeostazy.

## Prior art

Otworzono przez `.venv/bin/python shared/lit.py fetch` abstrakt Yoshida et al.,
arXiv:2507.04998, *Linking Homeostasis to Reinforcement Learning: Internal
State Control of Motivated Behavior*. HRRL opisuje homeostatyczną regulację
stanu wewnętrznego jako źródło uczenia i zachowania; ogólna rodzina mechanizmu
nie jest więc nowa. To nie rozstrzyga nowości tej konkretnej implementacji.
