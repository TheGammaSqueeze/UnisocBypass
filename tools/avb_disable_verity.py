#!/usr/bin/env python3
"""Rebuild a UMS512 vbmeta.img with dm-verity (and optionally all AVB
verification) disabled, so modified system/vendor/product partitions boot.

Why
---
On this device (UMS512 / T618) `androidboot.veritymode=enforcing` is emitted
by libavb from the vbmeta hashtree error mode, independent of the unlock
state. dm-verity then runs over system/vendor/product/socko/odmko in
`restart_on_corruption` mode, so any repack of those partitions (even your own
files) changes the hashtree and the kernel reboots at first read. boot /
vendor_boot / dtbo are not hashtree partitions, which is why they boot fine.

The fix is to set the hashtree-disabled flag in the top-level vbmeta:

    AVB_VBMETA_IMAGE_FLAGS_HASHTREE_DISABLED     (0x1)  -> veritymode=disabled
    AVB_VBMETA_IMAGE_FLAGS_VERIFICATION_DISABLED (0x2)  -> disables ALL AVB

Use 0x1 (the default, --mode hashtree). It keeps the full generated cmdline
(vbmeta digest/size, device_state, ...) but flips veritymode to "disabled", so
fs_mgr mounts those partitions with no dm-verity layer.

Do NOT use 0x2 alone on this device: with VERIFICATION_DISABLED libavb
deliberately emits NO androidboot.* options and, because this is a dynamic
partition device (no `system` partition, everything in `super`), the cmdline
becomes empty -- which reproduces the empty-g_sprd_vboot_cmdline boot failure.
--mode verification is provided for completeness and warns loudly.

Two integrity layers are handled:

1. AVB signature. The rebuilt vbmeta is re-signed with the key already trusted
   by the device (matched automatically from keys/ against the current
   top-level public key -- rsa4096_vbmeta.pem here). All chain partition
   descriptors are preserved exactly, so boot/vendor_boot/dtbo verification is
   unchanged.

2. SPRD wrapper. The vbmeta partition carries a SPRD `sys_img_header` at
   `partition_size - 0x200` (magic 0x42544844) whose SHA256 over the first
   `mImgSize` bytes uboot checks in `check_sprdimgheader`; a stale value hangs
   the boot. This header is preserved and its hash regenerated.

Usage
-----
    python3 tools/avb_disable_verity.py --vbmeta /path/to/vbmeta.img \
        --keys-dir keys -o vbmeta.disabled.img

Flash the output to `vbmeta` (and `vbmeta_bak` if present, since uboot falls
back to it). vbmeta_system / vbmeta_vendor are chained and unchanged.
"""

import argparse
import glob
import hashlib
import importlib.util
import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_AVBTOOL = os.path.join(HERE, "avbtool")
DEFAULT_KEYS_DIR = os.path.join(HERE, "..", "keys")

SPRD_HEADER_MAGIC = 0x42544844          # "DHTB"
SPRD_HEADER_SIZE = 0x200                 # sys_img_header lives in the last 0x200
HASHTREE_DISABLED = 0x1
VERIFICATION_DISABLED = 0x2


def load_avbtool(path):
    import importlib.machinery
    loader = importlib.machinery.SourceFileLoader("avbtool", path)
    spec = importlib.util.spec_from_loader("avbtool", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"command failed ({res.returncode}): {' '.join(cmd)}\n"
                           f"{(res.stdout or '') + (res.stderr or '')}")
    return res.stdout


def avb(avbtool_path, *args):
    return run([sys.executable, avbtool_path, *args])


def pubkey_sha1(avbtool_path, key_pem):
    with tempfile.NamedTemporaryFile(suffix=".avbpub", delete=False) as tf:
        tmp = tf.name
    try:
        avb(avbtool_path, "extract_public_key", "--key", key_pem, "--output", tmp)
        return hashlib.sha1(open(tmp, "rb").read()).hexdigest()
    finally:
        os.unlink(tmp)


