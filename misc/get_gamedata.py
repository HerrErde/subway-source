import io
import json
import re
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
import argparse
from pathlib import Path

manifest_api_url = "https://manifest.tower.sybo.net"
gamedata_api_url = "https://gamedata.tower.sybo.net"
download_dir = "temp/gamedata"

headers = {
    "User-Agent": "grpc-dotnet/2.63.0 (Mono Unity; CLR 4.0.30319.17020; netstandard2.0; arm64) com.kiloo.subwaysurf/3.45.0",
    "Content-Type": "application/json",
}

MAX_DOWNLOAD_RETRIES = 3
VERSION_RE = re.compile(r"\d{1,2}[.-]\d{1,2}[.-]\d{1,2}")


def get_version_folder(game_file, base_path, apkm=False):
    with zipfile.ZipFile(game_file, "r") as zf:
        if apkm:
            with zf.open("base.apk") as f:
                zip_bytes = f.read()
            zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")

        base_path = base_path.rstrip("/") + "/"

        folders = {
            p[len(base_path) :].split("/")[0]
            for p in zf.namelist()
            if p.startswith(base_path) and "/" in p[len(base_path) :]
        }

        return next(iter(folders), None)


def read_secret(game_file, internal_path, apkm=False):
    with zipfile.ZipFile(game_file, "r") as zf:
        if apkm:
            with zf.open("base.apk") as f:
                zip_bytes = f.read()
                zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
        with zf.open(internal_path) as f:
            data = json.load(f)
        return data.get("Secret"), data.get("Game")


def get_manifest(
    game: str,
    manifest_secret: str,
    version: str,
    platform: str,
    experiment: str = None,
    manifest_path: str = None,
):
    experiment_path = f"/{experiment}" if experiment else ""
    url = f"{manifest_api_url}/v1.0/{game}/{version}/{platform}/{manifest_secret}{experiment_path}/manifest.json"
    with httpx.Client(http2=True) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        manifest = r.json()
        if manifest_path:
            manifest_path.mkdir(parents=True, exist_ok=True)
            dest_path = manifest_path / "manifest.json"

            with dest_path.open("w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        return manifest.get("gamedata")


def get_objects(game: str, gamedata_secret: str):
    url = f"{gamedata_api_url}/v1.0/{game}/{gamedata_secret}/manifest.json"
    with httpx.Client(http2=True) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        gamedata_manifest = r.json()
        return gamedata_manifest.get("objects")


def download_file(game: str, secret: str, filename: str, output_path: str):
    url = f"{gamedata_api_url}/v1.0/{game}/{secret}/{filename}"
    output_path = Path(output_path)
    dest_path = output_path / Path(filename)

    if output_path.exists() and not output_path.is_dir():
        raise RuntimeError(f"'{output_path}' exists but is not a directory")

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    last_error = None
    with httpx.Client(http2=True) as client:
        for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
            try:
                r = client.get(url)
                if r.status_code == 200:
                    with dest_path.open("wb") as f:
                        f.write(r.content)

                    print(f"Downloaded {filename} -> {dest_path}")
                    return True

                last_error = f"HTTP {r.status_code}"
                if attempt < MAX_DOWNLOAD_RETRIES:
                    print(
                        f"Retrying {filename} immediately "
                        f"({attempt}/{MAX_DOWNLOAD_RETRIES}) after {last_error}"
                    )
            except httpx.HTTPError as exc:
                last_error = str(exc)
                if attempt < MAX_DOWNLOAD_RETRIES:
                    print(
                        f"Retrying {filename} immediately "
                        f"({attempt}/{MAX_DOWNLOAD_RETRIES}) after {last_error}"
                    )

    print(f"Failed to download {filename}: {last_error}")
    return False


def expected_filenames(objects: dict):
    return sorted(
        {obj.get("filename") for obj in (objects or {}).values() if obj.get("filename")}
    )


def missing_files(filenames, output_path):
    output_path = Path(output_path)
    missing = []
    for filename in filenames:
        dest_path = output_path / Path(filename)
        if not dest_path.is_file() or dest_path.stat().st_size == 0:
            missing.append(filename)
    return missing


def download_all_files(game: str, secret: str, objects: dict, output_path: str):
    filenames = expected_filenames(objects)
    if not filenames:
        print("No gamedata files found in manifest.")
        return

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(
                download_file, game, secret, filename, output_path
            ): filename
            for filename in filenames
        }
        for future in as_completed(futures):
            future.result()

    pending = missing_files(filenames, output_path)
    if not pending:
        return

    raise RuntimeError(
        "Failed to download all manifest files. Missing: " + ", ".join(pending)
    )


