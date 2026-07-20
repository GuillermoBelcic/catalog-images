import csv
import json
import mimetypes
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

PACK_DIR = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\local_image_pack"
)
MANIFEST_PATH = PACK_DIR / "image_pack_manifest.csv"
SUMMARY_PATH = PACK_DIR / "image_pack_summary.json"
COMMONS_REPORT = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\commons_image_selection_report.csv"
)
IMAGES_DIR = PACK_DIR / "images"

DOWNLOAD_UA = "CatalogImagePackBuilder/1.1 (+real image upgrade)"


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
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        body = response.read()
        return body, content_type


def load_commons_candidates():
    by_part = {}
    with open(COMMONS_REPORT, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("selectedUrl"):
                by_part[row["partNumber"]] = row
    return by_part


def main():
    commons = load_commons_candidates()

    with open(MANIFEST_PATH, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    upgraded = 0
    still_icons = 0
    attempts = 0
    failures = []

    for row in rows:
        if row["sourceKind"] != "fallback_icon":
            continue
        candidate = commons.get(row["partNumber"])
        if not candidate:
            still_icons += 1
            continue

        attempts += 1
        url = candidate["selectedUrl"]
        try:
            body, content_type = download_binary(url)
            ext = extension_from_content_type(content_type)
            safe_stem = f"{row['partNumber']}_{sanitize_filename(row['name'])}"
            output_path = IMAGES_DIR / f"{safe_stem}{ext}"
            output_path.write_bytes(body)
            row["sourceKind"] = "catalog_source"
            row["sourceUrl"] = url
            row["localImagePath"] = str(output_path)
            row["contentType"] = content_type
            upgraded += 1
            time.sleep(2)
        except urllib.error.HTTPError as e:
            failures.append({
                "partNumber": row["partNumber"],
                "name": row["name"],
                "url": url,
                "error": f"http error {e.code}",
            })
            still_icons += 1
            time.sleep(3)
        except Exception as e:
            failures.append({
                "partNumber": row["partNumber"],
                "name": row["name"],
                "url": url,
                "error": f"{type(e).__name__}: {e}",
            })
            still_icons += 1
            time.sleep(2)

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
        "upgradeAttempts": attempts,
        "upgradedToRealImages": upgraded,
        "failures": failures,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "manifest": str(MANIFEST_PATH),
        "summary": str(SUMMARY_PATH),
        "upgradeAttempts": attempts,
        "upgradedToRealImages": upgraded,
        "catalogSourceCount": summary["catalogSourceCount"],
        "fallbackIconCount": summary["fallbackIconCount"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
