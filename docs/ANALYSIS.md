# SPL RSA verify - reverse engineering analysis

Full reverse-engineering walkthrough of how Unisoc UMS512 SPL verifies each image it loads, and how the bypass works.

## Environment

- Binary: stock SPL dump from Anbernic RG Vita Pro (UMS512 / T618)
- Disassembler: `aarch64-linux-gnu-objdump -D -b binary -m aarch64`
- SPL code base address: 0 (BootROM strips DHTB header before execution)

## Entry and early boot

```
0x0000  b 0x38                  ; skip metadata
0x0038  mrs x1, currentel       ; setup EL3/2/1
0x0054  msr vbar_el3, x0
0x0084  bl 0x9fcc               ; icache invalidate
0x0090  bl 0x8                  ; BSS clear
0x0094  bl 0x8b8                ; init
0x00a0  b 0xa2a0                ; main
```

## Main function (0xa2a0)

Sets up two partition load areas:
- `x29+56 = 0x94000000` (buffer for first partition load, e.g. SML)
- `x29+64 = 0x94060000` (buffer for second partition load)
- `x29+80 = 0x94040000` (buffer for uboot load)

Then loads each partition and verifies it:

```
0xa36c  adrp x0, 0xd000
0xa370  add  x0, x0, #0xb78            ; partition descriptor table base
0xa374  mov  x3, #0xfe00
0xa378  mov  w1, #0x100000             ; 1 MiB read size
0xa37c  mov  x2, #0x94040000           ; DRAM load address (data start)
0xa380  movk x3, #0x9403, lsl #16      ; DHTB header at x2 - 0x200
0xa384  add  x0, x0, x20, lsl #4       ; x0 = table + slot_idx * 16
0xa388  bl   0xa16c                    ; read partition from eMMC
0xa38c  mov  x1, #0xfe00
0xa390  mov  x0, #0x5500               ; SPL's own DHTB header in SRAM
0xa394  movk x1, #0x9403, lsl #16      ; x1 = 0x9403FE00 = loaded DHTB
0xa398  mov  x2, #0
0xa39c  mov  w3, w19
0xa3a0  mov  w4, w21
0xa3a4  bl   0xa57c                    ; VERIFY the loaded partition
0xa3a8  cbz  w0, 0xa3b4                ; if verify passed (w0==0), continue
0xa3ac  mov  w0, #5                    ; error code 5
0xa3b0  bl   0x9fb8                    ; halt/infinite-loop error handler
0xa3b4  ...                            ; success path
```

The address `0x5500` is the SRAM address where the BootROM loads SPL's own DHTB image (confirmed from the CVE-2022-38694 tool's `spd_dump` command line: `fdl fdl1-dl.bin 0x5500`).

## Error handler at 0x9fb8

```
0x9fb8  stp  x29, x30, [sp, #-16]!
0x9fbc  mov  w0, #5
0x9fc0  mov  x29, sp
0x9fc4  bl   0x9f38                    ; write error code to UART/watchdog
0x9fc8  b    0x9fc8                    ; infinite loop
```

SPL hangs permanently if any verification fails. There is no reset, no fallback, no unlock-flag check.

## Verify wrapper chain

```
0xa57c: b 0xb5d8                       ; tail call
```

```
0xb5d8: stp  x29, x30, [sp, #-80]!
0xb5e8: mov  x20, x0                   ; x20 = SPL DHTB ptr (0x5500)
0xb5ec: mov  x19, x1                   ; x19 = loaded DHTB ptr (0x9403FE00)
0xb5f0: memset(sp+0x30, 0, 32)         ; clear hash scratch buffer
0xb5fc: mov  x0, x20
0xb600: add  x1, x29, #0x30
0xb604: bl   0xb58c                    ; extract stored hash from SPL SIMGHDR
0xb608: memset(sp+0x20, 0, 16)
0xb618: mov  x1, x19
0xb61c: add  x0, x29, #0x30
0xb620: bl   0xb52c                    ; compute & verify loaded partition hash
0xb624: cmp  w0, wzr
0xb628: cset w0, eq                    ; w0 = 1 if 0xb52c returned 0, else 0
0xb634: ret
```

Return convention: `0xb5d8` returns 0 on verify success, 1 on failure. This matches the caller's `cbz w0, success` pattern.

## Real verify function at 0xb52c

```
0xb52c: stp  x29, x30, [sp, #-80]!
0xb538: ldr  w21, [x1, #48]            ; data_size from loaded DHTB
0xb540: add  x21, x21, #0x200
0xb548: add  x21, x1, x21              ; x21 = SIMGHDR start
0xb54c: mov  x0, x1
0xb554: bl   0xb504                    ; get data ptr: x0 + SIMGHDR[0x18]
0xb558: ldr  w1, [x21, #16]            ; data_size from SIMGHDR
0xb560: bl   0xb118                    ; SHA256(data_ptr, data_size) -> sp+0x30
0xb568: bl   0xb518                    ; get SIMGHDR end address
0xb578: bl   0xb2f4                    ; RSA-2048 verify + hash compare
0xb588: ret
```

