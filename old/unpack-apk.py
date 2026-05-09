import io
import re
import sys
import zipfile
from pathlib import Path


def safe_output_path(output_folder, relative_path):
    base_path = Path(output_folder).resolve()
    target_path = (base_path / relative_path).resolve()

    if base_path not in target_path.parents and target_path != base_path:
        raise ValueError(f"Unsafe archive path: {relative_path}")

    return target_path


def extract_prefix(zip_file, prefix, output_folder):
    prefix = prefix.rstrip("/") + "/"
    extracted = False

    for member in zip_file.infolist():
        if not member.filename.startswith(prefix):
            continue

        relative_path = member.filename[len(prefix) :].lstrip("/")
        if not relative_path:
            continue

        target_path = safe_output_path(output_folder, relative_path)
        if member.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            extracted = True
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        with zip_file.open(member) as source, target_path.open("wb") as target:
            target.write(source.read())
        extracted = True

    return extracted


def resolve_archive_path(version, app_name):
    for extension in (".apk", ".apkm"):
        archive_path = Path(f"temp/{app_name}-{version}{extension}")
        if archive_path.exists():
            return archive_path
    return None


def main(version, app_name):
    archive_path = resolve_archive_path(version, app_name)
    if not archive_path:
        print(
            f"Error: No APK archive found for version '{version}' in temp/.",
            file=sys.stderr,
        )
        sys.exit(1)

    target_folder = Path("temp/gamedata")
    extract_folder = "assets/tower/gamedata"

    with zipfile.ZipFile(archive_path, "r") as archive:
        if extract_prefix(archive, extract_folder, target_folder):
            print("Extracted assets/tower/gamedata")
            return

        if "base.apk" not in archive.namelist():
            print(
                "Error: Neither assets/tower/gamedata nor base.apk was found.",
                file=sys.stderr,
            )
            sys.exit(1)

        with archive.open("base.apk") as nested_file:
            nested_bytes = nested_file.read()

    with zipfile.ZipFile(io.BytesIO(nested_bytes), "r") as base_archive:
        if not extract_prefix(base_archive, extract_folder, target_folder):
            print(
                "Error: assets/tower/gamedata was not found inside base.apk.",
                file=sys.stderr,
            )
            sys.exit(1)

    print("Extracted assets/tower/gamedata from base.apk")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python unpack-apk.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    app_name = "subway-surfers"

    if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", version):
        print(
            "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        sys.exit(1)

    main(version, app_name)
