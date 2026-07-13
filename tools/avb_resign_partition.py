#!/usr/bin/env python3
"""Re-sign a chained AVB partition (dtbo, boot, vendor_boot, ...) so it
verifies against a reference vbmeta image.

Why this exists
---------------
On this device (UMS512 / T618) every verified partition is a *chain*
partition: vbmeta.img stores, per partition, a chain descriptor that names
the public key the partition's own AVB footer must be signed with (it does
NOT store the partition's hash). The partition image carries its own vbmeta
in an AVB hash footer.

So when you modify a chained partition (e.g. patch dtbo for OC, or fix an
fstab), two things must hold or the bootloader hard-fails and the device
boot-loops:

  1. the footer's hash must cover the new content, and
  2. the footer must be signed with the key whose public half matches the
     chain descriptor in vbmeta.img.

The classic mistake is signing dtbo with the vbmeta key (or a test key)
instead of the boot key. avbtool will happily produce that image and it will
brick-loop, because the chain descriptor pubkey will not match.

This script removes that footgun: it reads the expected public key straight
out of the reference vbmeta.img chain descriptor, finds the private key in
your keys dir whose public half matches, and signs with that. If no local
key matches, it refuses rather than signing with the wrong one. vbmeta.img
is never modified (for a content change it does not need to be).

Usage
-----
    # Re-sign the modified dtbo so it matches the stock vbmeta:
    python3 tools/avb_resign_partition.py \
        --image /path/to/dtbo.img \
        --vbmeta /path/to/vbmeta.img \
        --keys-dir keys

    # Explicit partition name (otherwise inferred from the image footer):
    python3 tools/avb_resign_partition.py --image boot.img --partition boot \
        --vbmeta vbmeta.img --keys-dir keys -o boot.signed.img

By default the image is re-signed in place (a .bak copy is kept). Use -o to
write to a separate file instead.

Requirements
------------
avbtool. The repo ships a vendored copy at tools/avbtool (run with the system
python3, so it is not affected by snap sandboxing). Override with --avbtool.
avbtool shells out to `openssl`, which must be on PATH.
"""

import argparse
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AVBTOOL = os.path.join(HERE, "avbtool")
DEFAULT_KEYS_DIR = os.path.join(HERE, "..", "keys")


def run(cmd, capture=True):
    """Run a command, raising with useful context on failure."""
    res = subprocess.run(cmd, capture_output=capture, text=True)
    if res.returncode != 0:
        out = (res.stdout or "") + (res.stderr or "")
        raise RuntimeError(f"command failed ({res.returncode}): {' '.join(cmd)}\n{out}")
    return res.stdout if capture else ""


def avb(avbtool, *args):
    return run([sys.executable, avbtool, *args])


def info_image(avbtool, image):
    return avb(avbtool, "info_image", "--image", image)


def pubkey_sha1(avbtool, key_pem):
    """SHA1 of the AVB-format public key blob for a PEM key (matches the
    'Public key (sha1)' avbtool prints for chain descriptors)."""
    with tempfile.NamedTemporaryFile(suffix=".avbpub", delete=False) as tf:
        tmp = tf.name
    try:
        avb(avbtool, "extract_public_key", "--key", key_pem, "--output", tmp)
        return hashlib.sha1(open(tmp, "rb").read()).hexdigest()
    finally:
        os.unlink(tmp)


def parse_chain_descriptor(vbmeta_info, partition):
    """Return (pubkey_sha1, rollback_index_location) for `partition` from the
    text of `avbtool info_image` on a vbmeta image."""
    # Blocks look like:
    #     Chain Partition descriptor:
    #       Partition Name:          dtbo
    #       Rollback Index Location: 6
    #       Public key (sha1):       ea410c...
    pat = re.compile(
        r"Chain Partition descriptor:\s*"
        r"Partition Name:\s*(?P<name>\S+)\s*"
        r"Rollback Index Location:\s*(?P<ril>\d+)\s*"
        r"Public key \(sha1\):\s*(?P<pk>[0-9a-fA-F]+)",
        re.MULTILINE,
    )
    for m in pat.finditer(vbmeta_info):
        if m.group("name") == partition:
            return m.group("pk").lower(), int(m.group("ril"))
    return None, None


def parse_footer_params(image_info):
    """Pull the current footer parameters from `avbtool info_image` output.
    Returns a dict with keys that may be missing if there is no footer."""
    params = {"props": []}
    m = re.search(r"^Image size:\s*(\d+) bytes", image_info, re.MULTILINE)
    if m:
        params["partition_size"] = int(m.group(1))
    m = re.search(r"^Algorithm:\s*(\S+)", image_info, re.MULTILINE)
    if m:
        params["algorithm"] = m.group(1)
    # Rollback Index (the value, not the chain location); first match is the
    # footer vbmeta's own index.
    m = re.search(r"^Rollback Index:\s*(\d+)", image_info, re.MULTILINE)
    if m:
        params["rollback_index"] = int(m.group(1))
    m = re.search(r"Partition Name:\s*(\S+)", image_info)
    if m:
        params["partition_name"] = m.group(1)
    for pm in re.finditer(r"Prop:\s*(\S+)\s*->\s*'(.*)'", image_info):
        params["props"].append(f"{pm.group(1)}:{pm.group(2)}")
    return params


