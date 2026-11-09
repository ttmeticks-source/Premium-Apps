#!/bin/bash
set -euo pipefail

ARCH="$(uname -m)"
case "$ARCH" in
  arm64) ASSET="Premium-Apps-macOS-AppleSilicon.zip" ;;
  x86_64) ASSET="Premium-Apps-macOS-Intel.zip" ;;
  *) echo "Unsupported Mac architecture: $ARCH"; exit 1 ;;
esac

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
URL="https://github.com/ttmeticks-source/Premium-Apps/releases/download/latest/$ASSET"
echo "Downloading Premium Apps…"
curl -fL --progress-bar "$URL" -o "$TMP/Premium-Apps.zip"

APP_NAME="Premium Apps.app"
if [ -w "/Applications" ]; then
  TARGET="/Applications"
  rm -rf "$TARGET/$APP_NAME"
  ditto -x -k "$TMP/Premium-Apps.zip" "$TARGET"
elif sudo -v; then
  TARGET="/Applications"
  sudo rm -rf "$TARGET/$APP_NAME"
  sudo ditto -x -k "$TMP/Premium-Apps.zip" "$TARGET"
else
  TARGET="$HOME/Applications"
  mkdir -p "$TARGET"
  rm -rf "$TARGET/$APP_NAME"
  ditto -x -k "$TMP/Premium-Apps.zip" "$TARGET"
fi

echo "Installed to: $TARGET/$APP_NAME"
open "$TARGET/$APP_NAME"
