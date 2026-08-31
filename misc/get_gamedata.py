import io
import json
import re
import sys
import zipfile

import httpx
import argparse
from pathlib import Path

manifest_api_url = "https://manifest.tower.sybo.net"
gamedata_api_url = "https://gamedata.tower.sybo.net"

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
    version: str,
    platform: str,
    manifest_secret: str,
    output_path: Path | None,
    environment: str = "prod",
):
    url = f"{manifest_api_url}/v3.0/{game}/{environment}/{version}/{platform}/{manifest_secret}/manifest.json"

    with httpx.Client(http2=True) as client:
        r = client.get(url)
        r.raise_for_status()
        manifest = r.json()

        if output_path:
            dest = output_path / "manifest.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(json.dumps(manifest, indent=2).encode())

            print(f"Saved manifest -> {dest}")
        return manifest


def get_gamedata(
    game: str,
    version: str,
    platform: str,
    gamedata_hash: str,
    output_path: str | Path,
    save_manifest: bool = False,
    save_gamedata_manifest: bool = False,
    extract_data: bool = True,
):
    output_path = Path(output_path)

    url = f"{gamedata_api_url}/v2.0/{game}/{gamedata_hash}/archive.zip"

    with httpx.Client(http2=True) as client:
        r = client.get(url)
        r.raise_for_status()

        zf = zipfile.ZipFile(io.BytesIO(r.content))

        try:
            root_manifest_bytes = zf.read("manifest.json")
            if save_manifest:
                dest = output_path / "manifest.json"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(root_manifest_bytes)
        except KeyError:
            root_manifest_bytes = None

        try:
            data_manifest_bytes = zf.read("data/manifest.json")
            if save_gamedata_manifest:
                dest = output_path / "manifest.json"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data_manifest_bytes)
        except KeyError:
            data_manifest_bytes = None

        if extract_data:
            for member in zf.namelist():
                if not member.startswith("data/") or member.endswith("/"):
                    continue

                rel_path = Path(member[len("data/") :])
                dest_path = output_path / rel_path

                dest_path.parent.mkdir(parents=True, exist_ok=True)

                with zf.open(member) as src:
                    dest_path.write_bytes(src.read())

                print(f"Extracted {rel_path} -> {dest_path}")

    return True


def get_all_experiment(
    game: str,
    version: str,
    platform: str,
    manifest_secret: str,
    output_path: Path,
    environment: str = "prod",
):
    base_url = f"{manifest_api_url}/v3.0/{game}/{environment}/{version}/{platform}/{manifest_secret}/manifest.json"

    with httpx.Client(http2=True) as client:
        r = client.get(base_url)
        r.raise_for_status()
        manifest = r.json()

        base_dest = output_path / "manifest.json"
        base_dest.parent.mkdir(parents=True, exist_ok=True)
        base_dest.write_bytes(json.dumps(manifest, indent=2).encode())
        print(f"Saved base manifest -> {base_dest}")

        experiments = manifest.get("experiments", {})
        if not experiments:
            print("No experiments found in manifest")
            return manifest

        print(f"Found {len(experiments)} experiments, fetching gamedata for each...")

        experiments_dir = output_path / "experiments"
        experiments_dir.mkdir(parents=True, exist_ok=True)

        for name, gamedata_hash in experiments.items():
            exp_dir = experiments_dir / name
            exp_dir.mkdir(parents=True, exist_ok=True)

            try:
                archive_url = (
                    f"{gamedata_api_url}/v2.0/{game}/{gamedata_hash}/archive.zip"
                )
                r = client.get(archive_url)
                r.raise_for_status()

                zf = zipfile.ZipFile(io.BytesIO(r.content))

                try:
                    manifest_bytes = zf.read("data/manifest.json")
                    dest = exp_dir / "manifest.json"
                    dest.write_bytes(manifest_bytes)
                    print(f"  Saved gamedata manifest for {name} -> {dest}")
                except KeyError:
                    pass

                for member in zf.namelist():
                    if not member.startswith("data/") or member.endswith("/"):
                        continue
                    rel_path = Path(member[len("data/") :])
                    dest_path = exp_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src:
                        dest_path.write_bytes(src.read())
                    print(f"    Saved {rel_path}")

            except httpx.HTTPStatusError as e:
                print(f"  Failed experiment {name}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"  Failed experiment {name}: {e}", file=sys.stderr)

        return manifest


def main(args):
    internal_path = None
    ext = None
    version = args.version
    file_path = Path(args.file) if args.file else None

    if file_path:
        ext = file_path.suffix
        if ext not in (".ipa", ".apk", ".apkm"):
            sys.exit("Error: File must be an .ipa, .apk, or .apkm file.")

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

    try:
        if args.all_experiments:
            get_all_experiment(
                args.game,
                version,
                platform,
                args.secret,
                output_path,
            )
        else:
            manifest = get_manifest(
                args.game,
                version,
                platform,
                args.secret,
                output_path if args.manifest else None,
            )

            if args.gamedata or args.gamedatamanifest:
                gamedata_hash = manifest.get("gamedata")
                if not gamedata_hash:
                    sys.exit("Error: manifest does not contain a gamedata hash")

                get_gamedata(
                    args.game,
                    version,
                    platform,
                    gamedata_hash,
                    output_path,
                    save_manifest=args.gamedatamanifest,
                    extract_data=args.gamedata,
                )
    except httpx.HTTPStatusError as e:
        print(f"Archive request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gamedata downloader")

    parser.add_argument("-f", "--file", type=str, default=None)
    parser.add_argument("-v", "--version", type=str, help="Game version (X-Y-Z)")
    parser.add_argument(
        "-g", "--game", type=str, help="Game name (required with --secret)"
    )
    parser.add_argument("-s", "--secret", type=str, default=None)
    parser.add_argument(
        "--all-experiments",
        action="store_true",
        dest="all_experiments",
        help="Fetch manifest for every experiment",
    )
    parser.add_argument("-p", "--platform", type=str, default="android")

    parser.add_argument(
        "--gamedata",
        action="store_true",
        help="Gets the gamedata files",
    )

    parser.add_argument(
        "--gamedata-manifest",
        action="store_true",
        dest="gamedatamanifest",
        help="Gets the Gamedata Manifest",
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

    if not args.gamedata and not args.manifest:
        args.gamedata = True

    try:
        main(args)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
