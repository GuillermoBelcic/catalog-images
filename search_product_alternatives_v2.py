import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

INPUT_JSON = "inspect_values_v2.json"
OUTPUT_JSON = "product_alternatives_v2.json"

PRODUCT_DOMAINS = [
    "amazon.es",
    "manomano.es",
    "leroymerlin.es",
    "brikum.com",
    "fixami.es",
    "toolnation.com",
    "contorion.es",
    "doitcenter.com.pa",
    "rs-online.com",
    "es.rs-online.com",
    "mouser.es",
    "farnell.com",
    "es.farnell.com",
    "obramat.es",
    "carrefour.es",
]

BLOCK_PATTERNS = [
    r"/s\?",
    r"/search",
    r"/collections",
    r"/productos/.+-p\.html$",
    r"/cat",
    r"/home/?$",
    r"/musica/?$",
    r"/papeleria/.+/rotuladores/?$",
]


def norm(text):
    return re.sub(r"\s+", " ", unescape(str(text or ""))).strip()


def fetch(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read().decode("utf-8", errors="ignore")
        final = r.geturl()
    return final, data


def bing_rss(query):
    url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query) + "&setlang=es"
    _, xml = fetch(url, timeout=20)
    root = ET.fromstring(xml)
    rows = []
    for item in root.findall("./channel/item"):
        rows.append(
            {
                "title": norm(item.findtext("title")),
                "link": norm(item.findtext("link")),
                "desc": norm(item.findtext("description")),
            }
        )
    return rows


def host(url):
    return urllib.parse.urlparse(url).netloc.lower()


def looks_like_product_url(url):
    low = url.lower()
    if any(dom in host(url) for dom in PRODUCT_DOMAINS):
        if any(re.search(p, low) for p in BLOCK_PATTERNS):
            return False
        if "amazon.es" in low and "/dp/" not in low and "/gp/product/" not in low:
            return False
        return True
    return False


def extract_image(page_url, html):
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'"image"\s*:\s*"([^"]+)"',
        r'"imageUrl"\s*:\s*"([^"]+)"',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.I)
        if m:
            return urllib.parse.urljoin(page_url, m.group(1).replace("\\/", "/"))
    return None


def words(name, desc):
    raw = re.findall(r"[A-Za-z0-9\+\-]+", f"{name} {desc}")
    banned = {"para", "con", "sin", "por", "the", "and", "del", "las", "los", "una", "uno", "tipo", "modelo"}
    return [w.lower() for w in raw if len(w) > 2 and w.lower() not in banned][:8]


def score_candidate(row, cand):
    bundle = f'{cand["title"]} {cand["desc"]} {cand["link"]}'.lower()
    pts = 0
    if looks_like_product_url(cand["link"]):
        pts += 25
    for w in words(row["Nombre"], row["Descripción"]):
        if w in bundle:
            pts += 4
    if any(token in bundle for token in ["pack", "pieza", "pulgadas", "mm", "vde", "18v", "cat6", "ffp2", "rj45"]):
        pts += 3
    return pts


def valid_page(row, link):
    try:
        final, html = fetch(link, timeout=20)
    except Exception:
        return None
    low = final.lower()
    if not looks_like_product_url(final):
        return None
    title_match = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    title = norm(title_match.group(1)) if title_match else ""
    bundle = f"{title} {final} {html[:30000]}".lower()
    match_count = sum(1 for w in words(row["Nombre"], row["Descripción"]) if w in bundle)
    if match_count < 2:
        return None
    img = extract_image(final, html)
    return {"ficha": final, "imagen": img, "title": title, "matches": match_count}


def build_queries(row):
    name = str(row["Nombre"]).strip()
    desc = str(row["Descripción"]).strip()
    part = str(row["Part Number"]).strip()
    manu = str(row["Fabricante"]).strip()
    queries = [
        f'"{name}" "{desc}"',
        f'"{name}" "{manu}" "{desc}"',
        f'"{desc}" "{manu}"',
        f'"{name}" "{part}"',
        f'"{desc}" site:amazon.es OR site:manomano.es OR site:leroymerlin.es',
    ]
    return queries


def main():
    with open(INPUT_JSON, encoding="utf-8") as f:
        raw = json.load(f)
    headers = raw[0]
    rows = [dict(zip(headers, r)) | {"_row": i} for i, r in enumerate(raw[1:], start=2)]
    results = []
    for row in rows:
        if row["_row"] < 21:
            continue
        best = None
        for q in build_queries(row):
            try:
                items = bing_rss(q)
            except Exception:
                continue
            ranked = sorted(items, key=lambda c: score_candidate(row, c), reverse=True)
            for cand in ranked[:6]:
                checked = valid_page(row, cand["link"])
                if checked:
                    best = {"_row": row["_row"], **checked}
                    break
            if best:
                break
            time.sleep(0.2)
        if best:
            results.append(best)
            print(row["_row"], best["ficha"], flush=True)
        time.sleep(0.1)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
