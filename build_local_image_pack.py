import csv
import json
import mimetypes
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

INPUT_CSV = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\Base de Datos de Materiales y Herramientas_V2 - imagenes_reales_backend_safe.csv"
)
OUTPUT_DIR = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\local_image_pack"
)
IMAGES_DIR = OUTPUT_DIR / "images"
MANIFEST_PATH = OUTPUT_DIR / "image_pack_manifest.csv"
SUMMARY_PATH = OUTPUT_DIR / "image_pack_summary.json"

DOWNLOAD_UA = "CatalogImagePackBuilder/1.0 (+catalog prep; contactless)"

ICON_BASE = "https://api.iconify.design/mdi/{icon}.svg?color={color}&width=600&height=400"

CATEGORY_COLORS = {
    "Power Tools": "0F766E",
    "Cleaning Equipment": "0891B2",
    "Lighting": "CA8A04",
    "Batteries & Chargers": "65A30D",
    "Hand Tools": "B45309",
    "Precision Tools": "7C3AED",
    "Measuring & Layout Tools": "2563EB",
    "Tool Accessories": "7C3AED",
    "Cables & Wiring": "0EA5E9",
    "Electrical Consumables": "D97706",
    "Electrical Installation": "EA580C",
    "Networking": "0284C7",
    "Cable Management": "0891B2",
    "Fixings & Fasteners": "9333EA",
    "Sealants & Adhesives": "DB2777",
    "Maintenance & Cleaning": "16A34A",
    "Electrical Testing": "DC2626",
    "PPE": "475569",
    "First Aid": "E11D48",
    "Access Equipment": "1D4ED8",
    "Tool Storage & Transport": "334155",
    "Site Supplies": "0891B2",
    "Marking & Labels": "4F46E5",
}


