#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import urllib.parse
import zipfile
from pathlib import Path

ALLOWED_MODEL_CATEGORIES = {"none", "text", "multimodal", "code"}
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "upload-config.json"
DIRECT_UPLOAD_THRESHOLD_BYTES = int(4.5 * 1024 * 1024)
BLOB_API_URL = "https://vercel.com/api/blob"
BLOB_API_VERSION = "12"
DEFAULT_KEYCHAIN_SERVICE = "nima-tech-space-upload"
DEFAULT_SITE_URL = "https://www.nima-tech.space"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
ICON_MAX_BYTES = 1 * 1024 * 1024
THUMBNAIL_MAX_BYTES = 2 * 1024 * 1024
SCREENSHOT_MAX_BYTES = 3 * 1024 * 1024
ICON_MAX_DIMENSION = 1024
THUMBNAIL_MAX_DIMENSION = 1600
SCREENSHOT_MAX_DIMENSION = 2200


def fail(message: str) -> None:
    raise SystemExit(message)


def stage(message: str) -> None:
    print(f"[stage] {message}", file=sys.stderr)


def done(message: str) -> None:
    print(f"[done] {message}", file=sys.stderr)


def next_step(message: str) -> None:
    print(f"[next] {message}", file=sys.stderr)


def warn(message: str) -> None:
    print(f"[warn] {message}", file=sys.stderr)


def run_curl(command: list[str]) -> str:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or "curl request failed")
    return result.stdout


