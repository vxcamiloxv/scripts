#!/bin/sh
# Description:
# --------------
# An ugly and improvised script to get artifacts than maven can't get due are too old
# or archived. JDEE run `mvn dependency:build-classpath -Dclassifier=sources` to get
# the sources to maven project but when maven can't get the sources this script helps
# to look for the artifact on some repositories or install from manually download
# --------------
# Usage: /artifacts.sh PATH:PACKAGE:TYPE:VERSION PATH_TO_DOWNLOAD (under maven project)
# Example: ./artifacts.sh com.psddev:forms:jar:1.0-20141021.141426-97 $HOME/Downloads/
# ---------------
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
CP=/usr/bin/cp
WGET=/usr/bin/wget
MVN=/usr/bin/mvn
REPOS=("http://central.maven.org/maven2/" "https://artifactory.psdops.com/public/")

# get package values
PARTS=()
IFS=':' read -ra ADDR <<< "$1"
for i in "${ADDR[@]}"; do
    PARTS+=("$i")
done

version=${PARTS[3]}
numberVersion=(${version//-/ })
file="${PARTS[1]}-${PARTS[3]}.${PARTS[2]}"
packagePath=${PARTS[0]}
packageUrlPath=${packagePath//./\/}
urlPath="$packageUrlPath/${PARTS[1]}/${numberVersion[0]}/$file"
urlPathFallback="$packageUrlPath/${PARTS[1]}/$version/$file"
urlPathSnapshot="$packageUrlPath/${PARTS[1]}/${numberVersion[0]}-SNAPSHOT/$file"
localPath="$HOME/.m2/repository/$packageUrlPath/${PARTS[1]}/$version"
localPathSnapshot="$HOME/.m2/repository/$packageUrlPath/${PARTS[1]}/${numberVersion[0]}-SNAPSHOT"

# Custom download path
tempDir=/tmp/
if [ ! -z "$2" ]; then
    tempDir=$2
fi
# Install maven command
COMMAND="install:install-file -DgroupId=${PARTS[0]} -DartifactId=${PARTS[1]} -Dversion=$version -Dclassifier=sources -Dpackaging=jar -Dfile=$tempDir/$file"

ensureSource () {
    $CP "$localPath/${PARTS[1]}-$version-sources.${PARTS[2]}" "$localPath/${PARTS[1]}-$version-sources.jar"
    if [ $? -ne 0 ]; then
        $CP "$localPathSnapshot/${PARTS[1]}-${numberVersion[0]}-SNAPSHOT-sources.${PARTS[2]}" "$localPathSnapshot/${PARTS[1]}-$version-sources.jar"
        return $?
    fi
    return 0
}

download () {
    URL=$1
    $WGET -q --spider $URL
    if [ $? -eq 0 ]; then
        echo "Get file from $URL"
        $WGET $URL -P $tempDir
        $MVN $COMMAND
        ensureSource
        return 0
    fi
    return 1
}

for repo in ${REPOS[@]}; do
    echo "Try with: $repo"
    
    download "$repo/$urlPath"
    if [ $? -eq 0 ]; then
        echo "Success!!"
        exit 0
        break
    fi

    download "$repo/$urlPathFallback"
    if [ $? -eq 0 ]; then
        echo "Success!!"
        exit 0
        break
    fi

    echo "Look for SNAPSHOT:"
    download "$repo/$urlPathSnapshot"
    if [ $? -eq 0 ]; then
        echo "Success!!"
        exit 0
        break
    fi
    
    echo "Not found"
    echo ""
done

# Downloaded manually but helps to add and copy the source to a correct name
echo "Not found"
echo ""
if [ ! -f "$tempDir/$file" ]; then
    echo "$tempDir/$file not found!"
    exit 1
fi
echo "Try inatall manually: $file"
$MVN $COMMAND
ensureSource
if [ $? -ne 0 ]; then
    echo "Error install artefact $file"
    exit 1
fi

echo "Success!!"
