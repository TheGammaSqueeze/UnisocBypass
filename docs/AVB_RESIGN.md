# Re-signing AVB partitions (dtbo, boot, vendor_boot)

How to modify an AVB-verified partition on UMS512 / T618 and have the
bootloader accept it, using `tools/avb_resign_partition.py`.

## When you need this

After patching the SPL and applying `patch_uboot_unlock.py`, the bootloader
is forced-unlocked. On this device that does **not** mean AVB is skipped: the
TrustOS AVB pass still runs and still generates the kernel dm-verity command
line. What "unlocked" buys you is tolerance, but the tolerance is uneven:

| Partition | Verified by | Modified content when unlocked |
|-----------|-------------|--------------------------------|
| `boot`, `vendor_boot` | secboot path, gated by the lock check | tolerated, boots without re-signing |
| `dtbo` (and other `vboot_secure_process_flow` partitions) | TrustOS SMC | **hard-fails on mismatch, boot-loops** |

So a modified `boot` or `vendor_boot` boots as-is on an unlocked device, but a
modified `dtbo` must be correctly re-signed or the device boot-loops. Symptom:
the kernel command line is fine and Android starts, but the device resets in a
loop, and the uboot log shows the dtbo verify going through the TOS path.

## Why vbmeta.img does not change

Every verified partition here is a **chain partition**. `vbmeta.img` stores,
per partition, a *chain descriptor* naming the public **key** that partition's
own AVB footer must be signed with. It does **not** store the partition's hash.
The hash lives in the partition image's own AVB hash footer.

```
vbmeta.img
  chain descriptor "dtbo":  expects pubkey ea410c...  (rollback location 6)
                                   |
dtbo.img  ── AVB footer ──── vbmeta signed with rsa4096_boot.pem (pubkey ea410c...)
                             hash descriptor over the dtbo content
```

Consequences:

- Changing dtbo **content** only requires re-hashing + re-signing the dtbo
  footer. `vbmeta.img` stays stock.
