#!/usr/bin/env bash
# Self-test: run every tool against the example images and verify the output
# matches the known-good reference files.
#
# Usage:
#   ./scripts/selftest.sh

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0

check() {
    local name="$1"; shift
    if "$@" >/dev/null 2>&1; then
        echo "  PASS: $name"
        pass=$((pass + 1))
    else
        echo "  FAIL: $name"
        fail=$((fail + 1))
    fi
}

byte_equal() {
    local a="$1" b="$2"
    cmp -s "$a" "$b"
}

echo "Running self-tests..."
echo

echo "[1/6] dhtb_parse.py on stock SPL"
check "dhtb_parse exit 0" python3 tools/dhtb_parse.py examples/spl_stock.img

echo
echo "[2/6] verify_image.py on stock images"
check "verify stock SPL" python3 tools/verify_image.py examples/spl_stock.img
check "verify stock uboot" python3 tools/verify_image.py examples/uboot_stock.img

echo
echo "[3/6] patch_spl.py produces byte-exact output"
python3 tools/patch_spl.py examples/spl_stock.img "$TMP/spl.img" >/dev/null
check "patched SPL matches reference" byte_equal "$TMP/spl.img" examples/spl_patched.img
check "patched SPL hash valid" python3 tools/verify_image.py "$TMP/spl.img"

echo
echo "[4/6] modify_uboot.py produces byte-exact output"
python3 tools/modify_uboot.py examples/uboot_stock.img -o "$TMP/uboot.img" \
    --mask "WARNNING: LOCK FLAG IS : UNLOCK, SKIP VERIFY!!!" \
    --mask "INFO: LOCK FLAG IS : UNLOCK!!!" \
    --mask-char "1" >/dev/null
check "modified uboot matches reference" byte_equal "$TMP/uboot.img" examples/uboot_modified.img
check "modified uboot hash valid" python3 tools/verify_image.py "$TMP/uboot.img"

echo
echo "[5/6] example script produces byte-exact output"
python3 examples/uboot_modify_example.py examples/uboot_stock.img "$TMP/uboot_ex.img" >/dev/null
check "example uboot matches reference" byte_equal "$TMP/uboot_ex.img" examples/uboot_modified.img

echo
echo "[6/6] rehash.py roundtrip"
cp examples/uboot_stock.img "$TMP/roundtrip.img"
python3 tools/rehash.py "$TMP/roundtrip.img" >/dev/null
check "rehash produces same bytes on unmodified" byte_equal "$TMP/roundtrip.img" examples/uboot_stock.img

echo
echo "=== Results: $pass passed, $fail failed ==="
[[ $fail -eq 0 ]]
