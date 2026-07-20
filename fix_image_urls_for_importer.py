import csv
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

INPUT_PATH = Path(
    r"C:/Users/Lenovo/Documents/TicTap cosas/outputs/v2_completo/Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes_partnumbers_bonitos.csv"
)
OUTPUT_PATH = Path(
    r"C:/Users/Lenovo/Documents/TicTap cosas/outputs/v2_completo/Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes_partnumbers_bonitos_imagenes_validadas.csv"
)


def check_url(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        status = getattr(response, "status", None) or response.getcode()
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "")
    return status, final_url, content_type


def placeholder_for(name: str, description: str) -> str:
    text = name.strip() or description.strip() or "Product"
    text = text[:40]
    return f"https://placehold.co/600x400/png?text={urllib.parse.quote_plus(text)}"


def main():
    with open(INPUT_PATH, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    header = rows[0]
    out_rows = [header]

    for row in rows[1:]:
        while len(row) < 9:
            row.append("")
        image_url = row[4].strip()
        name = row[1]
        description = row[3]

        if image_url:
            try:
                status, final_url, content_type = check_url(image_url)
                if status == 200 and final_url == image_url and content_type.lower().startswith("image/"):
                    row[4] = image_url
                elif status == 200 and content_type.lower().startswith("image/"):
                    row[4] = final_url
                else:
                    row[4] = placeholder_for(name, description)
            except Exception:
                row[4] = placeholder_for(name, description)
        else:
            row[4] = placeholder_for(name, description)

        out_rows.append(row)

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(out_rows)

    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
