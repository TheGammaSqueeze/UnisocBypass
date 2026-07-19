# UMS9620 / T820 port status

Porting the unlock/bypass approach from UMS512 (T618) to UMS9620 (T820).
This is a work in progress: the SPL side is done, the uboot unlock offsets are
not yet finalized.

## Important: the T618 SPL route does NOT work on a fused T820

On T618 the DHTB hash is `SHA256(payload)`, so modifying the SPL and rehashing
is accepted by a hash-only BootROM. On T820 this is false: the stock DHTB hash
field is not `SHA256(payload)` (or any contiguous range), and the SIMGHDR
footer carries an RSA cert (exponent `0x10001` + modulus). The T820 SPL is
cryptographically verified, so a modified + rehashed SPL is rejected and the
device drops back to download mode (confirmed on hardware).

This matches `unisoc_chipram_signcheck`: its patch methods target
sml/teecfg/trustos/uboot, never the SPL, and it notes SPL/chipram patching
"only works on un-fused devices." A fused production T820 cannot run a modified
SPL without the private key.

So the model is inverted vs T618:

- Keep the STOCK signed SPL, do not modify it.
- Patch the uboot and make it pass the stock SPL's verification with a
  signature-preserving method (see below), which exploits a flaw in how the
  SPL verifies uboot (no private key needed).

## SPL analysis (kept for reference / un-fused devices only)

`tools/patch_spl_ums9620.py` neuters the SPL verify dispatcher at code offset
`0x045b4` (called with an image index in `w0`, returns 0 on pass; 9 cbz-gated
call sites) to `movz w0,#0 ; ret`. This is structurally correct but only useful
on an un-fused device where the SPL is hash-only; on a fused device (this one)
BootROM rejects it. Do not rely on it for a production T820.

## uboot: the actual path on a fused T820

Because the stock SPL must stay in place, a modified uboot has to pass that
SPL's verification. Use one of the `unisoc_chipram_signcheck` methods:

- `magic64` + `difftool` (Patch-Post-Verification): keep the signed uboot
  payload intact, append a runtime patcher, signature still verifies.
- `bsp_sign_fxxker_for_uboot` (Patch-Pre-Verification): fix the uboot cert chain.

Both need the uboot unlock byte-patches, which is the open item.

The T820 uboot is the same Unisoc u-boot15 codebase (identical strings
"INFO: LOCK FLAG IS : UNLOCK!!!", "WARNNING: LOCK FLAG IS : UNLOCK, SKIP
VERIFY!!!"), so the same unlock idea applies (force `get_lock_status` to report
unlocked; force verifiedbootstate). But the build's register/offset layout
differs from T618, and the exact patch sites are not yet pinned. Anchors found
so far (offsets in the `uboot_b` image):

- INFO_UNLOCK string refs at `0xb130` / `0xb158` / `0xb194`, SKIP_VERIFY ref at
  `0xb3d4`.
- Lock-status display reads `g_DeviceStatus`-area global via
  `adrp x,0x299000 ; ldr w,[x,#0x740] ; cmp #1` at `0xb1b0`; nearby flag
  struct is written at `0x1b5bc` (`#0x738`) and `0x639c4` (`#0x73c`).

Still needed: the `get_lock_status` cbz->b site and the verifiedbootstate site,
which require manual tracing of `sprd_sec_verify_lockstatus`'s caller plus an
on-device test round.

## Re-signing: not possible, not needed

The T820 AVB keys are all different from the T618 set (top-level vbmeta
`8e3c8f11`, boot/dtbo `3b0792d6`, vendor_boot `87bc5eef`), and we do not hold
the T820 private keys. The patch route needs no re-signing (BootROM checks only
the regenerated DHTB hash). Consequence: the T618 "re-sign dtbo with the boot
key" trick cannot be used on T820; a modified T820 dtbo would need vbmeta
hashtree-disable or a uboot/TOS patch instead.

## Related external tooling

`unisoc_chipram_signcheck` (magic32/64 + difftool, bsp_sign_fxxker) offers
alternative uboot packaging that keeps the original signature valid, and notes
that `dis_avb` in spd_dump_it / SPRDClientCore-Xia uses the same method; those
tools may already carry a ums9620 AVB-disable offset set worth checking before
finishing the manual RE.

## Structural differences vs T618

Adds `init_boot` (separate generic ramdisk), `hypervisor`, `ise`,
`avbmeta_rs`; newer platform (likely 5.15 kernel, so the erofs feature-`0x2`
mount problem seen on T618/5.4 will not apply).