def parse_vbmeta(avbmod, data):
    """Return (algorithm_name, rollback_index, flags, [(name, location, pubkey_bytes)])."""
    header = avbmod.AvbVBMetaHeader(data[0:avbmod.AvbVBMetaHeader.SIZE])
    aux_off = avbmod.AvbVBMetaHeader.SIZE + header.authentication_data_block_size
    desc_start = aux_off + header.descriptors_offset
    desc_data = data[desc_start:desc_start + header.descriptors_size]
    descriptors = avbmod.parse_descriptors(desc_data)

    alg_name = None
    for name, alg in avbmod.ALGORITHMS.items():
        if alg.algorithm_type == header.algorithm_type:
            alg_name = name
            break

    chains, others = [], []
    for d in descriptors:
        if isinstance(d, avbmod.AvbChainPartitionDescriptor):
            chains.append((d.partition_name, d.rollback_index_location, d.public_key))
        else:
            others.append(type(d).__name__)
    return alg_name, header.rollback_index, header.flags, chains, others


def sprd_rewrap(template_1mb, new_avb_blob):
    """Place new_avb_blob at offset 0 of a copy of the original 1MB vbmeta
    partition image, zero the rest of the hashed region, and regenerate the
    SPRD sys_img_header SHA256. Everything else in the header is preserved."""
    buf = bytearray(template_1mb)
    part_size = len(buf)
    hdr_off = part_size - SPRD_HEADER_SIZE
    magic = struct.unpack_from("<I", buf, hdr_off)[0]
    if magic != SPRD_HEADER_MAGIC:
        raise ValueError(f"SPRD header magic 0x{magic:x} at 0x{hdr_off:x} "
                         f"!= 0x{SPRD_HEADER_MAGIC:x}; is this a wrapped vbmeta?")
    m_img_size = struct.unpack_from("<I", buf, hdr_off + 0x30)[0]
    if len(new_avb_blob) > m_img_size:
        raise ValueError(f"new vbmeta blob ({len(new_avb_blob)}) exceeds hashed "
                         f"region mImgSize (0x{m_img_size:x})")
    # rewrite payload region: zero [0:mImgSize], then place the new blob
    buf[0:m_img_size] = b"\x00" * m_img_size
    buf[0:len(new_avb_blob)] = new_avb_blob
    new_hash = hashlib.sha256(bytes(buf[0:m_img_size])).digest()
    buf[hdr_off + 8:hdr_off + 8 + 32] = new_hash
    return bytes(buf), m_img_size, new_hash


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vbmeta", required=True, help="input vbmeta.img (SPRD-wrapped)")
    ap.add_argument("--keys-dir", default=DEFAULT_KEYS_DIR)
    ap.add_argument("--avbtool", default=DEFAULT_AVBTOOL)
    ap.add_argument("-o", "--output", help="output path (default: <input>.disabled.img)")
    ap.add_argument("--mode", choices=["hashtree", "verification", "both"],
                    default="hashtree",
                    help="hashtree=disable dm-verity only (0x1, recommended); "
                         "verification=disable all AVB (0x2, empties cmdline on this "
                         "device); both=0x3")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.vbmeta):
        sys.exit(f"error: not found: {args.vbmeta}")
    avbmod = load_avbtool(args.avbtool)

    raw = open(args.vbmeta, "rb").read()
    if raw[0:4] != b"AVB0":
        sys.exit("error: input does not start with an AVB0 vbmeta blob")

    alg_name, rollback_index, cur_flags, chains, others = parse_vbmeta(avbmod, raw)
    if alg_name is None:
        sys.exit("error: could not resolve vbmeta algorithm")
    if others:
        print(f"warning: non-chain descriptors present and will be dropped by "
              f"rebuild: {others}. Stop and use a footer-preserving method if these "
              f"matter.")

    flag_bits = {"hashtree": HASHTREE_DISABLED,
                 "verification": VERIFICATION_DISABLED,
                 "both": HASHTREE_DISABLED | VERIFICATION_DISABLED}[args.mode]
    new_flags = cur_flags | flag_bits

    print(f"algorithm:        {alg_name}")
    print(f"rollback index:   {rollback_index}")
    print(f"flags:            0x{cur_flags:x} -> 0x{new_flags:x} ({args.mode})")
    print(f"chain partitions: {len(chains)} preserved")
    if args.mode in ("verification", "both"):
        print("WARNING: VERIFICATION_DISABLED makes libavb emit NO androidboot.* "
              "options. On this dynamic-partition device the kernel cmdline becomes "
              "empty, which typically fails to boot. Prefer --mode hashtree.")

    # signing key: match the current top-level vbmeta pubkey to a key in keys/
    with tempfile.NamedTemporaryFile(suffix=".curpub", delete=False) as tf:
        cur_pub = tf.name
    try:
        # current top-level public key blob lives in the aux block
        hdr = avbmod.AvbVBMetaHeader(raw[0:avbmod.AvbVBMetaHeader.SIZE])
        aux_off = avbmod.AvbVBMetaHeader.SIZE + hdr.authentication_data_block_size
        pk = raw[aux_off + hdr.public_key_offset:
                 aux_off + hdr.public_key_offset + hdr.public_key_size]
        open(cur_pub, "wb").write(pk)
        want_sha1 = hashlib.sha1(pk).hexdigest()
    finally:
        pass
    key = None
    table = {}
    for pem in sorted(glob.glob(os.path.join(args.keys_dir, "*.pem"))):
        try:
            s = pubkey_sha1(args.avbtool, pem)
        except RuntimeError:
            continue
        table[os.path.basename(pem)] = s
        if s == want_sha1:
            key = pem
    os.unlink(cur_pub)
    if not key:
        print("\nkeys scanned:")
        for n, s in table.items():
            print(f"  {s}  {n}")
        sys.exit(f"\nerror: no key in {args.keys_dir} matches the top-level vbmeta "
                 f"pubkey {want_sha1}. Cannot re-sign.")
    print(f"signing key:      {os.path.relpath(key)}  (matches current vbmeta key)")

    if args.dry_run:
        print("\ndry run: no changes written.")
        return

    out = args.output or (args.vbmeta + ".disabled.img")

    # write chain pubkey blobs and rebuild the vbmeta blob
    tmpdir = tempfile.mkdtemp(prefix="avbdv_")
    try:
        chain_args = []
        for name, loc, pub in chains:
            pkf = os.path.join(tmpdir, f"{name}.avbpub")
            open(pkf, "wb").write(pub)
            chain_args += ["--chain_partition", f"{name}:{loc}:{pkf}"]
        blob_path = os.path.join(tmpdir, "vbmeta_new.bin")
        avb(args.avbtool, "make_vbmeta_image",
            "--output", blob_path,
            "--algorithm", alg_name,
            "--key", key,
            "--rollback_index", str(rollback_index),
            "--flags", str(new_flags),
            *chain_args)
        new_blob = open(blob_path, "rb").read()
    finally:
        for f in glob.glob(os.path.join(tmpdir, "*")):
            os.unlink(f)
        os.rmdir(tmpdir)

    wrapped, m_img_size, new_hash = sprd_rewrap(raw, new_blob)
    open(out, "wb").write(wrapped)

    # verify
    info = avb(args.avbtool, "info_image", "--image", out)
    got_flags = None
    for line in info.splitlines():
        if line.strip().startswith("Flags:"):
            got_flags = int(line.split(":")[1].strip())
            break
    veritymode = "disabled" if (new_flags & HASHTREE_DISABLED) else "(unchanged)"
    print(f"\nnew vbmeta blob:  {len(new_blob)} bytes (hashed region 0x{m_img_size:x})")
    print(f"SPRD wrapper:     regenerated, sha256 {new_hash.hex()[:16]}...")
    print(f"info_image flags: 0x{got_flags:x}" if got_flags is not None else
          "info_image flags: (unread)")
    if got_flags != new_flags:
        sys.exit(f"error: output flags 0x{got_flags:x} != expected 0x{new_flags:x}")
    n_chains_out = info.count("Chain Partition descriptor:")
    if n_chains_out != len(chains):
        sys.exit(f"error: chain descriptor count {n_chains_out} != {len(chains)}")
    print(f"chain descriptors: {n_chains_out} present (all preserved)")
    print(f"\nOK: wrote {os.path.relpath(out)}")
    print(f"    -> androidboot.veritymode will be '{veritymode}'.")
    print("    Flash to vbmeta (and vbmeta_bak). system/vendor/product then mount "
          "without dm-verity.")


if __name__ == "__main__":
    main()
