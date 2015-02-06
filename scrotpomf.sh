#!/bin/bash
# scrot -> pomf.se, by @__akiaki

SCROTARGS=()

while (( "$#" )); do
    if [ "$1" == "--delete" ]; then
        DELETE=1
    else
        SCROTARGS+=($1)
    fi
    shift
done

# take the shot
    FILE="`scrot ${SCROTARGS[@]} -e 'echo -n $f'`"

# upload it and grab the URL
BASE=""; TRY=0
while [[ "x$BASE" == "x" ]] && [[ $TRY -lt 3 ]]; do
    TRY=$[$TRY + 1]
    echo "Uploading... (try $TRY)"
    JSON="`curl -sf -F "files[]=@$FILE" http://pomf.se/upload.php`"
    BASE="`echo "$JSON" | python -c "from __future__ import print_function;print(__import__('json').loads(__import__('sys').stdin.read())['files'][0]['url'])" 2>/dev/null`"
done

if [[ $TRY -eq 3 ]]; then
    echo "Giving up."
    exit 1
fi

URL="http://a.pomf.se/$BASE"

# copy the URL to the clipboard
if [[ `type -p xclip` ]]; then
    echo -n "$URL" | xclip -selection clipboard
    echo "$URL (has been copied to clipboard)"
elif [[ `type -p pbcopy` ]]; then
    echo -n "$URL" | pbcopy
    echo "$URL (has been copied to clipboard)"
else
    echo "$URL"
fi

if [[ $DELETE -eq 1 ]]; then
    rm -f "${FILE}"
fi
