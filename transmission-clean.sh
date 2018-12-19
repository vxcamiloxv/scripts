#!/bin/sh
# 
# Script to clean completed torrent after seed ratio limit
#
# Copyright (C) 2018 Distopico <distopico@riseup.net>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# Configuration
HOST=localhost
POST=9091
USER=test
PASS=test
REMOVE_PATH=/Torrents/movies
SERVER="$HOST:$9091 -n $USER:$PASS" 

# use transmission-remote to get done torrent list
TORRENTLIST=`transmission-remote $SERVER --list | sed -e '1d;s/^ *//' | grep 'Done' | cut --only-delimited --delimiter=' ' --fields=1`

# for each torrent in the list
for TORRENTID in $TORRENTLIST
do
    echo Processing: $TORRENTID 

    # check if torrent download is completed
    DONE=`transmission-remote $SERVER --torrent $TORRENTID --info | grep 'Percent Done: 100%'`
    # check torrents ratio 
    RATIO_LIMIT=`transmission-remote $SERVER --session-info | grep 'Default seed ratio limit:' | sed -e 's/[A-Z|a-z]\:*//g' | bc -l`
    RATIO=`transmission-remote $SERVER --torrent $TORRENTID --info | grep 'Ratio:' | sed -e 's/[A-Z|a-z]\:*//g' | bc -l`
    LOCATION=`transmission-remote $SERVER --torrent $TORRENTID --info | grep 'Location:' | sed -e 's/Location\: //g'`
    echo $DONE
    echo Ratio: "${RATIO%.*}"

    # if the torrent is complete and has ratio limit
    if [ "$DONE" ] && [ "${RATIO%.*}" -ge "${RATIO_LIMIT%.*}" ]; then
        # remove the torrent from Transmission
        if [ $LOCATION =~ $REMOVE_PATH ]; then
            echo "Torrent #$TORRENTID is completed, Removing torrent and data from list"
            transmission-remote $SERVER --torrent $TORRENTID --remove-and-delete
        else 
            echo "Torrent #$TORRENTID is completed, Removing torrent from list"
            transmission-remote $SERVER --torrent $TORRENTID --remove
        fi
    else
        echo "Torrent #$TORRENTID is not completed. Ignoring."
    fi
    printf "\n"
done
