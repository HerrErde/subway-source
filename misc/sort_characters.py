import json
import re
import unicodedata
from typing import Any, Optional, Set, Dict, List, Tuple

json_input = "temp/output/characters_output.json"
json_input_links = "temp/upload/characters_links.json"
json_output = "temp/upload/characters_data.json"
products_file = "temp/gamedata/products.json"
locale_file = "temp/output/en_locale.json"


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_string(value):
    return (
        unicodedata.normalize("NFKD", value).encode("ASCII", "ignore").decode("utf-8")
    )


def keyify(value):
    return re.sub(r"[^a-zA-Z0-9]", "", normalize_string(value)).lower()


def _is_outfit_variant_id(value):
    return isinstance(value, str) and value.endswith("Outfit")


def _locale_code_priority(display_key, code):
    return (
        1 if code == display_key else 0,
        1 if not _is_outfit_variant_id(code) else 0,
        1 if not code.startswith("bs") else 0,
    )


def _extract_default_item_id(prod, product_type):
    for item in prod.get("items", []):
        if item.get("type") != product_type:
            continue
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id.endswith(".default"):
            return item_id
    return None


def build_locale_display_to_codes(locale_data):
    mapping: Dict[str, List[str]] = {}
    for key, value in locale_data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            continue
        m = re.match(r"^characters\.([^.]+)\.name$", key)
        if m:
            display_key = keyify(value)
            code = m.group(1)
            if display_key not in mapping:
                mapping[display_key] = []
            if code not in mapping[display_key]:
                mapping[display_key].append(code)
    for display_key, codes in mapping.items():
        codes.sort(key=lambda c: _locale_code_priority(display_key, c), reverse=True)
    return mapping


def build_locale_code_set(locale_data):
    codes = set()
    for key in locale_data.keys():
        if not isinstance(key, str):
            continue
        m = re.match(r"^characters\.([^.]+)\.name$", key)
        if m:
            codes.add(m.group(1))
    return codes


def _resolve_product_display_name(prod, locale):
    raw_name = prod.get("name")
    if not isinstance(raw_name, str) or not raw_name:
        return None

    m = re.match(r"^characters\.([^.]+)\.name$", raw_name)
    if m:
        return locale.get(raw_name, m.group(1))
    else:
        return raw_name


def build_products_name_to_id(products_data, locale_data):
    products = products_data.get("products", {})
    name_to_id = {}

    for prod_id, prod in products.items():
        if not isinstance(prod, dict) or prod.get("productType") != "Character":
            continue

        item_id = _extract_default_item_id(prod, "Character")
        if not item_id:
            continue

        base_id = item_id.split(".", 1)[0]

        k_id = prod_id
        if k_id:
            name_to_id[k_id] = base_id

        display_name = _resolve_product_display_name(prod, locale_data)
        if display_name:
            k_display = keyify(display_name)
            if k_display:
                existing = name_to_id.get(k_display)
                if existing is None:
                    name_to_id[k_display] = base_id
                elif _is_outfit_variant_id(existing) and not _is_outfit_variant_id(
                    base_id
                ):
                    # Prefer the base character ID when display names collide.
                    name_to_id[k_display] = base_id

        if _is_outfit_variant_id(prod_id):
            name_to_id[prod_id] = prod_id

    return name_to_id


def build_link_order_ids(link_data, products_data, locale_data):
    locale_display_to_codes = build_locale_display_to_codes(locale_data)
    locale_codes = build_locale_code_set(locale_data)
    products_name_to_id = build_products_name_to_id(products_data, locale_data)

    ordered = []

    for item in link_data:
        original_name = item.get("name")
        if not isinstance(original_name, str) or not original_name:
            continue

        name_before_paren = re.split(r"\s*\(", original_name, maxsplit=1)[0]
        k = keyify(name_before_paren)
        candidates: List[str] = []

        for base_id in locale_display_to_codes.get(k, []):
            if base_id not in candidates:
                candidates.append(base_id)

        product_id = products_name_to_id.get(k)
        if product_id is not None and product_id not in candidates:
            candidates.append(product_id)

        if k in locale_codes and k not in candidates:
            candidates.append(k)

        if not candidates:
            candidates.append(original_name)

        ordered.append((candidates, original_name))

    return ordered


def sort_json(data, link_ids):
    item_dict = {keyify(item["id"]): item for item in data}
    ordered_data = []
    matched_items = set()

    for candidate_ids, original_name in link_ids:
        matched_dict_key = None
        for c in candidate_ids:
            k_c = keyify(c)
            if k_c in item_dict:
                matched_dict_key = k_c
                break
        if not matched_dict_key:
            for c in candidate_ids:
                k_c = keyify(c)
                for dict_key in item_dict:
                    if dict_key.startswith(k_c) or k_c.startswith(dict_key):
                        matched_dict_key = dict_key
                        break
                if matched_dict_key:
                    break

        if matched_dict_key is not None:
            entry = item_dict.pop(matched_dict_key)
            matched_items.add(keyify(entry["id"]))
            print(f"[{len(ordered_data) + 1}] Match: {entry['id']} -> {original_name}")
            ordered_data.append(
                {
                    "number": len(ordered_data) + 1,
                    "id": entry["id"],
                    "outfits": entry.get("outfits"),
                }
            )
            outfit_keys = sorted(
                [
                    k
                    for k in item_dict
                    if k.startswith(matched_dict_key) and k.endswith("outfit")
                ],
            )
            for ok in outfit_keys:
                outfit_entry = item_dict.pop(ok)
                matched_items.add(keyify(outfit_entry["id"]))
                print(
                    f"[{len(ordered_data) + 1}] Match outfit: "
                    f"{outfit_entry['id']} -> {original_name}"
                )
                ordered_data.append(
                    {
                        "number": len(ordered_data) + 1,
                        "id": outfit_entry["id"],
                        "outfits": outfit_entry.get("outfits"),
                    }
                )
        else:
            fallback_id = candidate_ids[0] if candidate_ids else original_name
            print(
                f"[{len(ordered_data) + 1}] No match for link: "
                f"{original_name} (using {fallback_id})"
            )
            ordered_data.append(
                {
                    "number": len(ordered_data) + 1,
                    "id": fallback_id,
                    "outfits": None,
                }
            )

    # append rest items alphabetically
    remaining_items = [item for item in data if keyify(item["id"]) not in matched_items]
    remaining_items.sort(key=lambda x: x["id"].lower())
    for item in remaining_items:
        ordered_data.append(
            {
                "number": len(ordered_data) + 1,
                "id": item["id"],
                "outfits": item.get("outfits"),
            }
        )
        print(f"Rest: {item['id']} gets appended alphabetically.")

    return ordered_data


def main():
    link_data = read_json(json_input_links)
    products_data = read_json(products_file)
    json_data = read_json(json_input)
    locale_data = read_json(locale_file)

    ordering = build_link_order_ids(link_data, products_data, locale_data)
    ordered_data = sort_json(json_data, ordering)

    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(ordered_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
