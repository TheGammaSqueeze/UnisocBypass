# End to end workflow

Walkthrough of using this repo to permanently enable modified uboot on a UMS512 device.

## Prerequisites

1. The device must already be bootloader-unlocked (`ro.boot.flash.locked = 0`, `verifiedbootstate = orange`). If not, run the CVE-2022-38694 unlock first.
2. `adb` with root access.
3. Python 3.6 or later.

## One-shot automated workflow

```bash
./scripts/full_workflow.sh
```

This runs backup, patch_spl, flash_spl, and reboot. After it completes, the device has a patched SPL that ignores all downstream signature checks.

## Manual step by step

### Step 1: back up

```bash
./scripts/backup.sh backups
```

Creates `backups/mmcblk0boot0.bin`, `backups/mmcblk0boot1.bin`, `backups/uboot_a.bin`, `backups/uboot_b.bin`. Keep these: they are your recovery images.

### Step 2: patch SPL

```bash
python3 tools/patch_spl.py backups/mmcblk0boot0.bin patched_spl.img
```

Output:

```
Found 4 RSA verify call sites in backups/mmcblk0boot0.bin:
  file 0xa5a4  (code offset 0xa3a4)
  file 0xa6c0  (code offset 0xa4c0)
  file 0xa6e8  (code offset 0xa4e8)
  file 0xa710  (code offset 0xa510)

Patched 64 bytes across 4 sites.
New DHTB hash:    97bda8aa13e922e3ef780053e53ba660644bdbc0469f70b671e84ff52502b45d
Output:           patched_spl.img
```

### Step 3: flash patched SPL

```bash
./scripts/flash_spl.sh patched_spl.img
```

This:
1. Runs `verify_image.py` to confirm the DHTB hash is valid
2. Disables write-protect on mmcblk0boot0 and mmcblk0boot1
3. Writes the image to both partitions
4. Reads back the hash and compares with the file hash

If verification fails the script bails before flashing.

### Step 4: reboot

```bash
adb reboot
```

Wait for the device to come back:

```bash
until adb shell getprop sys.boot_completed 2>/dev/null | grep -q 1; do sleep 3; done
```

The device should boot normally. All downstream signature checks are now disabled.

### Step 5: modify uboot (optional)

Modify the uboot image however you want. For string replacements:

```bash
python3 tools/modify_uboot.py backups/uboot_b.bin -o uboot_mod.img \
    --mask "LOCK FLAG IS : UNLOCK, SKIP VERIFY" --mask-char "1"
```

For binary modifications, write your own script and call `tools/rehash.py` at the end to update the DHTB hash:

```python
import sys, struct
sys.path.insert(0, "tools")
from rehash import rehash

with open("backups/uboot_b.bin", "rb") as f:
    data = bytearray(f.read())

# ... your modifications to data[0x200 : 0x200 + data_size] ...

rehash(data)
with open("uboot_mod.img", "wb") as f:
    f.write(data)
```

Then flash:

```bash
./scripts/flash_uboot.sh uboot_mod.img
adb reboot
```

## Recovery

If something goes wrong after flashing a modified SPL:

- Cold boot (fully power cycle): if the SPL has a valid DHTB hash and is otherwise functional, it will boot.
- If the SPL is broken: hold volume down while connecting USB to enter BootROM download mode, then use `spd_dump` with the CVE-2022-38694 exploit to restore the stock SPL from `backups/mmcblk0boot0.bin`.

If something goes wrong after flashing a modified uboot:

- If the patched SPL is working, any uboot (with valid DHTB hash) will boot, so the broken uboot will still run just enough for fastboot recovery.
- Enter download mode, flash stock uboot from `backups/uboot_b.bin` via `spd_dump w uboot uboot_b.bin`.

## Verifying the bypass

After flashing, check the NOP sites on-device:

```bash
adb shell 'dd if=/dev/block/mmcblk0boot0 bs=1 skip=$((0x200 + 0xa3a4)) count=16 2>/dev/null' | xxd
# 00000000: 1f20 03d5 1f20 03d5 1f20 03d5 1f20 03d5
# All four d503201f = NOP
```

And the DHTB hash:

```bash
adb shell 'dd if=/dev/block/mmcblk0boot0 bs=1 skip=8 count=32 2>/dev/null' | xxd
# should match the "New DHTB hash" from patch_spl.py output
```

## Clean uninstall

Put the stock SPL back:

```bash
./scripts/unpatch.sh backups
adb reboot
```

This restores both eMMC boot partitions and (if uboot backups exist) both uboot slots.
