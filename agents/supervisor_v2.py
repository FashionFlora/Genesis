#!/usr/bin/env python3
"""Nadzorca zespołu v2 (5 agentów) GENESIS na Codexie (codex2 = gpt-6.1-sol przez moduleapi).
- start: agent bez logu -> uruchamia go z agents/prompts/<nazwa>.txt (rozłożone w czasie)
- agent skończył przed celem -> `codex exec resume <thread_id>` z poleceniem kontynuacji (max MAX_ROUNDS)
- błąd 429 / brak tunelu -> czeka i ponawia BEZ zużywania rund
Log: logs/supervisor_v2.log, stan: logs/supervisor_cx_state.json. Agent = sesja tmux genesis-<nazwa>, log logs/cx_<nazwa>.jsonl."""
import glob, json, os, shlex, subprocess, time

G = "/opt/dlami/nvme/genesis"
CODEX2 = os.path.expanduser("~/.local/bin/codex2")
MAX_ROUNDS = 40
AREA_TARGET = 15
STATE = f"{G}/logs/supervisor_v2_state.json"
STAGGER = 25  # s między startami, żeby nie dostać 429

AREAS = []
TIMED = {"eksperymentator": 8.0, "odkrywca_axioms": 8.0, "odkrywca_life": 8.0, "biolog": 8.0, "krytyk": 8.0}  # godziny
ORDER = ["eksperymentator", "odkrywca_axioms", "odkrywca_life", "biolog", "krytyk"]
FLAGS = "--json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check"


