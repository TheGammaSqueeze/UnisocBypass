#!/usr/bin/env python3
"""Patch a UMS512 uboot image to short-circuit ALL TOS-side AVB
verification calls.

This is the complement to ``patch_uboot_unlock.py``. The unlock patch
makes uboot believe the bootloader is unlocked, which lets the
generic Sprd code path skip standard AVB hash compares. But on
``CONFIG_VBOOT_SYSTEMASROOT`` builds (UMS512 included), the dtbo
verification is hoisted into ``vboot_secure_process_flow("dtb"/"dtbo")``
which calls ``uboot_vboot_verify_img`` -- an SMC into TrustOS -- and
hangs in an infinite loop on any non-zero return. That hang is what
bricked us when modifying dtbo content.

Source for the affected functions is in
``lib/trustzone/uboot_drv_api.c`` (line numbers are from the public
sharkl5Pro u-boot15 source). Each one has the same shape::

    int uboot_verify_img(unsigned long start_addr, uint32_t lenth)
    {
        smc_param *param = tee_common_call(FUNCTYPE_VERIFY_IMG, ...);
        if (param->a0 != NO_ERROR) {
            printf("uboot_verify_img() return error:param->a0=%d\\n", ...);
            while (1);              // <-- the hang
        }
        return param->a0;
    }

We patch the function prologue itself to ``mov w0, #0 ; ret`` so the
SMC is never issued and 0 (=NO_ERROR) is always returned. Every
caller treats this as "verification passed".

Functions we neuter:

| code offset | symbol                                     | source line |
|-------------|--------------------------------------------|-------------|
| 0x82c00     | uboot_verify_img                           | 43          |
| 0x82c40     | uboot_vboot_verify_img                     | 54          |
| 0x82c90     | uboot_verify_product_sn_signature          | 64          |
| 0x82cd0     | uboot_set_root_of_trust                    | 82          |

``uboot_config_os_version`` (line 73 in source) was not found in the
shipped binary -- its callers were either compiled out or inlined --
so it isn't patched here.

Encoding details: we replace the first two instructions of each
function with::

    mov  w0, #0     0x52800000
    ret             0xd65f03c0

The original ``stp x29, x30, [sp, #-N]!`` plus ``mov x3, x0`` are
clobbered, but since the function returns immediately none of the
spilled-onto-stack state matters and the caller's link register and
frame pointer are untouched.

Prerequisites:
    - the running uboot must already be the patched-unlock variant
      from ``tools/patch_uboot_unlock.py`` (this script supplements it)
    - the SPL must already be the NOPed variant from
      ``tools/patch_spl.py``

Usage::

    python3 tools/patch_uboot_full_avb_bypass.py <input_uboot.img> <output_uboot.img>
    python3 tools/patch_uboot_full_avb_bypass.py <input_uboot.img> /dev/null --dry-run
"""

import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rehash import rehash


PATCHES = [
    # code_off  orig_word_0  orig_word_1  new_word_0  new_word_1  description
    (0x82c00, 0xa9bf7bfd, 0xaa0003e3, 0x52800000, 0xd65f03c0,
     "uboot_verify_img: prologue -> mov w0,#0 ; ret"),
    (0x82c40, 0xa9be7bfd, 0xaa0003e3, 0x52800000, 0xd65f03c0,
     "uboot_vboot_verify_img: prologue -> mov w0,#0 ; ret"),
    (0x82c90, 0xa9bf7bfd, 0xaa0003e3, 0x52800000, 0xd65f03c0,
     "uboot_verify_product_sn_signature: prologue -> mov w0,#0 ; ret"),
    (0x82cd0, 0xa9bf7bfd, 0xaa0003e3, 0x52800000, 0xd65f03c0,
     "uboot_set_root_of_trust: prologue -> mov w0,#0 ; ret"),
]


def apply_patches(data: bytearray, dry_run: bool = False):
    if data[0:4] != b"DHTB":
        raise ValueError("Not a DHTB image")
    data_size = struct.unpack("<Q", data[0x30:0x38])[0]
    results = []
    for code_off, orig_w0, orig_w1, new_w0, new_w1, desc in PATCHES:
        file_off = 0x200 + code_off
        if file_off + 8 > 0x200 + data_size:
            raise ValueError(f"patch offset 0x{code_off:x} past end of code")
        actual_w0 = struct.unpack_from("<I", data, file_off)[0]
        actual_w1 = struct.unpack_from("<I", data, file_off + 4)[0]
        matched = (actual_w0 == orig_w0 and actual_w1 == orig_w1)
        results.append({
            "code_off": code_off,
            "file_off": file_off,
            "expected_orig": (orig_w0, orig_w1),
            "actual": (actual_w0, actual_w1),
            "new": (new_w0, new_w1),
            "desc": desc,
            "matched": matched,
        })
        if matched and not dry_run:
            struct.pack_into("<I", data, file_off, new_w0)
            struct.pack_into("<I", data, file_off + 4, new_w1)

    failed = [r for r in results if not r["matched"]]
    rh = None
    if not failed and not dry_run:
        rh = rehash(data)
    return results, failed, rh


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--dry-run", action="store_true",
                    help="report patch sites without writing output")
    args = p.parse_args()

    data = bytearray(open(args.input, "rb").read())
    results, failed, rh = apply_patches(data, args.dry_run)

    for r in results:
        status = "OK" if r["matched"] else "FAIL"
        print(f"  [{status}] @ code 0x{r['code_off']:06x} "
              f"(file 0x{r['file_off']:06x}): {r['desc']}")
        if not r["matched"]:
            print(f"        expected {r['expected_orig'][0]:#010x},{r['expected_orig'][1]:#010x}"
                  f" got {r['actual'][0]:#010x},{r['actual'][1]:#010x}")

    if failed:
        print("\nABORT: not all patch points matched their expected original "
               "instruction.")
        sys.exit(1)

    if args.dry_run:
        print("\nDry run only, no file written.")
        sys.exit(0)

    open(args.output, "wb").write(bytes(data))
    if rh is not None:
        print(f"\nDHTB sha256 / SIMGHDR hash refreshed.")
    print(f"wrote {args.output} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
