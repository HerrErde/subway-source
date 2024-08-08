import json

input_file_path = "temp/gamedata/calendars.json"
output_file_path = "temp/upload/calendar_data.json"

with open(input_file_path, "r") as input_file:
    data = json.load(input_file)
    calendars = data.get("calendars", [])
    calendar_id = calendars[0].get("id")

output_data = {"calendarId": calendar_id}

with open(output_file_path, "w") as output_file:
    json.dump(output_data, output_file, indent=2)