def log(msg):
    with open(f"{G}/logs/supervisor_v2.log", "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def logpath(name):
    return f"{G}/logs/v2_{name}.jsonl"


def alive(name):
    return subprocess.run(["tmux", "has-session", "-t", f"genesis-{name}"], capture_output=True).returncode == 0


def tunnel_ok():
    return subprocess.run(["bash", "-c", "exec 3<>/dev/tcp/127.0.0.1/8443"], capture_output=True).returncode == 0


def last_events(name):
    tid, last_err = None, None
    for line in open(logpath(name), errors="replace"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "thread.started":
            tid = d.get("thread_id")
        elif d.get("type") in ("error", "turn.failed"):
            last_err = json.dumps(d)
        elif d.get("type") == "turn.completed":
            last_err = None
    return tid, last_err


def n_records(area):
    p = f"{G}/registry/areas/{area}.jsonl"
    return sum(1 for l in open(p) if l.strip()) if os.path.exists(p) else 0


def status(name, st):
    """(cel osiągnięty?, polecenie kontynuacji)"""
    read = f"Najpierw `python3 shared/board.py read {name}` i odpowiedz na pytania do Ciebie."
    if name in AREAS:
        n = n_records(name)
        return n >= AREA_TARGET, (
            f"Orkiestrator: w registry/areas/{name}.jsonl jest {n} rekordów, cel to co najmniej {AREA_TARGET} — nie kończ. "
            f"{read} Potem kolejne metody (lit.py arxiv/search/fetch/github). Brak pełnego tekstu nie jest powodem do pominięcia "
            "(rekord z abstraktu, verified_from: abstract). Wypełniaj self_building i brain_relevance. Na końcu zaktualizuj raport.")
    if name == "experiment_engine_unused":
        done = os.path.exists(f"{G}/reports/task_E1.md") and len(glob.glob(f"{G}/experiments/*/result.json")) >= 2 \
            and st["rounds"] >= 1
        return done, (
            f"Orkiestrator: kontynuuj E1. {read} Wymagane: harness z reward-free i obsługą zmiennej architektury, "
            "result.json z FAKTYCZNYCH przebiegów (random + baseline reward-free), porównanie z artykułem, reports/task_E1.md. "
            "Potem testuj kandydatów z tablicy (teoretycy, agenci literatury) — krótkie przebiegi.")
    hours = TIMED[name]
    el = (time.time() - st["start"]) / 3600
    return el >= hours, (
        f"Orkiestrator: kontynuuj (minęło {el:.1f} h z ~{hours:.0f} h) — nie kończ. {read} {leader()} "
        + {"krytyk": "Przejrzyj `hyp.py list` i THEORY.md odkrywców, a także nowe wpisy w sandbox/leaderboard.jsonl: czy wynik nie został naciągnięty (ukryte progi, przemycone mechanizmy, czytanie plików). Między przeglądami `sleep 120`.",
           "eksperymentator": "Testuj hipotezy z hyp.py i ustawiaj supported/refuted z wynikami. Pomagaj odkrywcom przenieść ich zasady do formatu sędziego (candidates/<nazwa>/principle.py, PARAMS) i uruchamiaj `.venv/bin/python sandbox/judge.py candidates/<nazwa>`.",
           "biolog": "Odpowiedz na pytania z tablicy, przeczytaj nowe hipotezy i THEORY.md odkrywców; szukaj w biologii, jak uczenie i zmienność (mutacja) mogłyby wynikać z tej samej zasady co wzrost i śmierć."}
          .get(name, "Szukaj JEDNEJ zasady, z której wzrost, przycinanie, uczenie, pamięć i eksploracja wynikają same (krytyk: w H003 uczenie i mutacja są wciąż osobne). Gdy kandydat przeżyje Twoją symulację, zapisz go jako candidates/<nazwa>/principle.py (kontrakt w sandbox/README.md, parametry w PARAMS) i oceń: `.venv/bin/python sandbox/judge.py candidates/<nazwa>`. Aktualizuj JOURNAL.md i THEORY.md."))


def leader():
    """Najlepszy kandydat (bez baseline'ów) z tablicy wyników sędziego."""
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
        elif not best or s > best[1]:
            best = (c, s, d.get("author", "?"))
    if not best:
        return (f"Tablica wyników sędziego: jeszcze żadnego kandydata, najlepszy baseline ma {base:.1f}. "
                "Bądź pierwszy z kandydatem, który go pobije.")
    return (f"Tablica wyników: lider {best[0]} ({best[2]}) z wynikiem {best[1]:.1f}, najlepszy baseline {base:.1f}. "
            "Pobij lidera prostszą i bardziej odporną zasadą albo znajdź głębszy fundament.")


def launch(name, resume_tid=None, prompt=None):
    lp = logpath(name)
    if resume_tid:
        cmd = f"{CODEX2} exec resume {resume_tid} {shlex.quote(prompt)} {FLAGS}"
    else:
        cmd = f'{CODEX2} exec {FLAGS} -C {G} "$(cat {G}/agents/prompts_v2/{name}.txt)"'
    full = f"cd {G} && nice -n 15 {cmd} < /dev/null >> {lp} 2>> {lp.replace('.jsonl', '.err')}; echo EXIT $? >> {lp.replace('.jsonl', '.err')}"
    subprocess.run(["tmux", "new-session", "-d", "-s", f"genesis-{name}", full], check=True)


def main():
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    log("start nadzorcy")
    while True:
        if not tunnel_ok():
            log("brak tunelu 8443 — czekam"); time.sleep(120); continue
        for name in ORDER:
            st = state.setdefault(name, {"rounds": 0, "start": None, "done": False, "wait_until": 0})
            if st["done"] or alive(name) or time.time() < st["wait_until"]:
                continue
            if not os.path.exists(logpath(name)):
                st["start"] = time.time()
                log(f"{name}: start")
                launch(name)
                json.dump(state, open(STATE, "w"), indent=1)
                time.sleep(STAGGER)
                continue
            tid, err = last_events(name)
            done, prompt = status(name, st)
            if done:
                st["done"] = True; log(f"{name}: cel osiągnięty"); continue
            if not tid:
                log(f"{name}: brak thread_id — start od nowa"); launch(name); time.sleep(STAGGER); continue
            if st.pop("pending_free", False):
                launch(name, tid, "Orkiestrator: poprzednia tura przerwana błędem bramki. Kontynuuj od miejsca, w którym przerwałeś. " + prompt)
                log(f"{name}: wznowienie po błędzie bramki"); time.sleep(STAGGER); continue
            if err and ("429" in err or "Too Many" in err or "connect" in err.lower()):
                st["wait_until"] = time.time() + 300
                st["pending_free"] = True
                log(f"{name}: błąd bramki ({err[:80]}) — wznowię za 5 min bez zużywania rundy")
                continue
            if st["rounds"] >= MAX_ROUNDS:
                st["done"] = True; log(f"{name}: limit {MAX_ROUNDS} wznowień — zostawiam"); continue
            st["rounds"] += 1
            log(f"{name}: wznowienie {st['rounds']}/{MAX_ROUNDS}")
            launch(name, tid, prompt)
            time.sleep(STAGGER)
        json.dump(state, open(STATE, "w"), indent=1)
        if all(state.get(n, {}).get("done") for n in ORDER):
            log("wszyscy agenci zakończeni"); return
        time.sleep(60)


if __name__ == "__main__":
    main()
