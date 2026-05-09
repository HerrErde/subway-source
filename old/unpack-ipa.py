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


def main(version, app_name):
    ipa_file = Path(f"temp/{app_name}-{version}.ipa")
    if not ipa_file.exists():
        print(f"Error: The specified .ipa file '{ipa_file}' does not exist.")
        sys.exit(1)

    extract_folder = "Payload/SubwaySurf.app/Data/Raw/tower/gamedata"
    target_folder = Path("temp/gamedata")

    with zipfile.ZipFile(ipa_file, "r") as archive:
        if not extract_prefix(archive, extract_folder, target_folder):
            print(
                f"Error: '{extract_folder}' was not found in '{ipa_file}'.",
                file=sys.stderr,
            )
            sys.exit(1)

    print(f"Extracted {extract_folder}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python unpack-ipa.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    app_name = "subway-surfers"

    if not re.match(r"^\d{1,2}-\d{1,2}-\d{1,2}$", version):
        print(
            "Error: Invalid version format. Please use the format 'X-Y-Z' (e.g., '3-12-2')."
        )
        sys.exit(1)

    main(version, app_name)
