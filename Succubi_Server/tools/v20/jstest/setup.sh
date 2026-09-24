#!/bin/sh
# setup.sh <pack scripts dir> <sandbox dir>: copies the scripts next to fake @minecraft modules
set -e
rm -rf "$2"; mkdir -p "$2/node_modules/@minecraft/server" "$2/node_modules/@minecraft/server-ui"
cp -r "$1"/. "$2/"
HERE=$(dirname "$0")
cp "$HERE/mock_server.js" "$2/node_modules/@minecraft/server/index.js"
cp "$HERE/mock_ui.js" "$2/node_modules/@minecraft/server-ui/index.js"
echo '{"type":"module","main":"index.js"}' > "$2/node_modules/@minecraft/server/package.json"
echo '{"type":"module","main":"index.js"}' > "$2/node_modules/@minecraft/server-ui/package.json"
echo '{"type":"module"}' > "$2/package.json"
