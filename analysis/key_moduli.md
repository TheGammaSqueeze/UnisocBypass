# Unisoc signing keys (UMS512 / T618)

Two distinct RSA-2048 keys sign the bootloader-chain images on UMS512. Neither matches any public AOSP test key. They appear to originate from the Unisoc/Spreadtrum alps SDK.

Both use exponent 65537 (0x10001).

## Key A (SPL + FDL1)

Signs: `spl_a`, `spl_b`, `fdl1-sign.bin`

Modulus (256 bytes, big-endian):

```
d0a0300adc72c62f824126905c717b924188e820a64d070b6cbc97f1bb88e854
9a5565c8f2bdb227c10c7827b07e548e6a572b7e6b2d5777db7feb8111370191
7c73d587427350b463d8a9c6acf11dbedf41ba95519d21d062508f2b2c717ec9
1305f29f03fe88d281600c02dce8f5e46dd69ca44b33b8f62e15d3d4c7e1b1be
df0653a1822d414ba7bffdf9a664d48d8630539e0243975f8bb94013c2578594
66089cd28a2a80fa9cf67517530d2fb1aee16c9fbeecc0148de20127b4c11967
f7747fe6510748f596bad868129a50cd1921071c3e1e3c3a3c0b60dacb5cadf5
ec6955d21c3977fe0b926bc132a394d40bdb9f0e5a2b23c69bca2170c6ba6a9b
```

SHA256 of full modulus: `2a513d9854dedc12abe875e30b69ef5975317d2fe0c8b84fa3741e00629c6652`

## Key B (SML + TrustOS + UBoot + FDL2)

Signs: `sml_a`, `sml_b`, `trustos_a`, `trustos_b`, `uboot_a`, `uboot_b`, `fdl2-sign.bin`

Modulus:

```
ad7e67e09f57f0a391493de4f96fdfbc1b53f3f2c56dfbc1991020c6337bf680
d05655de5e99991a3db373a3cf78edb54d4dda423e91ffe363cba434fc7c1187
ced76fc8b37e2373e986bbb5cd48204dd18559c7cdb21c8da185c98529d73120
50096a612ae6108f06c3025e46cb5bffc469548f62555c18ae1b00a18c6fce1c
c480f4522caa563cff1d82151f6e5951bad57fed2fffbe2d3aca52e163c69a29
e4836cd00f36accd872748d86c6d319b3ddbcc6c90755f7957265235391bce75
67a8a7a42d597b5ed1eb617ea30b376387642b0bdaf5ab260d0344529b7c2cc2
d661d811f8e170cde781118cd8e0941b1ae16d14874c04e7b334b5890d032f6d
```

SHA256 of full modulus: `725e218acc8ddaa0eca688bc96f5dc9587b243f4c0eeede0e80d660e9d69f9c7`

## vbmeta key (for reference)

The vbmeta chain uses a different key: **AOSP test key RSA-4096**.

Public key SHA1 (AVB canonical form): `2597c218aae470a130f61162feaae70afd97f011`

This is the test key included in the AOSP source tree at `external/avb/test/data/testkey_rsa4096.pem`. Corresponding private key is public. AVB signing can be reproduced freely using `avbtool` with that key.

## Why we cannot forge Key A or Key B signatures

Both are RSA-2048 with unknown private halves. Breaking them directly would require solving the integer factorization problem for two ~617-digit numbers, which is not feasible with classical computing resources.

The practical bypass is to patch the verifier (SPL) rather than forge signatures. That is what this repo does.

## Private key availability

As of this analysis, Key A and Key B private halves have not been located in:
- Public AOSP test key sets
- `android_boot_image_editor` test keys
- The Unisoc alps SDK share (no `*_prvk.pem` files corresponding to these moduli)
- Any public leak catalog checked

If a private key is ever located, it could sign modified images such that SPL accepts them without patching SPL. Until then, the patch-SPL approach is the practical method.
