#!/bin/bash

userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
packageId="com.kiloo.subwaysurf"
orgName="sybo-games"
appName="subwaysurfers"
appName2="subway-surfers"

version=$(curl -s "https://gplayapi.srik.me/api/apps/$packageId" | jq -r '.version')
appVer=$(echo $version | tr '.' '-')

page1=$(curl -vsL -A "$userAgent" "https://www.apkmirror.com/apk/$orgName/$appName/$appName-$appVer-release" 2>&1)

grep -q 'class="error404"' <<<"$page1" && echo noversion >&2 && exit 1

#page2=$(pup -p --charset utf-8 ':parent-of(:parent-of(span:contains("APK")))' <<<"$page1")

#readarray -t url1 < <(pup -p --charset utf-8 ':parent-of(div:contains("arm64-v8a + armeabi-v7a")) attr{href}' <<<"$page2")

#[ "${#url1[@]}" -eq 0 ] && echo noapk >&2 && exit 1

#temp fix
url1="/apk/$orgName/$appName/$appName-$appVer-release/$appName2-$appVer-android-apk-download/"

url2=$(curl -sL -A "$userAgent" "https://www.apkmirror.com$url1" | pup -p --charset utf-8 'a:contains("Download APK") attr{href}')

[ "$url2" == "" ] && echo error >&2 && exit 1

url3=$(curl -sL -A "$userAgent" "https://www.apkmirror.com$url2" | pup -p --charset UTF-8 'a[data-google-vignette="false"][rel="nofollow"] attr{href}')

[ "$url3" == "" ] && echo error >&2 && exit 1

echo "https://www.apkmirror.com$url3" >&2

wget -q -c "https://www.apkmirror.com$url3" -O "$appName"-"$appVer".apk --user-agent="$userAgent"
