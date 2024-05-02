import json

input_file_path = "gamedata/mailbox.json"
output_file_path = "upload/mailbox_data.json"

with open(input_file_path, "r") as input_file:
    data = json.load(input_file)
    entries = data.get(
        "entries", {}
    )  # Get the "entries" dictionary from the loaded JSON data

    # Extract names of each entry dictionary
    entry_names = list(entries.keys())

output_data = {"entries": entry_names}

with open(output_file_path, "w") as output_file:
    json.dump(output_data, output_file, indent=2)
