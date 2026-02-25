import json
import re
import unicodedata

json_input = "temp/output/characters_output.json"
json_input_links = "temp/upload/characters_links.json"
json_output = "temp/upload/characters_data.json"
replace_file = "replace.json"

ignore_strings = ["nflpa"]
other_strings = ["dak", "lamar", "tom", "odell", "patrick", "saquon", "outfit"]


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_string(value):
    return (
        unicodedata.normalize("NFKD", value).encode("ASCII", "ignore").decode("utf-8")
    )


def normalize_id(value):
    return re.sub(r"[ .\-&]", "", value.lower())


def build_link_entries(link_data, replace_data):
    item_replace = replace_data.get("Characters", {})
    entries = []

    for item in link_data:
        if not item.get("available", True):
            continue

        original = item.get("name", "")
        processed = normalize_string(original)
        for src, dst in item_replace.items():
            processed = processed.replace(src, dst)
        processed = normalize_id(processed)

        candidates = [processed]
        replacement = item_replace.get(original)
        if isinstance(replacement, str) and replacement:
            candidates.append(normalize_id(replacement))
        candidates.append(re.sub(r"\s+", "", normalize_string(original).lower()))

        seen = set()
        candidates = [c for c in candidates if c and not (c in seen or seen.add(c))]
        entries.append((processed, original, candidates))

    return entries


def append_data(ordered_data, item):
    ordered_data.append(
        {
            "number": len(ordered_data) + 1,
            "id": item["id"],
            "outfits": item.get("outfits"),
        }
    )


def find_exact_remaining_key(item_dict, candidate):
    cand_norm = normalize_id(candidate)
    for key in item_dict:
        if normalize_id(key) == cand_norm:
            return key
    return None


def sort_json(data, link_entries):
    item_dict = {item["id"].lower(): item for item in data}
    ordered_data = []

    for processed, original, candidates in link_entries:
        found_key = None

        for cand in candidates:
            found_key = find_exact_remaining_key(item_dict, cand)
            if found_key:
                break

        if not found_key:
            for key in item_dict:
                modified_key = key
                for ignore in ignore_strings:
                    modified_key = modified_key.replace(ignore, "")
                for other in other_strings:
                    if other in modified_key:
                        modified_key = modified_key.split(other)[0] + other
                        break
                if processed == modified_key:
                    found_key = key
                    break
                if modified_key.startswith(processed) or processed.startswith(
                    modified_key
                ):
                    found_key = key
                    break

        if not found_key:
            for key in item_dict:
                for cand in candidates:
                    cand_l = cand.lower()
                    if not cand_l:
                        continue
                    if (
                        cand_l == key
                        or key.startswith(cand_l)
                        or cand_l.startswith(key)
                    ):
                        found_key = key
                        break
                if found_key:
                    break

        if found_key:
            item = item_dict.pop(found_key)
            print(f"[{len(ordered_data) + 1}] Match: {item['id']} -> {original}")
            append_data(ordered_data, item)
        else:
            remaining = ", ".join(sorted(item_dict.keys())[:20])
            print(
                f"[{len(ordered_data) + 1}] No match for link: {original} (processed: {processed})"
            )

    for item in data:
        key = item["id"].lower()
        if key in item_dict:
            append_data(ordered_data, item)
            item_dict.pop(key, None)

    return ordered_data


def main():
    link_data = read_json(json_input_links)
    replace_data = read_json(replace_file)
    json_data = read_json(json_input)
    ordered_data = sort_json(json_data, build_link_entries(link_data, replace_data))

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(ordered_data, f, indent=2)


if __name__ == "__main__":
    main()
