#!/usr/bin/env python3
"""Nadzorca v3: 4 agentów na codex3 (api.artemcmd.dev, gpt-6.1-sol), świeża sesja co turę.
Pamięć agenta = jego pliki + HANDOFF.md. Stop: po RUN_HOURS albo przy błędzie braku środków / autoryzacji.
Log: logs/supervisor_v3.log, logi agentów: logs/v3_<nazwa>.jsonl (dopisywane)."""
import json, os, subprocess, time

G = "/opt/dlami/nvme/genesis"
CODEX = os.path.expanduser("~/.local/bin/codex3")
RUN_HOURS = 10**6  # bez limitu czasu (decyzja użytkownika 2026-10-23): do wyczerpania salda, stop na FATAL
STAGGER = 30
COOLDOWN = {"krytyk": 300}
PAUSED_WHEN_FROZEN = {"krytyk", "eksperymentator"}
MAX_CONCURRENT = 8  # nowy klucz: płatność za tokeny, bez limitu zapytań na minutę  # min. sekund między startami tur (krytyk ma krótkie tury i zjada limit 10/min)
FLAGS = "--json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check"
FATAL = ("403", "401", "402", "insufficient", "expired", "paid time", "зарезерв", "invalid x-api-key")

ROLES = {
    "odkrywca_life": ("theory/theorist_life/",
        "Jesteś odkrywcą. Twój punkt wyjścia: ŻYCIE — zasoby, metabolizm, podział, śmierć, ekologia procesów. Szukaj "
        "zasady, z której wzrost, przycinanie, uczenie, pamięć i eksploracja wynikają same. Gdy coś przeżyje Twoją "
        "symulację, zapisz to jako candidates/<nazwa>/principle.py i oceń sędzią. TWOJA WYSPA: życie i zasoby."),
    "odkrywca_axioms": ("theory/theorist_axioms/",
        "Jesteś odkrywcą. Twój punkt wyjścia: jakie warunki musi spełniać każdy system, który sam się buduje i uczy bez "
        "końca, i jaka zasada z nich wynika. Gdy coś przeżyje Twoją symulację, zapisz to jako "
        "candidates/<nazwa>/principle.py i oceń sędzią. TWOJA WYSPA: zasady wyprowadzone z warunków (aksjomatów)."),
    "odkrywca_agency": ("theory/theorist_agency/",
        "Jesteś odkrywcą. Twój punkt wyjścia: DZIAŁANIE. Skąd system, bez nagrody z zewnątrz, wie, co chce zrobić? "
        "Wewnętrzna nagroda, którą system sam wytwarza (jak u człowieka), jest dozwolona; zewnętrzny cel wpisany ręcznie "
        "nie. Szukaj zasady, z której naraz wynikają przewidywanie i działanie. Sprawdzaj w małych światach z działaniem, "
        "potem w Snake (candidates/<nazwa>/principle.py z act). TWOJA WYSPA: zasady działania."),
    "odkrywca_growth": ("theory/theorist_growth/",
        "Jesteś odkrywcą. Twoja wyspa: WZROST. System startuje z kilku jednostek, bez gotowej tabeli wszystkich par; "
        "jednostki i połączenia mają powstawać tam, gdzie świat tego wymaga, i zanikać, gdy przestają być potrzebne — "
        "z zasady, nie z osobnych reguł wzrostu i przycinania. Mierz liczbę istniejących jednostek i połączeń w czasie, "
        "koszt pamięci względem rozmiaru, jakość predykcji, i to samo przy różnych rozmiarach świata."),
    "odkrywca_dynamics": ("theory/theorist_dynamics/",
        "Jesteś odkrywcą. Twoja wyspa: FIZYKA UKŁADÓW DYNAMICZNYCH. Szukaj lokalnej dynamiki, z której same wynikają "
        "uczenie, pamięć, struktura i docelowo działanie. Sprawdzaj w symulacjach, potem w sędzim. Pułapka: dynamika, "
        "która tylko ładnie wygląda, ale niczego nie przewiduje."),
    "biolog": ("biology/",
        "Jesteś biologiem. Wydobywasz z neuronauki i biologii rozwoju ZASADY, które odkrywcy mogą przekuć w mechanizmy, "
        "i prowadzisz biology/PRINCIPLES.md. Najpierw odpowiadasz na pytania z tablicy. Konkretnie, z liczbami i "
        "źródłami otwartymi przez lit.py, ze wskazówką, jak to przełożyć na system cyfrowy. Pisz na tablicy tylko nowe "
        "fakty i odpowiedzi na pytania."),
    "krytyk": ("audit/",
        "Jesteś krytykiem. Zakładasz, że „nowy” pomysł już istnieje, a wynik może być artefaktem, dopóki nie wykażesz "
        "inaczej. Sprawdzasz hipotezy w hyp.py, THEORY.md odkrywców i każdy nowy wpis w sandbox/leaderboard.jsonl: prior "
        "art, przemycone mechanizmy, ukryte progi, czytanie plików, czy test naprawdę sprawdza to, co twierdzi. Konkretne "
        "uwagi wysyłaj autorom przez tablicę. Przy kandydatach z act sprawdzaj, czy działanie wynika z zasady, a nie z "
        "wpisanej strategii, i czy nie koduje celu gry (np. zasób na sztywno powiązany z jabłkami). Wewnętrzny napęd, "
        "który system sam wytwarza, jest dozwolony."),
    "eksperymentator": ("experiments/, reports/eksperymentator.md",
        "Jesteś eksperymentatorem. Niezależnie replikujesz NOWE wyniki odkrywców (hyp.py: proposed/testing, nowe wpisy na "
        "tablicy). Nie powtarzaj testu, którego wynik już jest w Twoim HANDOFF.md. Pomagasz przenieść zasady do formatu "
        "sędziego (candidates/<nazwa>/principle.py, PARAMS) i uruchamiasz sędziego. Wyniki ustawiasz w hyp.py. Nie "
        "przeszukuj wartości parametrów pod wynik na tablicy: to strojenie, nie zasada."),
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
        if c == "_baseline_online":  # uczciwy baseline szczebla 1 (pozostałe _baseline_* to wzorce oszustw)
            base = max(base, s)
        elif c.startswith("_baseline") or c in disqualified():
            continue
        elif not best or s > best[1]:
            best = (c, s, d.get("author", "?"))
    if not best:
        return f"Tablica wyników: żadnego kandydata, baseline {base:.1f}, próg szczebla 1 to 1.25× baseline."
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


def at_snake_door(name):
    """Kandydaci autora, którzy przeszli szczebel 2 i stoją przed Snake'iem (bez dyskwalifikacji)."""
    out, p = set(), f"{G}/sandbox/leaderboard.jsonl"
    for l in open(p) if os.path.exists(p) else []:
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            continue
        c = str(d.get("candidate", ""))
        if d.get("author") == name and (d.get("highest_passed_level") or 0) >= 2 and c not in disqualified():
            out.add(c)
    return sorted(out)


def maturity_block(name):
    """Test dojrzałości zasady: czy wynika z niej działanie (Snake bez nagrody). Nie osobny front."""
    asked_p = f"{G}/logs/maturity_asked.json"
    asked = json.load(open(asked_p)) if os.path.exists(asked_p) else {}
    # pytanie pada raz na kandydata; odpowiedzi z nocy (HANDOFF) już są dla obecnych kandydatów
    door = [c for c in at_snake_door(name) if c not in asked.get(name, [])]
    if name.startswith("odkrywca"):
        door = [c for c in door if not c.startswith("coactivity")]
    if not door:
        return ""
    asked.setdefault(name, []).extend(door[:3])
    json.dump(asked, open(asked_p, "w"), indent=1)
    return (f"\nTEST DOJRZAŁOŚCI: Twój kandydat {', '.join(door[:3])} przeszedł szczebel 2 i stoi przed Snake'iem bez "
            "funkcji act. Raz w tej turze zadaj sobie pytanie: czy z TEJ SAMEJ zasady da się wyprowadzić działanie, bez "
            "nagrody zewnętrznej i bez wpisanej strategii (wewnętrzna, samowytworzona jest dozwolona)?Jeśli tak, dodaj act wynikające z zasady i oceń sędzią. Jeśli nie, zapisz "
            "w HANDOFF.md uczciwie, czego zasadzie brakuje, żeby działać. Obie odpowiedzi są wartościowe. Nie wiąż "
            "wewnętrznych zasobów na sztywno z jabłkami ani z długością węża — to nagroda w przebraniu.")


def island_candidates(name, k=3):
    """Wyspa (wzorzec FunSearch): tylko kandydaci tego odkrywcy, bez monokultury coactivity_*."""
    return [t for t in top_candidates(50) if t[1] == name and not t[0].startswith("coactivity")][:k]


def evolution_block(name, turn):
    """Ewolucja na wyspach (FunSearch / AlphaEvolve): co druga tura mutuje kandydatów z WŁASNEJ wyspy;
    co czwarta tura wolno skrzyżować z najlepszym kandydatem spoza wyspy. Chroni przed przedwczesną zbieżnością."""
    top = island_candidates(name) if turn % 4 != 0 else top_candidates()
    if not top and turn % 4 != 0:
        return ("\nWYSPA PUSTA: nie masz jeszcze na tablicy kandydata ze swojej wyspy. Przenieś swoją najlepszą zasadę "
                "do candidates/<nazwa>/principle.py i oceń ją sędzią, nawet jeśli przegrywa z liderem.")
    if not top:
        return ("\nPRIORYTET TEJ TURY: na tablicy wyników nie ma jeszcze żadnego prawdziwego kandydata. Przenieś swoją "
                "najlepszą obecną zasadę do candidates/<nazwa>/principle.py i oceń ją sędzią, nawet jeśli jest niedoskonała. "
                "Bez kandydatów na tablicy nie ma czego ulepszać.")
    lst = "; ".join(f"{c} ({a}, {s:.1f}, kod: candidates/{c}/)" for c, a, s in top)
    if turn % 2 == 0:
        where = ("KRZYŻÓWKA MIĘDZY WYSPAMI (raz na 4 tury): najlepsi na całej tablicy" if turn % 4 == 0
                 else "TURA EWOLUCJI NA TWOJEJ WYSPIE: Twoi kandydaci")
        return (f"\n{where}: {lst}. W tej turze stwórz NOWEGO kandydata jako mutację albo krzyżówkę. Zmiana samej "
                "wartości parametru NIE jest nowym kandydatem. Cel: mniej ręcznych reguł, "
                "więcej zjawisk wynikających z jednej zasady, większa odporność. Zapisz go jako candidates/<nowa_nazwa>/ "
                "z plikiem PARENTS.txt (rodzice + co zmieniłeś i dlaczego) i oceń sędzią. Przed zapisem sprawdź, czy to "
                "nie powtórka: `python3 shared/ideas.py check \"<opis mechanizmu po angielsku>\"`.")
    return (f"\nTwoja wyspa: {lst}. W tej turze rozwijasz swój własny kierunek; w następnej będzie tura ewolucji "
            "na Twojej wyspie.")


def prompt(name, turn=1):
    own, role = ROLES[name]
    handoff = own.split(",")[0].strip().rstrip("/") + "/HANDOFF.md"
    frozen = os.path.exists(f"{G}/sandbox/FROZEN")
    extra = evolution_block(name, turn) if name.startswith("odkrywca") and not frozen else ""
    if name != "krytyk":
        extra += maturity_block(name)
    tp = f"{G}/logs/last_tournament_pair.txt"
    pair = "|".join(sorted(c for c, _, _ in top_candidates(2)))
    if name == "krytyk" and len(top_candidates(2)) == 2 and pair != (open(tp).read() if os.path.exists(tp) else ""):
        open(tp, "w").write(pair)  # turniej tylko dla nowej pary czołowych kandydatów
        (c1, a1, _), (c2, a2, _) = top_candidates(2)
        extra = (f"\nTURNIEJ: porównaj parami dwóch czołowych kandydatów, {c1} ({a1}) i {c2} ({a2}), pod kątem tego, czego "
                 "sędzia nie mierzy: który jest bardziej fundamentalny (ile zjawisk wynika z zasady, a ile jest wpisanych), "
                 "bardziej nowy względem literatury i ma lepsze perspektywy skalowania. Werdykt z uzasadnieniem dopisz jako "
                 "jedną linię JSON do audit/tournament.jsonl i wyślij autorom. To uzupełnienie wyniku sędziego, nie jego zamiennik.")
    if name.startswith("odkrywca"):
        extra += ("\nŚLEPE ULICZKI: dla kierunku, nad którym pracujesz, w HANDOFF.md trzymaj trzy linie: KIERUNEK, KRYTERIUM "
                  "PORZUCENIA (jaka metryka, jaki próg) i BUDŻET (najwyżej 3 tury). Co turę zapisz, czy główna metryka się "
                  "poprawiła. Po budżecie bez postępu odłóż kierunek z opisem dlaczego (hyp.py status ... parked) i weź inny. "
                  "Sprawdź też, czy Twój test w ogóle MOŻE pokazać efekt (np. pamięć nie pokaże oszczędności, jeśli pierwsze "
                  "nauczenie trwa 1 krok).")
    return (f"Jesteś agentem GENESIS `{name}`. Przeczytaj AGENTS.md. {role}\n\n"
            f"Twoje pliki: {own}. Twoja pamięć z poprzednich tur: {handoff} (jeśli nie istnieje, przeczytaj swoje THEORY.md, "
            f"JOURNAL.md lub raport). Potem `python3 shared/board.py read {name}`.\n{leader()}{extra}\n"
            f"Pracuj tę turę konkretnie (kilka kroków: myśl → kod → uruchom → wnioski). Na koniec nadpisz {handoff} "
            "(najwyżej 25 linii) i zakończ turę. Następna tura zacznie się od świeżej sesji.")


START_OFFSETS = {}  # rozmiar logów przy starcie nadzorcy: stare błędy (np. wygasły klucz) nie zatrzymują nowego startu


def last_fatal(name):
    """Błąd krytyczny (brak środków, wygasły klucz, zła autoryzacja) zapisany OD STARTU nadzorcy."""
    p = f"{G}/logs/v3_{name}.jsonl"
    if not os.path.exists(p):
        return None
    with open(p, errors="replace") as f:
        f.seek(START_OFFSETS.get(name, 0))
        tail = f.readlines()[-30:]
    for l in reversed(tail):
        if '"turn.completed"' in l:
            return None
        if ('"error"' in l or "turn.failed" in l) and any(x in l for x in FATAL):
            return l[:300]
    return None


BUDGET_USD = float("inf")  # bez limitu (decyzja użytkownika 2026-10-23); wydatek tylko logowany
PRICE = {"in": 2.0, "cached": 0.10, "out": 10.0}  # gpt-6.1-sol, $ za 1M tokenów


def spend_usd():
    """Wydatek od startu nadzorcy, z rzeczywistego zużycia (turn.completed) we wszystkich logach agentów."""
    total = 0.0
    for n in ROLES:
        p = f"{G}/logs/v3_{n}.jsonl"
        if not os.path.exists(p):
            continue
        with open(p, errors="replace") as f:
            f.seek(START_OFFSETS.get(n, 0))
            for l in f:
                if '"turn.completed"' not in l:
                    continue
                try:
                    u = json.loads(l)["usage"]
                except (json.JSONDecodeError, KeyError):
                    continue
                cached = u.get("cached_input_tokens", 0)
                total += ((u.get("input_tokens", 0) - cached) * PRICE["in"] + cached * PRICE["cached"]
                          + u.get("output_tokens", 0) * PRICE["out"]) / 1e6
    return total


def news_since(t):
    """Czy od czasu t pojawiło się coś do oceny: nowe wpisy sędziego albo zmiany w rejestrze hipotez."""
    paths = [f"{G}/sandbox/leaderboard.jsonl", f"{G}/shared/hypotheses.json"]
    return any(os.path.exists(p) and os.path.getmtime(p) > t for p in paths)


def stop_all(reason):
    for n in ROLES:
        subprocess.run(["tmux", "kill-session", "-t", f"genesis-{n}"], capture_output=True)
    log(f"ZATRZYMANO WSZYSTKICH AGENTÓW: {reason}")


def launch(name, turn=1):
    lp = f"{G}/logs/v3_{name}.jsonl"
    with open(f"{G}/logs/v3_{name}.prompt.txt", "w") as f:
        f.write(prompt(name, turn))
    cmd = (f'cd {G} && nice -n 15 {CODEX} exec {FLAGS} -C {G} "$(cat {G}/logs/v3_{name}.prompt.txt)" '
           f"< /dev/null >> {lp} 2>> {lp.replace('.jsonl', '.err')}; echo EXIT $? >> {lp.replace('.jsonl', '.err')}")
    subprocess.run(["tmux", "new-session", "-d", "-s", f"genesis-{name}", cmd], check=True)


def main():
    """Rotacja: najwyżej MAX_CONCURRENT agentów naraz (limit bramki 10 zapytań/min na wszystkich);
    kolejny start dostaje ten, kto najdłużej czeka."""
    t0 = time.time()
    turns = {n: 0 for n in ROLES}
    last = {n: 0.0 for n in ROLES}
    for n in ROLES:
        p = f"{G}/logs/v3_{n}.jsonl"
        START_OFFSETS[n] = os.path.getsize(p) if os.path.exists(p) else 0
    log("start nadzorcy v3 (rotacja, max %d naraz)" % MAX_CONCURRENT)
    last_spend_log = 0.0
    while time.time() - t0 < RUN_HOURS * 3600:
        running = [n for n in ROLES if alive(n)]
        spent = spend_usd()
        if spent >= BUDGET_USD:
            stop_all(f"osiągnięty budżet przebiegu: {spent:.0f} $ z {BUDGET_USD:.0f} $")
            return
        if time.time() - last_spend_log >= 1800:
            log(f"wydatek od startu: {spent:.2f} $")
            last_spend_log = time.time()
        for n in running:  # agent w trakcie tury może utknąć na ponowieniach po wygaśnięciu klucza
            err = last_fatal(n)
            if err:
                stop_all(f"błąd krytyczny u {n}: {err}")
                return
        ready = [n for n in ROLES if n not in running
                 and time.time() - last[n] >= COOLDOWN.get(n, 0)
                 and not (n in PAUSED_WHEN_FROZEN and os.path.exists(f"{G}/sandbox/FROZEN"))
                 and not (n == "krytyk" and not news_since(last[n]))]
        for name in sorted(ready, key=lambda n: last[n])[:max(0, MAX_CONCURRENT - len(running))]:
            err = last_fatal(name)
            if err:
                stop_all(f"błąd krytyczny u {name}: {err}")
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
