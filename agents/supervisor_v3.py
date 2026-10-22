#!/usr/bin/env python3
"""Nadzorca v3: 4 agentów na codex3 (api.artemcmd.dev, gpt-6.1-sol), świeża sesja co turę.
Pamięć agenta = jego pliki + HANDOFF.md. Stop: po RUN_HOURS albo przy błędzie braku środków / autoryzacji.
Log: logs/supervisor_v3.log, logi agentów: logs/v3_<nazwa>.jsonl (dopisywane)."""
import json, os, subprocess, time

G = "/opt/dlami/nvme/genesis"
CODEX = os.path.expanduser("~/.local/bin/codex3")
RUN_HOURS = 9.3
STAGGER = 30
COOLDOWN = {"krytyk": 300}  # min. sekund między startami tur (krytyk ma krótkie tury i zjada limit 10/min)
FLAGS = "--json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check"
FATAL = ("403", "401", "402", "insufficient", "expired", "зарезерв", "invalid x-api-key")

ROLES = {
    "odkrywca_life": ("theory/theorist_life/",
        "Jesteś odkrywcą. Twój kierunek: przepływ zasobów jako jedyne prawo (H003→H004→H005). Krytyk i biolog wskazali, "
        "że uczenie i zmienność muszą wynikać z tej samej zasady, a w większym świecie Twoja zasada przegrywa z regułą "
        "Hebba. Rozwijaj zasadę tak, by to przezwyciężyć, albo znajdź głębszą. Gdy coś przeżyje Twoją symulację, zapisz "
        "to jako candidates/<nazwa>/principle.py i oceń sędzią."),
    "odkrywca_axioms": ("theory/theorist_axioms/",
        "Jesteś odkrywcą. Twój punkt wyjścia: jakie warunki musi spełniać każdy system, który sam się buduje i uczy bez "
        "końca, i jaka zasada z nich wynika. H002 (MDL) jest obalona, a Twój system nie pamięta po powrocie (A–B–A). "
        "Szukaj innej, głębszej zasady. Nie kopiuj kierunku odkrywca_life. Gdy coś przeżyje Twoją symulację, zapisz to "
        "jako candidates/<nazwa>/principle.py i oceń sędzią."),
    "krytyk": ("audit/",
        "Jesteś krytykiem. Zakładasz, że „nowy” pomysł już istnieje, a wynik może być artefaktem, dopóki nie wykażesz "
        "inaczej. Sprawdzasz hipotezy w hyp.py, THEORY.md odkrywców i każdy nowy wpis w sandbox/leaderboard.jsonl: prior "
        "art, przemycone mechanizmy, ukryte progi, czytanie plików, czy test naprawdę sprawdza przewidywanie. Konkretne "
        "uwagi wysyłaj autorom przez tablicę."),
    "eksperymentator": ("engine/, experiments/, reports/eksperymentator.md",
        "Jesteś eksperymentatorem. Niezależnie replikujesz wyniki odkrywców (najpierw H005 i pomysł biologa z tablicy: "
        "połączenie powstaje przy współaktywności, jeden stan połączenia robi wszystko). Pomagasz przenieść zasady do "
        "formatu sędziego (candidates/<nazwa>/principle.py, PARAMS) i uruchamiasz sędziego. Wyniki ustawiasz w hyp.py."),
}


