import csv
import urllib.parse
from pathlib import Path

INPUT_PATH = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes_partnumbers_bonitos.csv"
)
OUTPUT_PATH = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes_partnumbers_bonitos_backend_safe.csv"
)


def make_safe_image_url(name: str, description: str) -> str:
    text = (name or description or "Product").strip()
    text = text[:42]
    encoded = urllib.parse.quote(text, safe="")
    return f"https://placehold.jp/24/f2f2f2/222222/600x400.png?text={encoded}"


def main():
    with open(INPUT_PATH, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    output_rows = [rows[0]]
    for row in rows[1:]:
        while len(row) < 9:
            row.append("")
        row[4] = make_safe_image_url(row[1], row[3])
        output_rows.append(row)

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(output_rows)

    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
