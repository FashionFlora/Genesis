# GENESIS

**Cel:** jedna fundamentalna zasada, z której sama wynika cyfrowa biointeligencja: system, który rośnie, przycina się,
uczy, pamięta i bada świat, bez nagrody zewnętrznej i bez backpropagation. Nie dokładamy osobnych mechanizmów.
Szukamy prawa, z którego one wynikają. Może to wymagać nowej matematyki. Biologia (biology/PRINCIPLES.md) jest źródłem
inspiracji.

**Kotwica:** liczy się tylko to, co faktycznie uruchomiono. Liczby wyłącznie z plików wyników. Obalony pomysł to też
wynik. Fakty z literatury tylko ze źródeł, które otworzyłeś (`.venv/bin/python shared/lit.py search|arxiv|fetch|github`).

**Sędzia:** `.venv/bin/python sandbox/judge.py candidates/<nazwa>` (kontrakt w sandbox/README.md). Parametry w `PARAMS`
są dozwolone, ale sędzia sprawdza odporność na ich zmianę. Ukryte progi i warunki są karane. Tablica wyników:
sandbox/leaderboard.jsonl. Nie modyfikuj sandbox/.

**Wspólne narzędzia:** tablica `python3 shared/board.py read|post <ja> ...` (krótko, konkretnie), hipotezy
`python3 shared/hyp.py list|add|status|note`.

**Pamięć między turami:** każda tura to nowa sesja. Zaczynasz od swojego `HANDOFF.md`, a kończysz, nadpisując go
krótko (najwyżej 25 linii): co zrobiłeś, co wyszło (liczby i ścieżki), co dalej.

**Granice serwera (współdzielony z produkcją datasetu TTS):** piszesz tylko w `/opt/dlami/nvme/genesis/`, w swoich
plikach. Nie dotykasz `/opt/dlami/nvme/dataset/`, cudzych procesów ani sesji tmux. GPU wolno (przed startem
`nvidia-smi`, max 40 GB). Python tylko z `.venv`. Długie komendy z `nice -n 15`, max ~6 GB RAM i 3 rdzenie.
