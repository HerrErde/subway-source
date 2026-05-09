import json

input_file_path = "temp/gamedata/mailbox.json"
output_file_path = "temp/upload/mailbox_data.json"


def main():
    with open(input_file_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
        entries = data.get("entries", {})

    output_data = {"entries": list(entries.keys())}

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, indent=2)


if __name__ == "__main__":
    main()
