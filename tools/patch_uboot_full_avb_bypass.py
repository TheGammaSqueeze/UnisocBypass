#!/usr/bin/env python3
"""DEPRECATED / DO NOT USE -- this patch bricks the boot.

Root cause (confirmed against sharkl5Pro u-boot15 source in
lib/secureboot/common/sec_common.c and lib/trustzone/uboot_drv_api.c):

    uboot_vboot_verify_img() (code 0x82c40) is NOT a "verify and hang on
    error" stub. It is the SMC into TrustOS that runs the real AVB pass
    AND writes the generated kernel command line back into
    g_sprd_vboot_cmdline via VbootVerifyInfo->vb_cmdline_addr.

    vboot_secure_process_flow() (sec_common.c:1019-1023) does:

        vboot_verify_info->vboot_unlock_status = g_DeviceStatus;   // UNLOCK
        uboot_vboot_verify_img(vboot_verify_info, ...);            // <- fills cmdline
        // g_sprd_vboot_cmdline now holds:
        //   androidboot.vbmeta.digest=..., androidboot.vbmeta.device_state=unlocked,
        //   androidboot.veritymode=enforcing, ...

    On CONFIG_VBOOT_SYSTEMASROOT builds (UMS512 / sharkl5Pro) the uboot-side
    ALLOW_VERIFICATION_ERROR flag is compiled out (avb_check.c uses
    "#ifndef CONFIG_VBOOT_SYSTEMASROOT"), so the ONLY thing that both
    tolerates a modified/mismatched image AND emits the dm-verity cmdline is
    that TrustOS SMC. TrustOS honours vboot_unlock_status: when it is UNLOCK
    it returns NO_ERROR for a mismatched boot/dtbo/vbmeta and still produces
    the cmdline. That is exactly why a genuinely-unlocked stock uboot boots
    fine with modified boot partitions.

    Stubbing uboot_vboot_verify_img() to "mov w0,#0 ; ret" skips the SMC, so
    g_sprd_vboot_cmdline stays empty (it was memset to 0). The kernel then
    gets no dm-verity digest, panics, and the device falls back to
    recovery/charging. That is the failure this script caused.

The correct fix -- and the whole point of the project -- is:

    tools/patch_uboot_unlock.py ALONE.

Its 0x78c98 patch forces get_lock_status() to always store
g_DeviceStatus = VBOOT_STATUS_UNLOCK. Every AVB path (boot, dtb, dtbo,
vbmeta) then passes vboot_unlock_status = UNLOCK to TrustOS, which tolerates
the modified images AND generates the cmdline -- no image re-signing needed.
The four TOS calls this script used to neuter behave on our forced-unlock
uboot exactly as they do on a stock uboot running on an unlocked device:

    0x82c00 uboot_verify_img                 - not on the CONFIG_VBOOT_V2 boot
                                               path (compiled out at
                                               sec_common.c:708/713).
    0x82c40 uboot_vboot_verify_img           - GENERATES the cmdline. Must run.
    0x82c90 uboot_verify_product_sn_signature- fastboot unlock flow only.
    0x82cd0 uboot_set_root_of_trust          - runs at boot (loader_nvm.c:1670)
                                               to hand the Root-of-Trust to
                                               Keymaster; succeeds when
                                               unlocked, so no need to stub it.

Keeping this script importable so old pipelines fail loudly instead of
silently producing a bricking image.
"""

import sys

_MSG = __doc__


def apply_patches(*_args, **_kwargs):
    raise RuntimeError(
        "patch_uboot_full_avb_bypass is deprecated: it neuters "
        "uboot_vboot_verify_img (0x82c40), the TrustOS SMC that generates the "
        "kernel dm-verity cmdline, which bricks the boot. Use "
        "tools/patch_uboot_unlock.py alone."
    )


def main():
    sys.stderr.write(_MSG + "\n")
    sys.stderr.write(
        "REFUSING TO RUN. This patch removes kernel-cmdline generation and "
        "bricks the boot.\nUse: python3 tools/patch_uboot_unlock.py "
        "<stock_uboot.img> <patched_uboot.img>\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
