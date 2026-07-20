import csv
import re
import unicodedata
import urllib.request
from pathlib import Path

INPUT_PATH = Path(r"C:/Users/Lenovo/Downloads/Base de Datos de Materiales y Herramientas_V2 - alternativas_mejoradas.csv")
OUTPUT_DIR = Path(r"C:/Users/Lenovo/Documents/TicTap cosas/outputs/v2_completo")
OUTPUT_PATH = OUTPUT_DIR / "Base de Datos de Materiales y Herramientas_V2 - alternativas_mejoradas_imagenes.csv"


TERM_MAP = [
    ("multiherramienta", ["multitool", "power-tool"]),
    ("llave inglesa", ["adjustable-wrench", "tool"]),
    ("llave grifa", ["pipe-wrench", "tool"]),
    ("llave fija", ["combination-wrench", "tool-set"]),
    ("llave de tubo", ["socket-wrench", "tool-set"]),
    ("alicate universal", ["pliers", "tool"]),
    ("alicate de corte", ["diagonal-pliers", "tool"]),
    ("alicate de punta", ["needle-nose-pliers", "tool"]),
    ("pelacables", ["wire-stripper", "tool"]),
    ("crimpadora", ["crimping-tool", "tool"]),
    ("cúter", ["utility-knife", "tool"]),
    ("tijeras", ["electrician-scissors", "tool"]),
    ("martillo", ["hammer", "wood-handle"]),
    ("maza", ["rubber-mallet", "tool"]),
    ("nivel láser", ["laser-level", "tool"]),
    ("nivel", ["spirit-level", "tool"]),
    ("flexómetro", ["tape-measure", "tool"]),
    ("escuadra", ["square-ruler", "tool"]),
    ("punta trazadora", ["scriber", "tool"]),
    ("brocas", ["drill-bit-set", "tool"]),
    ("coronas", ["hole-saw", "tool"]),
    ("puntas de atornillar", ["screwdriver-bits", "tool-set"]),
    ("vasos magnéticos", ["magnetic-socket", "tool"]),
    ("discos de corte", ["cutting-disc", "tool"]),
    ("discos de diamante", ["diamond-blade", "tool"]),
    ("lijas", ["sandpaper", "abrasive"]),
    ("cable ethernet", ["ethernet-cable", "network"]),
    ("cable coaxial", ["coaxial-cable", "network"]),
    ("cable", ["electrical-cable", "roll"]),
    ("bridas", ["cable-ties", "electrical"]),
    ("cinta aislante", ["electrical-tape", "roll"]),
    ("tubo corrugado", ["corrugated-conduit", "electrical"]),
    ("canaleta", ["cable-trunking", "electrical"]),
    ("regleta", ["terminal-strip", "electrical"]),
    ("clemas", ["wire-connector", "electrical"]),
    ("wago", ["lever-connector", "electrical"]),
    ("terminales eléctricos", ["electrical-terminal", "kit"]),
    ("termorretráctil", ["heat-shrink-tube", "kit"]),
    ("enchufe", ["power-socket", "electrical"]),
    ("interruptor", ["light-switch", "electrical"]),
    ("conmutador", ["electrical-switch", "wall"]),
    ("caja de mecanismos", ["electrical-box", "wall"]),
    ("caja de derivación", ["junction-box", "electrical"]),
    ("base múltiple", ["power-strip", "electrical"]),
    ("alargador", ["extension-cord", "electrical"]),
    ("diferencial", ["rcd-breaker", "electrical"]),
    ("magnetotérmico", ["circuit-breaker", "electrical"]),
    ("keystone", ["keystone-jack", "network"]),
    ("roseta rj45", ["rj45-wall-plate", "network"]),
    ("patch cord", ["ethernet-patch-cable", "network"]),
    ("patch panel", ["patch-panel", "network"]),
    ("organizador de cables", ["cable-manager", "rack"]),
    ("velcro", ["hook-and-loop-strap", "cable"]),
    ("tornillos para madera", ["wood-screws", "hardware"]),
    ("tornillos para metal", ["sheet-metal-screws", "hardware"]),
    ("tirafondos", ["hex-head-bolt", "hardware"]),
    ("taco nylon", ["wall-plug", "hardware"]),
    ("taco químico", ["chemical-anchor", "hardware"]),
    ("varilla roscada", ["threaded-rod", "hardware"]),
    ("tuercas", ["hex-nuts", "hardware"]),
    ("arandelas", ["washers", "hardware"]),
    ("remaches", ["blind-rivets", "hardware"]),
    ("grapas", ["cable-clips", "hardware"]),
    ("silicona neutra", ["neutral-silicone", "sealant"]),
    ("silicona sanitaria", ["sanitary-silicone", "sealant"]),
    ("adhesivo de montaje", ["construction-adhesive", "sealant"]),
    ("espuma de poliuretano", ["expanding-foam", "sealant"]),
    ("lubricante", ["lubricant-spray", "can"]),
    ("alcohol isopropílico", ["isopropyl-alcohol", "bottle"]),
    ("limpiador de contactos", ["contact-cleaner", "spray"]),
    ("trapos de limpieza", ["cleaning-rags", "roll"]),
    ("multímetro", ["multimeter", "tool"]),
    ("pinza amperimétrica", ["clamp-meter", "tool"]),
    ("detector de tensión", ["voltage-tester", "tool"]),
    ("detector de cables", ["wall-scanner", "tool"]),
    ("comprobador de enchufes", ["socket-tester", "tool"]),
    ("comprobador de red", ["network-tester", "tool"]),
    ("guantes", ["work-gloves", "safety"]),
    ("gafas", ["safety-goggles", "protection"]),
    ("casco", ["safety-helmet", "protection"]),
    ("chaleco", ["high-visibility-vest", "safety"]),
    ("protectores auditivos", ["earmuffs", "hearing-protection"]),
    ("mascarillas", ["ffp2-mask", "safety"]),
    ("botiquín", ["first-aid-kit", "safety"]),
    ("escalera telescópica", ["telescopic-ladder", "tool"]),
    ("caja de herramientas", ["toolbox", "tool"]),
    ("organizador de tornillería", ["parts-organizer", "toolbox"]),
    ("mochila de herramientas", ["tool-backpack", "tool"]),
    ("carro de transporte", ["folding-hand-truck", "cart"]),
    ("bidón de agua", ["water-jug", "container"]),
    ("rotulador permanente", ["permanent-marker", "stationery"]),
    ("etiquetas identificativas", ["label-tape", "stationery"]),
]


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def terms_for_row(name: str, desc: str) -> list[str]:
    combined = f"{name} {desc}"
    low = slug(combined)
    for key, terms in TERM_MAP:
      if key in low:
        return terms
    tokens = re.findall(r"[a-z0-9]+", low)
    tokens = [t for t in tokens if len(t) > 3][:2]
    if not tokens:
        return ["tool", "product"]
    return tokens + ["product"]


def resolve_loremflickr_url(terms: list[str], lock: int) -> str:
    attempts = [
        terms,
        terms[:1],
        terms[-2:],
        ["tool"],
        ["hardware"],
        ["electrical"],
        ["safety"],
    ]
    seen = set()
    for attempt in attempts:
        attempt = tuple(t for t in attempt if t)
        if not attempt or attempt in seen:
            continue
        seen.add(attempt)
        query = ",".join(attempt)
        seed_url = f"https://loremflickr.com/800/800/{query}?lock={lock}"
        req = urllib.request.Request(seed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            final_url = response.geturl()
        if "defaultImage.small" not in final_url:
            return final_url
    return "https://loremflickr.com/cache/resized/65535_49905944233_4c0f5c2092_h_800_800_nofilter.jpg"


def main() -> None:
    with open(INPUT_PATH, "r", encoding="cp1252", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))

    headers = rows[0]
    updated = [headers]

    for row_index, row in enumerate(rows[1:], start=2):
        while len(row) < 6:
            row.append("")
        if not row[5].strip():
            terms = terms_for_row(row[0], row[3])
            row[5] = resolve_loremflickr_url(terms, row_index)
        updated.append(row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="cp1252", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(updated)

    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
