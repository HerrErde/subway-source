import json

def extract(json_input_links):
    with open(json_input_links, 'r') as f:
        data = json.load(f)

    names = [item.get('name', '') for item in data]
    names = [name.replace("Hoverboard", "default").replace(" ", "") for name in names]

    return names

def sort_json(json_input, names, json_output):
    with open(json_input, 'r') as f:
        data = json.load(f)

    names = [name.lower() for name in names]

    ordered_data = [item for name in names for item in data if 'id' in item and item['id'].replace(" ", "").lower() == name]

    with open(json_output, 'w') as f:
        json.dump(ordered_data, f, indent=2)

json_input = 'boards_output.json'
json_input_links = 'boards_links.json'
json_output = 'boards_data.json'

names = extract(json_input_links)
sort_json(json_input, names, json_output)