def get_gamedata(args):
    internal_path = None
    ext = None
    version = args.version
    file_path = Path(args.file) if args.file else None

    if file_path:
        ext = file_path.suffix
        if ext not in (".ipa", ".apk", ".apkm"):
            sys.exit("Error: File must have .ipa, .apk, or .apkm extension.")

        platform = "ios" if ext == ".ipa" else "android"

        internal_path = (
            "Payload/SubwaySurf.app/Data/Raw/settings/sybo.tower.default.json"
            if platform == "ios"
            else "assets/settings/sybo.tower.default.json"
        )

        if not version:
            if ext == ".ipa":
                version = get_version_folder(
                    file_path, "Payload/SubwaySurf.app/Data/Raw/aa/iOS"
                )
            elif ext in [".apk", ".apkm"]:
                version = get_version_folder(
                    file_path, "assets/aa/Android", apkm=(ext == ".apkm")
                )

            if not version or not VERSION_RE.match(version):
                print("Error: Could not detect game version folder", file=sys.stderr)
                sys.exit(1)

    elif args.platform:
        # secret-only mode
        platform = args.platform

    # read secret from file if needed
    if file_path and not args.secret:
        args.secret, args.game = read_secret(
            file_path,
            internal_path,
            apkm=(ext == ".apkm"),
        )

    if not args.secret:
        sys.exit("Error: manifest secret is required")

    output_path = Path(args.output or f"{args.game}/{version.replace('.', '-')}")
    output_path.mkdir(parents=True, exist_ok=True)

    version = version.replace("-", ".")

    manifest_path = None
    if args.manifest:
        manifest_path = output_path

    gamedata_secret = get_manifest(
        args.game, args.secret, version, platform, args.experiment, manifest_path
    )

    if args.gamedata:
        objects = get_objects(args.game, gamedata_secret)
        download_all_files(args.game, gamedata_secret, objects, output_path)


def main():
    parser = argparse.ArgumentParser(description="Extract gamedata from Subway Surfers")

    parser.add_argument("-f", "--file", type=str, default=None)
    parser.add_argument("-v", "--version", type=str, help="Game version (X-Y-Z)")
    parser.add_argument(
        "-g", "--game", type=str, help="Game name (required with --secret)"
    )
    parser.add_argument("-s", "--secret", type=str, default=None)
    parser.add_argument("-ex", "--experiment", type=str, default=None)
    parser.add_argument("-p", "--platform", type=str, default="android")

    parser.add_argument(
        "--gamedata",
        action="store_true",
        help="Gets the gamedata files",
    )

    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Gets the Manifest",
    )
    parser.add_argument("-o", "--output", help="Output folder path")

    args = parser.parse_args()

    if not args.file and not args.secret:
        print("Error: either --file or --secret must be provided", file=sys.stderr)
        sys.exit(1)

    if not args.file:
        if not args.version:
            print(
                "Error: --version is required when --file is not set", file=sys.stderr
            )
            sys.exit(1)

        if not VERSION_RE.match(args.version):
            print("Invalid version format. Use X-Y-Z (e.g. 3-57-0).", file=sys.stderr)
            sys.exit(1)

    if args.secret and not args.game:
        print("Error: --game is required when using --secret", file=sys.stderr)
        sys.exit(1)

    if args.file:
        if not Path(args.file).exists():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)

    if not args.file and not args.platform:
        print(
            "Error: either --file or --platform is required",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.gamedata and not args.manifest:
        args.gamedata = True

    try:
        get_gamedata(args)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
