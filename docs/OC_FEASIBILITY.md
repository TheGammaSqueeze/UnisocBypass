# Overclock feasibility analysis: RG Vita (UMS512 / T618)

Scope: reverse-engineering of where CPU/GPU frequency and voltage limits are enforced in the UMS512 boot chain, so we can reason about which patches are needed to extend OPPs safely.

## TL;DR

| Layer | Enforces OC? | Can we modify? |
|-------|------------|----------------|
| BootROM | no | yes via CVE-2022-38694 + DHTB hash fix (already done) |
| SPL | no | yes (SPL verify was fully NOPed in `patch_spl.py`) |
| SML (ATF BL31) | **no DVFS role** | yes, but not needed |
| UBoot | no DVFS role | already fully patched |
| Kernel vmlinux | no DVFS logic in vmlinux | not needed (OC logic is in modules) |
| `sprd-hwdvfs-ums512-arch.ko` | reads DTB dep tables | patch if needed, unlikely |
| `sprd-hwdvfs-policy.ko` | reads DTB OPP tables by name | patch if needed, unlikely |
| **DTB in `vendor_boot`** | **yes, primary enforcement** | **yes, easy (AVB is disabled)** |
| SC2730 PMIC via `sc2730-regulator.ko` | hard voltage ceiling 1.597 V | not needed, generous headroom |

The entire OC story is a DTB modification. Everything else is permissive.

## Kernel

- Linux 5.4.161, ARM64, GKI-style: small vmlinux with most Unisoc drivers as `.ko` modules
- vmlinux contains only 13 `sprd,` compatible strings; the rest are in modules
- Modules live inside the vendor_boot ramdisk at `/lib/modules`

Key OC-relevant modules (extracted from `vendor_boot_b.img` ramdisk):

| Module | Role |
|--------|------|
| `sprd-cpufreq-public.ko` | cpufreq framework glue, exports `sprd_cpufreq_update_opp` |
| `sprd-hwdvfs-policy.ko` | policy driver: OPP selection by cpu_bin and temperature |
| `sprd-hwdvfs-ums512-arch.ko` | UMS512 architecture-specific DVFS (MPLL, DCDC, cluster tbls) |
| `sc2730-regulator.ko` | SC2730 PMIC driver, enforces voltage ranges from DT |
| `apsys-dvfs.ko` | display/VSP DVFS (not GPU) |
| `mmdvfs.ko` | camera/ISP/JPEG DVFS (not GPU) |

### How table selection works

`sprd-hwdvfs-policy.ko` does table selection in `sprd_opp_select`:

1. Read `dvfs_bin` from `nvmem-cells` (this is an efuse value).
2. Build table name: `operating-points-<SoC>-<bin>` where SoC is T610, T618, or T700 and bin is one of `ff`, `tt`, `ss`, `od`, or `ff_65`, `tt_65`, `ss_65`, `od_65` (65 means 65C-tuned).
3. Read the matching OPP table from DT.
4. At runtime, switch between high-temp and low-temp variants based on current temperature vs `temp-threshold` (currently `0x41` = 65).

This means adding OPPs requires modifying the matching `operating-points-T618*` variants, not just the generic `operating-points`.

## SML (ATF BL31)

File: `sml_a.img`

- Version: BL31 v1.4 `sharkl5pro`, build `0415943b`
- Purpose: PSCI (Power State Coordination Interface), Trusty secure monitor, FIQ routing, system reset
- **Does NOT perform DVFS.** There are no voltage setter functions, no cluster-freq setters, no PMIC writes. Only PSCI CPU power-state transitions (on/off, suspend, system off).
- Therefore: SML patching is NOT needed for CPU or GPU OC on this SoC.

This is a material difference from some MediaTek and Qualcomm SoCs where EL3 firmware enforces DVFS limits.

## UBoot

Has no DVFS role beyond passing the cmdline. We already patched it separately for unlock + AVB bypass; no additional patching needed for OC.