def log(msg):
    with open(f"{G}/logs/supervisor_v3.log", "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def alive(name):
    return subprocess.run(["tmux", "has-session", "-t", f"genesis-{name}"], capture_output=True).returncode == 0


def leader():
    if os.path.exists(f"{G}/sandbox/FROZEN"):
        return ("TABLICA WYNIKÓW JEST ZAMROŻONA do czasu poprawki sędziego, bo trzech kandydatów ją obeszło (wpisane strategie "
                "w Snake, ukryte stałe, stała predykcja). Nie zgłaszaj kandydatów i nie pisz żadnych ręcznych strategii. "
                "Pracuj nad samą zasadą w strumieniach: czy się uczy, czy pamięta po powrocie, czy może zgrokować.")
    best, base = None, 0.0
    p = f"{G}/sandbox/leaderboard.jsonl"
    for l in open(p) if os.path.exists(p) else []:
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            continue
        c, s = str(d.get("candidate", "")), float(d.get("score") or 0)
        if c.startswith("_baseline"):
            base = max(base, s)
        elif c in disqualified():
            continue
        elif not best or s > best[1]:
            best = (c, s, d.get("author", "?"))
    if not best:
        return f"Tablica wyników: żadnego kandydata, najlepszy baseline {base:.1f}. Bądź pierwszy, który go pobije."
    return (f"Tablica wyników: lider {best[0]} ({best[2]}) {best[1]:.1f}, najlepszy baseline {base:.1f}. "
            "Pobij lidera prostszą i bardziej odporną zasadą albo znajdź głębszy fundament.")


def disqualified():
    p = f"{G}/sandbox/disqualified.tsv"
    return {l.split("\t")[0].strip() for l in open(p)} if os.path.exists(p) else set()


def top_candidates(k=3):
    """Najlepszy wynik każdego prawdziwego kandydata (bez baseline'ów), malejąco."""
    best = {}
    p = f"{G}/sandbox/leaderboard.jsonl"
    for l in open(p) if os.path.exists(p) else []:
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            continue
        c, s = str(d.get("candidate", "")), float(d.get("score") or 0)
        if c and not c.startswith("_baseline") and c not in disqualified() and s > best.get(c, (None, -1))[1]:
            best[c] = (d.get("author", "?"), s)
    return sorted(((c, a, s) for c, (a, s) in best.items()), key=lambda x: -x[2])[:k]


def evolution_block(name, turn):
    """Ewolucja pomysłów (wzorzec Co-Scientist / AlphaEvolve): odkrywcy co drugą turę krzyżują lub mutują
    najlepszych kandydatów z tablicy, także cudzych."""
    top = top_candidates()
    if not top:
        return ("\nPRIORYTET TEJ TURY: na tablicy wyników nie ma jeszcze żadnego prawdziwego kandydata. Przenieś swoją "
                "najlepszą obecną zasadę do candidates/<nazwa>/principle.py i oceń ją sędzią, nawet jeśli jest niedoskonała. "
                "Bez kandydatów na tablicy nie ma czego ulepszać.")
    lst = "; ".join(f"{c} ({a}, {s:.1f}, kod: candidates/{c}/)" for c, a, s in top)
    if turn % 2 == 0:
        return (f"\nTURA EWOLUCJI: najlepsi kandydaci na tablicy: {lst}. W tej turze stwórz NOWEGO kandydata jako "
                "mutację albo krzyżówkę jednego lub dwóch z nich (wolno i warto brać cudze). Cel: mniej ręcznych reguł, "
                "więcej zjawisk wynikających z jednej zasady, większa odporność. Zapisz go jako candidates/<nowa_nazwa>/ "
                "z plikiem PARENTS.txt (rodzice + co zmieniłeś i dlaczego) i oceń sędzią. Przed zapisem sprawdź, czy to "
                "nie powtórka: `python3 shared/ideas.py check \"<opis mechanizmu po angielsku>\"`.")
    return (f"\nNajlepsi kandydaci na tablicy: {lst}. W tej turze rozwijasz swój własny kierunek; w następnej będzie tura "
            "ewolucji (krzyżowanie i mutowanie najlepszych).")


def prompt(name, turn=1):
    own, role = ROLES[name]
    handoff = own.split(",")[0].strip().rstrip("/") + "/HANDOFF.md"
    frozen = os.path.exists(f"{G}/sandbox/FROZEN")
    extra = evolution_block(name, turn) if name.startswith("odkrywca") and not frozen else ""
    if name == "krytyk" and len(top_candidates(2)) == 2:
        (c1, a1, _), (c2, a2, _) = top_candidates(2)
        extra = (f"\nTURNIEJ: porównaj parami dwóch czołowych kandydatów, {c1} ({a1}) i {c2} ({a2}), pod kątem tego, czego "
                 "sędzia nie mierzy: który jest bardziej fundamentalny (ile zjawisk wynika z zasady, a ile jest wpisanych), "
                 "bardziej nowy względem literatury i ma lepsze perspektywy skalowania. Werdykt z uzasadnieniem dopisz jako "
                 "jedną linię JSON do audit/tournament.jsonl i wyślij autorom. To uzupełnienie wyniku sędziego, nie jego zamiennik.")
    return (f"Jesteś agentem GENESIS `{name}`. Przeczytaj AGENTS.md. {role}\n\n"
            f"Twoje pliki: {own}. Twoja pamięć z poprzednich tur: {handoff} (jeśli nie istnieje, przeczytaj swoje THEORY.md, "
            f"JOURNAL.md lub raport). Potem `python3 shared/board.py read {name}`.\n{leader()}{extra}\n"
            f"Pracuj tę turę konkretnie (kilka kroków: myśl → kod → uruchom → wnioski). Na koniec nadpisz {handoff} "
            "(najwyżej 25 linii) i zakończ turę. Następna tura zacznie się od świeżej sesji.")


def last_fatal(name):
    p = f"{G}/logs/v3_{name}.jsonl"
    if not os.path.exists(p):
        return None
    tail = open(p, errors="replace").readlines()[-30:]
    for l in reversed(tail):
        if '"turn.completed"' in l:
            return None
        if ('"error"' in l or "turn.failed" in l) and any(f in l for f in FATAL):
            return l[:300]
    return None


def launch(name, turn=1):
    lp = f"{G}/logs/v3_{name}.jsonl"
    with open(f"{G}/logs/v3_{name}.prompt.txt", "w") as f:
        f.write(prompt(name, turn))
    cmd = (f'cd {G} && nice -n 15 {CODEX} exec {FLAGS} -C {G} "$(cat {G}/logs/v3_{name}.prompt.txt)" '
           f"< /dev/null >> {lp} 2>> {lp.replace('.jsonl', '.err')}; echo EXIT $? >> {lp.replace('.jsonl', '.err')}")
    subprocess.run(["tmux", "new-session", "-d", "-s", f"genesis-{name}", cmd], check=True)


def main():
    t0 = time.time()
    turns = {n: 0 for n in ROLES}
    last = {n: 0.0 for n in ROLES}
    log("start nadzorcy v3")
    while time.time() - t0 < RUN_HOURS * 3600:
        for name in ROLES:
            if alive(name) or time.time() - last[name] < COOLDOWN.get(name, 0):
                continue
            err = last_fatal(name)
            if err:
                log(f"BŁĄD KRYTYCZNY u {name}: {err} — zatrzymuję nadzorcę")
                return
            turns[name] += 1
            log(f"{name}: tura {turns[name]}")
            launch(name, turns[name])
            last[name] = time.time()
            time.sleep(STAGGER)
        time.sleep(30)
    log("koniec czasu nadzorcy")


if __name__ == "__main__":
    main()
