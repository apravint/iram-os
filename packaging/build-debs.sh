#!/usr/bin/env bash
# ==============================================================================
# IRAM OS Modular Debian Package Builder
# Builds:
#   1. iram-desktop-core.deb
#   2. iram-agentic-stack.deb
#   3. storytold-craft-suite.deb
#   4. iram-os.deb (metapackage)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$REPO_DIR/dist/packages"
mkdir -p "$OUTPUT_DIR"

echo "📦 Building IRAM OS Modular Packages..."

build_pkg() {
    local name="$1"
    local staging="$SCRIPT_DIR/$name"
    echo "  → Packaging $name..."

    # Ensure permissions
    chmod 0755 "$staging/DEBIAN"
    chmod 0644 "$staging/DEBIAN/control"

    dpkg-deb --build --root-owner-group "$staging" "$OUTPUT_DIR/${name}_26.10.1_all.deb"
    echo "    ✓ Generated $OUTPUT_DIR/${name}_26.10.1_all.deb"
}

build_pkg "iram-desktop-core"
build_pkg "iram-agentic-stack"
build_pkg "storytold-craft-suite"
build_pkg "iram-os"

echo -e "\n🎉 All Debian packages built successfully in: $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/*.deb
