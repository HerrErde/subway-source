#!/bin/bash

# Read the file content into a variable
file_content=$(cat boards.json)

# Extract the board names
board_names=$(echo "$file_content" | jq -r '.boards | keys[]')

# Loop through each board name
for name in $board_names; do
  echo "Board Name: $name"

  # Extract the data for the current board
  data=$(echo "$file_content" | jq ".boards[\"$name\"]")

  # Extract the desired fields from the data
  board_id=$(echo "$data" | jq -r '.id')
  priority=$(echo "$data" | jq -r '.priority')

  # Extract upgrades if available, otherwise set as "none"
  upgrades=$(echo "$data" | jq -r '.upgrades | if length > 0 then .[] | {id, variation: {name, powerType}} else "none" end')

  # Print the extracted data
  echo "Board ID: $board_id"
  echo "Priority: $priority"
  echo "Upgrades:"
  if [ "$upgrades" != "none" ]; then
    echo "$upgrades"
  else
    echo "none"
  fi
  echo
done
