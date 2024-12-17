import json
import re
import unicodedata

from rapidfuzz import fuzz

json_input = "temp/output/boards_output.json"
json_input_links = "temp/upload/boards_links.json"
json_output = "temp/upload/boards_data.json"
replace_file = "replace.json"

ignore_strings = ["nflpa", "sakar"]


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_string(input_string):
    # Normalize strings by replacing accented characters with their base counterparts
    normalized = (
        unicodedata.normalize("NFKD", input_string)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    return normalized


def extract(link_data, replace_data):
    # Extract and process link names
    item_replace = replace_data.get("Hoverboards", {})

    def process_name(name):
        name = normalize_string(name)
        for item, replacement in item_replace.items():
            name = name.replace(item, replacement)
        name = re.sub(r"[^a-zA-Z0-9]", "", name)
        name = re.sub(r"\bhoverboard\b", "default", name.lower())
        return name

    link_names = [
        process_name(item.get("name", ""))
        for item in link_data
        if item.get("available", True)
    ]

    # Replace birthdays in link names
    year = 2021
    for i in range(2, len(link_names) + 1):
        exponent = i + 7
        birthday = f"{exponent}thbirthday"
        link_names = [name.replace(birthday, f"birthday{year}") for name in link_names]
        year += 1

    return link_names


def append_data(item_id, count, ordered_data, item):
    ordered_data.append(
        {
            "number": count,
            "id": item["id"],
            "upgrades": item.get("upgrades"),
        }
    )


def calculate_similarity(name1, name2):
    similarity = fuzz.ratio(name1, name2)
    return similarity


def sort_json(data, link_names, ignore_strings):
    # Sort and process JSON data based on link names with additional preprocessing

    # Initialize lists to store sorted data and unmatched link names
    ordered_data = []  # List for sorted JSON items
    unmatched_data = []  # List for names that couldn't be matched

    # Preprocess items and create a dictionary for fast lookups by ID (lowercased and cleaned)
    data_dict = {}
    for item in data:
        item_id = item["id"].lower()
        for ignore in ignore_strings:
            item_id = item_id.replace(ignore, "")
        data_dict[item_id] = item

    # Iterate over the provided link names to match them with data items
    for name in link_names:
        best_match = None  # Track the best-matching item
        best_score = 0  # Track the highest similarity score

        # Try to find an exact match first
        item = data_dict.pop(name, None)
        if item:
            append_data(name, len(ordered_data) + 1, ordered_data, item)
            continue

        # If no exact match is found, look for the best fuzzy match
        for key, item in data_dict.items():
            modified_key = key  # Start with the current key (ID)

            # Remove unwanted strings specified in 'ignore_strings'
            for ignore in ignore_strings:
                modified_key = modified_key.replace(ignore, "")

            # Calculate the similarity score between the modified key and the current link name
            score = calculate_similarity(name, modified_key)

            # Update the best match if the current score is the highest
            if score > best_score:
                best_score = score
                best_match = (key, item)

        # If a match is found, append the data and remove it from the dictionary
        if best_match:
            key, item = best_match
            append_data(key, len(ordered_data) + 1, ordered_data, item)
            data_dict.pop(key, None)  # Remove matched item to avoid duplicates
        else:
            # Add the unmatched name to the unmatched_data list
            unmatched_data.append(name)

    # Append any remaining items in the dictionary that were not matched
    for item_id, item in data_dict.items():
        append_data(item_id, len(ordered_data) + 1, ordered_data, item)

    # Write the processed data to the output JSON file
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(ordered_data, f, indent=2)

    # Return the ordered data and the list of unmatched names
    return ordered_data, unmatched_data


def main():
    link_data = read_json(json_input_links)
    replace_data = read_json(replace_file)
    json_data = read_json(json_input)

    link_names = extract(link_data, replace_data)
    sort_json(json_data, link_names, ignore_strings)


if __name__ == "__main__":
    main()
