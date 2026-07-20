import csv
import json
import mimetypes
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from replace_failed_images_with_commons import SEARCH_TERMS

PACK_DIR = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\local_image_pack"
)
MANIFEST_PATH = PACK_DIR / "image_pack_manifest.csv"
SUMMARY_PATH = PACK_DIR / "image_pack_summary.json"
IMAGES_DIR = PACK_DIR / "images"

OPENVERSE_UA = "CatalogPhotoFinder/1.0"
DOWNLOAD_UA = "CatalogPhotoDownloader/1.0"

BAD_TITLE_MARKERS = [
    "logo",
    "icon",
    "diagram",
    "blueprint",
    "schematic",
    "clipart",
    "cartoon",
    "meme",
    "without",
]


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


def openverse_search(term: str, page_size: int = 8):
    url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": term, "page_size": page_size, "license_type": "all"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": OPENVERSE_UA})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response).get("results", [])


def is_reasonable_result(result: dict, term: str) -> bool:
    title = (result.get("title") or "").lower()
    width = result.get("width") or 0
    height = result.get("height") or 0
    url = result.get("url") or ""
    provider = (result.get("provider") or "").lower()

    if provider not in {"wikimedia", "flickr"}:
        return False
    if width < 400 or height < 300:
        return False
    if not url.startswith("http"):
        return False
    if any(marker in title for marker in BAD_TITLE_MARKERS):
        return False

    term_tokens = [token for token in re.split(r"[^a-z0-9]+", term.lower()) if len(token) > 2]
    if term_tokens and title:
        overlap = sum(1 for token in term_tokens if token in title)
        if overlap == 0 and provider == "flickr":
            return False

    return True


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


def query_terms_for_row(row: dict) -> list[str]:
    part_number = row["partNumber"]
    if part_number in SEARCH_TERMS:
        return SEARCH_TERMS[part_number]
    name = row["name"]
    return [name]


def remove_orphan_files(active_paths: set[str]):
    removed = []
    for file in IMAGES_DIR.iterdir():
        if str(file) not in active_paths:
            file.unlink(missing_ok=True)
            removed.append(str(file))
    return removed


def main():
    with open(MANIFEST_PATH, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    improved = []
    checked = 0
    failures = []

    for row in rows:
        if row["sourceKind"] != "fallback_icon":
            continue

        part_number = row["partNumber"]
        name = row["name"]
        terms = query_terms_for_row(row)
        checked += 1
        found = False

        for term in terms[:3]:
            try:
                results = openverse_search(term)
            except Exception as e:
                failures.append({"partNumber": part_number, "name": name, "term": term, "error": str(e)})
                time.sleep(2)
                continue

            for result in results:
                if not is_reasonable_result(result, term):
                    continue
                try:
                    body, content_type = download_binary(result["url"])
                    ext = extension_from_content_type(content_type)
                    safe_stem = f"{part_number}_{sanitize_filename(name)}"
                    output_path = IMAGES_DIR / f"{safe_stem}{ext}"
                    output_path.write_bytes(body)
                    row["sourceKind"] = "catalog_source"
                    row["sourceUrl"] = result["url"]
                    row["localImagePath"] = str(output_path)
                    row["contentType"] = content_type
                    improved.append({
                        "partNumber": part_number,
                        "name": name,
                        "term": term,
                        "title": result.get("title", ""),
                        "url": result["url"],
                    })
                    found = True
                    time.sleep(2)
                    break
                except Exception as e:
                    failures.append({"partNumber": part_number, "name": name, "term": term, "error": str(e)})
                    time.sleep(1)
                    continue
            if found:
                break
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
        writer.writerows(rows)

    active_paths = {row["localImagePath"] for row in rows if row["localImagePath"]}
    removed = remove_orphan_files(active_paths)

    summary = {
        "totalProducts": len(rows),
        "catalogSourceCount": sum(1 for r in rows if r["sourceKind"] == "catalog_source"),
        "fallbackIconCount": sum(1 for r in rows if r["sourceKind"] == "fallback_icon"),
        "checkedFallbacks": checked,
        "upgradedWithOpenverse": len(improved),
        "removedOrphans": len(removed),
        "improved": improved,
        "failures": failures[:200],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "manifest": str(MANIFEST_PATH),
                "summary": str(SUMMARY_PATH),
                "checkedFallbacks": checked,
                "upgradedWithOpenverse": len(improved),
                "catalogSourceCount": summary["catalogSourceCount"],
                "fallbackIconCount": summary["fallbackIconCount"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
