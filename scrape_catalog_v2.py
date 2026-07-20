import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape


INPUT_JSON = "inspect_values_v2.json"
OUTPUT_JSON = "scrape_results_v2.json"


OFFICIAL_DOMAINS = {
    "super-ego": ["super-ego.es", "super-ego.tools"],
    "palmera": ["palmeraherramientas.com"],
    "stanley": ["stanleyworks.es", "stanleytools.es", "stanley1913.com", "stanleytools.com"],
    "knipex": ["knipex.com", "knipex.de", "knipex-tools.com"],
    "jokari": ["jokari.de", "jokari.com"],
    "intercable": ["intercable-tools.com", "intercable.com"],
    "bellota": ["bellota.com"],
    "stabila": ["stabila.com"],
    "bosch professional": ["bosch-professional.com"],
    "bosch": ["bosch-pt.com", "bosch-professional.com", "bosch-homecomfort.com", "boschtools.com"],
    "facom": ["facom.com"],
    "alpen": ["alpen-drills.com", "alpenmaykestag.com"],
    "makita": ["makita.es", "makita.com", "makita.ae", "makita.fr", "makita-groupe.fr"],
    "starrett": ["starrett.com"],
    "wera": ["wera.de", "wera.com"],
    "rubi": ["rubi.com"],
    "prysmian": ["prysmian.com", "prysmianclub.com"],
    "top cable": ["topcable.com"],
    "excel": ["excel-networking.com", "excel-networking.com/en"],
    "televés": ["televes.com"],
    "unex": ["unex.net"],
    "3m": ["3m.com"],
    "courbi": ["courbi.com"],
    "tekox": ["tekox.com"],
    "wago": ["wago.com"],
    "bm group": ["bmspa.com", "bm-group.com"],
    "hellermanntyton": ["hellermanntyton.com"],
    "simon": ["simon.es", "simon-electric.com"],
    "legrand": ["legrand.es", "legrand.com"],
    "niessen": ["niessen.es", "new.abb.com"],
    "schneider electric": ["se.com", "schneider-electric.es", "schneider-electric.com"],
    "solera": ["solera.es"],
    "brennenstuhl": ["brennenstuhl.es", "brennenstuhl.com"],
    "tayg": ["tayg.com"],
    "d-link": ["dlink.com", "eu.dlink.com"],
    "velcro": ["velcro.com"],
    "spax": ["spax.com"],
    "fischer": ["fischer.es", "fischer-international.com"],
    "bralo": ["bralo.com"],
    "sapiselco": ["sapiselco.com"],
    "quilosa": ["quilosa.com"],
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
    "salvelox": ["cederroth.com"],
    "telesteps": ["telesteps.com"],
    "igloo": ["igloocoolers.com"],
    "edding": ["edding.com"],
    "brother": ["brother.es", "brother.eu"],
}

FALLBACK_DOMAINS = [
    "rs-online.com",
    "es.rs-online.com",
    "farnell.com",
    "es.farnell.com",
    "mouser.es",
    "mouser.com",
    "amazon.es",
    "amazon.com",
    "manomano.es",
    "leroymerlin.es",
    "obrmat.es",
    "obramat.es",
]


def slug(text):
    return str(text or "").strip().lower()


def clean_text(text):
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def part_variants(part):
    raw = str(part).strip()
    variants = {raw.lower()}
    compact = re.sub(r"[\s\"'.,]", "", raw).lower()
    if compact:
        variants.add(compact)
    dashed = raw.replace(" ", "-").lower()
    variants.add(dashed)
    nodash = re.sub(r"[-_/]", "", raw).lower()
    if nodash:
        variants.add(nodash)
    return [v for v in variants if v]


def fetch(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        final_url = r.geturl()
        ctype = r.headers.get("Content-Type", "")
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    return final_url, ctype, text


def bing_rss(query):
    url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query) + "&setlang=es"
    final_url, ctype, xml = fetch(url, timeout=20)
    root = ET.fromstring(xml)
    items = []
    for item in root.findall("./channel/item"):
        items.append(
            {
                "title": clean_text(item.findtext("title")),
                "link": clean_text(item.findtext("link")),
                "description": clean_text(item.findtext("description")),
            }
        )
    return items


def domain_of(url):
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""


def is_preferred_domain(url, manufacturer):
    netloc = domain_of(url)
    if not netloc:
        return False
    official = OFFICIAL_DOMAINS.get(slug(manufacturer), [])
    for dom in official:
        if dom in netloc:
            return True
    return False


