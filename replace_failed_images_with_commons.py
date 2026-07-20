import csv
import json
import socket
import ssl
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE_CSV = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\version que funciona - Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes_partnumbers_bonitos_solo_fallidas_backend_safe.csv"
)
SOURCE_AUDIT = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\backend_image_audit.csv"
)
OUTPUT_CSV = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\Base de Datos de Materiales y Herramientas_V2 - imagenes_reales_backend_safe.csv"
)
SELECTION_REPORT = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\commons_image_selection_report.csv"
)
OUTPUT_AUDIT = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\backend_image_audit_imagenes_reales.csv"
)

BACKEND_UA = "BackendImageAuditor/1.0 (+no-browser; no-cookies; no-js)"
COMMONS_UA = "CatalogCommonsFinder/1.0 (+catalog image enrichment)"
READ_BYTES = 4096

ANTI_BOT_MARKERS = [
    "just a moment",
    "cloudflare",
    "akamai",
    "captcha",
    "access denied",
    "bot verification",
    "please enable javascript",
    "enable cookies",
    "challenge-platform",
    "perimeterx",
    "datadome",
]

BAD_TITLE_MARKERS = [
    "icon",
    "logo",
    "symbol",
    "abstract",
    "diagram",
    "pictogram",
    "clipart",
    "schema",
    "sign",
]

