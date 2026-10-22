#!/usr/bin/env python3
"""Wspólna tablica agentów GENESIS (append-only, bezpieczna przy równoległym zapisie).

  board.py post  <od> <do|all> "<wiadomość>"     wyślij wiadomość
  board.py read  <ja>                             nowe wiadomości do mnie / do all (od ostatniego odczytu)
  board.py claim <ja> <method_id>                 zajmij metodę; jeśli zajęta, wypisze właściciela
  board.py claims                                 lista zajętych metod
"""
import fcntl, json, os, sys, time

D = os.path.dirname(os.path.abspath(__file__))
BOARD, CLAIMS, CURSORS = (os.path.join(D, n) for n in ("board.jsonl", "claims.json", "cursors"))


def locked(path, mode):
    f = open(path, mode)
    fcntl.flock(f, fcntl.LOCK_EX)
    return f


def post(frm, to, msg):
    with locked(BOARD, "a") as f:
        f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "from": frm, "to": to, "msg": msg}, ensure_ascii=False) + "\n")
    print("wysłano")


def read(me):
    os.makedirs(CURSORS, exist_ok=True)
    cur = os.path.join(CURSORS, me)
    start = int(open(cur).read() or 0) if os.path.exists(cur) else 0
    lines = open(BOARD).readlines() if os.path.exists(BOARD) else []
    new = [json.loads(l) for l in lines[start:]]
    shown = [m for m in new if m["to"] in ("all", me) and m["from"] != me]
    for m in shown:
        print(f"[{m['t']}] {m['from']} -> {m['to']}: {m['msg']}")
    if not shown:
        print("(brak nowych wiadomości)")
    open(cur, "w").write(str(len(lines)))


def claim(me, mid):
    if not os.path.exists(CLAIMS):
        open(CLAIMS, "w").write("{}")
    with locked(CLAIMS, "r+") as f:
        c = json.load(f)
        owner = c.setdefault(mid.lower(), me)
        f.seek(0); f.truncate(); json.dump(c, f, ensure_ascii=False, indent=0)
    print("OK, twoja" if owner == me else f"ZAJĘTA przez {owner} — pomiń albo napisz do niego")


cmd, *a = sys.argv[1:] or ["help"]
if cmd == "post" and len(a) == 3: post(*a)
elif cmd == "read" and len(a) == 1: read(*a)
elif cmd == "claim" and len(a) == 2: claim(*a)
elif cmd == "claims": print(open(CLAIMS).read() if os.path.exists(CLAIMS) else "{}")
else: print(__doc__)