def find_matching_key(avbtool, keys_dir, want_sha1):
    """Find the private PEM in keys_dir whose AVB pubkey sha1 == want_sha1."""
    candidates = sorted(glob.glob(os.path.join(keys_dir, "*.pem")))
    matches = []
    table = {}
    for pem in candidates:
        try:
            s = pubkey_sha1(avbtool, pem)
        except RuntimeError:
            continue  # public-only or unreadable key, skip
        table[os.path.basename(pem)] = s
        if s == want_sha1:
            matches.append(pem)
    return matches, table


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--image", required=True, help="partition image to re-sign")
    ap.add_argument("--vbmeta", required=True,
                    help="reference vbmeta.img holding the chain descriptor")
    ap.add_argument("--partition",
                    help="partition name (default: inferred from image footer)")
    ap.add_argument("--keys-dir", default=DEFAULT_KEYS_DIR,
                    help="directory of *.pem signing keys (default: repo keys/)")
    ap.add_argument("--avbtool", default=DEFAULT_AVBTOOL,
                    help="path to avbtool (default: vendored tools/avbtool)")
    ap.add_argument("-o", "--output",
                    help="output path (default: re-sign in place, keep .bak)")
    ap.add_argument("--partition-size", type=int,
                    help="override partition size (default: from footer)")
    ap.add_argument("--rollback-index", type=int,
                    help="override footer rollback index (default: from footer)")
    ap.add_argument("--salt", help="hex salt (default: avbtool random salt)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report the plan and key match, do not write")
    args = ap.parse_args()

    for p in (args.image, args.vbmeta):
        if not os.path.isfile(p):
            sys.exit(f"error: not found: {p}")

    img_info = info_image(args.avbtool, args.image)
    footer = parse_footer_params(img_info)

    partition = args.partition or footer.get("partition_name")
    if not partition:
        sys.exit("error: could not infer partition name; pass --partition")

    partition_size = args.partition_size or footer.get("partition_size")
    if not partition_size:
        sys.exit("error: could not determine partition size; pass --partition-size")

    algorithm = footer.get("algorithm", "SHA256_RSA4096")
    rollback_index = args.rollback_index
    if rollback_index is None:
        rollback_index = footer.get("rollback_index", 0)

    vbmeta_info = info_image(args.avbtool, args.vbmeta)
    want_sha1, ril = parse_chain_descriptor(vbmeta_info, partition)
    if not want_sha1:
        sys.exit(f"error: no chain descriptor for '{partition}' in {args.vbmeta}. "
                 f"This partition may not be a chain partition, or the name is wrong.")

    matches, table = find_matching_key(args.avbtool, args.keys_dir, want_sha1)
    print(f"partition:        {partition}")
    print(f"vbmeta expects:   pubkey sha1 {want_sha1} (rollback location {ril})")
    print(f"footer params:    size={partition_size} alg={algorithm} rollback_index={rollback_index}")
    if footer["props"]:
        print(f"props preserved:  {len(footer['props'])}")
    if not matches:
        print("\nkeys scanned:")
        for name, s in table.items():
            print(f"  {s}  {name}")
        sys.exit(f"\nerror: no key in {args.keys_dir} matches the chain descriptor "
                 f"pubkey {want_sha1}. Refusing to sign with the wrong key.")
    key = matches[0]
    print(f"signing key:      {os.path.relpath(key)}  (pubkey matches chain descriptor)")

    if args.dry_run:
        print("\ndry run: no changes written.")
        return

    # Choose the working file.
    if args.output:
        shutil.copyfile(args.image, args.output)
        target = args.output
    else:
        bak = args.image + ".bak"
        if not os.path.exists(bak):
            shutil.copyfile(args.image, bak)
            print(f"backup:           {os.path.relpath(bak)}")
        target = args.image

    # Re-sign: strip any existing footer, then add a correctly-signed one.
    try:
        avb(args.avbtool, "erase_footer", "--image", target)
    except RuntimeError:
        pass  # no existing footer is fine

    add_args = [
        "add_hash_footer",
        "--image", target,
        "--partition_size", str(partition_size),
        "--partition_name", partition,
        "--algorithm", algorithm,
        "--rollback_index", str(rollback_index),
        "--key", key,
    ]
    if args.salt:
        add_args += ["--salt", args.salt]
    for pr in footer["props"]:
        add_args += ["--prop", pr]
    avb(args.avbtool, *add_args)

    # Verify the result end-to-end.
    verify = avb(args.avbtool, "verify_image", "--image", target, "--key", key)
    got = None
    out_info = info_image(args.avbtool, target)
    m = re.search(r"Public key \(sha1\):\s*([0-9a-fA-F]+)", out_info)
    if m:
        got = m.group(1).lower()

    print()
    print(verify.strip())
    if got != want_sha1:
        sys.exit(f"error: post-sign pubkey {got} != expected {want_sha1}")
    print(f"\nOK: {os.path.relpath(target)} signed with the key vbmeta expects "
          f"({want_sha1}).")
    print("Flash this image; vbmeta.img does not need to change.")


if __name__ == "__main__":
    main()
