import json
import re

input_file_path = "temp/gamedata/calendars.json"
output_file_path = "temp/upload/calendar_data.json"


def extract_number(s):
    match = re.search(r"\d+", s)
    return int(match.group()) if match else float("-inf")


with open(input_file_path, "r", encoding="utf-8") as input_file:
    calendars = json.load(input_file).get("calendars", [])

if not calendars:
    raise ValueError("No calendars found in the data.")

highest_calendar_id = max(calendars, key=lambda c: extract_number(c.get("id", "")))[
    "id"
]

output_data = {"calendarId": highest_calendar_id}

with open(output_file_path, "w", encoding="utf-8") as output_file:
    json.dump(output_data, output_file, indent=2)
