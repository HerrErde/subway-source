import io
import json
import zipfile
import UnityPy
import argparse
import sys
from pathlib import Path

from Crypto.Cipher import AES

HEADER_SIZE = 32
COUNTER_SIZE = 16
KEY_SIZE = 16


def open_inner_android_apk(zf):
    if "base.apk" in zf.namelist():
        return zipfile.ZipFile(io.BytesIO(zf.read("base.apk")), "r")

    apk_files = [n for n in zf.namelist() if n.lower().endswith(".apk")]
    if not apk_files:
        raise FileNotFoundError("No APK found inside archive")

    return zipfile.ZipFile(io.BytesIO(zf.read(apk_files[0])), "r")


def find_bundle(apk_zip, locale):
    bundle_name_part = f"sybo.localization-builtin_assets_localization_strings_{locale}"

    for name in apk_zip.namelist():
        if name.startswith("assets/aa/Android/") and bundle_name_part in name:
            return name

    raise FileNotFoundError(f"Localization bundle not found for locale '{locale}'")


def extract_bundle_bytes(game_file, locale):
    with zipfile.ZipFile(game_file, "r") as outer_zf:
        if game_file.endswith((".apkm", ".xapk")):
            apk_zip = open_inner_android_apk(outer_zf)
        else:
            apk_zip = outer_zf

        try:
            bundle_path = find_bundle(apk_zip, locale)
            print("Bundle:", bundle_path)
            return bundle_path, apk_zip.read(bundle_path)
        finally:
            if apk_zip is not outer_zf:
                apk_zip.close()


def load_text_asset(bundle_bytes, locale):
    environment = UnityPy.load(bundle_bytes)
    text_assets = [obj for obj in environment.objects if obj.type.name == "TextAsset"]
    if not text_assets:
        raise RuntimeError("No TextAsset found in bundle")

    for obj in text_assets:
        text_asset = obj.read()
        name = getattr(text_asset, "m_Name", "")

        if name == locale:
            raw = text_asset.m_Script
            if isinstance(raw, str):
                raw = raw.encode("utf-8", "surrogateescape")
            return name, raw

    available = []
    for obj in text_assets:
        try:
            available.append(getattr(obj.read(), "m_Name", ""))
        except Exception:
            pass

    raise RuntimeError(
        f"TextAsset '{locale}' not found in bundle. Available: {available}"
    )


def decrypt_ctr_header_bytes(data):
    if len(data) < HEADER_SIZE:
        raise ValueError(
            f"File too small: expected at least {HEADER_SIZE} bytes, got {len(data)}"
        )

    counter = data[:COUNTER_SIZE]
    key = data[COUNTER_SIZE:HEADER_SIZE]
    body = data[HEADER_SIZE:]

    out = bytearray()
    counter_value = int.from_bytes(counter, "big")
    aes = AES.new(key, AES.MODE_ECB)

    for offset in range(0, len(body), 16):
        block = body[offset : offset + 16]
        keystream = aes.encrypt(counter_value.to_bytes(16, "big"))
        out.extend(cipher ^ stream for cipher, stream in zip(block, keystream))
        counter_value = (counter_value + 1) & ((1 << 128) - 1)

    return bytes(out)


def iter_bundle_paths(game_file):
    with zipfile.ZipFile(game_file, "r") as outer_zf:
        if game_file.endswith((".apkm", ".xapk")):
            apk_zip = open_inner_android_apk(outer_zf)
        else:
            apk_zip = outer_zf

        try:
            for name in apk_zip.namelist():
                if name.startswith("assets/aa/Android/") and (
                    "sybo.localization-builtin_assets_localization_strings_" in name
                ):
                    yield name
        finally:
            if apk_zip is not outer_zf:
                apk_zip.close()


def list_locales(game_file):
    found = set()

    for bundle_path in iter_bundle_paths(game_file):
        name = bundle_path.split(
            "sybo.localization-builtin_assets_localization_strings_", 1
        )[-1]
        name = name.split("_", 1)[0]
        found.add(name)

    if not found:
        print("No locale bundles found")
        return

    print(", ".join(sorted(found)))


def get_locale(args):
    bundle_path, bundle_bytes = extract_bundle_bytes(args.file, args.locale)
    asset_name, raw_bytes = load_text_asset(bundle_bytes, args.locale)
    plaintext = decrypt_ctr_header_bytes(raw_bytes)

    text = plaintext.decode("utf-8")
    parsed_json = json.loads(text)

    if args.output:
        output_path = Path(args.output)

        # if it's a directory, append filename
        if output_path.exists() and output_path.is_dir():
            output_path = output_path / "locale.json"
        elif not output_path.suffix:
            # path like "temp/output" but doesn't exist yet, treat as dir
            output_path = output_path / "locale.json"
    else:
        output_path = Path("locale.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(parsed_json, indent=2) + "\n",
        encoding="utf-8",
    )


def extract_all_locales(args):
    for bundle_path in iter_bundle_paths(args.file):
        locale = bundle_path.split(
            "sybo.localization-builtin_assets_localization_strings_", 1
        )[-1].split("_", 1)[0]

        print(f"[+] Extracting {locale}")

        with zipfile.ZipFile(args.file, "r") as outer_zf:
            if args.file.endswith((".apkm", ".xapk")):
                apk_zip = open_inner_android_apk(outer_zf)
            else:
                apk_zip = outer_zf

            try:
                bundle_bytes = apk_zip.read(bundle_path)
            finally:
                if apk_zip is not outer_zf:
                    apk_zip.close()

        asset_name, raw_bytes = load_text_asset(bundle_bytes, locale)
        plaintext = decrypt_ctr_header_bytes(raw_bytes)

        text = plaintext.decode("utf-8")
        parsed_json = json.loads(text)

        out_dir = Path(args.output) if args.output else Path("locales")
        out_dir.mkdir(parents=True, exist_ok=True)

        out_file = out_dir / f"{locale}.json"
        out_file.write_text(
            json.dumps(parsed_json, indent=2) + "\n",
            encoding="utf-8",
        )


def main():
    parser = argparse.ArgumentParser(
        description="Extract and decrypt locale data from Subway Surfers"
    )
    parser.add_argument("-f", "--file", required=True, type=str)
    parser.add_argument("-l", "--locale", type=str, default="en")
    parser.add_argument(
        "-L",
        "--list-locales",
        action="store_true",
        help="List available locales in the game file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: <locale>.json)",
    )

    parser.add_argument(
        "-A",
        "--extract-all",
        action="store_true",
        help="Extract all locales",
    )

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.list_locales:
            list_locales(args.file)
        elif args.extract_all:
            extract_all_locales(args)
        else:
            get_locale(args)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
