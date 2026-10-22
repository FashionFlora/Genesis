#!/usr/bin/env python3
"""Wspólne narzędzie literaturowe GENESIS (zamiast wbudowanego web search, który przez bramkę nie działa).
Wspólna kolejka (limit zapytań na serwis dla WSZYSTKICH agentów) + wspólny cache — nie omijaj go curl-em po tych samych serwisach.

  lit.py search "<zapytanie>" [n]     wyszukiwarka www (DuckDuckGo HTML) -> tytuł, URL
  lit.py arxiv  "<zapytanie>" [n]     wyszukiwarka arXiv -> arXiv ID, tytuł
  lit.py fetch  <url> [max_znaków]    strona/PDF jako tekst (arXiv: użyj arxiv.org/abs/<id> lub arxiv.org/html/<id>)
  lit.py github "<zapytanie>" [n]     repozytoria GitHub -> nazwa, gwiazdki, opis
"""
import fcntl, hashlib, html, json, os, re, subprocess, sys, time, urllib.parse, urllib.request

D = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(D, "cache")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
MIN_GAP = {"duckduckgo.com": 4.0, "arxiv.org": 3.0, "api.github.com": 2.0}  # sekundy między zapytaniami (globalnie)


def _wait_turn(host):
    gap = next((g for h, g in MIN_GAP.items() if host.endswith(h)), 1.0)
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, f".rate_{host}"), "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        last = float(f.read() or 0)
        time.sleep(max(0.0, last + gap - time.time()))
        f.seek(0); f.truncate(); f.write(str(time.time()))


def get(url, binary=False):
    key = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest())
    if os.path.exists(key):
        data = open(key, "rb").read()
    else:
        _wait_turn(urllib.parse.urlparse(url).hostname or "")
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                data = urllib.request.urlopen(req, timeout=40).read()
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 503) and attempt < 2:
                    time.sleep(15 * (attempt + 1)); continue
                sys.exit(f"HTTP {e.code} dla {url}")
            except Exception as e:
                sys.exit(f"Błąd pobierania {url}: {e}")
        open(key, "wb").write(data)
    return data if binary else data.decode("utf-8", "replace")


def text_of(page):
    page = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?i)<(br|p|div|h[1-6]|li|tr)[^>]*>", "\n", page)
    t = html.unescape(re.sub(r"<[^>]+>", " ", page))
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", t)).strip()


def search(q, n=8):
    page = get("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
    for m in list(re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S))[:int(n)]:
        u = m.group(1)
        if "uddg=" in u:
            u = urllib.parse.unquote(re.search(r"uddg=([^&]+)", u).group(1))
        print(f"- {text_of(m.group(2))}\n  {u}")


def arxiv(q, n=8):
    page = get("https://arxiv.org/search/?searchtype=all&order=&query=" + urllib.parse.quote(q))
    for blk in page.split('<li class="arxiv-result">')[1:int(n) + 1]:
        aid = re.search(r"arxiv.org/abs/([\w.]+)", blk)
        title = re.search(r'<p class="title is-5 mathjax">(.*?)</p>', blk, re.S)
        print(f"- {aid.group(1) if aid else '?'}  {text_of(title.group(1)) if title else '?'}")


def fetch(url, limit=40000):
    if url.lower().endswith(".pdf") or "/pdf/" in url:
        key = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest() + ".pdf")
        if not os.path.exists(key):
            open(key, "wb").write(get(url, binary=True))
        try:
            out = subprocess.run(["pdftotext", "-layout", key, "-"], capture_output=True, text=True).stdout
        except FileNotFoundError:
            try:
                from pypdf import PdfReader
                out = "\n".join(p.extract_text() or "" for p in PdfReader(key).pages)
            except ImportError:
                sys.exit("Brak pdftotext/pypdf. Dla arXiv użyj arxiv.org/html/<id>, albo uruchom przez .venv/bin/python z pypdf.")
    else:
        out = text_of(get(url))
    print(out[:int(limit)])
    if len(out) > int(limit):
        print(f"\n[... ucięte, całość {len(out)} znaków — podaj większy max_znaków]")


def github(q, n=8):
    d = json.loads(get("https://api.github.com/search/repositories?per_page=%d&q=%s" % (int(n), urllib.parse.quote(q))))
    for r in d.get("items", []):
        print(f"- {r['full_name']}  ★{r['stargazers_count']}  {r['html_url']}\n  {(r.get('description') or '')[:150]}")


cmds = {"search": search, "arxiv": arxiv, "fetch": fetch, "github": github}
if len(sys.argv) < 3 or sys.argv[1] not in cmds:
    sys.exit(__doc__)
cmds[sys.argv[1]](*sys.argv[2:])
