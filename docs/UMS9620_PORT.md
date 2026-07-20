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

### magic64 signature-preserving packaging: CONFIRMED WORKING

`tools/magic_pack_ums9620.py` reproduces the `magic64` (Patch-Post-Verification)
method as a reusable, parameterized packer. It keeps the signed uboot payload
byte-for-byte (so the stock SPL's RSA check still passes), appends the AArch64
relocation+patch shellcode and a patch table, moves the SIMGHDR footer, and
truncates the result back to the partition size (only zero padding is dropped).

Confirmed on hardware (Anbernic T820):

- Load base `0xb5000000` is correct (the header `mImgAddr` is a placeholder
  `0xaaaaaaaacccccccc`; base derived from BSS/SP literals and the PAC XML image
  base `0xb4fffe00 + 0x200`). Runtime patch address = load base + code offset.
- Patch `0xafe8 = 0xd503201f` (nop) removes the `INFO: LOCK FLAG IS : UNLOCK!!!`
  line and the "press power button" 10s timeout. Device boots, silent and fast.
- Output MUST be truncated to the uboot partition size (`0x300000` here); a
  `0x300100`-byte image gets "write flash failed" from the download tool.

Usage:

    python3 tools/magic_pack_ums9620.py uboot_b.img out.img \
        --patch 0xafe8=0xd503201f [--load-base 0xb5000000]

The shellcode is hand-assembled in pure Python (no binutils dependency), so the
output is byte-for-byte deterministic and reproducible across machines.

### One-step unlock tool (parity with the T618 `patch_uboot_unlock.py`)

`tools/patch_uboot_unlock_ums9620.py` wraps the packer to give the same
user-visible result as the T618 unlock tool: the device reports unlocked and
boots with no warning text and no timeout. It applies all four patches at once:

    0x604c0  cbnz w0 -> nop   get_lock_status always reports UNLOCK
    0xafe8   b.eq   -> nop    remove INFO_UNLOCK line + 10s timeout
    0xb2a4   bl     -> nop    remove SKIP_VERIFY line (UART)
    0xb2ac   bl     -> nop    remove SKIP_VERIFY line (screen)

Like the T618 tool, each patch point is bitmask-verified against the stock
instruction before anything is written (masks ignore only branch targets /
condition-branch offsets that legitimately drift between builds), so a
different UMS9620 build that no longer matches is rejected rather than silently
mis-patched. Confirmed on hardware with the 0xafe8/0xb2a4/0xb2ac subset.

    python3 tools/patch_uboot_unlock_ums9620.py uboot_b.img out.img
    python3 tools/patch_uboot_unlock_ums9620.py uboot_b.img --dry-run

### Pinned offsets (resolved via aarch64 objdump + capstone)

Code offsets are relative to the uboot DHTB payload (file offset 0x200 + code
offset). Values verified against `uboot_b.img`.

| purpose | code offset | stock | patch to | effect |
|---|---|---|---|---|
| remove unlocked-warning message + 10s timeout | `0xafe8` | `54000180` (`b.eq 0xb018`) | `d503201f` (nop) | unlocked device boots silently (skips UART print `0xb020`, screen print `0xb038`, and the 10s power-button countdown `bl 0xae68` at `0xb040`) |
| force get_lock_status = UNLOCK | `0x604c0` | `35000160` (`cbnz w0, 0x604ec`) | `d503201f` (nop) | always takes the UNLOCK arm (g_DeviceStatus=1, returns 1) |
| remove `SKIP VERIFY` warning (UART) | `0xb2a4` | `9400a21c` (`bl 0x33b14`) | `d503201f` (nop) | drops the UART print of `WARNNING: LOCK FLAG IS : UNLOCK, SKIP VERIFY!!!` |
| remove `SKIP VERIFY` warning (screen) | `0xb2ac` | `9401e7a2` (`bl 0x85134`) | `d503201f` (nop) | drops the screen print of the same line |

The `SKIP VERIFY` line comes from a separate status-print function at `0xb238`
that dispatches on a lock-state global (`adrp 0x260000 ; ldr w0,[x0,#0xd80]`)
through a jump table (`br x2` at `0xb294`). The unlock case loads the string at
`0xb5588` (`adrp+add` at `0xb298/0xb29c`) and prints it twice, via `bl 0x33b14`
(UART) at `0xb2a4` and `bl 0x85134` (screen) at `0xb2ac`. NOPing both bl calls
suppresses only that line and leaves the jump table intact.

Supporting map:
- `get_lock_status` = `0x60470`: malloc(476) -> `common_raw_read(productinfo,
  476, 0x2000, buf)` (bl `0x3e184`) -> `sprd_sec_verify_lockstatus(buf, 0x40)`
  (bl `0xb094`) -> `cbnz w0, LOCK` at `0x604c0` -> stores 1/0 to `g_DeviceStatus`.
- `g_DeviceStatus` global: `[0x111000 + 0x8c8]` (base-independent page).
- boot-time lock-warning display fn = `0xafc4`: calls `get_lock_status`, reads
  `g_DeviceStatus`, branches LOCK (`0xaffc`) / UNLOCK-warning (`0xb018`).
- `read_is_device_unlocked` is AvbOps vtable slot `[ops+0x48]`, called in
  `avb_append_options` (`~0x67060`, refs "Error getting device lock state").

IMPORTANT: on a fused T820 the SPL RSA-verifies uboot, so modify+rehash of these
offsets is likely rejected. Package with a signature-preserving method
(magic64+difftool or bsp_sign_fxxker). The uboot mImgAddr header field is a
placeholder (0xaaaaaaaacccccccc), so difftool needs the real load base supplied
separately; the patch runtime address is load_base + the code offset above.

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
