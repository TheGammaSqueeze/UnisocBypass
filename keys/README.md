# AVB / vbmeta signing keys

RSA-4096 (and RSA-2048) signing key pairs that match the public keys
embedded in the device's `vbmeta_b.img` chain partition descriptors and
in the boot-chain SIMGHDR signature blocks.

These were validated against an Anbernic RG Vita (Unisoc UMS512 / T618)
shipped firmware by extracting each chain partition's pubkey from
`vbmeta_b.img` and comparing the SHA-256 of the pubkey blob to each
`rsa4096_*_pub.bin` here.

## Key to partition mapping (validated)

| Partition | Rollback location in vbmeta_b | Signing key |
|---|---:|---|
| boot | 1 | `rsa4096_boot.pem` |
| vbmeta_system | 2 | `rsa4096_system.pem` |
| vbmeta_system_ext | 3 | unknown (no match in this set) |
| vbmeta_vendor | 4 | `rsa4096_vendor.pem` |
| vbmeta_product | 5 | `rsa4096_product.pem` |
| **dtbo** | **6** | **`rsa4096_boot.pem`** |
| l_modem | 7 | `rsa4096_modem.pem` |
| l_ldsp | 8 | `rsa4096_modem.pem` |
| l_gdsp | 9 | `rsa4096_modem.pem` |
| pm_sys | 10 | `rsa4096_modem.pem` |
| l_agdsp | 11 | `rsa4096_modem.pem` |
| l_cdsp | 12 | `rsa4096_modem.pem` |
| vendor_boot | 15 | `rsa4096_vendor.pem` |
| vbmeta (top-level) | n/a | `rsa4096_vbmeta.pem` |

Note: `dtbo` and `boot` share the same key
(`rsa4096_boot.pem`) but have separate rollback index locations. This
matches the upstream sharkl5Pro `security_feature.mk` convention
(`BOARD_AVB_DTBO_KEY_PATH:=$(CONFIG_PATH)/rsa4096_boot.pem`,
`BOARD_AVB_DTBO_ROLLBACK_INDEX_LOCATION:=5` - the device shipped
with location 6 instead).

## Public key fingerprints (SHA-256 of `_pub.bin` blob)

| Key | sha256 |
|---|---|
| `rsa4096_boot_pub.bin` | `eb0619c347731386b26d1a116a5705a437e3268d840d892d7fa83400ea89466f` |
| `rsa4096_vbmeta_pub.bin` | `7728e30f50bfa5cea165f473175a08803f6a8346642b5aa10913e9d9e6defef6` |
| `rsa4096_vendor_pub.bin` | `db43fce3407465af0dee506d2318108d636a756d00cae1e0be9b725b58784c78` |
| `rsa4096_system_pub.bin` | `754a54e3a8f4e8cc339cf7c55c708f9ae30bf3ee54e00bd7e935bda104ecdd6b` |
| `rsa4096_product_pub.bin` | `31d44f8f7baf629fcc00bfc7f9fceea1fbdfc7fe6139e5c418efe2fe0690ab68` |
| `rsa4096_modem_pub.bin` | `c1694a13baf4185f6dbc522c15393dffa23de9f1276ac1d7a0d42addcd5cc60f` |
| `rsa4096_recovery_pub.bin` | not used by this device's stock partition table |

## Why this matters

UMS512 uboot is built with `CONFIG_VBOOT_SYSTEMASROOT`, which causes the
generic libavb `allow_verification_error` tolerance to be compiled out.
On unlocked devices, hash verification of `boot` and `vendor_boot` is
still skipped via the secboot path's lock check, but `dtbo` (and a
handful of other partitions) goes through `vboot_secure_process_flow`
which makes a TOS SMC call that hard-fails on hash or signature
mismatch regardless of the unlock flag.

The clean way past this is to re-sign the modified `dtbo.img.signed`
with `rsa4096_boot.pem` so the chained vbmeta inside the dtbo footer
verifies against the same pubkey already trusted by the device.

## Signing recipe (dtbo)

```bash
# Re-pack with new content via android_boot_image_editor as usual,
# then strip its testkey-signed AVB footer and add one signed by
# the real OEM key:

avbtool erase_footer --image dtbo.img.signed
avbtool add_hash_footer \
    --image dtbo.img.signed \
    --partition_size 8388608 \
    --partition_name dtbo \
    --algorithm SHA256_RSA4096 \
    --rollback_index 0 \
    --key keys/rsa4096_boot.pem
```

Use the same recipe for any other partition by substituting the right
`--partition_name`, `--rollback_index_location`, and `--key`.

## RSA-2048 keys

`rsa2048_0.pem` and `rsa2048_1.pem` are the SPL/SML/TrustOS/UBoot
SIMGHDR signing keys (Sprd's pre-AVB chain). Now superseded by
`tools/patch_spl.py` for our use case (which NOPs the SPL verify call
sites entirely), but they're kept here for completeness.

`rsa2048_devkey_pub.pem` is a development public key.
