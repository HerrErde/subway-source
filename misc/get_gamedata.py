import io
import json
import os
import re
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor

import httpx
import argparse

manifest_api_url = "https://manifest.tower.sybo.net"
gamedata_api_url = "https://gamedata.tower.sybo.net"
download_dir = "temp/gamedata"

headers = {
    "User-Agent": "grpc-dotnet/2.63.0 (Mono Unity; CLR 4.0.30319.17020; netstandard2.0; arm64) com.kiloo.subwaysurf/3.45.0",
    "Content-Type": "application/json",
}


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
            dest_path = os.path.join(manifest_path, "manifest.json")
            os.makedirs(manifest_path, exist_ok=True)

            with open(dest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            return
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
    dest_path = os.path.join(output_path, filename)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with httpx.Client(http2=True) as client:
        r = client.get(url)

        if r.status_code == 403:
            print(f"Skipped (403): {url}")
            return

        if r.status_code != 200:
            print(f"Skipped ({r.status_code}): {url}")
            return

        with open(dest_path.lower(), "wb") as f:
            f.write(r.content)

    print(f"Downloaded {filename} -> {dest_path}")


def download_all_files(game: str, secret: str, objects: dict, output_path: str):
    with ThreadPoolExecutor() as executor:
        for obj in objects.values():
            filename = obj.get("filename")
            if filename:
                executor.submit(download_file, game, secret, filename, output_path)


def get_gamedata(args):
    internal_path = None
    ext = None
    version = args.version

    if args.file:
        _, ext = os.path.splitext(args.file)
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
                    args.file, "Payload/SubwaySurf.app/Data/Raw/aa/iOS"
                )
            elif ext in [".apk", ".apkm"]:
                version = get_version_folder(
                    args.file, "assets/aa/Android", apkm=(ext == ".apkm")
                )

            if not version or not re.match(r"^\d{1,2}[.-]\d{1,2}[.-]\d{1,2}$", version):
                print("Error: Could not detect game version folder", file=sys.stderr)
                sys.exit(1)

    elif args.platform:
        # secret-only mode
        platform = args.platform

    # read secret from file if needed
    if args.file and not args.secret:
        args.secret, args.game = read_secret(
            args.file,
            internal_path,
            apkm=(ext == ".apkm"),
        )

    if not args.secret:
        sys.exit("Error: manifest secret is required")

    output_path = args.output or str(version.replace(".", "-"))
    os.makedirs(output_path, exist_ok=True)

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

        if not re.match(r"^\d{1,2}[.-]\d{1,2}[.-]\d{1,2}$", args.version):
            print("Invalid version format. Use X-Y-Z (e.g. 3-57-0).", file=sys.stderr)
            sys.exit(1)

    if args.secret and not args.game:
        print("Error: --game is required when using --secret", file=sys.stderr)
        sys.exit(1)

    filename = None
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        filename = args.file

    if args.version:
        m = re.search(r"(\d{1,2}[.-]\d{1,2}[.-]\d{1,2})", os.path.basename(filename))
        if not m:
            print(
                "Invalid version format. Use X-Y-Z or X.Y.Z (e.g., 3-58-2).",
                file=sys.stderr,
            )
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