def sanitize_filename(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def icon_url(icon: str, category: str) -> str:
    color = CATEGORY_COLORS.get(category, "222222")
    return ICON_BASE.format(icon=icon, color=color)


def choose_icon(name: str, description: str, category: str) -> str:
    text = f"{name} {description}".lower()

    if "taladro" in text or "atornillador" in text or "multiherramienta" in text or "amoladora" in text or "sierra" in text:
        return "tools"
    if "aspirador" in text:
        return "tools"
    if "linterna" in text or "proyector" in text:
        return "flashlight"
    if "bater" in text or "cargador" in text or "adaptador usb" in text:
        return "battery-charging" if "cargador" in text else "battery"
    if "destornillador" in text or "punta" in text:
        return "screwdriver"
    if "llave inglesa" in text or "grifa" in text:
        return "pipe-wrench"
    if "llave" in text or "vaso" in text:
        return "wrench"
    if "alicate" in text or "crimpadora" in text or "pelacables" in text:
        return "pliers"
    if "cúter" in text or "cuter" in text:
        return "knife"
    if "tijera" in text:
        return "scissors-cutting"
    if "martillo" in text or "maza" in text:
        return "hammer"
    if "nivel láser" in text or "laser" in text or "detector" in text or "comprobador" in text:
        return "laser-pointer"
    if "nivel" in text or "escuadra" in text or "flexómetro" in text or "metro" in text:
        return "ruler-square-compass"
    if "broca" in text or "corona" in text or "disco" in text or "lija" in text:
        return "circular-saw"
    if "cable" in text or "ethernet" in text or "coaxial" in text or "rj45" in text:
        return "cable-data"
    if "enchufe" in text or "schuko" in text or "base múltiple" in text or "alargador" in text:
        return "power-socket-eu"
    if "interruptor" in text or "conmutador" in text or "diferencial" in text or "magnetotérmico" in text:
        return "power-plug"
    if "patch panel" in text or "roseta" in text or "organizador de cables" in text:
        return "ethernet"
    if "velcro" in text:
        return "cable-data"
    if "tornillo" in text or "taco" in text or "tuerca" in text or "arandela" in text or "remache" in text or "grapa" in text:
        return "package-variant-closed"
    if "silicona" in text or "adhesivo" in text or "espuma" in text:
        return "package-variant-closed"
    if "lubricante" in text or "alcohol" in text or "limpiador" in text or "trapo" in text or "agua" in text:
        return "water"
    if "guante" in text or "casco" in text or "chaleco" in text or "mascarilla" in text or "auditiv" in text:
        return "hard-hat"
    if "gafa" in text:
        return "safety-goggles"
    if "botiquín" in text or "botiquin" in text:
        return "package-variant-closed"
    if "escalera" in text:
        return "ladder"
    if "caja de herramientas" in text or "mochila" in text or "carro" in text or "organizador de tornillería" in text:
        return "toolbox"
    if "bidón" in text:
        return "water"
    if "etiqueta" in text or "cinta" in text:
        return "label"
    return "tools"


def extension_from_content_type(content_type: str) -> str:
    content_type = (content_type or "").split(";")[0].strip().lower()
    if content_type == "image/jpeg":
        return ".jpg"
    if content_type == "image/png":
        return ".png"
    if content_type == "image/webp":
        return ".webp"
    if content_type == "image/svg+xml":
        return ".svg"
    guessed = mimetypes.guess_extension(content_type)
    return guessed or ".img"


def download_binary(url: str, timeout: int = 30):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": DOWNLOAD_UA,
            "Accept": "image/*,*/*;q=0.1",
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        body = response.read()
        return body, content_type


def write_file(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    with open(INPUT_CSV, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    manifest_rows = []
    summary = {
        "totalProducts": len(rows),
        "downloadedFromCatalogSource": 0,
        "downloadedFromFallbackIcon": 0,
        "failed": 0,
        "failures": [],
    }

    for index, row in enumerate(rows, start=1):
        part_number = row["partNumber"]
        name = row["name"]
        description = row["description"]
        category = row["categoryName"]
        source_url = row["image"]
        safe_stem = f"{part_number}_{sanitize_filename(name)}"

        final_url = source_url
        source_kind = "catalog_source"

        if "placehold.jp" in source_url or "placehold.co" in source_url:
            icon = choose_icon(name, description, category)
            final_url = icon_url(icon, category)
            source_kind = "fallback_icon"

        body = None
        content_type = ""
        error_summary = ""

        attempts = [
            ("selected", final_url),
        ]
        if source_kind != "fallback_icon":
            icon = choose_icon(name, description, category)
            attempts.append(("fallback_icon", icon_url(icon, category)))

        for attempt_kind, attempt_url in attempts:
            try:
                body, content_type = download_binary(attempt_url)
                final_url = attempt_url
                source_kind = attempt_kind if attempt_kind != "selected" else source_kind
                break
            except urllib.error.HTTPError as e:
                error_summary = f"http error {e.code} for {attempt_url}"
                if e.code == 429:
                    time.sleep(2)
                continue
            except Exception as e:
                error_summary = f"{type(e).__name__}: {e}"
                continue

        if body:
            ext = extension_from_content_type(content_type)
            output_path = IMAGES_DIR / f"{safe_stem}{ext}"
            write_file(output_path, body)
            if source_kind == "fallback_icon":
                summary["downloadedFromFallbackIcon"] += 1
            else:
                summary["downloadedFromCatalogSource"] += 1
            manifest_rows.append({
                "partNumber": part_number,
                "name": name,
                "categoryName": category,
                "sourceKind": source_kind,
                "sourceUrl": final_url,
                "localImagePath": str(output_path),
                "contentType": content_type,
            })
        else:
            summary["failed"] += 1
            summary["failures"].append({
                "partNumber": part_number,
                "name": name,
                "sourceUrl": final_url,
                "errorSummary": error_summary,
            })
            manifest_rows.append({
                "partNumber": part_number,
                "name": name,
                "categoryName": category,
                "sourceKind": "failed",
                "sourceUrl": final_url,
                "localImagePath": "",
                "contentType": "",
            })

        if index % 10 == 0:
            time.sleep(1)

    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "partNumber",
                "name",
                "categoryName",
                "sourceKind",
                "sourceUrl",
                "localImagePath",
                "contentType",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "outputDir": str(OUTPUT_DIR),
        "manifest": str(MANIFEST_PATH),
        "summary": str(SUMMARY_PATH),
        "downloadedFromCatalogSource": summary["downloadedFromCatalogSource"],
        "downloadedFromFallbackIcon": summary["downloadedFromFallbackIcon"],
        "failed": summary["failed"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