def is_fallback_domain(url):
    netloc = domain_of(url)
    return any(dom in netloc for dom in FALLBACK_DOMAINS)


def contains_part(text, part):
    hay = clean_text(text).lower()
    return any(v in hay for v in part_variants(part))


def contains_manufacturer(text, manufacturer):
    man = slug(manufacturer)
    hay = clean_text(text).lower()
    return man in hay


def extract_image(page_url, html):
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'"image"\s*:\s*"([^"]+)"',
        r'"imageUrl"\s*:\s*"([^"]+)"',
    ]
    for pattern in patterns:
        m = re.search(pattern, html, re.I)
        if m:
            img = m.group(1).replace("\\/", "/")
            return urllib.parse.urljoin(page_url, img)
    return None


def score_candidate(candidate, row):
    score = 0
    link = candidate["link"]
    title = candidate["title"]
    desc = candidate["description"]
    if is_preferred_domain(link, row["Fabricante"]):
        score += 50
    elif is_fallback_domain(link):
        score += 20
    if contains_part(" ".join([link, title, desc]), row["Part Number"]):
        score += 40
    if contains_manufacturer(" ".join([link, title, desc]), row["Fabricante"]):
        score += 20
    return score


def inspect_candidate(link, row):
    try:
        final_url, ctype, html = fetch(link, timeout=20)
    except Exception as e:
        return {"ok": False, "reason": f"fetch failed: {e}"}
    text = " ".join([final_url, html[:50000]])
    part_ok = contains_part(text, row["Part Number"])
    manufacturer_ok = contains_manufacturer(text, row["Fabricante"]) or is_preferred_domain(final_url, row["Fabricante"])
    image = extract_image(final_url, html)
    ok = part_ok and manufacturer_ok
    return {
        "ok": ok,
        "url": final_url,
        "image": image,
        "part_ok": part_ok,
        "manufacturer_ok": manufacturer_ok,
        "official": is_preferred_domain(final_url, row["Fabricante"]),
        "fallback": is_fallback_domain(final_url),
    }


def build_queries(row):
    manufacturer = str(row["Fabricante"]).strip()
    part = str(row["Part Number"]).strip()
    desc = str(row["Descripción"]).strip()
    name = str(row["Nombre"]).strip()
    official = OFFICIAL_DOMAINS.get(slug(manufacturer), [])
    queries = []
    if official:
        for dom in official[:2]:
            queries.append(f'site:{dom} "{part}" "{manufacturer}"')
            queries.append(f'site:{dom} "{part}"')
    queries.append(f'"{manufacturer}" "{part}"')
    queries.append(f'"{manufacturer}" "{part}" "{name}"')
    queries.append(f'"{manufacturer}" "{part}" "{desc}"')
    return queries[:6]


def process_row(row):
    for query in build_queries(row):
        try:
            results = bing_rss(query)
        except Exception:
            time.sleep(1)
            continue
        ranked = sorted(results, key=lambda c: score_candidate(c, row), reverse=True)
        for candidate in ranked[:4]:
            link = candidate["link"]
            if not link.startswith("http"):
                continue
            info = inspect_candidate(link, row)
            if info.get("ok"):
                return {
                    "status": "ok",
                    "ficha": info["url"],
                    "imagen": info["image"],
                    "official": info["official"],
                    "query": query,
                }
        time.sleep(0.5)
    return {
        "status": "needs_review",
        "comment": "No se pudo validar con suficiente certeza una coincidencia exacta de fabricante y Part Number.",
    }


def main():
    start_row = int(sys.argv[1]) if len(sys.argv) > 1 else 21
    end_row = int(sys.argv[2]) if len(sys.argv) > 2 else 9999

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        rows = json.load(f)

    headers = rows[0]
    data_rows = []
    for idx, values in enumerate(rows[1:], start=2):
        row = dict(zip(headers, values))
        row["_row"] = idx
        data_rows.append(row)

    pending = [
        row
        for row in data_rows
        if start_row <= row["_row"] <= end_row and not row.get("URL ficha") and not row.get("URL imagen")
    ]

    results = []
    for row in pending:
        result = process_row(row)
        result["_row"] = row["_row"]
        result["Nombre"] = row["Nombre"]
        result["Fabricante"] = row["Fabricante"]
        result["Part Number"] = row["Part Number"]
        results.append(result)
        print(f'row {row["_row"]}: {result["status"]} - {row["Fabricante"]} {row["Part Number"]}', flush=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        time.sleep(0.5)


if __name__ == "__main__":
    sys.exit(main())
