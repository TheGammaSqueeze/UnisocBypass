# SIMGHDR signature block format

The SIMGHDR is a 1172-byte (0x494) signature block appended after the data payload in every DHTB image. It holds the RSA-2048 public key, two SHA256 hashes, and the RSA signature that a bootloader would verify.

## Layout

```
offset  size  field
-----------------------------------------------------------------
0x000   8     magic              "SIMGHDR\0"
0x008   8     (reserved)
0x010   8     data_size          payload size (matches DHTB data_size)
0x018   8     header_size        0x200 (DHTB header size)
0x020   8     sig_struct_size    0x254 (signature structure size)
0x028   8     total_offset       DHTB + data + SIMGHDR header offset
0x030   48    padding
0x060   8     flags              0x00000800'00000001 (RSA-2048 marker?)
0x068   4     RSA_exponent       65537 (0x00010001), big-endian
0x06c   252   RSA_modulus        (key is 256 bytes total including the 4-byte exponent)
0x168   4     modulus_tail       last 4 bytes of modulus if you treat 0x68 as exponent-first
0x16c   32    data_hash_copy     same as DHTB hash (SHA256 of payload)
0x18c   32    second_hash        unknown purpose (not the DHTB header hash, not a header-zeroed hash)
0x1ac   8     end_flags          0x00000000'00000001
0x1b4   256   RSA_signature      PKCS / PSS-style signature (256 bytes = 2048 bits)
0x2b4   480   padding            zeros
```

Total: 0x494 (1172) bytes.

## The two hashes

The `data_hash_copy` at +0x16C is a duplicate of the DHTB hash. SPL's RSA verify function reads SHA256 of the loaded data into a local buffer and compares it against this field (after RSA verifying the signature).

The `second_hash` at +0x18C is unidentified. It is not the SHA256 of:
- The DHTB header (full or zeroed)
- The first 0x60 bytes of SIMGHDR
- The key region 0x60..0x16c
- Any obvious combination

Empirically, it is also read by the SPL verify code path (see `tools/patch_spl.py` analysis). Since we NOP the verify path entirely, we do not need to reproduce this hash correctly for the bypass to work.

## Key identification

Two distinct signing keys are used across the Vita firmware:

| Key | Modulus prefix | Images signed |
|-----|---------------|---------------|
| A | `d0a0300adc72c62f...` | SPL, FDL1 |
| B | `ad7e67e09f57f0a3...` | SML, TrustOS, UBoot, FDL2 |

Both keys are RSA-2048 with exponent 65537. Their modulus values do NOT match any public AOSP test key. They appear to be Unisoc reference/test keys from the alps SDK (not publicly distributed at this time).

## Why we cannot re-sign

Without the private keys matching these moduli, we cannot produce valid SIMGHDR signatures. The SPL's `verify_rsa` function would reject any modified image. This is why we instead patch the SPL to skip verification entirely, at which point SIMGHDR signature validity becomes irrelevant.

Only the DHTB hash remains enforced (by BootROM on SPL, and implicitly by nothing on other images since SPL no longer checks).

## Inspecting a SIMGHDR

```bash
python3 tools/dhtb_parse.py some_image.img
```

Sample output from stock uboot:

```
SIMGHDR (at 0xdaa20):
  magic:           b'SIMGHDR\x00'
  data_size:       0xda820
  header_size:     0x200
  sig_struct_size: 0x254
  total_offset:    0xdaa80
  flags:           0100000000080000
  RSA exponent:    65537 (0x10001)
  RSA modulus:     ad7e67e09f57f0a3d14993... (32 hex)
  data_hash_copy:  7f76eb50ccf636d7dc451feaaa4b8bc53fd91c9431f9a58949e5376ae44fbc95
  second_hash:     7728e30f50bfa5cea165f473175a08803f6a8346642b5aa10913e9d9e6defef6
  signature:       3923dfd691afa7801... (32 hex)

SIMGHDR data hash matches DHTB hash: [OK]
RSA signature present (image is formally signed)
Signing key: Key B (SML / TrustOS / UBoot / FDL2 group)
```