## DTB: where the actual limits live

### CPU OPP tables

Two OPP table nodes in the DTB:

**`opp-table0` (LITTLE, cpumask `0x3f` = cores 0-5, Cortex-A55)**

T618 default, 10 OPPs:

| Freq (MHz) | Volt (mV) |
|-----------:|----------:|
| 614.4 | 756.250 |
| 768 | 756.250 |
| 962 | 756.250 |
| 1144 | 756.250 |
| 1228.8 | 787.500 |
| 1482 | 875.000 |
| 1536 | 890.625 |
| 1716 | 953.125 |
| 1820 | 990.625 |
| **2002** | **1050.000** (stock max) |

**`opp-table1` (BIG, cpumask `0xc0` = cores 6-7, Cortex-A75)**

T618 default, 6 OPPs:

| Freq (MHz) | Volt (mV) |
|-----------:|----------:|
| 1228.8 | 750.000 |
| 1482 | 850.000 |
| 1536 | 870.000 |
| 1742 | 950.000 |
| 1872 | 1000.000 |
| **2002** | **1050.000** (stock max) |

Per-bin variants exist: `operating-points-T618`, `-ff`, `-tt`, `-ff-65`, `-tt-65`. The `-65` variants are applied when temperature is above the `temp-threshold` (0x41 = 65 C). Many other T610/T700 variants are present but not used on T618 silicon.

### Dependency tables (critical for CPU OC)

The `hardware-dvfs-platform` node has per-cluster dependency tables whose rows correspond 1:1 with OPP rows:

- `lit_core_cluster_tbl_T618` - maps LITTLE OPP index to voltage-grade tuples
- `big_core_cluster_tbl_T618` - same for BIG cluster
- `scu_cluster_tbl_T618` - SCU (Snoop Control Unit) frequency mapping
- `periph_cluster_tbl_T618` - peripheral bus mapping
- `gic_cluster_tbl_T618` - GIC (interrupt controller) mapping

Each has a row per OPP. **When adding CPU OPPs, these tables must be extended in parallel.** Just adding rows to `operating-points-T618` without extending the cluster tables will cause `sprd-hwdvfs-ums512-arch.ko` to read past table end and either crash or silently clamp.

### GPU OPP table (Mali-G52 MC2)

Different format. The GPU node uses both `operating-points` and a parallel `sprd,dvfs-lists`:

```
operating-points = <
    0x5dc00 0xaae60    // 384 MHz @ 700 mV
    0x7d000 0xb71b0    // 512 MHz @ 750 mV
    0x96000 0xb71b0    // 614.4 MHz @ 750 mV
    0xbb800 0xc3500    // 768 MHz @ 800 mV
    0xcf850 0xc3500    // 850 MHz @ 800 mV
>;

sprd,dvfs-lists = <
    0x5dc00 0xaae60 0x04 0x01    // freq, volt, hw_index=4, flag=1
    0x7d000 0xb71b0 0x05 0x01
    0x96000 0xb71b0 0x06 0x01
    0xbb800 0xc3500 0x07 0x01
    0xcf850 0xc3500 0x08 0x01
>;

sprd,dvfs-range-max = <0x04>;       // highest valid OPP index (0-based)
sprd,dvfs-range-min = <0x00>;
sprd,dvfs-scene-extreme = <0x03>;   // index chosen for "extreme" scene
sprd,dvfs-scene-high    = <0x02>;
sprd,dvfs-scene-medium  = <0x01>;
sprd,dvfs-scene-low     = <0x00>;
```

This is the **cause of past GPU-OPP boot failures.** Adding OPPs only to `operating-points` produces a list with N entries that does not match `sprd,dvfs-lists` (still N-1 entries) or `sprd,dvfs-range-max` (still N-1). The hardware DVFS driver in `sprd-hwdvfs-ums512-arch.ko` reads from `sprd,dvfs-lists`, so new OPPs are ignored or, worse, the driver probes into undefined memory.

