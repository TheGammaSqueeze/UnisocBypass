# Why does dtbo modification of widevine crash the device?

Investigation of the runtime crash that hits when `widevine@e3800000`
is changed (size shrunk, or `reusable;` flag added), even when the
dtbo is OEM-signed with `rsa4096_boot.pem` and uboot/TOS verification
passes cleanly.

## Symptoms

| Change | Pre-boot | Runtime |
|---|---|---|
| `widevine@e3800000` `reusable; compatible="shared-dma-pool";` | passes verification | freezes post boot_completed |
| `widevine@e3800000` `reg = <0xe3800000 0x2000000>` (32 MB) | passes verification | crashes |
| `widevine@e3800000` left at 200 MB stock | passes verification | clean boot |
| `vdsp-mem@fd770000` shrunk to 1 MB | passes verification | clean boot, +39 MB |
| `cp-mem@89600000` shrunk to 1 MB | passes verification | clean boot, +72 MB |

So the issue is *specifically* the widevine carveout. cp-mem and vdsp
shrink without complaint.

## What references widevine on this device

The 200 MB at `0xe3800000` is referenced by:

1. **ION heap@1** (label `carveout_mm`, phandle 0x06 -> widevine).
   In the running kernel this is registered via
   `drivers/staging/android/ion/sprd/sprd_ion.c` -> `ion_carveout_heap_create`,
   which:
   - calls `ion_heap_pages_zero(page, size, pgprot_writecombine(PAGE_KERNEL))`
     to zero the entire region at boot,
   - creates a `gen_pool` over the region,
   - sets `heap.type = ION_HEAP_TYPE_DMA` regardless of what DT says.

   Shrinking just makes the pool smaller. This path is not size-fragile.

2. **TrustOS DPU TA** (port `com.android.trusty.disp`). The kernel
   side is `drivers/gpu/drm/sprd/disp_trusty.c` which the DRM driver
   `dpu_r6p0.c` uses for secure-layer composition. The relevant call
   pattern (line 1700-1726):

   ```c
   ctx->tos_msg->cmd = TA_FIREWALL_SET;
   ctx->tos_msg->version = DPU_R6P0;
   disp_ca_write(ctx->tos_msg, sizeof(*ctx->tos_msg));
   disp_ca_wait_response();
   ```

   This only fires when `hwlayer->secure_en || ctx->secure_debug`
   *and* `ctx->fastcall_en == false`. On this device
   `sprd,widevine-use-fastcall` is *not* in the DT, so `fastcall_en`
   is false. Secure layers normally only activate during DRM-protected
   playback - which isn't running at boot - so this is not the boot
   path.

3. **Upstream BSP `ion_cma_heap.c`** has an `ion_notice_firewall`
   helper that sends `TA_LOCK_DRM_MEM` to a TOS port `com.android.trusty.ion`
   with the widevine base + size as payload. **This file isn't built
   into the running kernel** (sprd_ion.c is the chosen path here), so
   it's not what's failing.

4. **uboot's `fdt_reserved_mem_multimedia_parse`** (in
   `lib/secureboot/common/sec_common.c` and friends) iterates the
   reserved-memory tree at uboot time and calls the TOS firewall TA
   via `uboot_set_secure_range_paraneters` for these tags:
   `cp-modem`, `multimediabuffer`, `tos-mem`, `audio-mem`,
   `framebuffer`, `overlaybuffer`. **Note widevine is not in this
   list.** And the call site itself
   (`common/loader/loader_nvm.c:1726`) is `//commented out` in the
   upstream BSP source, gated by `#ifdef CONFIG_TEE_FIREWALL`. The
   actual production uboot string `fdt_reserved_mem_multimedia_parse`
   is in our running uboot binary, so it may or may not be wired in -
   but it doesn't program widevine bounds either way.

## Two concrete crash paths and which one fits the symptom

### A. CMA-pool variant (the `reusable;` attempt)

When we add `compatible = "shared-dma-pool"; reusable;`, the kernel
hands the region to the **CMA allocator**. ION heap@1 then calls
`ion_carveout_heap_create` against memory that has already been
reserved as CMA. The carveout heap works on a fixed gen_pool that
expects to *own* its region. CMA pages can be migrated/reclaimed by
the kernel for movable allocations - which means the gen_pool's
backing pages aren't stable. Result: when ION starts handing out
buffers, it's handing out pages that the kernel allocator may
have re-claimed. This is the freeze we observed.

### B. Smaller-region variant (the 32 MB attempt)

When we shrink `reg` to 32 MB:

- ION heap@1 zero-init runs on the new 32 MB. This succeeds.
- ION buffer allocations that fit in 32 MB succeed.
- BUT: the **DPU r6p0 ATF/TA pre-config** runs at sprd-drm probe.
  The trusty `disp` TA, when it gets the first `TA_FIREWALL_SET`
  call (or even at TA load time), reads the widevine reservation
  range from a TZ-managed memory map that is set up out of uboot.
  If uboot's TZ side was told widevine is 200 MB at e3800000 (via
  whatever Sprd-specific firewall hook our build actually uses),
  but the kernel-side iommu mapping is now 32 MB, the next secure
  layer commit hits the firewall and faults.
