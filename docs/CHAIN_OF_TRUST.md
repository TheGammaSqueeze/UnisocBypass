# UMS512 chain of trust

How the Unisoc UMS512 boot chain verifies each stage, and where the holes are.

## Stage 0: BootROM

Immutable mask ROM burned into the SoC. Runs from on-chip SRAM at reset.

Responsibilities:
- Select boot source (eMMC, NAND, USB)
- Load SPL from the chosen source into SRAM at address 0x5500
- Verify SPL and jump to it
- Provide USB download mode fallback (entered via hardware key combo or when no valid SPL is found)

**Verification performed:** DHTB SHA256 hash only. The BootROM does NOT verify the SIMGHDR RSA signature, because the secure-boot efuse is not blown on consumer UMS512 parts.

With a secure-boot-blown efuse, BootROM would additionally check the SIMGHDR RSA signature against a key whose hash is burned into the efuse. This would prevent any SPL modification regardless of hash validity.

**Vulnerabilities:**
- [CVE-2022-38694](https://research.nccgroup.com/2022/09/02/theres-another-hole-in-your-soc-unisoc-rom-vulnerabilities/) - stack buffer overflow in USB download mode handler, allows arbitrary code execution at BootROM privilege level.

## Stage 1: SPL (Secondary Program Loader)

Small (~60 KB) AArch64 binary loaded from the `splloader` partition (eMMC boot partition 0 on UMS512).

Responsibilities:
- Initialize DDR
- Initialize power rails
- Load SML, TrustOS, and UBoot from eMMC
- Verify each loaded image
- Hand off to the trust stack (SML -> TrustOS -> UBoot)

**Verification performed (stock):** RSA-2048 signature verification on SML, TrustOS, and UBoot. Four call sites in the SPL code all follow the same pattern:

```
bl  verify_rsa
cbz w0, ok          ; verify returns 0 on success
mov w0, #5
bl  halt_infinite   ; deadlock on failure
```

There is no unlock-flag bypass. SPL verifies regardless of whether the bootloader is "unlocked" at the Android level.

**Verification performed (after bypass):** None. All four verify call sites are NOPed and SPL simply loads each image and jumps to it.

## Stage 2: SML / TrustOS / UBoot

These run after SPL hands off. UBoot is the user-facing stage: it implements fastboot, reads the misc partition for lock state, and loads Android's boot and vendor_boot images.

**Verification performed:**
- UBoot implements AVB (Android Verified Boot) for `boot`, `vendor_boot`, `dtbo`, and the `vbmeta*` chain partitions.
- AVB uses the AOSP test key (RSA-4096, SHA1 `2597c218aae470a130f61162feaae70afd97f011`), which is publicly known.
- AVB is SKIPPED when the bootloader is unlocked:
  ```
  WARNNING: LOCK FLAG IS : UNLOCK, SKIP VERIFY!!!
  ```

**Post-unlock signing implications:**
- `boot`, `vendor_boot`, `dtbo`, `vbmeta` can be freely modified with no key required (AVB is skipped)
- Even without skipping, these can be legitimately signed with the AOSP test key (available in every AOSP tree)

## Stage 3: Android

Standard Android userspace. SELinux, apex, etc. Not covered by this repo.

## Summary table

| Stage | Verifier | Check | Bypass |
|-------|----------|-------|--------|
| SPL | BootROM | DHTB SHA256 hash | None required when efuse unblown (just keep hash valid) |
| SPL | BootROM (efuse blown) | SIMGHDR RSA + hash | Would require private key or efuse vulnerability |
| SML, TrustOS, UBoot | SPL | SIMGHDR RSA-2048 | Patch SPL to NOP verify calls (this repo) |
| boot, vendor_boot, dtbo | UBoot | AVB (AOSP test key RSA-4096) | Already skipped when bootloader unlocked |

## The attack surface

```
stock:
  BootROM -> SPL (hash ok)
             -> SML (RSA ok) -> TrustOS (RSA ok) -> UBoot (RSA ok)
                                                    -> boot (AVB ok, skipped if unlocked)

after this repo's bypass:
  BootROM -> SPL (hash ok, code patched, verify NOPed)
             -> SML (accepted, not verified) -> TrustOS (accepted) -> UBoot (accepted, may be modified)
                                                                      -> boot (AVB ok, skipped if unlocked)
```

The only remaining integrity gate is BootROM -> SPL. Everything downstream is modifiable with just a DHTB hash update.
