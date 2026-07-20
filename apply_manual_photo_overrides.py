import csv
import json
import mimetypes
import re
import urllib.request
from pathlib import Path

PACK_DIR = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\local_image_pack"
)
MANIFEST_PATH = PACK_DIR / "image_pack_manifest.csv"
SUMMARY_PATH = PACK_DIR / "image_pack_summary.json"
IMAGES_DIR = PACK_DIR / "images"

DOWNLOAD_UA = "CatalogManualPhotoOverride/1.0"

OVERRIDES = {
    "HDT0000018": "https://live.staticflickr.com/65535/48617391993_977b83830f_b.jpg",
    "CBL0000005": "https://live.staticflickr.com/8584/16050775634_07b7a41f73_b.jpg",
    "ELC0000004": "https://live.staticflickr.com/8466/8100854388_a06f543734_b.jpg",
    "ELC0000005": "https://live.staticflickr.com/8196/8100860436_e9b30ae9a9_b.jpg",
    "CBM0000001": "https://live.staticflickr.com/6131/5937249661_bf2c3643b8_b.jpg",
    "FIX0000007": "https://live.staticflickr.com/792/27565221868_9bc224e0bc_b.jpg",
    "SEA0000001": "https://live.staticflickr.com/3709/11225966856_e90eab280c_b.jpg",
    "TST0000004": "https://live.staticflickr.com/2046/2198624960_76825b34d3_b.jpg",
}


def sanitize_filename(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def extension_from_content_type(content_type: str) -> str:
    content_type = (content_type or "").split(";")[0].strip().lower()
    if content_type == "image/jpeg":
        return ".jpg"
    if content_type == "image/png":
        return ".png"
    if content_type == "image/webp":
        return ".webp"
    guessed = mimetypes.guess_extension(content_type)
    return guessed or ".img"


def download_binary(url: str, timeout: int = 40):
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


def remove_previous_files(part_number: str, keep_path: Path):
    for file in IMAGES_DIR.glob(f"{part_number}_*"):
        if file.resolve() != keep_path.resolve():
            file.unlink(missing_ok=True)


def main():
    with open(MANIFEST_PATH, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    changed = []
    failures = []

    for row in rows:
        part_number = row["partNumber"]
        url = OVERRIDES.get(part_number)
        if not url:
            continue

        try:
            body, content_type = download_binary(url)
            ext = extension_from_content_type(content_type)
            safe_stem = f"{part_number}_{sanitize_filename(row['name'])}"
            output_path = IMAGES_DIR / f"{safe_stem}{ext}"
            output_path.write_bytes(body)
            remove_previous_files(part_number, output_path)

            row["sourceKind"] = "catalog_source"
            row["sourceUrl"] = url
            row["localImagePath"] = str(output_path)
            row["contentType"] = content_type
            changed.append({
                "partNumber": part_number,
                "name": row["name"],
                "url": url,
                "localImagePath": str(output_path),
            })
        except Exception as e:
            failures.append({
                "partNumber": part_number,
                "name": row["name"],
                "url": url,
                "error": str(e),
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
        "manualOverridesApplied": changed,
        "manualOverrideFailures": failures,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "manifest": str(MANIFEST_PATH),
        "summary": str(SUMMARY_PATH),
        "applied": len(changed),
        "catalogSourceCount": summary["catalogSourceCount"],
        "fallbackIconCount": summary["fallbackIconCount"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
