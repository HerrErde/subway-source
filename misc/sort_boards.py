import json
import re
import unicodedata
from typing import Optional

json_input = "temp/output/boards_output.json"
json_input_links = "temp/upload/boards_links.json"
json_output = "temp/upload/boards_data.json"
products_file = "temp/gamedata/products.json"


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_string(input_string):
    # Normalize strings by replacing accented characters with their base counterparts
    return (
        unicodedata.normalize("NFKD", input_string)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )


def keyify(value):
    return re.sub(r"[^a-zA-Z0-9]", "", normalize_string(value)).lower()


def _extract_default_item_id(prod, product_type):
    for it in prod.get("items") or []:
        if it.get("type") != product_type:
            continue
        item_id = it.get("id")
        if isinstance(item_id, str) and item_id.endswith(".default"):
            return item_id
    return None


def build_products_name_to_hoverboard_id(products_data):
    products = products_data.get("products") or {}
    name_to_id = {}

    for prod_id, prod in products.items():
        if not isinstance(prod, dict) or prod.get("productType") != "Hoverboard":
            continue
        name = prod.get("name")
        if not isinstance(name, str) or not name:
            continue

        item_id = _extract_default_item_id(prod, "Hoverboard")
        if not item_id:
            continue

        base_id = item_id.split(".", 1)[0]
        k = keyify(name)
        if not k:
            continue

        # Prefer canonical default-product id for the board (usually f"{base_id}_default").
        pri = (
            0 if str(prod_id).lower() == f"{base_id}_default".lower() else 1,
            0 if str(prod_id).lower().endswith("_default") else 1,
            len(str(prod_id)),
        )
        existing = name_to_id.get(k)
        if not existing or pri < existing[0]:
            name_to_id[k] = (pri, base_id)

    return {k: v for k, (_, v) in name_to_id.items()}


def extract_order_ids(link_data, products_data):
    name_to_id = build_products_name_to_hoverboard_id(products_data)
    ordered = []

    for item in link_data:
        if not item.get("available", True):
            continue
        original = item.get("name", "")
        if not isinstance(original, str) or not original:
            continue

        name_before_paren = re.split(r"\s*\(", original, maxsplit=1)[0]
        k = keyify(name_before_paren)
        base_id = name_to_id.get(k)
        if not base_id:
            base_id = name_to_id.get(keyify("Ukulele")) if k == "ukelele" else None
        if base_id:
            ordered.append((base_id, original))
        else:
            # Fallback: try matching the wiki name directly against internal ids.
            ordered.append((original, original))

    return ordered


def append_data(count, ordered_data, item):
    ordered_data.append(
        {
            "number": count,
            "id": item["id"],
            "upgrades": item.get("upgrades"),
        }
    )


def sort_json(data, link_ids):
    item_dict = {keyify(item["id"]): item for item in data}
    ordered_data = []
    matched_items = set()

    for idx, (base_id, original) in enumerate(link_ids):
        found_item = item_dict.get(keyify(base_id))
        if found_item and keyify(found_item["id"]) not in matched_items:
            append_data(
                len(ordered_data) + 1,
                ordered_data,
                found_item,
            )
            matched_items.add(keyify(found_item["id"]))
            print(f"[{idx+1}] Match: {original} -> {found_item['id']}")
        else:
            print(f"[{idx+1}] No match for link: {original}")

    # append rest items alphabetically
    remaining_items = [item for item in data if keyify(item["id"]) not in matched_items]
    remaining_items.sort(key=lambda x: x["id"].lower())
    for item in remaining_items:
        append_data(len(ordered_data) + 1, ordered_data, item)
        print(f"Rest: {item['id']} gets appended alphabetically.")

    return ordered_data


def main():
    link_data = read_json(json_input_links)
    products_data = read_json(products_file)
    json_data = read_json(json_input)

    extracted_ids = extract_order_ids(link_data, products_data)
    ordered_data = sort_json(json_data, extracted_ids)

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(ordered_data, f, indent=2)


if __name__ == "__main__":
    main()
