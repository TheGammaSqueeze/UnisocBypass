# DHTB header format

Unisoc's DHTB ("Device Hash Trust Block"?) header is a 512-byte (0x200) prefix attached to every bootloader-chain image on UMS512 and related SoCs.

## Layout

```
offset  size  field          notes
---------------------------------------------------------
0x000   4     magic          "DHTB" (0x44485442)
0x004   4     version        always 1
0x008   32    data_hash      SHA256 of the data payload
0x028   4     marker1        0xcccccccc
0x02c   4     marker2        0xaaaaaaaa
0x030   8     data_size      size of data payload (not including SIMGHDR)
0x038   8     field_38       (varies, often zero)
0x040   8     field_40       (varies)
0x048   8     field_48       (varies)
0x050   432   padding        zeros
---------------------------------------------------------
0x200   N     data payload   (code or firmware bytes, length = data_size)
0x200+N 1172  SIMGHDR        (see SIMGHDR_FORMAT.md)
```

## What BootROM checks

The BootROM on UMS512 only verifies the **DHTB hash** when loading SPL:

```
computed = SHA256(data[0x200 : 0x200 + data_size])
if computed != data[0x008 : 0x028]:
    reject
```

It does NOT verify the RSA signature in SIMGHDR. This is what makes the bypass possible: modifying code and updating only the DHTB hash produces a BootROM-acceptable SPL.

## What SPL checks for downstream images

SPL performs full RSA-2048 signature verification on SML, TrustOS, and UBoot. See [ANALYSIS.md](ANALYSIS.md) for the disassembly. After running `tools/patch_spl.py`, those checks are NOPed out and only the DHTB hash is effectively enforced anywhere in the boot chain.

## Example: parsing with Python

```python
import struct, hashlib
with open("spl.img", "rb") as f:
    data = f.read()

assert data[0:4] == b"DHTB"
data_size = struct.unpack("<Q", data[0x30:0x38])[0]
stored = data[8:0x28]
computed = hashlib.sha256(data[0x200:0x200 + data_size]).digest()
print(f"DHTB hash valid: {stored == computed}")
```

Or use the included tool:

```bash
python3 tools/dhtb_parse.py spl.img
```

## Images using DHTB format

On a typical UMS512 device, these partitions are DHTB-wrapped:

- `splloader` / `splloader_bak` (mmcblk0boot0/boot1) - SPL
- `sml_a` / `sml_b` - Secure Monitor Layer
- `trustos_a` / `trustos_b` - TEE OS
- `uboot_a` / `uboot_b` - U-Boot
- `fdl1-sign.bin` / `fdl2-sign.bin` - Download mode FDLs (distributed with the SP flash tool)

Other partitions use different formats:
- `boot`, `vendor_boot`, `init_boot` - Android boot image (`ANDROID!` magic)
- `vbmeta*` - AVB (Android Verified Boot)
- `dtbo` - Device tree overlay
- `l_modem`, `wcnmodem`, etc. - Spreadtrum modem formats (SCI1, etc.)
