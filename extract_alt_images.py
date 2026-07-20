import json
import re
import urllib.request
from urllib.parse import urljoin

INPUT = "alternative_results_v2.json"
OUTPUT = "alternative_results_with_images_v2.json"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read().decode("utf-8", errors="ignore")
        final = r.geturl()
    return final, body

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
            return urljoin(page_url, m.group(1).replace("\\/", "/"))
    return None

with open(INPUT, encoding="utf-8") as f:
    rows = json.load(f)

out = []
for row in rows:
    result = dict(row)
    try:
        final, html = fetch(row["ficha"])
        result["ficha"] = final
        result["imagen"] = extract_image(final, html)
        result["ok"] = True
    except Exception as e:
        result["ok"] = False
        result["error"] = str(e)
    out.append(result)
    print(result["_row"], result.get("imagen"), flush=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
