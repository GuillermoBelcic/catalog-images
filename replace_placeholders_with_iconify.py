import csv
import json
import urllib.parse
from pathlib import Path

from audit_backend_image_urls import audit_url, build_opener

INPUT_PATH = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\version que funciona - Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes_partnumbers_bonitos_solo_fallidas_backend_safe.csv"
)
OUTPUT_PATH = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\Base de Datos de Materiales y Herramientas_V2 - iconify_backend_safe.csv"
)
AUDIT_PATH = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\backend_image_audit_iconify_backend_safe.csv"
)

ICON_BASE = "https://api.iconify.design/mdi/{icon}.svg?color={color}&width=600&height=400"

CATEGORY_COLORS = {
    "Power Tools": "0F766E",
    "Lighting": "CA8A04",
    "Batteries & Chargers": "65A30D",
    "Hand Tools": "B45309",
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


def icon_url(icon: str, category: str) -> str:
    color = CATEGORY_COLORS.get(category, "222222")
    return ICON_BASE.format(icon=icon, color=color)


def choose_icon(name: str, description: str, category: str) -> str:
    text = f"{name} {description}".lower()

    if "taladro" in text or "atornillador" in text or "multiherramienta" in text:
        return "tools"
    if "linterna" in text or "proyector" in text:
        return "flashlight"
    if "bater" in text or "cargador" in text:
        return "battery-charging" if "cargador" in text else "battery"
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
    if "nivel láser" in text or "laser" in text:
        return "laser-pointer"
    if "nivel" in text or "escuadra" in text or "punta trazadora" in text:
        return "ruler-square-compass"
    if "flexómetro" in text or "metro" in text:
        return "tape-measure"
    if "broca" in text or "punta" in text:
        return "screwdriver"
    if "corona" in text or "disco" in text:
        return "circular-saw"
    if "lija" in text:
        return "hand-saw"
    if "cable" in text or "ethernet" in text or "coaxial" in text:
        return "cable-data"
    if "enchufe" in text or "schuko" in text or "base múltiple" in text or "alargador" in text:
        return "power-socket-eu"
    if "interruptor" in text or "conmutador" in text or "diferencial" in text or "magnetotérmico" in text:
        return "power-plug"
    if "rj45" in text or "patch panel" in text or "patch cord" in text or "roseta" in text:
        return "ethernet"
    if "organizador" in text or "velcro" in text:
        return "cable-data"
    if "tornillo" in text or "taco" in text or "tuerca" in text or "arandela" in text or "remache" in text or "grapa" in text:
        return "package-variant-closed"
    if "silicona" in text or "adhesivo" in text or "espuma" in text:
        return "package-variant-closed"
    if "lubricante" in text or "alcohol" in text or "limpiador" in text or "trapo" in text:
        return "water"
    if "detector" in text or "comprobador" in text:
        return "laser-pointer"
    if "guante" in text or "casco" in text:
        return "hard-hat"
    if "gafa" in text:
        return "safety-goggles"
    if "chaleco" in text or "auditivo" in text or "mascarilla" in text:
        return "hard-hat"
    if "botiquín" in text or "botiquin" in text:
        return "package-variant-closed"
    if "escalera" in text:
        return "ladder"
    if "caja de herramientas" in text or "mochila" in text or "carro" in text:
        return "toolbox"
    if "bidón" in text or "agua" in text:
        return "water"
    if "etiqueta" in text or "cinta" in text:
        return "label"

    category_defaults = {
        "Power Tools": "tools",
        "Lighting": "flashlight",
        "Batteries & Chargers": "battery",
        "Hand Tools": "tools",
        "Measuring & Layout Tools": "ruler-square-compass",
        "Tool Accessories": "screwdriver",
        "Cables & Wiring": "cable-data",
        "Electrical Consumables": "label",
        "Electrical Installation": "power-socket-eu",
        "Networking": "ethernet",
        "Cable Management": "cable-data",
        "Fixings & Fasteners": "package-variant-closed",
        "Sealants & Adhesives": "package-variant-closed",
        "Maintenance & Cleaning": "water",
        "Electrical Testing": "laser-pointer",
        "PPE": "hard-hat",
        "First Aid": "package-variant-closed",
        "Access Equipment": "ladder",
        "Tool Storage & Transport": "toolbox",
        "Site Supplies": "water",
        "Marking & Labels": "label",
    }
    return category_defaults.get(category, "tools")


def write_audit(rows: list[list[str]]) -> None:
    with open(AUDIT_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)


def main():
    opener = build_opener()

    with open(INPUT_PATH, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    replaced = 0
    output_rows = []
    audit_rows = [[
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

    for row_number, row in enumerate(rows, start=2):
        image = row["image"]
        if "placehold.jp" in image or "placehold.co" in image:
            icon = choose_icon(row["name"], row["description"], row["categoryName"])
            row["image"] = icon_url(icon, row["categoryName"])
            replaced += 1

        audit = audit_url(opener, row["image"])
        audit_rows.append([
            str(row_number),
            row["partNumber"],
            row["image"],
            audit["downloadableByBackend"],
            audit["statusCode"],
            audit["contentType"],
            audit["finalUrl"],
            audit["antiBotDetected"],
            audit["errorSummary"],
        ])
        output_rows.append(row)

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    write_audit(audit_rows)

    failed = sum(1 for row in audit_rows[1:] if row[3] != "yes" or row[7] != "no")
    print(json.dumps({
        "outputCsv": str(OUTPUT_PATH),
        "auditCsv": str(AUDIT_PATH),
        "replacedPlaceholders": replaced,
        "totalRows": len(output_rows),
        "failedAuditRows": failed,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
