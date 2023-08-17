#!/bin/bash

packageId="com.kiloo.subwaysurf"
appName="subwaysurfers"

version=$(curl -s "https://gplayapi.herrerde.xyz/api/apps/$packageId" | jq -r '.version')
appVer=$(echo $version | tr '.' '-')

# Specify the path to the .apk file
apk_file="$appName-$appVer.apk"
echo $apk_file

# Specify the folder to be extracted
extract_folder="assets/tower/gamedata"

# Check if the specified file exists
if [ ! -f "$apk_file" ]; then
    echo "Error: The specified .apk file does not exist."
    exit 1
fi

# Rename the .apk file to .zip
zip_file="${apk_file%.apk}.zip"
mv "$apk_file" "$zip_file"

echo $zip_file

# Unpack the .zip file to the temporary directory
unzip "$zip_file" "$extract_folder/*"

echo "Unpacking completed!"