def run_curl_with_metadata(command: list[str]) -> tuple[str, int, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        header_path = Path(temp_dir) / "headers.txt"
        body_path = Path(temp_dir) / "body.txt"
        result = subprocess.run(
            [
                *command,
                "-D",
                str(header_path),
                "-o",
                str(body_path),
                "-w",
                "\n%{http_code}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise SystemExit(result.stderr.strip() or "curl request failed")

        status_line = (result.stdout or "").strip().splitlines()
        status_code = 0
        if status_line:
            try:
                status_code = int(status_line[-1])
            except ValueError:
                status_code = 0

        body = body_path.read_text(encoding="utf-8", errors="replace") if body_path.exists() else ""
        headers = header_path.read_text(encoding="utf-8", errors="replace") if header_path.exists() else ""
        return body, status_code, headers


def extract_content_type(headers: str) -> str:
    for line in headers.splitlines():
        if line.lower().startswith("content-type:"):
            return line.split(":", 1)[1].strip()
    return ""


def summarize_non_json_response(body: str, status_code: int, headers: str) -> str:
    content_type = extract_content_type(headers) or "unknown"
    snippet = re.sub(r"\s+", " ", body).strip()[:280] or "empty body"
    hint = ""
    if "text/html" in content_type or body.lstrip().startswith("<!DOCTYPE") or body.lstrip().startswith("<html"):
        hint = " This usually means the server returned an HTML error page (for example a timeout, proxy error, or platform crash) instead of JSON."
    elif status_code >= 500:
        hint = " This usually means the import finalize step failed server-side before a JSON response was produced."
    return f"HTTP {status_code or 'unknown'}, content-type: {content_type}. Response snippet: {snippet}.{hint}"


def run_curl_json(command: list[str], error_message: str) -> dict:
    output, status_code, headers = run_curl_with_metadata(command)
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{error_message}: {summarize_non_json_response(output, status_code, headers)}") from exc

    if not isinstance(payload, dict):
        raise SystemExit(f"{error_message}: response must be a JSON object")

    return payload


def sanitize_blob_pathname(filename: str) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", filename)
    return f"package-uploads/{safe_name}"


def get_image_dimensions(image_path: Path) -> tuple[int, int] | None:
    if platform.system() == "Darwin":
        result = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(image_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            width_match = re.search(r"pixelWidth:\s*(\d+)", result.stdout)
            height_match = re.search(r"pixelHeight:\s*(\d+)", result.stdout)
            if width_match and height_match:
                return int(width_match.group(1)), int(height_match.group(1))
    return None


def get_zip_image_dimensions(zip_file: zipfile.ZipFile, name: str) -> tuple[int, int] | None:
    suffix = Path(name).suffix.lower()
    if suffix not in IMAGE_EXTENSIONS:
        return None
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / Path(name).name
        temp_path.write_bytes(zip_file.read(name))
        return get_image_dimensions(temp_path)


def inspect_package_assets(package_path: Path) -> dict:
    warnings: list[str] = []
    errors: list[str] = []

    with zipfile.ZipFile(package_path) as zf:
        names = {entry.filename for entry in zf.infolist() if not entry.is_dir()}

        for info in zf.infolist():
            if info.is_dir():
                continue

            name = info.filename
            lower_name = name.lower()
            size = info.file_size

            if size == 0 and (name.startswith("assets/") or name.startswith("app/")):
                errors.append(f"{name} is empty (0 bytes)")
                continue

            dimensions = get_zip_image_dimensions(zf, name)

            if lower_name == "assets/icon.png" or lower_name == "assets/icon.jpg" or lower_name == "assets/icon.jpeg" or lower_name == "assets/icon.webp":
                if size > ICON_MAX_BYTES:
                    warnings.append(f"{name} is large ({size} bytes). Recommended <= {ICON_MAX_BYTES} bytes.")
                if dimensions and max(dimensions) > ICON_MAX_DIMENSION:
                    warnings.append(f"{name} is {dimensions[0]}x{dimensions[1]}. Recommended <= {ICON_MAX_DIMENSION}px on the longest side.")

            if lower_name.startswith("assets/thumbnail.") and Path(lower_name).suffix in IMAGE_EXTENSIONS:
                if size > THUMBNAIL_MAX_BYTES:
                    warnings.append(f"{name} is large ({size} bytes). Recommended <= {THUMBNAIL_MAX_BYTES} bytes.")
                if dimensions and max(dimensions) > THUMBNAIL_MAX_DIMENSION:
                    warnings.append(f"{name} is {dimensions[0]}x{dimensions[1]}. Recommended <= {THUMBNAIL_MAX_DIMENSION}px on the longest side.")

            if lower_name.startswith("assets/screenshot") and Path(lower_name).suffix in IMAGE_EXTENSIONS:
                if size > SCREENSHOT_MAX_BYTES:
                    warnings.append(f"{name} is large ({size} bytes). Recommended <= {SCREENSHOT_MAX_BYTES} bytes.")
                if dimensions and max(dimensions) > SCREENSHOT_MAX_DIMENSION:
                    warnings.append(f"{name} is {dimensions[0]}x{dimensions[1]}. Recommended <= {SCREENSHOT_MAX_DIMENSION}px on the longest side.")

        if "assets/thumbnail.svg" in names and "assets/thumbnail.png" not in names and "assets/thumbnail.jpg" not in names and "assets/thumbnail.webp" not in names:
            warnings.append(
                "Package only provides assets/thumbnail.svg. Web will use it, but mobile shells may fall back to a default PNG cover."
            )

    return {"warnings": warnings, "errors": errors}


def can_optimize_images() -> bool:
    return platform.system() == "Darwin"


def optimize_package_images(package_path: Path) -> Path:
    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = Path(temp_dir) / "package"
        work_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(package_path) as zf:
            zf.extractall(work_dir)

        image_limits = {
            "assets/icon.png": ICON_MAX_DIMENSION,
            "assets/icon.jpg": ICON_MAX_DIMENSION,
            "assets/icon.jpeg": ICON_MAX_DIMENSION,
            "assets/icon.webp": ICON_MAX_DIMENSION,
            "assets/thumbnail.png": THUMBNAIL_MAX_DIMENSION,
            "assets/thumbnail.jpg": THUMBNAIL_MAX_DIMENSION,
            "assets/thumbnail.jpeg": THUMBNAIL_MAX_DIMENSION,
            "assets/thumbnail.webp": THUMBNAIL_MAX_DIMENSION,
        }

        for relative_path, max_dimension in image_limits.items():
            image_path = work_dir / relative_path
            if image_path.is_file():
                subprocess.run(["sips", "-Z", str(max_dimension), str(image_path)], check=False, capture_output=True, text=True)

        screenshots_dir = work_dir / "assets"
        if screenshots_dir.is_dir():
            for candidate in screenshots_dir.iterdir():
                lower_name = candidate.name.lower()
                if candidate.is_file() and lower_name.startswith("screenshot") and candidate.suffix.lower() in IMAGE_EXTENSIONS:
                    if candidate.stat().st_size == 0:
                        candidate.unlink(missing_ok=True)
                    else:
                        subprocess.run(["sips", "-Z", str(SCREENSHOT_MAX_DIMENSION), str(candidate)], check=False, capture_output=True, text=True)

        manifest_path = work_dir / "manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            screenshots = manifest.get("screenshots")
            if isinstance(screenshots, list):
                manifest["screenshots"] = [
                    item for item in screenshots if (work_dir / item).is_file() and (work_dir / item).stat().st_size > 0
                ]
                manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        optimized_path = Path(temp_dir) / f"{package_path.stem}-optimized.zip"
        with zipfile.ZipFile(optimized_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(work_dir.rglob("*")):
                if path.is_dir():
                    continue
                zf.write(path, path.relative_to(work_dir).as_posix())

        final_path = package_path.parent / f"{package_path.stem}-optimized.zip"
        final_path.write_bytes(optimized_path.read_bytes())
        return final_path


def normalize_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower().replace("_", "-").replace(" ", "-"))
    return re.sub(r"^-+|-+$", "", normalized)


def load_manifest_slug_from_zip(package_path: Path) -> str:
    import zipfile

    try:
        with zipfile.ZipFile(package_path) as zf:
            with zf.open("manifest.json") as manifest_file:
                manifest = json.load(manifest_file)
    except KeyError as exc:
        raise SystemExit("package missing manifest.json") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"manifest.json is not valid JSON: {exc}") from exc

    if not isinstance(manifest, dict):
        raise SystemExit("manifest.json must be a JSON object")

    slug = normalize_slug(str(manifest.get("slug") or manifest.get("id") or ""))
    if not slug:
        raise SystemExit("manifest.json must contain a valid slug or id")

    return slug


def check_slug(site_url: str, cookie_path: Path, slug: str) -> dict:
    payload = run_curl_json([
        "curl",
        "-sS",
        "-b",
        str(cookie_path),
        f"{site_url}/api/app-slug-check?slug={urllib.parse.quote(slug)}",
    ], "slug check failed")

    if not payload.get("success"):
        raise SystemExit(payload.get("error") or "slug check failed")

    return payload


def summarize_slug_check(slug_check: dict) -> str:
    slug = slug_check.get("slug") or ""
    if slug_check.get("exists") and not slug_check.get("canOverwrite"):
        owner_name = slug_check.get("ownerName") or "unknown user"
        return f"slug '{slug}' is owned by {owner_name} and cannot be uploaded by this account"
    if slug_check.get("exists") and slug_check.get("canOverwrite"):
        return f"slug '{slug}' already exists and will be overwritten by this account"
    return f"slug '{slug}' is available"


def upload_via_blob(site_url: str, cookie_path: Path, package_path: Path) -> dict:
    pathname = sanitize_blob_pathname(package_path.name)
    token_payload = run_curl_json([
        "curl",
        "-sS",
        "-b",
        str(cookie_path),
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps({
            "type": "blob.generate-client-token",
            "payload": {
                "pathname": pathname,
                "clientPayload": None,
                "multipart": False,
            },
        }),
        f"{site_url}/api/upload-package-token",
    ], "failed to get Blob client token")

    client_token = str(token_payload.get("clientToken") or "").strip()
    if not client_token:
        raise SystemExit("failed to get Blob client token")

    pathname_query = urllib.parse.urlencode({"pathname": pathname})
    upload_payload = run_curl_json([
        "curl",
        "-sS",
        "-X",
        "PUT",
        "-H",
        f"authorization: Bearer {client_token}",
        "-H",
        f"x-api-version: {BLOB_API_VERSION}",
        "-H",
        "x-vercel-blob-access: public",
        "-H",
        "x-content-type: application/zip",
        "-H",
        f"x-content-length: {package_path.stat().st_size}",
        "--data-binary",
        f"@{package_path}",
        f"{BLOB_API_URL}/?{pathname_query}",
    ], "failed to upload package to Blob")

    if not upload_payload.get("url") or not upload_payload.get("pathname"):
        raise SystemExit("Blob upload did not return url/pathname")

    return upload_payload


def load_config(path: Path) -> dict:
    if not path.exists():
        return {"siteUrl": DEFAULT_SITE_URL, "email": "", "password": "", "useKeychain": False, "keychainService": DEFAULT_KEYCHAIN_SERVICE}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid config JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("config file must contain a JSON object")

    return {
        "siteUrl": str(data.get("siteUrl", DEFAULT_SITE_URL) or DEFAULT_SITE_URL),
        "email": str(data.get("email", "")),
        "password": str(data.get("password", "")),
        "useKeychain": bool(data.get("useKeychain", False)),
        "keychainService": str(data.get("keychainService", DEFAULT_KEYCHAIN_SERVICE) or DEFAULT_KEYCHAIN_SERVICE),
    }


def save_config(path: Path, site_url: str, email: str, password: str) -> None:
    path.write_text(
        json.dumps({
            "siteUrl": site_url,
            "email": email,
            "password": password,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(path, 0o600)


def supports_keychain() -> bool:
    return platform.system() == "Darwin"


def read_password_from_keychain(service: str, account: str) -> str:
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-a",
            account,
            "-s",
            service,
            "-w",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a packaged app to Nima Tech Space.")
    parser.add_argument("--site-url", help=f"Base site URL, defaults to {DEFAULT_SITE_URL}")
    parser.add_argument("--email", help="Login email")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--package", required=True, help="Path to package zip")
    parser.add_argument("--model-category", default="none", help="none, text, multimodal, or code")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to reusable upload config JSON")
    parser.add_argument("--save-config", action="store_true", help="Save provided credentials back into the config file")
    parser.add_argument("--dry-run", action="store_true", help="Validate login, manifest, package size, and slug ownership without uploading")
    parser.add_argument("--optimize-images", action="store_true", help="On macOS, create an optimized copy with resized cover images before upload")
    args = parser.parse_args()

    if args.model_category not in ALLOWED_MODEL_CATEGORIES:
        raise SystemExit("model category must be one of: none, text, multimodal, code")

    package_path = Path(args.package).expanduser().resolve()
    if not package_path.is_file():
        raise SystemExit(f"package not found: {package_path}")
    stage("Starting CLAWSPACE publish mode")
    done(f"Package located: {package_path}")

    asset_diagnostics = inspect_package_assets(package_path)
    for message in asset_diagnostics["warnings"]:
        warn(message)
    if asset_diagnostics["errors"]:
        fail("Package asset validation failed:\n- " + "\n- ".join(asset_diagnostics["errors"]))

    if args.optimize_images:
        if not can_optimize_images():
            fail("--optimize-images is currently only supported on macOS")
        stage("Optimizing oversized package images")
        optimized_package = optimize_package_images(package_path)
        package_path = optimized_package.resolve()
        done(f"Using optimized package copy: {package_path}")
        asset_diagnostics = inspect_package_assets(package_path)
        for message in asset_diagnostics["warnings"]:
            warn(message)
        if asset_diagnostics["errors"]:
            fail("Optimized package still has invalid assets:\n- " + "\n- ".join(asset_diagnostics["errors"]))

    config_path = Path(args.config).expanduser().resolve()
    config = load_config(config_path)

    site_url = (args.site_url or config.get("siteUrl") or "").strip()
    email = (args.email or config.get("email") or "").strip()
    keychain_service = str(config.get("keychainService") or DEFAULT_KEYCHAIN_SERVICE).strip() or DEFAULT_KEYCHAIN_SERVICE
    config_password = (config.get("password") or "").strip()
    keychain_password = ""
    if not args.password and config.get("useKeychain") and supports_keychain() and email:
        keychain_password = read_password_from_keychain(keychain_service, email)
    password = (args.password or config_password or keychain_password or "").strip()
    password_source = "flag" if args.password else ("config" if config_password else ("keychain" if keychain_password else "unknown"))

    if not site_url or not email or not password:
        fail(
            "Missing upload credentials.\n"
            f"- Current config file: {config_path}\n"
            f"- Expected fields: siteUrl, email, password (or Keychain password)\n"
            "- New user? Run `python3 scripts/register_clawspace_account.py`\n"
            "- Quick fix: run `python3 scripts/setup_upload_config.py`\n"
            f"- Production site: {DEFAULT_SITE_URL}"
        )

    base_url = site_url.rstrip("/")

    with tempfile.TemporaryDirectory() as temp_dir:
        cookie_path = Path(temp_dir) / "cookies.txt"

        stage("Verifying account credentials")
        login_payload = run_curl_json([
            "curl",
            "-sS",
            "-c",
            str(cookie_path),
            "-H",
            "Content-Type: application/x-www-form-urlencoded",
            "--data-urlencode",
            f"email={email}",
            "--data-urlencode",
            f"password={password}",
            f"{base_url}/api/auth/login",
        ], "login failed")
        if not login_payload.get("success"):
            fail(
                f"{login_payload.get('error') or 'login failed'}\n"
                "Please check your saved credentials or run `python3 scripts/setup_upload_config.py` again.\n"
                "If you do not have an account yet, run `python3 scripts/register_clawspace_account.py` first."
            )
        user = login_payload.get("user") or {}
        done(
            f"Logged in as: {user.get('displayName') or '(no display name)'} <{user.get('email') or email}>"
        )
        done(f"Account role: {user.get('role') or 'member'}")
        if password_source == "config":
            warn(
                "Password is currently being read from plaintext upload-config.json. "
                "For better security on macOS, rerun `python3 scripts/setup_upload_config.py` and choose `keychain`."
            )

        stage("Reading manifest and checking slug ownership")
        slug = load_manifest_slug_from_zip(package_path)
        slug_check = check_slug(base_url, cookie_path, slug)
        done(summarize_slug_check(slug_check))
        if slug_check.get("exists") and not slug_check.get("canOverwrite"):
            owner_name = slug_check.get("ownerName") or "unknown user"
            raise SystemExit(
                f"slug conflict: '{slug}' is already owned by {owner_name}. Change the slug before uploading."
            )

        if slug_check.get("exists") and slug_check.get("canOverwrite"):
            print(f"Notice: '{slug}' already exists and will be overwritten by this account.", file=sys.stderr)

        if args.dry_run:
            next_step("Dry run complete. If everything looks good, run the same command without --dry-run.")
            print(json.dumps({
                "success": True,
                "dryRun": True,
                "package": str(package_path),
                "packageSizeBytes": package_path.stat().st_size,
                "uploadStrategy": "blob-client-upload" if package_path.stat().st_size > DIRECT_UPLOAD_THRESHOLD_BYTES else "direct-form-upload",
                "slug": slug,
                "slugCheck": slug_check,
                "summary": summarize_slug_check(slug_check),
            }, ensure_ascii=False, indent=2))
            return

        if package_path.stat().st_size > DIRECT_UPLOAD_THRESHOLD_BYTES:
            stage("Uploading large package via Blob")
            blob_upload = upload_via_blob(base_url, cookie_path, package_path)
            done("Blob upload finished")
            stage("Finalizing import")
            upload_payload = run_curl_json([
                "curl",
                "-sS",
                "-b",
                str(cookie_path),
                "-H",
                "Content-Type: application/json",
                "-d",
                json.dumps({
                    "blobUrl": blob_upload["url"],
                    "blobPathname": blob_upload["pathname"],
                    "modelCategory": args.model_category,
                }),
                f"{base_url}/api/import-app",
            ], "upload finalize failed")
        else:
            stage("Uploading package directly")
            upload_payload = run_curl_json([
                "curl",
                "-sS",
                "-b",
                str(cookie_path),
                "-F",
                f"package=@{package_path}",
                "-F",
                f"modelCategory={args.model_category}",
                f"{base_url}/api/import-app",
            ], "upload failed")
        done("Upload finished")

        if not upload_payload.get("success"):
            raise SystemExit(upload_payload.get("error") or "upload failed")

    if args.save_config:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        save_config(config_path, base_url, email, password)

    app = upload_payload["app"]
    result = {
        "success": True,
        "slug": app.get("slug"),
        "detailUrl": f"{base_url}/apps/{app.get('slug')}",
        "launchUrl": f"{base_url}{app.get('launchUrl', '')}",
        "downloadUrl": f"{base_url}{app.get('downloadUrl', '')}",
        "overwritten": upload_payload.get("overwritten", False),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\nUpload complete.")
    print(f"App detail page: {result['detailUrl']}")
    print(f"App launch page: {result['launchUrl']}")
    if result.get("downloadUrl"):
        print(f"App download link: {result['downloadUrl']}")
    print("\nShare summary:")
    print(f"- App: {app.get('name') or result['slug']}")
    print(f"- Detail: {result['detailUrl']}")
    print(f"- Launch: {result['launchUrl']}")
    if result.get("downloadUrl"):
        print(f"- Download: {result['downloadUrl']}")
    share_text_lines = [
        f"我刚刚发布了一个 CLAWSPACE 应用：{app.get('name') or result['slug']}",
        f"详情页：{result['detailUrl']}",
        f"体验页：{result['launchUrl']}",
    ]
    if result.get("downloadUrl"):
        share_text_lines.append(f"下载页：{result['downloadUrl']}")
    print("\nReady-to-copy share text:")
    print("\n".join(share_text_lines))


if __name__ == "__main__":
    main()
