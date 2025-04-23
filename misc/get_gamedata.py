import os
import sys
import zipfile
import json
import re
import httpx
from concurrent.futures import ThreadPoolExecutor

manifest_api_url = "https://manifest.tower.sybo.net"
gamedata_api_url = "https://gamedata.tower.sybo.net"
user_agent = "grpc-dotnet/2.63.0 (Mono Unity; CLR 4.0.30319.17020; netstandard2.0; arm64) com.kiloo.subwaysurf/3.45.0"
download_dir = "temp/gamedata"


def read_secret(zip_file, internal_path):
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
    game_file = f"temp/{game_file}"
    _, ext = os.path.splitext(game_file)
    if ext not in [".ipa", ".apk"]:
        print("Error: File must have .ipa or .apk extension.")
        sys.exit(1)

    platform = "ios" if ext == ".ipa" else "android"
    zip_file = f"{os.path.splitext(game_file)[0]}.zip"
    os.rename(game_file, zip_file)

    internal_path = (
        "Payload/SubwaySurf.app/Data/Raw/settings/sybo.tower.default.json"
        if platform == "ios"
        else "assets/settings/sybo.tower.default.json"
    )
    secret = read_secret(zip_file, internal_path)
    os.rename(zip_file, game_file)

    gamedata_secret = get_manifest("subway", secret, version, platform)
    objects = get_objects("subway", gamedata_secret)
    download_all_files("subway", gamedata_secret, objects)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python unpack.py <file> <version>")
        sys.exit(1)

    version = sys.argv[2]
    if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", version):
        print("Error: Invalid version format. Use 'X-Y-Z', e.g., '3-12-2'.")
        sys.exit(1)

    main(sys.argv[1], version)
