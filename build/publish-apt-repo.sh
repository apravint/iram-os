#!/usr/bin/env bash
# ==============================================================================
# IRAM OS - Signed APT Repository Generator
# Turns built .deb files into a static, signed repository servable from any web
# host (GitHub Pages, S3). Signs InRelease and Release.gpg with IRAM_GPG_KEY.
#
# Usage: IRAM_GPG_KEY=<fingerprint> build/publish-apt-repo.sh <deb-dir> <repo-dir> [suite]
#
# Client setup (keep the public key out of the global trust store):
#   curl -fsSL https://<host>/iram-archive-key.asc | sudo tee /etc/apt/keyrings/iram.asc
#   echo "deb [signed-by=/etc/apt/keyrings/iram.asc] https://<host> resolute main" \
#       | sudo tee /etc/apt/sources.list.d/iram.list
#   sudo apt update && sudo apt install iram-os
# ==============================================================================
set -euo pipefail

DEB_DIR="${1:?Usage: publish-apt-repo.sh <deb-dir> <repo-dir> [suite]}"
REPO_DIR="${2:?Usage: publish-apt-repo.sh <deb-dir> <repo-dir> [suite]}"
SUITE="${3:-resolute}"
: "${IRAM_GPG_KEY:?Set IRAM_GPG_KEY to the signing key fingerprint}"

command -v apt-ftparchive >/dev/null || { echo "apt-ftparchive is required (package: apt-utils)" >&2; exit 1; }
gpg --list-secret-keys "$IRAM_GPG_KEY" >/dev/null || { echo "No secret key for $IRAM_GPG_KEY" >&2; exit 1; }

POOL="pool/main"
DIST="dists/$SUITE"
BINARY="$DIST/main/binary-all"
mkdir -p "$REPO_DIR/$POOL" "$REPO_DIR/$BINARY" "$REPO_DIR/$DIST/main/binary-amd64"
cp "$DEB_DIR"/*.deb "$REPO_DIR/$POOL/"

cd "$REPO_DIR"
apt-ftparchive packages "$POOL" > "$BINARY/Packages"
gzip -9 -k -f "$BINARY/Packages"
cp "$BINARY/Packages" "$BINARY/Packages.gz" "$DIST/main/binary-amd64/"

apt-ftparchive \
    -o "APT::FTPArchive::Release::Origin=IRAM OS" \
    -o "APT::FTPArchive::Release::Label=IRAM OS" \
    -o "APT::FTPArchive::Release::Suite=$SUITE" \
    -o "APT::FTPArchive::Release::Codename=$SUITE" \
    -o "APT::FTPArchive::Release::Architectures=all amd64" \
    -o "APT::FTPArchive::Release::Components=main" \
    release "$DIST" > "$DIST/Release.tmp"
mv "$DIST/Release.tmp" "$DIST/Release"

gpg --batch --yes --local-user "$IRAM_GPG_KEY" --armor --detach-sign --output "$DIST/Release.gpg" "$DIST/Release"
gpg --batch --yes --local-user "$IRAM_GPG_KEY" --clearsign --output "$DIST/InRelease" "$DIST/Release"
gpg --armor --export "$IRAM_GPG_KEY" > iram-archive-key.asc

echo "Repository ready in $REPO_DIR (suite: $SUITE)."
