#!/usr/bin/env python3
"""Automat startu agentów po sprzątaniu świata. Sprawdza twarde warunki; jeśli spełnione: archiwizuje fazę 3,
czyści stan i uruchamia nadzorcę. Inaczej zapisuje powód i nic nie startuje. Log: logs/autostart.log."""
import importlib.util, json, os, shutil, subprocess, sys, time, traceback

G = "/opt/dlami/nvme/genesis"
ARC = "/opt/dlami/nvme/genesis_archive/2026-10-24_phase4"
LOG = f"{G}/logs/autostart.log"


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def alive(s):
    return subprocess.run(["tmux", "has-session", "-t", s], capture_output=True).returncode == 0


def run_tests():
    p = f"{G}/sandbox/test_organism.py"
    if not os.path.exists(p):
        return False, "brak sandbox/test_organism.py"
    sys.path[:0] = [G, f"{G}/sandbox"]
    spec = importlib.util.spec_from_file_location("test_organism", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    tests = [n for n in dir(m) if n.startswith("test_") and callable(getattr(m, n))]
    if not tests:
        return False, "brak funkcji test_*"
    failed = []
    for n in tests:
        try:
            getattr(m, n)()
        except Exception:
            failed.append(n + ": " + traceback.format_exc().splitlines()[-1])
    return (not failed), (f"{len(tests)} testów OK" if not failed else "nieudane: " + "; ".join(failed))


def room2(row):
    return row["sizes"][0]["summary"]["room_reach_fraction"][1]["mean"]


def calibration():
    final = None
    for l in open(f"{G}/sandbox/organism_calibration.jsonl"):
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            continue
        if "baseline_table" in d and (d.get("protocol") or {}).get("version") == "organism-v4":
            final = d  # końcowa tabela kalibracji (ostatnia wygrywa)
    if final:
        v = {k: t["summary"]["room_reach_fraction"][1]["mean"] for k, t in final["baseline_table"].items()}
        ok = v.get("control", 0) >= 0.5 and v.get("random", 1) <= 0.05 and v.get("braitenberg", 1) <= 0.05
        return ok, "pokój 2 (tabela końcowa): " + ", ".join(f"{k}={x:.3f}" for k, x in sorted(v.items())), v
    rows = {}
    for l in open(f"{G}/sandbox/organism_calibration.jsonl"):
        try:
            d = json.loads(l)
        except json.JSONDecodeError:
            continue
        prot = d.get("protocol") or {}
        if not isinstance(prot, dict) or prot.get("version") != "organism-v4" or d.get("interoception") is False:
            continue
        key = d.get("baseline") or ("control" if d.get("candidate", "").startswith("_calibration") else None)
        if key:
            rows[key] = d  # ostatni wpis wygrywa
    need = {"control", "random", "braitenberg"}
    if not need <= set(rows):
        return False, f"brak wpisów v3 dla: {sorted(need - set(rows))}", {}
    v = {k: room2(rows[k]) for k in rows}
    ok = v["control"] >= 0.5 and v["random"] <= 0.05 and v["braitenberg"] <= 0.05
    return ok, "pokój 2: " + ", ".join(f"{k}={x:.3f}" for k, x in sorted(v.items())), v


def archive_and_reset():
    os.makedirs(f"{ARC}/candidates", exist_ok=True); os.makedirs(f"{ARC}/shared", exist_ok=True)
    os.makedirs(f"{ARC}/logs", exist_ok=True); os.makedirs(f"{ARC}/sandbox", exist_ok=True)
    for d in ("theory", "biology", "audit", "experiments", "reports"):
        if os.path.exists(f"{G}/{d}"):
            shutil.move(f"{G}/{d}", f"{ARC}/{d}"); os.makedirs(f"{G}/{d}")
    for c in os.listdir(f"{G}/candidates"):
        if not c.startswith("_"):
            shutil.move(f"{G}/candidates/{c}", f"{ARC}/candidates/{c}")
    for f in ("board.jsonl", "claims.json", "cursors", "hypotheses.json", "ideas.jsonl", "cache"):
        if os.path.exists(f"{G}/shared/{f}"):
            shutil.move(f"{G}/shared/{f}", f"{ARC}/shared/{f}")
    shutil.copy(f"{G}/sandbox/leaderboard.jsonl", f"{ARC}/sandbox/leaderboard.jsonl")
    keep = [l for l in open(f"{G}/sandbox/leaderboard.jsonl") if l.strip() and json.loads(l).get("candidate", "").startswith("_")]
    open(f"{G}/sandbox/leaderboard.jsonl", "w").writelines(keep)
    for f in os.listdir(f"{G}/logs"):
        if f.startswith("v3_") and not f.startswith(("v3_gpu", "v3_nursery", "v3_sedzia")) or f in ("supervisor_v3.log", "maturity_asked.json", "last_tournament_pair.txt"):
            shutil.move(f"{G}/logs/{f}", f"{ARC}/logs/{f}")
    open(f"{G}/shared/hypotheses.json", "w").write("[]")
    open(f"{G}/shared/claims.json", "w").write("{}")
    for f in ("board.jsonl", "ideas.jsonl"):
        open(f"{G}/shared/{f}", "w").close()
    os.makedirs(f"{G}/shared/cursors", exist_ok=True); os.makedirs(f"{G}/shared/cache", exist_ok=True)


def main():
    log("automat czeka na koniec sprzątania świata")
    while alive("genesis-sedzia"):
        time.sleep(60)
    handoff = open(f"{G}/HANDOFF.md").read().splitlines()
    if "KONIEC" not in handoff:
        log("STOP: budowniczy nie dopisał KONIEC w HANDOFF.md; agenci nie startują"); return
    ok_t, msg_t = run_tests()
    log(f"testy: {msg_t}")
    ok_c, msg_c, v = calibration()
    log(f"kalibracja: {msg_c}")
    if not (ok_t and ok_c):
        log("STOP: warunki niespełnione (testy, random/odruch <=5% w pokoju 1, kontrola >=50%); agenci nie startują"); return
    archive_and_reset()
    subprocess.run([sys.executable, f"{G}/shared/board.py", "post", "sedzia", "all",
        "Sędzia (infrastruktura). Główny test: świat organizmów organism-v4 — jedno ciągłe życie w zagnieżdżonych pokojach, "
        "wejście: oko RGB i opcjonalnie poziom energii (--no-interoception), wyjście: ruch; świat nie daje nagrody. "
        "Uruchom: nice -n 15 .venv/bin/python sandbox/judge.py candidates/<nazwa> --organism --author <imię>. "
        "Kontrakt i opcje: sandbox/README.md. Kalibracja (poza rankingiem), odsetek światów, które przeszły pokój 1: "
        f"losowy ruch {v['random']:.1%}, odruch na sztywno {v['braitenberg']:.1%}, kontrola ucząca się z nagrodą (tylko kalibracja) "
        f"{v['control']:.1%}. Pole routine w wyniku to tylko obserwacja. Żłobek: judge.py --nursery."], cwd=G)
    subprocess.run(["tmux", "new-session", "-d", "-s", "genesis-supervisor",
                    f"cd {G} && python3 agents/supervisor_v3.py"], check=True)
    log("START: faza 3 zarchiwizowana, nadzorca i agenci uruchomieni")


if __name__ == "__main__":
    main()