SEARCH_TERMS = {
    "PWT0000002": ["cordless drill driver", "power drill", "cordless screwdriver"],
    "PWT0000007": ["oscillating multi tool", "oscillating tool", "multitool power tool"],
    "LGT0000001": ["work light flashlight", "led flashlight", "portable work light"],
    "BAT0000003": ["battery charger", "power tool battery charger"],
    "HDT0000004": ["adjustable wrench", "adjustable spanner"],
    "HDT0000006": ["box wrench set", "tubular wrench", "double box wrench"],
    "HDT0000007": ["combination wrench set", "spanner set"],
    "HDT0000008": ["combination pliers", "lineman pliers"],
    "HDT0000009": ["diagonal cutting pliers", "side cutters"],
    "HDT0000010": ["needle nose pliers", "long nose pliers"],
    "HDT0000011": ["wire stripper", "automatic wire stripper"],
    "HDT0000012": ["rj45 crimping tool", "modular crimping tool"],
    "HDT0000013": ["crimping pliers insulated terminals", "terminal crimping tool"],
    "HDT0000014": ["utility knife", "box cutter"],
    "HDT0000015": ["electrician scissors", "wire scissors"],
    "HDT0000016": ["hammer wooden handle", "carpenter hammer"],
    "HDT0000017": ["rubber mallet", "soft faced mallet"],
    "MEA0000001": ["spirit level", "bubble level"],
    "MEA0000002": ["laser level", "cross line laser level"],
    "MEA0000003": ["tape measure"],
    "MEA0000004": ["carpenter square", "try square"],
    "MEA0000005": ["scriber tool", "marking scribe"],
    "ACC0000001": ["metal drill bits set", "hss drill bits"],
    "ACC0000002": ["wood drill bits set", "wood drill bit"],
    "ACC0000003": ["masonry drill bits set", "concrete drill bit"],
    "ACC0000004": ["sds plus drill bits", "sds drill bit"],
    "ACC0000005": ["hole saw set", "bi metal hole saw"],
    "ACC0000006": ["screwdriver bit set", "driver bits"],
    "HDT0000018": ["magnetic nut driver", "hex nut setter"],
    "ACC0000007": ["metal cutting disc", "cutoff wheel"],
    "ACC0000008": ["diamond blade", "segmented diamond saw blade"],
    "ACC0000009": ["sandpaper sheets", "abrasive paper"],
    "CBL0000001": ["blue electrical wire spool", "blue copper wire"],
    "CBL0000002": ["black electrical wire spool", "black copper wire"],
    "CBL0000003": ["flexible electrical cable", "power cable roll"],
    "CBL0000004": ["electrical cable roll", "power cable coil"],
    "CBL0000005": ["ethernet cable reel", "cat6 cable reel"],
    "CBL0000006": ["coaxial cable spool", "coaxial cable roll"],
    "ELC0000002": ["black electrical tape"],
    "ELC0000003": ["colored electrical tape"],
    "ELC0000004": ["corrugated conduit roll", "electrical conduit coil"],
    "ELC0000005": ["corrugated conduit roll", "electrical conduit coil"],
    "ELC0000006": ["pvc cable trunking", "cable duct"],
    "ELC0000007": ["terminal block strip", "connector strip"],
    "ELC0000008": ["lever wire connector", "electrical connector"],
    "ELC0000009": ["lever wire connector", "wire connector"],
    "ELC0000010": ["insulated terminals assortment", "electrical terminals"],
    "ELC0000011": ["heat shrink tubing assortment", "heat shrink tubes"],
    "ELI0000001": ["schuko socket outlet", "electrical wall outlet"],
    "ELI0000002": ["surface mount socket outlet", "wall socket"],
    "ELI0000003": ["light switch"],
    "ELI0000004": ["double light switch"],
    "ELI0000005": ["two way light switch", "wall switch"],
    "ELI0000006": ["drywall electrical box", "flush mount box"],
    "ELI0000007": ["junction box"],
    "ELI0000008": ["power strip"],
    "ELI0000009": ["extension cable reel", "extension cord reel"],
    "ELI0000010": ["residual current circuit breaker", "rcd breaker"],
    "ELI0000011": ["miniature circuit breaker", "circuit breaker"],
    "NET0000001": ["rj45 keystone jack", "ethernet keystone"],
    "NET0000002": ["rj45 wall outlet", "network wall plate"],
    "NET0000003": ["ethernet patch cable", "cat6 patch cable"],
    "NET0000004": ["ethernet patch cable", "cat6 patch cable"],
    "NET0000005": ["patch panel network", "ethernet patch panel"],
    "NET0000006": ["cable management panel", "rack cable organizer"],
    "CBM0000001": ["hook and loop cable ties roll", "velcro cable tie roll"],
    "FIX0000001": ["wood screws"],
    "FIX0000002": ["self tapping screws", "sheet metal screws"],
    "FIX0000003": ["lag screw", "hex head screw"],
    "FIX0000004": ["nylon wall plug", "plastic anchor"],
    "FIX0000005": ["nylon wall plug", "plastic anchor"],
    "FIX0000006": ["nylon wall plug", "plastic anchor"],
    "FIX0000007": ["chemical anchor cartridge", "injection resin"],
    "FIX0000008": ["threaded rod"],
    "FIX0000009": ["hex nuts", "nuts fastener"],
    "FIX0000010": ["flat washers", "washers fastener"],
    "FIX0000011": ["blind rivets", "pop rivets"],
    "FIX0000012": ["cable clips", "wire clips"],
    "SEA0000001": ["silicone sealant cartridge", "white silicone sealant"],
    "SEA0000002": ["bathroom silicone sealant", "sanitary silicone"],
    "SEA0000003": ["construction adhesive cartridge", "mounting adhesive"],
    "SEA0000004": ["expanding foam can", "polyurethane foam spray"],
    "MNT0000001": ["lubricant spray can", "maintenance spray"],
    "MNT0000002": ["isopropyl alcohol bottle"],
    "MNT0000003": ["contact cleaner spray"],
    "MNT0000004": ["cleaning rags roll", "shop towels roll"],
    "TST0000004": ["non contact voltage tester", "voltage detector pen"],
    "TST0000005": ["wall scanner", "cable detector"],
    "ELI0000012": ["socket tester", "plug tester"],
    "TST0000006": ["network cable tester", "ethernet cable tester"],
    "PPE0000001": ["work gloves"],
    "PPE0000002": ["safety glasses"],
    "PPE0000003": ["safety helmet", "hard hat"],
    "PPE0000004": ["high visibility vest", "reflective vest"],
    "PPE0000005": ["hearing protection earmuffs", "earmuffs"],
    "PPE0000006": ["ffp2 respirator mask", "dust mask"],
    "FAD0000001": ["first aid kit"],
    "ACS0000001": ["telescopic ladder"],
    "STO0000001": ["toolbox"],
    "STO0000002": ["parts organizer box", "small parts organizer"],
    "STO0000003": ["tool backpack"],
    "STO0000004": ["folding hand truck", "folding trolley"],
    "SIT0000001": ["water cooler dispenser", "portable water dispenser"],
    "MRK0000002": ["label tape cassette", "laminated label tape"],
}


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

    http_error_301 = urllib.request.HTTPRedirectHandler.http_error_302
    http_error_302 = urllib.request.HTTPRedirectHandler.http_error_302
    http_error_303 = urllib.request.HTTPRedirectHandler.http_error_302
    http_error_307 = urllib.request.HTTPRedirectHandler.http_error_302
    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_302