**To add GPU OPPs safely, all of the following must be updated together:**

1. `operating-points` - add `freq, volt` pair
2. `sprd,dvfs-lists` - add `freq, volt, hw_index, flag` quad with next unused hw_index
3. `sprd,dvfs-range-max` - increment to new highest index
4. optionally `sprd,dvfs-scene-extreme` if you want the new top OPP used for "extreme" scene

The `core_index0_map` through `core_index7_map` registers (one per core) currently all set to `0x1c000`; this appears to be a register initialization value not a per-OPP table, so no update needed.

## SC2730 PMIC

From the DTB regulator nodes:

| Rail | Min | Max |
|------|-----|-----|
| VDDCPU | 0.200 V | **1.597 V** |
| VDDGPU | 0.200 V | **1.597 V** |
| VDDCORE | 0.200 V | 1.597 V |
| VDDMEM | 0.400 V | 1.594 V |

PMIC imposes no meaningful ceiling for reasonable OC. A 1.100-1.150 V CPU OC is trivially within range.

## Feasibility summary per phase

### Phase 1: DTB-only OC (recommended first attempt)

- Rehash `vendor_boot` after modification. Our already-patched uboot skips AVB, so this just works. No SPL retouch needed.
- **CPU LITTLE**: add rows to `operating-points` and `operating-points-T618` plus matching rows to `lit_core_cluster_tbl_T618`. Also update the `-65`, `-ff`, `-tt` variants if we want OC to apply at high temperature or on other bins; for a single-device OC, only T618 variants used by this specific chip bin need updating.
- **CPU BIG**: same pattern in `opp-table1` + `big_core_cluster_tbl_T618`.
- **GPU**: update four fields in parallel (`operating-points`, `sprd,dvfs-lists`, `sprd,dvfs-range-max`, optionally scene maps).

Risk: low. Worst case the kernel rejects an OPP with `Disabling freq X MHz as it's out of OF limits` and we boot at stock. Cluster-table mismatch will crash early boot though, so the updates must be self-consistent.

### Phase 2: kernel module patch (likely unnecessary)

- `sprd-hwdvfs-policy.ko` iterates its OPP list via `dev_pm_opp_of_add_table_indexed`; no fixed-size arrays seen in strings.
- `sprd-hwdvfs-ums512-arch.ko` handles MPLL configuration; the number of MPLL entries is a DT property `mpll-cells` so it's sized dynamically.
- If Phase 1 silently caps frequencies, check: thermal driver, cpufreq cooling driver, userspace governor, then consider module patches.

### Phase 3: SML / ATF patch

Not applicable. SML has no DVFS role on UMS512.

## Known good cpu_bin for this SoC

The `nvmem-cells = <0xb3>` reference in `opp-table0` points to an efuse block that returns the bin number. On-device path:

```
cat /sys/kernel/debug/sprd-cpufreq/cpu_bin
```

Default is usually T618 (bin 1) for Anbernic RG Vita. The resulting active table would be `operating-points-T618` unless the temperature has already crossed the threshold to the `-65` variant.

Writing to debugfs `cpu_bin` lets you force a different bin table at runtime, which is handy for testing whether a more aggressive table (like `-od`) is kernel-accepted without re-flashing.

## What's next if OC is pursued

1. Tool: extend `tools/modify_uboot.py`-style helper that parses DTB, adds conservative OPP rows to all dependent tables atomically, reassembles DTB and vendor_boot, rehashes.
2. Test case: add `0xe33c4 @ 0x1086a0` (1168 MHz at 1085 mV) to GPU plus matching `sprd,dvfs-lists` quad and `sprd,dvfs-range-max = 0x05`. Very conservative, barely above stock 850 MHz, tests the modification path.
3. If that boots and shows up as `/sys/class/devfreq/*/available_frequencies`, incrementally push higher with thermal observation.
