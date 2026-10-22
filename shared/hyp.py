#!/usr/bin/env python3
"""Rejestr hipotez GENESIS (deterministyczny, bezpieczny przy równoległym zapisie).

  hyp.py add <autor> "<tytuł>" "<mechanizm>" "<przewidywanie>" "<co by obaliło>" [pliki]   -> nowe ID
  hyp.py list [status]                     lista (opcjonalnie tylko o danym statusie)
  hyp.py show <id>                         szczegóły z historią
  hyp.py status <id> <ja> <status> "<uzasadnienie / ścieżka do wyników / źródła>"
  hyp.py note <id> <ja> "<notatka>"
Statusy: proposed critiqued testing supported refuted known parked
"""
import fcntl, json, os, sys, time

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hypotheses.json")
STATUSES = {"proposed", "critiqued", "testing", "supported", "refuted", "known", "parked"}


def load_locked():
    if not os.path.exists(P):
        open(P, "w").write("[]")
    f = open(P, "r+")
    fcntl.flock(f, fcntl.LOCK_EX)
    return f, json.load(f)


def save(f, data):
    f.seek(0); f.truncate(); json.dump(data, f, ensure_ascii=False, indent=1); f.close()


def now():
    return time.strftime("%m-%d %H:%M")


def find(data, hid):
    for h in data:
        if h["id"] == hid.upper():
            return h
    sys.exit(f"Brak hipotezy {hid}")


cmd, *a = sys.argv[1:] or ["help"]
if cmd == "add" and len(a) >= 5:
    f, data = load_locked()
    hid = f"H{len(data) + 1:03d}"
    data.append({"id": hid, "author": a[0], "title": a[1], "mechanism": a[2], "prediction": a[3], "falsifier": a[4],
                 "files": a[5] if len(a) > 5 else "", "status": "proposed",
                 "history": [{"t": now(), "who": a[0], "status": "proposed", "text": "dodana"}]})
    save(f, data); print(hid)
elif cmd == "list":
    data = json.load(open(P)) if os.path.exists(P) else []
    for h in data:
        if not a or h["status"] == a[0]:
            print(f"{h['id']}  [{h['status']:9}]  {h['author']:15}  {h['title']}")
elif cmd == "show" and len(a) == 1:
    h = find(json.load(open(P)), a[0])
    for k in ("id", "title", "author", "status", "mechanism", "prediction", "falsifier", "files"):
        print(f"{k}: {h[k]}")
    for e in h["history"]:
        print(f"  [{e['t']}] {e['who']} -> {e['status']}: {e['text']}")
elif cmd in ("status", "note") and len(a) >= 3:
    f, data = load_locked()
    h = find(data, a[0])
    st = a[2] if cmd == "status" else h["status"]
    if st not in STATUSES:
        f.close(); sys.exit(f"Nieznany status {st}; dozwolone: {' '.join(sorted(STATUSES))}")
    h["status"] = st
    h["history"].append({"t": now(), "who": a[1], "status": st, "text": a[3] if cmd == "status" else a[2]})
    save(f, data); print(f"{h['id']} -> {st}")
else:
    print(__doc__)
