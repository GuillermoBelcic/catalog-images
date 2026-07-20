import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

INPUT_JSON = "inspect_values_v2.json"
OUTPUT_JSON = "scrape_results_v2_secondpass.json"

RECOGNIZED_DOMAINS = [
    "amazon.es", "amazon.com", "es.rs-online.com", "rs-online.com", "farnell.com", "es.farnell.com",
    "mouser.es", "mouser.com", "obrmat.es", "obramat.es", "manomano.es", "bricolemar.com",
    "suministros-intec.com", "ferrovicmar.com", "electrocomponentes.es", "rubix.com", "sotel.de",
    "toolnation.com", "contorion.es", "fixami.es", "ifixit.com", "kcprofessional.com", "leroymerlin.es",
    "kcprofessional.com", "bd.com", "wolfcraft.com", "bauhaus.es", "medid.es", "brikum.com",
]

OFFICIAL_HINTS = {
    "bahco": ["bahco.com"],
    "stanley": ["stanley1913.com", "stanleyworks.es", "stanleytools.com"],
    "knipex": ["knipex.com", "knipex-tools.com"],
    "jokari": ["jokari.de"],
    "intercable": ["intercable-tools.com"],
    "bellota": ["bellota.com"],
    "stabila": ["stabila.com"],
    "bosch professional": ["bosch-professional.com"],
    "bosch": ["bosch-pt.com", "bosch-professional.com"],
    "facom": ["facom.com"],
    "alpen": ["alpen-drills.com"],
    "makita": ["makita.es", "makita.com"],
    "starrett": ["starrett.com"],
    "wera": ["wera.de", "wera.com"],
    "rubi": ["rubi.com"],
    "excel": ["excel-networking.com"],
    "televés": ["televes.com"],
    "3m": ["3m.com"],
    "unex": ["unex.net"],
    "wago": ["wago.com"],
    "hellermanntyton": ["hellermanntyton.com"],
    "simon": ["simon.es"],
    "legrand": ["legrand.es", "legrand.com"],
    "niessen": ["niessen.es", "new.abb.com"],
    "schneider electric": ["se.com", "schneider-electric.com"],
    "brennenstuhl": ["brennenstuhl.es", "brennenstuhl.com"],
    "fischer": ["fischer.es", "fischer.de"],
    "bralo": ["bralo.com"],
    "soudal": ["soudal.com"],
    "pattex": ["pattex.es", "pattex.com"],
    "wd-40": ["wd40.com", "wd40.es"],
    "crc": ["crcindustries.com", "crcindustries.eu"],
    "würth": ["wurth.es", "wurth.com"],
    "fluke": ["fluke.com"],
    "fluke networks": ["flukenetworks.com"],
    "testboy": ["testboy.de"],
    "delta plus": ["deltaplus.eu"],
    "petzl": ["petzl.com"],
    "telesteps": ["telesteps.com"],
    "edding": ["edding.com"],
    "brother": ["brother.es", "store.brother.es"],
}

SKIP_ROWS = {50, 51, 52, 53, 72, 73, 108, 110}

def slug(s):
    return str(s or "").strip().lower()

def textnorm(s):
    return re.sub(r"\s+", " ", unescape(str(s or ""))).strip()

def variants(part):
    p = str(part).strip()
    vals = {p.lower(), p.replace(" ", "").lower(), p.replace(" ", "-").lower(), p.replace("-", "").replace(" ", "").lower()}
    return [v for v in vals if v]

def domain(url):
    return urllib.parse.urlparse(url).netloc.lower()

def is_recognized(url, man):
    d = domain(url)
    for dom in OFFICIAL_HINTS.get(slug(man), []):
        if dom in d:
            return "official"
    for dom in RECOGNIZED_DOMAINS:
        if dom in d:
            return "distributor"
    return ""

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        final = r.geturl()
    return final, data.decode("utf-8", errors="ignore")

def bing_rss(query):
    url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query) + "&setlang=es"
    _, xml = fetch(url, timeout=20)
    root = ET.fromstring(xml)
    items = []
    for item in root.findall("./channel/item"):
        items.append({
            "title": textnorm(item.findtext("title")),
            "link": textnorm(item.findtext("link")),
            "description": textnorm(item.findtext("description")),
        })
    return items

def part_in(text, part):
    hay = textnorm(text).lower()
    return any(v in hay for v in variants(part))

def man_in(text, man):
    return slug(man) in textnorm(text).lower()

def desc_words(desc):
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9\+\-]+", str(desc))]
    return [w for w in words if len(w) > 3][:6]

def extract_image(page_url, html):
    for pat in [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'"image"\s*:\s*"([^"]+)"',
        r'"imageUrl"\s*:\s*"([^"]+)"',
    ]:
        m = re.search(pat, html, re.I)
        if m:
            return urllib.parse.urljoin(page_url, m.group(1).replace("\\/", "/"))
    return None

def good_candidate(row, cand):
    bundle = " ".join([cand["title"], cand["description"], cand["link"]])
    rel = is_recognized(cand["link"], row["Fabricante"])
    if not rel:
        return False, ""
    if not part_in(bundle, row["Part Number"]):
        return False, ""
    # accept if manufacturer appears or description has 2 keywords
    if man_in(bundle, row["Fabricante"]):
        return True, rel
    hits = sum(1 for w in desc_words(row["Descripción"]) if w in bundle.lower())
    if hits >= 2:
        return True, rel
    return False, ""

def inspect(row, link):
    try:
        final, html = fetch(link, timeout=20)
    except Exception:
        return None
    body = " ".join([final, html[:90000]])
    if not part_in(body, row["Part Number"]):
        return None
    rel = is_recognized(final, row["Fabricante"])
    if not rel:
        return None
    img = extract_image(final, html)
    return {"ficha": final, "imagen": img, "source_type": rel}

def queries(row):
    man = str(row["Fabricante"]).strip()
    part = str(row["Part Number"]).strip()
    desc = str(row["Descripción"]).strip()
    q = [
        f'"{man}" "{part}"',
        f'"{part}" "{desc}"',
        f'"{man}" "{part}" "{row["Nombre"]}"',
        f'"{part}" "{man}" site:amazon.es',
        f'"{part}" "{man}" site:rs-online.com OR site:es.rs-online.com OR site:mouser.es OR site:es.farnell.com',
    ]
    return q

def main():
    with open(INPUT_JSON, encoding="utf-8") as f:
        rows = json.load(f)
    headers = rows[0]
    data = [dict(zip(headers, r)) | {"_row": i} for i, r in enumerate(rows[1:], start=2)]
    results = []
    for row in data:
        if row["_row"] < 21 or row["_row"] in SKIP_ROWS:
            continue
        found = None
        for q in queries(row):
            try:
                hits = bing_rss(q)
            except Exception:
                continue
            for cand in hits[:6]:
                ok, rel = good_candidate(row, cand)
                if not ok:
                    continue
                inspected = inspect(row, cand["link"])
                if inspected:
                    found = inspected | {"_row": row["_row"], "status": "ok"}
                    break
            if found:
                break
            time.sleep(0.3)
        if found:
            results.append(found)
            print("ok", row["_row"], row["Fabricante"], row["Part Number"], flush=True)
        time.sleep(0.2)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    sys.exit(main())
