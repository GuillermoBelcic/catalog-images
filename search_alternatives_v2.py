import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

INPUT_JSON = "inspect_values_v2.json"
OUTPUT_JSON = "alternative_results_v2.json"

RECOGNIZED = [
    "knipex.com", "knipex-tools.com", "bahco.com", "bosch-professional.com", "bosch-pt.com",
    "makita.com", "makita.es", "wera.de", "wiha.com", "wago.com", "unex.net", "se.com",
    "schneider-russia.com", "fischer.es", "fischer.de", "fischer.it", "fischer.com.tr",
    "stanleyworks.es", "stanleytools.com", "manomano.es", "leroymerlin.es", "brother.co.uk",
    "brother.ca", "brothermobilesolutions.com", "fluke.com", "brennenstuhl.es", "televes.com",
    "petzl.com", "edding.com", "3m.com", "hellermanntyton.com", "soudal.com", "pattex.es",
    "wd40.com", "crcindustries.com", "deltaplus.eu", "stabila.com", "rubi.com", "facom.com",
    "jokari.de", "bellota.com", "bralo.com", "spax.com", "excel-networking.com",
]

SKIP = {50, 51, 52, 53}

def norm(text):
    return re.sub(r"\s+", " ", unescape(str(text or ""))).strip()

def fetch(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", errors="ignore")
        final = r.geturl()
    return final, body

def bing_rss(query):
    url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query) + "&setlang=es"
    _, xml = fetch(url)
    root = ET.fromstring(xml)
    items = []
    for item in root.findall("./channel/item"):
        items.append(
            {
                "title": norm(item.findtext("title")),
                "link": norm(item.findtext("link")),
                "desc": norm(item.findtext("description")),
            }
        )
    return items

def domain(url):
    return urllib.parse.urlparse(url).netloc.lower()

def recognized(url):
    d = domain(url)
    return any(x in d for x in RECOGNIZED)

def words(text):
    return [w.lower() for w in re.findall(r"[A-Za-z0-9\+\-]+", norm(text)) if len(w) > 2]

def score(row, item):
    bundle = " ".join([item["title"], item["desc"], item["link"]]).lower()
    pts = 0
    if recognized(item["link"]):
        pts += 10
    for w in words(row["Nombre"])[:4]:
        if w in bundle:
            pts += 5
    for w in words(row["Descripción"])[:6]:
        if w in bundle:
            pts += 2
    man = str(row["Fabricante"]).strip().lower()
    if man and man in bundle:
        pts += 6
    return pts

def queries(row):
    return [
        f'"{row["Nombre"]}" "{row["Descripción"]}"',
        f'"{row["Nombre"]}" "{row["Fabricante"]}"',
        f'"{row["Nombre"]}" herramienta',
        f'"{row["Nombre"]}" producto',
    ]

def main():
    with open(INPUT_JSON, encoding="utf-8") as f:
        rows = json.load(f)
    headers = rows[0]
    data = [dict(zip(headers, r)) | {"_row": i} for i, r in enumerate(rows[1:], start=2)]
    out = []
    for row in data:
        if row["_row"] < 21 or row["_row"] in SKIP:
            continue
        best = None
        for q in queries(row):
            try:
                items = bing_rss(q)
            except Exception:
                continue
            ranked = sorted(items, key=lambda it: score(row, it), reverse=True)
            for item in ranked[:5]:
                if score(row, item) < 14:
                    continue
                best = {
                    "_row": row["_row"],
                    "ficha": item["link"],
                    "title": item["title"],
                    "score": score(row, item),
                }
                break
            if best:
                break
            time.sleep(0.2)
        if best:
            out.append(best)
            print(best["_row"], best["ficha"], flush=True)
        time.sleep(0.1)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    sys.exit(main())
