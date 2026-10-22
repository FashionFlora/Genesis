#!/usr/bin/env python3
"""Bank pomysłów GENESIS z automatyczną kontrolą powtórzeń (pamięć przeciw zapętlaniu się).

Każdy pomysł jest porównywany (TF-IDF, cosinus) ze WSZYSTKIM, co już widzieliśmy: rekordami literatury
(registry/areas/*.jsonl), wcześniejszymi pomysłami (shared/ideas.jsonl) i hipotezami (shared/hypotheses.json).
Zbyt podobny = odrzucony, z listą najbliższych odpowiedników.

  ideas.py check "<opis>"                       tylko sprawdź (nic nie zapisuje)
  ideas.py add <autor> "<nazwa>" "<opis>" "<technika>"   zapisz, jeśli wystarczająco nowy -> ID albo ODRZUCONY
  ideas.py list [autor]                         lista pomysłów
  ideas.py stats                                ile pomysłów, ile odrzuconych, rozkład technik
  ideas.py spark [n]                            losuje n par odległych pojęć jako zapalnik (domyślnie 3)
Opis: PO ANGIELSKU (rejestr literatury jest po angielsku), 2-5 zdań, sam MECHANIZM (co jest obiektem, jak się zmienia,
co go napędza), bez ogólników.
"""
import fcntl, glob, json, math, os, re, sys, time
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__))
G = os.path.dirname(D)
IDEAS = os.path.join(D, "ideas.jsonl")
REJECTED = os.path.join(D, "ideas_rejected.jsonl")
THRESHOLD = 0.30  # cosinus powyżej = powtórka
STOP = set("""a i w z na do o że to jest się nie od po przez dla jak oraz lub albo czy co gdy jego jej ich ten ta te tym tej
the of and to in is for on with by as that this be are an or from at it its which can each into using based""".split())


def tokens(t):
    w = [x for x in re.findall(r"[a-ząćęłńóśźż0-9]+", t.lower()) if len(x) > 2 and x not in STOP]
    return w + [f"{a}_{b}" for a, b in zip(w, w[1:])]  # słowa + bigramy


def corpus():
    docs = []
    for p in glob.glob(f"{G}/registry/areas/*.jsonl"):
        for l in open(p):
            try:
                r = json.loads(l)
            except json.JSONDecodeError:
                continue
            docs.append((f"lit:{r.get('id')}", r.get("name", ""),
                         " ".join(str(r.get(k, "")) for k in ("name", "principle", "learning_rule", "family"))))
    if os.path.exists(IDEAS):
        for l in open(IDEAS):
            r = json.loads(l)
            docs.append((f"idea:{r['id']}", r["name"], r["name"] + " " + r["desc"]))
    hp = os.path.join(D, "hypotheses.json")
    if os.path.exists(hp):
        for h in json.load(open(hp)):
            docs.append((f"hyp:{h['id']}", h["title"], h["title"] + " " + h["mechanism"]))
    return docs


def nearest(text, k=5):
    docs = corpus()
    toks = [Counter(tokens(d[2])) for d in docs]
    q = Counter(tokens(text))
    n = len(docs) + 1
    df = Counter(t for c in toks + [q] for t in c)
    idf = {t: math.log(n / df[t]) + 1 for t in df}

    def vec(c):
        v = {t: (1 + math.log(f)) * idf[t] for t, f in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        return {t: x / norm for t, x in v.items()}

    qv = vec(q)
    sims = [(sum(qv.get(t, 0) * x for t, x in vec(c).items()), d) for c, d in zip(toks, docs)]
    return sorted(sims, key=lambda s: -s[0])[:k]


def show(near):
    for s, (ref, name, _) in near:
        print(f"   {s:.2f}  {ref}  {name}")


cmd, *a = sys.argv[1:] or ["help"]
if cmd == "check" and len(a) == 1:
    near = nearest(a[0])
    top = near[0][0] if near else 0
    print("POWTÓRKA" if top >= THRESHOLD else "NOWY", f"(max podobieństwo {top:.2f}, próg {THRESHOLD})")
    show(near)
elif cmd == "add" and len(a) == 4:
    author, name, desc, tech = a
    with open(IDEAS, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        near = nearest(name + " " + desc)
        top = near[0][0] if near else 0
        f.seek(0)
        nid = f"I{sum(1 for _ in f) + 1:03d}"
        rec = {"id": nid, "t": time.strftime("%m-%d %H:%M"), "author": author, "name": name, "desc": desc,
               "technique": tech, "max_sim": round(top, 3), "nearest": [d[0] for _, d in near[:3]]}
        if top >= THRESHOLD:
            with open(REJECTED, "a") as r:
                r.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"ODRZUCONY: za podobny ({top:.2f} >= {THRESHOLD}). Najbliższe:"); show(near)
            print("Nie przerabiaj kosmetycznie. Zmień założenie, obiekt albo dynamikę.")
        else:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{nid} zapisany (max podobieństwo {top:.2f})"); show(near[:3])
elif cmd == "list":
    for l in open(IDEAS) if os.path.exists(IDEAS) else []:
        r = json.loads(l)
        if not a or r["author"] == a[0]:
            print(f"{r['id']}  {r['author']:15} sim={r['max_sim']:.2f}  [{r['technique']}]  {r['name']}")
elif cmd == "spark":
    import random
    pool = """immune clonal selection|mycelium nutrient routing|ant pheromone evaporation|river delta formation|crystal growth defects|
    market auction|tax and subsidy|language creole formation|viral horizontal gene transfer|prion templated misfolding|
    slime mold tube reinforcement|bone remodeling under load|sleep deprivation|apoptosis|tumor angiogenesis|
    termite mound ventilation|quorum sensing|epigenetic marks|glial support cells|blood-brain barrier|hormone cascade|
    plate tectonics|glacier erosion|forest succession after fire|predator-prey cycles|parasitic manipulation|
    symbiogenesis (mitochondria)|cell differentiation|stem cell niche|scar tissue|placebo effect|immune memory|
    jazz improvisation|legal precedent|currency inflation|bureaucratic procedure|tool-making culture|myth and ritual|
    phase transition|spin glass frustration|percolation threshold|topological defects|renormalization|entropy production|
    sheaf gluing of local data|category of open games|tropical algebra|p-adic distance|hypergraph rewriting|
    cellular automaton rule 110|knot invariants|persistent homology|non-commutative probability|fractional calculus|
    origami folding|bridge truss load paths|traffic jam waves|power grid frequency balancing|compiler garbage collection|
    version control merges|peer review|apprenticeship|forgetting curve|childhood play|dreaming|boredom|surprise|pain""".split("|")
    pool = [x.strip() for x in pool if x.strip()]
    for _ in range(int(a[0]) if a else 3):
        print(" x ".join(random.sample(pool, 2)))
elif cmd == "stats":
    ok = [json.loads(l) for l in open(IDEAS)] if os.path.exists(IDEAS) else []
    rej = [json.loads(l) for l in open(REJECTED)] if os.path.exists(REJECTED) else []
    print(f"przyjęte {len(ok)}, odrzucone {len(rej)}")
    print("techniki (przyjęte):", dict(Counter(r["technique"] for r in ok)))
    print("autorzy:", dict(Counter(r["author"] for r in ok)))
else:
    print(__doc__)
