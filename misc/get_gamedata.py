import io
import json
import os
import re
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor

import httpx

manifest_api_url = "https://manifest.tower.sybo.net"
gamedata_api_url = "https://gamedata.tower.sybo.net"
user_agent = "grpc-dotnet/2.63.0 (Mono Unity; CLR 4.0.30319.17020; netstandard2.0; arm64) com.kiloo.subwaysurf/3.45.0"
download_dir = "temp/gamedata"


def read_secret(zip_file, internal_path, apkm=False):
    if apkm:
        with zipfile.ZipFile(zip_file, "r") as zf:
            with zf.open("base.apk") as f:
                zip_bytes = f.read()
                zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
                with zf.open(internal_path) as f2:
                    data = json.load(f2)
                    return data.get("Secret")
    else:
        with zipfile.ZipFile(zip_file, "r") as zf:
            with zf.open(internal_path) as f:
                data = json.load(f)
                return data.get("Secret")


def get_manifest(game: str, manifest_secret: str, version: str, platform: str):
    headers = {
        "User-Agent": user_agent,
        "Content-Type": "application/json",
    }

    url = f"{manifest_api_url}/v1.0/{game}/{version.replace("-", ".")}/{platform}/{manifest_secret}/manifest.json"
    with httpx.Client(http2=True) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        manifest = r.json()
        return manifest.get("gamedata")


def get_objects(game: str, gamedata_secret: str):
    headers = {
        "User-Agent": user_agent,
        "Content-Type": "application/json",
    }

    url = f"{gamedata_api_url}/v1.0/{game}/{gamedata_secret}/manifest.json"
    with httpx.Client(http2=True) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        gamedata_manifest = r.json()
        return gamedata_manifest.get("objects")


def download_file(game: str, secret: str, filename: str):
    url = f"{gamedata_api_url}/v1.0/{game}/{secret}/{filename}"
    dest_path = os.path.join(download_dir, filename)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    headers = {"User-Agent": user_agent}
    with httpx.Client(http2=True) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        with open(dest_path.lower(), "wb") as f:
            f.write(r.content)
        print(f"Downloaded {filename}")


def download_all_files(game: str, secret: str, objects: dict):
    with ThreadPoolExecutor() as executor:
        for obj in objects.values():
            filename = obj.get("filename")
            if filename:
                executor.submit(download_file, game, secret, filename)


def main(game_file, version):
    _, ext = os.path.splitext(game_file)
    if ext not in [".ipa", ".apk", ".apkm"]:
        print("Error: File must have .ipa, .apk, or .apkm extension.")
        sys.exit(1)

    platform = "ios" if ext == ".ipa" else "android"
    zip_file = f"{os.path.splitext(game_file)[0]}.zip"
    os.rename(game_file, zip_file)

    if platform == "ios":
        internal_path = (
            "Payload/SubwaySurf.app/Data/Raw/settings/sybo.tower.default.json"
        )
    else:
        internal_path = "assets/settings/sybo.tower.default.json"
    secret = read_secret(zip_file, internal_path, apkm=ext == ".apkm")
    os.rename(zip_file, game_file)

    gamedata_secret = get_manifest("subway", secret, version, platform)
    objects = get_objects("subway", gamedata_secret)
    download_all_files("subway", gamedata_secret, objects)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_gamedata.py <file>")
        sys.exit(1)

    filename = sys.argv[1]

    pattern = re.compile(r"^([a-zA-Z0-9\-]+?)-(\d+(?:-\d+)+)\.(?:apk|ipa|apkm)[m]?$")
    match = pattern.match(filename)
    if match:
        version = match.group(2)
    else:
        print("Error: Invalid version format. Use 'X-Y-Z', e.g., '3-12-2'.")
        sys.exit(1)

    main(filename, version)
