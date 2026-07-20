import csv
import json
from pathlib import Path

PACK_DIR = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\local_image_pack"
)
MANIFEST_PATH = PACK_DIR / "image_pack_manifest.csv"
SUMMARY_PATH = PACK_DIR / "image_pack_summary.json"
IMAGES_DIR = PACK_DIR / "images"


def find_svg_for_part(part_number: str) -> Path | None:
    matches = list(IMAGES_DIR.glob(f"{part_number}_*.svg"))
    return matches[0] if matches else None


def main():
    with open(MANIFEST_PATH, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    reverted = []

    for row in rows:
        if "placehold" not in row["sourceUrl"]:
            continue

        svg_path = find_svg_for_part(row["partNumber"])
        if not svg_path:
            continue

        row["sourceKind"] = "fallback_icon"
        row["sourceUrl"] = ""
        row["localImagePath"] = str(svg_path)
        row["contentType"] = "image/svg+xml; charset=utf-8"
        reverted.append({
            "partNumber": row["partNumber"],
            "name": row["name"],
            "svgPath": str(svg_path),
        })

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
        writer.writerows(rows)

    summary = {
        "totalProducts": len(rows),
        "catalogSourceCount": sum(1 for r in rows if r["sourceKind"] == "catalog_source"),
        "fallbackIconCount": sum(1 for r in rows if r["sourceKind"] == "fallback_icon"),
        "revertedPlaceholderRegressions": len(reverted),
        "reverted": reverted,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "manifest": str(MANIFEST_PATH),
        "summary": str(SUMMARY_PATH),
        "revertedPlaceholderRegressions": len(reverted),
        "catalogSourceCount": summary["catalogSourceCount"],
        "fallbackIconCount": summary["fallbackIconCount"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
