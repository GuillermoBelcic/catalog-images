import csv
import json
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

INPUT_PATH = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\Base de Datos de Materiales y Herramientas_V2 - formato_objetivo_desde_imagenes_partnumbers_bonitos_backend_safe.csv"
)
OUTPUT_PATH = Path(
    r"C:\Users\Lenovo\Documents\TicTap cosas\outputs\v2_completo\backend_image_audit_backend_safe.csv"
)

BACKEND_UA = "BackendImageAuditor/1.0 (+no-browser; no-cookies; no-js)"
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


def main():
    with open(INPUT_PATH, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    opener = build_opener()
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
        part_number = row[0] if len(row) > 0 else ""
        image_url = row[4] if len(row) > 4 else ""
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

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(report_rows)

    print(json.dumps({
        "input": str(INPUT_PATH),
        "output": str(OUTPUT_PATH),
        "total": len(report_rows) - 1,
        "downloadable_yes": totals["yes"],
        "downloadable_no": totals["no"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