- The footer must be signed with the key the chain descriptor names. For dtbo
  and boot that is `rsa4096_boot.pem`; for vendor_boot it is
  `rsa4096_vendor.pem`. See [`keys/README.md`](../keys/README.md) for the full
  partition-to-key map (validated against the device's `vbmeta_b`).
- The classic brick is signing dtbo with the vbmeta key (or a repack tool's
  test key). avbtool produces the image happily and it boot-loops, because the
  footer pubkey will not match the chain descriptor.

You would only regenerate `vbmeta.img` to change which key signs a partition,
or to add/remove partitions.

## Usage

```bash
# Re-sign a modified dtbo so it matches the stock vbmeta. The tool reads the
# expected key out of vbmeta.img, finds the matching key in keys/, preserves
# the footer parameters, re-signs, and verifies.
python3 tools/avb_resign_partition.py \
    --image /path/to/dtbo.img \
    --vbmeta /path/to/vbmeta.img \
    --keys-dir keys

# Preview without writing:
python3 tools/avb_resign_partition.py --image dtbo.img --vbmeta vbmeta.img \
    --keys-dir keys --dry-run

# Any chain partition works; write to a new file instead of in place:
python3 tools/avb_resign_partition.py --image boot.img --vbmeta vbmeta.img \
    --keys-dir keys --partition boot -o boot.signed.img
```

By default it re-signs in place and keeps a `.bak`. It refuses to run if no key
in `--keys-dir` matches the chain descriptor, so it cannot sign with the wrong
key. Then flash the re-signed image; `vbmeta.img` does not need to change.

Expected output on success:

```
partition:        dtbo
vbmeta expects:   pubkey sha1 ea410c... (rollback location 6)
signing key:      keys/rsa4096_boot.pem  (pubkey matches chain descriptor)
...
vbmeta: Successfully verified footer and SHA256_RSA4096 vbmeta struct in dtbo.img
dtbo:   Successfully verified sha256 hash of dtbo.img
OK: dtbo.img signed with the key vbmeta expects (ea410c...).
```

## avbtool

The script runs the repo-vendored `tools/avbtool` (AOSP avbtool 1.3.0) with the
system `python3`. This matters on WSL: the `android-platform-tools` **snap**
avbtool is sandboxed and cannot read keys under `/work` or other paths outside
`/mnt/c` and `$HOME`, which silently breaks signing. The vendored copy has no
such restriction. `avbtool` shells out to `openssl`, which must be on PATH.

Point `--avbtool` at a different binary if you prefer your own.

## Manual fallback

If you want to do it by hand (same result):

```bash
avbtool erase_footer --image dtbo.img
avbtool add_hash_footer \
    --image dtbo.img \
    --partition_size 8388608 \
    --partition_name dtbo \
    --algorithm SHA256_RSA4096 \
    --rollback_index 0 \
    --key keys/rsa4096_boot.pem

# sanity check: the footer pubkey must equal the vbmeta chain descriptor pubkey
avbtool info_image --image dtbo.img   | grep 'Public key'
avbtool info_image --image vbmeta.img | grep -A3 'Partition Name:          dtbo'
```

## Troubleshooting

- **Boot-loop after flashing a modified dtbo**: the dtbo footer key does not
  match the vbmeta chain descriptor. Re-run the script; check that the reported
  `signing key` line matches the partition in `keys/README.md`.
- **`no key ... matches the chain descriptor`**: your `keys/` set does not
  contain the private key for that partition. You cannot correctly sign it.
- **avbtool "could not open ... key"**: you are using the sandboxed snap
  avbtool on a path it cannot read. Use the vendored `tools/avbtool` (the
  default) or move inputs under `/mnt/c` or `$HOME`.

# Disabling dm-verity (modified system / vendor / product)

Re-signing a chain partition (above) covers `boot`, `vendor_boot`, `dtbo`,
which use whole-image AVB **hash** descriptors. It does not help with
`system` / `vendor` / `product` / `socko` / `odmko`, which use **hashtree**
(dm-verity) descriptors in `vbmeta_system` / `vbmeta_vendor`.

`libavb` emits `androidboot.veritymode=enforcing` from the vbmeta hashtree
error mode (`avb_cmdline.c`), and this is **independent of the unlock state**
(unlock only tolerates a bad vbmeta signature; it does not turn off
dm-verity). So dm-verity runs over those partitions in `restart_on_corruption`
mode, and any repack of them (even with your own unmodified files) changes the
hashtree and the kernel reboots on first read. Symptom: `boot.img` boots but a
custom `system.img`/`vendor.img` reboot-loops with `device-mapper: verity ...
corruption` in the kernel log.

The fix is to set the hashtree-disabled flag in the top-level vbmeta:

```bash
python3 tools/avb_disable_verity.py \
    --vbmeta /path/to/vbmeta.img \
    --keys-dir keys \
    -o vbmeta.disabled.img
# flash vbmeta.disabled.img to vbmeta (and vbmeta_bak)
```

What it does:

- Rebuilds the vbmeta with `AVB_VBMETA_IMAGE_FLAGS_HASHTREE_DISABLED` (0x1),
  which makes libavb emit `androidboot.veritymode=disabled` while keeping the
  rest of the cmdline (vbmeta digest, size, device_state, ...). fs_mgr then
  mounts system/vendor/product with no dm-verity layer.
- Preserves every chain partition descriptor exactly, so boot/vendor_boot/dtbo
  verification is unchanged.
- Re-signs with the key already trusted by the device, auto-matched from
  `keys/` against the current top-level vbmeta public key (`rsa4096_vbmeta.pem`).
- Regenerates the SPRD `sys_img_header` at `partition_size - 0x200` (magic
  `0x42544844`), whose SHA256 uboot checks in `check_sprdimgheader`; a stale
  value hangs the boot, so this is not optional.

This disabled vbmeta is **static and content-independent**: it does not depend
on what you put in system/vendor, so generate it once and keep it in your
flash package. After it is flashed, any modified system/vendor/product boots.

Do NOT use `--mode verification` (flag 0x2) on this device. With
`VERIFICATION_DISABLED`, libavb (`avb_slot_verify.c:1452`) deliberately emits
no `androidboot.*` options; on a dynamic-partition device that yields an empty
kernel command line and fails to boot. `--mode hashtree` (0x1, the default) is
the correct choice. `--mode both` is offered only for completeness.