- Even *without* a secure layer commit, certain Sprd kernel modules
  (`sprd_drm`, `sprd_gsp`, `sprd_camera`, `sprd_vdsp`) connect to
  trusty IPC at probe time. If TOS rejects the dtbo's reservation
  inconsistency at trusty bring-up (e.g. a sanity check inside TOS
  during `kernelbootcp` early calls), trusty can refuse to come up,
  which then causes any kernel module that depends on it to fail
  probe. Kernel modules failing to probe in a chain is what produces
  the multiple `Modules linked in:` traces we saw at t+45s during
  the vdsp test (those were soft errors, kernel survived). With
  widevine the chain involves bring-up-critical drivers, hence the
  hang/crash instead of soft warnings.

## What the SDK source confirms

- `bsp_bootloader_u-boot15-master/lib/secureboot/common/sec_common.c`
  contains `secboot_secure_process_flow` (line 647) which calls
  `vboot_secure_process_flow("dtbo")` (line 659/665). This is the
  TOS smc that hard-fails on hash mismatch even on unlocked. We've
  already worked around it with OEM-signed dtbo.

- The actual hard-fail of TOS-rejected partitions is in
  `lib/trustzone/uboot_drv_api.c:54..62`.

- `bsp_modules-master/` does NOT contain a kernel build environment
  matching our running 5.4.161. The `kernel.cfg` there says 4.14.

- No source for `sml`, `trustos`, or `teecfg`. These are pulled from
  a separate `vendor/sprd/proprietories-source/` tree we don't have.
  Therefore we can't directly inspect the TOS-side widevine firewall
  policy or the TA's expectation about size.

- `bsp_build-master/packimage_scripts/config/` confirmed: keys match
  the device's vbmeta_b chain partition pubkeys 1:1 (already
  validated, see `keys/README.md`).

## What's actually fixable with what we have

| Knob | Current state | Action available |
|---|---|---|
| dtbo verification | Already solved with OEM key | none needed |
| ION carveout_mm pool size | Sensitive to TOS-side firewall | won't reclaim from this path |
| widevine -> CMA | Incompatible with carveout heap consumer | no; would need to also patch ION heap@1 type to DMA backend, which lives in kernel modules we can't rebuild against 5.4.161 from this SDK |
| Disable widevine entirely (drop ION heap@1) | Higher overlay surgery | possible but high risk - the DPU's secure path code references it via phandle |
| Build a uboot that fully bypasses dtbo + AVB | Source available | yes; agent's recommendation - sec_common.c patches |
| Build a kernel module that patches widevine_size at runtime | Matching 5.4.x source available | viable - see below |

## Practical conclusion

Widevine is the wrong target for RAM reclaim on this device. The
200 MB carveout participates in the SoC's hardware firewall fabric
through paths that span uboot, kernel, sprd-trusty TAs, and the DPU
R6P0 secure layer flow. We do not have visibility into the TOS-side
expectation of size/base, and the running kernel's ION carveout
allocator is fragile against any change to that backing.

Recommended next moves, in order:

1. Stop poking widevine. Take the +111 MB win we already have.
2. If we want more reclaim, look at unallocated runtime regions
   (the unidentified `0xa0000000-0xa157afff` 21.5 MB block in
   `/proc/iomem` which is *not* in any DT reservation - it's a
   driver `request_resource` of System RAM). Trace the driver
   that's holding it.
3. If we still want DRM/Widevine RAM specifically, the kernel side
   is rebuildable. All the relevant drivers (`sprd_ion`, `sprd_drm`
   incl `disp_trusty.c` + `dpu_r6p0.c`, `sprd_gsp`, `trusty_ipc`)
   are loaded as `.ko` on this device and the matching 5.4.x source
   is in our fork at
   [github.com/TheGammaSqueeze/kernel_ums512_5.4](https://github.com/TheGammaSqueeze/kernel_ums512_5.4)
   (cloned to `/work/ums512_kernel`, vermagic + CFI + LTO already
   verified to match the running kernel via the GPU voltage module
   in `voltage-ceiling-hunt/`). Concretely we could rebuild
   `sprd_ion.ko` to drop the widevine size strictness or rebuild
   `sprd_drm.ko` to NOP the `disp_ca_*` secure-layer fastcalls.
   What this still won't reach is the TrustOS-side widevine TA's
   own size expectation (TOS source is not in our public BSP drop).
   So we'd find out by experiment whether the freeze is kernel-side
   or TOS-side. For a gaming handheld with no L1 DRM workload, this
   is a separate workstream and not warranted by the gain alone.