## RSA verify at 0xb2f4

```
0xb2f4: stp  x29, x30, [sp, #-480]!    ; 480-byte stack frame
...
0xb338: bl   0xb0ac                    ; memset 256-byte buffer
0xb33c: mov  w0, #0x15                 ; 21 (algorithm tag?)
0xb344: mov  w0, #0x4                  ; exponent size
0xb348: movk w0, #0x200, lsl #16       ; key size (512 bits... no, 0x2000004)
...
0xb388: bl   0xb118                    ; SHA256 again
0xb398: bl   0xb0e8                    ; memcmp (first hash compare)
0xb3ac: bl   0xb0e8                    ; memcmp (second hash compare)
0xb3f0: bl   0xb118                    ; SHA256
0xb420: bl   0xc07c                    ; RSA modexp + PKCS verify
0xb4ec: bl   0xb218                    ; success path
0xb4fc: ldp  x29, x30, [sp], #480
```

Key arguments to `0xc07c` (RSA modexp):
- x0 = reference hash (from SPL SIMGHDR)
- x1 = computed hash buffer
- x2 = SHA256 hash size (32)
- x3 = offset to RSA signature inside SIMGHDR
- x4 = key size info
- x5 = modulus buffer
- x6 = exponent/scratch

The 480-byte stack frame is the giveaway: it's holding a 256-byte modulus copy, a 256-byte signature copy, plus hashes and scratch - classic RSA-2048 verify workspace.

## The four verify call sites

Using the pattern `bl / cbz w0 / mov w0, #5 / bl`, there are exactly four occurrences in SPL code:

| Code offset | Context |
|-------------|---------|
| 0xa3a4 | Main uboot-slot verify |
| 0xa4c0 | Alternate boot-mode uboot verify (when w21 != 1) |
| 0xa4e8 | SML verify |
| 0xa510 | TrustOS / TEE verify |

Each call site has the same 4-instruction error path. `tools/patch_spl.py` finds all of them and replaces `bl/cbz/mov/bl` with four NOPs (`0xd503201f`), so the verify function's return value becomes irrelevant and execution always falls through to the success path.

## The BootROM's role

BootROM does NOT call `0xb2f4` or anything like it. It only:
1. Reads the SPL DHTB image from mmcblk0boot0 into SRAM at 0x5500
2. Computes SHA256 of the data section
3. Compares against the DHTB hash at file offset 0x8
4. If match, branches into the code at 0x5700 (0x5500 + 0x200)

No RSA verification happens in BootROM on this chip. This was empirically confirmed:
- Flashing an SPL with modified code and WRONG DHTB hash -> device bricks (BootROM rejects)
- Flashing an SPL with modified code and CORRECT DHTB hash -> boots fine (even though the SIMGHDR RSA signature is now invalid for the new code)

This is because the secure-boot efuse is not blown on these consumer devices. With the efuse set, BootROM would additionally verify the SIMGHDR RSA signature against a key stored in the efuse and would reject any modified SPL regardless of hash.

## Why the CVE-2022-38694 tool's `gen_spl-unlock` bricks when flashed directly

The tool NOPs the four verify sites correctly, but it:
1. Leaves the DHTB hash pointing at the unmodified code's hash
2. Truncates the SIMGHDR from 1172 bytes to 692 bytes

Problem (1) causes BootROM to reject the image. The tool was designed to run the patched SPL in RAM via the BootROM USB exploit (where BootROM verification is bypassed by the exploit itself), then write it back only after unlocking. It was never designed to be flashed directly.

This repo fixes both problems: we update the DHTB hash after NOPing and preserve the full SIMGHDR.

## Confirming on a live device

Before patching:
```bash
adb shell dd if=/dev/block/mmcblk0boot0 bs=1 skip=$((0x200 + 0xa3a4)) count=16 2>/dev/null | xxd
# 00000000: 7600 0094 6000 0034 a000 8052 02ff ff97
#           ^bl      ^cbz      ^mov      ^bl
```

After patching:
```bash
adb shell dd if=/dev/block/mmcblk0boot0 bs=1 skip=$((0x200 + 0xa3a4)) count=16 2>/dev/null | xxd
# 00000000: 1f20 03d5 1f20 03d5 1f20 03d5 1f20 03d5
#           ^NOP     ^NOP     ^NOP     ^NOP
```

All four NOPs confirm the patch landed correctly and the verify return value is now ignored.