def build_opener():
    return urllib.request.build_opener(NoRedirectHandler())


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower().strip()


def detect_antibot(content_type: str, sample: bytes, headers: dict[str, str]) -> bool:
    header_blob = " ".join(f"{k}:{v}" for k, v in headers.items()).lower()
    sample_text = sample.decode("utf-8", errors="ignore").lower()
    blob = f"{content_type.lower()} {header_blob} {sample_text}"
    return any(marker in blob for marker in ANTI_BOT_MARKERS)


def audit_url(opener, url: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": BACKEND_UA,
            "Accept": "image/*,application/octet-stream;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
    )

    try:
        with opener.open(req, timeout=20) as response:
            status_code = getattr(response, "status", None) or response.getcode()
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            body_sample = response.read(READ_BYTES)
            anti_bot = detect_antibot(content_type, body_sample, dict(response.headers.items()))

            error_summary = ""
            downloadable = "yes"

            if status_code < 200 or status_code >= 300:
                downloadable = "no"
                error_summary = f"unexpected status {status_code}"
            elif final_url != url:
                downloadable = "no"
                error_summary = "redirected"
            elif not content_type.lower().startswith("image/"):
                downloadable = "no"
                error_summary = "content-type is not image/*"
            elif anti_bot:
                downloadable = "no"
                error_summary = "anti-bot or challenge detected"
            elif not body_sample:
                downloadable = "no"
                error_summary = "empty response body"

            return {
                "downloadableByBackend": downloadable,
                "statusCode": str(status_code),
                "contentType": content_type,
                "finalUrl": final_url,
                "antiBotDetected": "yes" if anti_bot else "no",
                "errorSummary": error_summary,
            }
    except urllib.error.HTTPError as e:
        status_code = getattr(e, "code", "")
        headers = dict(e.headers.items()) if e.headers else {}
        content_type = headers.get("Content-Type", "")
        final_url = getattr(e, "geturl", lambda: url)()
        try:
            body_sample = e.read(READ_BYTES)
        except Exception:
            body_sample = b""
        anti_bot = detect_antibot(content_type, body_sample, headers)
        if 300 <= int(status_code) < 400:
            location = headers.get("Location", "")
            error_summary = f"redirect response to {location}" if location else "redirect response"
        else:
            error_summary = f"http error {status_code}"
        if anti_bot:
            error_summary = f"{error_summary}; anti-bot or challenge detected"
        return {
            "downloadableByBackend": "no",
            "statusCode": str(status_code),
            "contentType": content_type,
            "finalUrl": final_url,
            "antiBotDetected": "yes" if anti_bot else "no",
            "errorSummary": error_summary,
        }
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, OSError) as e:
        return {
            "downloadableByBackend": "no",
            "statusCode": "",
            "contentType": "",
            "finalUrl": "",
            "antiBotDetected": "no",
            "errorSummary": str(e),
        }


def read_bad_parts() -> set[str]:
    bad_parts = set()
    with open(SOURCE_AUDIT, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["downloadableByBackend"] != "yes" or row["antiBotDetected"] != "no":
                bad_parts.add(row["partNumber"])
    return bad_parts


def commons_search(term: str):
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": term,
        "gsrnamespace": "6",
        "gsrlimit": "8",
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": COMMONS_UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                return sorted(
                    (json.load(response).get("query", {}).get("pages", {}) or {}).values(),
                    key=lambda item: item.get("index", 9999),
                )
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(2 + attempt * 3)
                continue
            raise
    return []


def is_good_title(title: str) -> bool:
    lowered = title.lower()
    return not any(marker in lowered for marker in BAD_TITLE_MARKERS)


