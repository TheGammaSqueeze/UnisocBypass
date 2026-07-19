# UMS9620 / T820 port status

Porting the unlock/bypass approach from UMS512 (T618) to UMS9620 (T820).
This is a work in progress: the SPL side is done, the uboot unlock offsets are
not yet finalized.

## What carries over unchanged

- DHTB / SIMGHDR image format is identical, so `tools/rehash.py` works as-is
  (verified `is_packed=0` on the T820 spl/uboot, so the `data_size` read is
  correct).
- The verification bug is in SPL/FDL1 on this SoC (BOOTROM -> SPL/FDL1 -> TOS
  -> UBOOT), so patching the SPL gives control of TOS and uboot. Only
  ums9360 / ums9632 relocate verification into POSTROM; ums9620 does not.

## SPL: done

`tools/patch_spl_ums9620.py`. Unlike the T618 SPL, the T820 SPL does not use
the uniform `bl / cbz w0,+0x60 / mov w0,#5 / bl` verify pattern. Instead every
image check goes through one verify dispatcher at code offset `0x045b4`
(image index in `w0`, returns 0 on pass; 9 call sites, each gating on
`cbz w0`). The tool neuters that prologue to `movz w0,#0 ; ret` and rehashes,
so all 9 gates take the success path.

```bash
python3 tools/patch_spl_ums9620.py spl_a.img spl_a_patched.img
python3 tools/patch_spl_ums9620.py spl_b.img spl_b_patched.img
```

Not yet confirmed on a device.

## uboot: not finished

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