def collect_candidates(term: str):
    pages = commons_search(term)
    preferred = []
    fallback = []
    for page in pages:
        imageinfo = (page.get("imageinfo") or [{}])[0]
        mime = imageinfo.get("mime", "")
        url = imageinfo.get("url", "")
        title = page.get("title", "")
        if not mime.startswith("image/") or mime.endswith("svg+xml"):
            continue
        candidate = {
            "term": term,
            "title": title,
            "url": url,
            "mime": mime,
        }
        if is_good_title(title):
            preferred.append(candidate)
        else:
            fallback.append(candidate)
    return preferred + fallback


def choose_image(opener, part_number: str, search_cache: dict[str, list[dict]], search_offsets: dict[str, int]):
    for term in SEARCH_TERMS.get(part_number, []):
        try:
            candidates = search_cache.get(term)
            if candidates is None:
                candidates = collect_candidates(term)
                search_cache[term] = candidates
        except Exception:
            continue
        if not candidates:
            continue
        offset = search_offsets.get(term, 0)
        candidate = candidates[offset % len(candidates)]
        search_offsets[term] = offset + 1
        return candidate
    return None


def audit_csv_images(opener, input_path: Path, output_path: Path):
    with open(input_path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    report_rows = [[
        "rowNumber",
        "partNumber",
        "imageUrl",
        "downloadableByBackend",
        "statusCode",
        "contentType",
        "finalUrl",
        "antiBotDetected",
        "errorSummary",
    ]]

    totals = {"yes": 0, "no": 0}

    for row_number, row in enumerate(rows[1:], start=2):
        image_url = row[4] if len(row) > 4 else ""
        part_number = row[0] if len(row) > 0 else ""
        result = audit_url(opener, image_url) if image_url else {
            "downloadableByBackend": "no",
            "statusCode": "",
            "contentType": "",
            "finalUrl": "",
            "antiBotDetected": "no",
            "errorSummary": "empty imageUrl",
        }
        totals[result["downloadableByBackend"]] += 1
        report_rows.append([
            str(row_number),
            part_number,
            image_url,
            result["downloadableByBackend"],
            result["statusCode"],
            result["contentType"],
            result["finalUrl"],
            result["antiBotDetected"],
            result["errorSummary"],
        ])

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(report_rows)

    return totals


def main():
    opener = build_opener()
    bad_parts = read_bad_parts()

    with open(SOURCE_CSV, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    selection_rows = []
    replaced = 0
    unresolved = 0
    search_cache: dict[str, list[dict]] = {}
    search_offsets: dict[str, int] = {}

    for row in rows:
        part_number = row["partNumber"]
        if part_number not in bad_parts:
            selection_rows.append({
                "partNumber": part_number,
                "name": row["name"],
                "searchTerm": "",
                "selectedTitle": "",
                "selectedUrl": row["image"],
                "status": "kept_existing_valid",
                "errorSummary": "",
            })
            continue

        chosen = choose_image(opener, part_number, search_cache, search_offsets)
        if chosen:
            row["image"] = chosen["url"]
            replaced += 1
            selection_rows.append({
                "partNumber": part_number,
                "name": row["name"],
                "searchTerm": chosen["term"],
                "selectedTitle": chosen["title"],
                "selectedUrl": chosen["url"],
                "status": "replaced_with_commons",
                "errorSummary": "",
            })
        else:
            unresolved += 1
            selection_rows.append({
                "partNumber": part_number,
                "name": row["name"],
                "searchTerm": " | ".join(SEARCH_TERMS.get(part_number, [])),
                "selectedTitle": "",
                "selectedUrl": row["image"],
                "status": "unresolved_kept_previous",
                "errorSummary": "no backend-safe commons image found with current search terms",
            })

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with open(SELECTION_REPORT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "partNumber",
                "name",
                "searchTerm",
                "selectedTitle",
                "selectedUrl",
                "status",
                "errorSummary",
            ],
        )
        writer.writeheader()
        writer.writerows(selection_rows)

    totals = audit_csv_images(opener, OUTPUT_CSV, OUTPUT_AUDIT)
    print(json.dumps({
        "outputCsv": str(OUTPUT_CSV),
        "selectionReport": str(SELECTION_REPORT),
        "auditReport": str(OUTPUT_AUDIT),
        "badPartsInput": len(bad_parts),
        "replacedWithCommons": replaced,
        "unresolvedKeptPrevious": unresolved,
        "finalDownloadableYes": totals["yes"],
        "finalDownloadableNo": totals["no"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
