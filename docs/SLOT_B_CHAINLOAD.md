# Slot-B chainloader (A-default) design

Research notes for an optional "hold a button at boot to chainload a second
u-boot" feature on UMS9620 / T820, built on top of the signature-preserving
`magic64` uboot patch (see [MAGIC64_EXPLAINED.md](MAGIC64_EXPLAINED.md) and
[UMS9620_PORT.md](UMS9620_PORT.md)).

Status: design only. Nothing here is built or hardware-tested yet. The addresses
are reverse-engineered from a stock RG406H `uboot_b.img` (load base
`0xb5000000`, `mImgSize = 0x108870`) and verified against the disassembly, but a
wrong dead-region choice or a bad relative offset will brick the boot, so this
must be prototyped behind the diag path and validated on-device before it goes
near a production image.

## The idea, and why slot A is the chain starter

The obvious layout is "put a launcher in slot B that jumps to slot A or to SD."
The better layout for a device that already ships everything on slot A (as
GammaOS does) is the inverse: keep the real OS in slot A, make slot A a `magic64`
image, and have its runtime patch, on a button hold, load the `uboot_b`
partition and jump to it.

The reason is where the SPL verification lands. On a fused T820 the SPL
RSA-verifies whichever slot it boots. The stock SPL boots the BCB-active slot,
and on GammaOS that is always slot A. So:

- Slot A is the slot the SPL verifies. It is a `magic64` image, so the signed
  payload is byte-for-byte intact and the SPL accepts it.
- Slot B is loaded by full u-boot (slot A), not by the SPL. It never passes
  through the SPL's DHTB + RSA path, so it can be raw, unsigned, arbitrary code.

That gives three wins over a B-default launcher:

1. No BCB manipulation. The active slot never changes, so Android's slot logic
   stays coherent and there is no "default to B and the BCB now reads B" problem.
2. The secure world is already up. The SPL brings up the secure world for the A
   boot before it ever reaches u-boot, so a chainloaded B inherits an
   initialized secure environment instead of having to recreate it.
3. Fail-safe. The experimental payload (B) is opt-in behind a button. The default
   path is the well-tested production A. A broken B just means "do not hold the
   button."

## Delivery: `magic64` recap

`magic64` keeps the signed payload untouched and appends a jump stub, a small
relocate-then-patch shellcode, and a patch table. At load time, before u-boot's
`_start`, the shellcode copies the payload into place and applies the patch table
(a list of `[addr, len_words, word...]` writes terminated by a zero address),
then jumps to the real `_start`. The four unlock edits are already delivered this
way. The chainloader is just more patch-table entries: one blob that writes a
trampoline into a dead region of the payload, plus one word that redirects a
single instruction to it. Writing payload bytes in memory does not affect the
signature, because the patch runs after the SPL has already verified the on-flash
bytes.

## The hook point

Replace one instruction in the cboot dispatcher (prologue `0xb5005f54`):

```
b5005f84: bl 0xb503730c     ; check reboot-magic (fastboot/recovery)
b5005f88: mov w20, w0        ; w20 = 0 on normal boot (callee-saved, must stay 0)
b5005f8c: cbnz w0, 0xb50061dc
b5005f90: bl 0xb5005eec      ; HOOK. orig word 0x97ffffd7 ("ANDROID: Booting slot%s" logger)
b5005f94: bl 0xb5035e40      ; RETURN HERE (get cached bootmode)
b5005f98: cmp w0, #0x104
```

This instruction runs exactly once on a normal boot, after all button, mode, and
reboot-reason detection has already happened and after eMMC is up (the misc
partition was read during that detection), and before the boot-stage handler loop
at `0xb5005fa8` that loads and launches the kernel. The displaced instruction is
a `bl`, so the trampoline must preserve `x0-x18` and `x30` around its own calls,
replay `bl 0xb5005eec` (so the slot log still prints), then branch back to
`0xb5005f94`. `w20` (0 on normal boot) and `x22` are callee-saved and survive an
AAPCS-compliant call automatically.

## Reading the button

`read_volkeys()` at `0xb50767f0` takes no arguments and returns in `w0`:

| `w0` | meaning |
|------|---------|
| `0x00` | no volume key held |
| `0x72` | VOLUME-DOWN held |
| `0x73` | VOLUME-UP held |
| `0xE5` | both held |
| `< 0`  | key read error |

Use **VOLUME-UP** (`0x73`) as the chainload trigger. VOLUME-DOWN (`0x72`) already
maps to stock RECOVERY_MODE and HOME (`0x66`) to FASTBOOT in the key-to-mode
table, so those would collide; VOLUME-UP alone is not in the table, so it reaches
the hook as a normal boot and the trampoline reads it directly. This is the exact
reader the stock fastboot key-poll uses, so it is proven live. (`0xb50769f8` maps
a keycode to a boot-mode int if you ever want the mode instead; the power key
reader is `0xb50768d8`.)

## Loading uboot_b

`read_partition_by_name(name /*x0*/, num_bytes /*x1*/, byte_offset /*x2*/, dst /*x3*/)`
at `0xb503e184`, byte granularity, returns `w0 = 0` on success. To land the
uboot_b payload at `0xb5000000`, skip its DHTB header with `x2 = 0x200`:

```
x0 = "uboot_b\0"
x1 = 0x2ff000        ; count; keep x1 + x2 <= 0x300000 (partition size) or it errors
x2 = 0x200           ; skip uboot_b's DHTB header so the payload lands at the base
x3 = 0xb5000000
```

Sectors are 512 bytes. Lower-level helpers if you prefer LBA work:
`get_partition_start_by_name` at `0xb503df50` (start byte offset, `>> 9` for LBA),
and raw `blk_read(dev, num_bytes, start_bytes, buf)` at `0xb503ca7c`.

## The relocation crux (the part that is easy to get wrong)

`_start` at `0xb5000000` self-relocates u-boot to high DRAM. The entry loads SP
and `__bss` bounds from the literal pool (`0xb5000068`/`0x70`/`0x78` =
`0xb510e000`, `0xb510e000`, `0xb56b4a78`), clears BSS, then calls `board_init_f`;
u-boot then relocates the whole image to near the top of DRAM and runs
`board_init_r` from there. The cboot hook fires from `board_init_r`, i.e. from the
relocated high copy.

Consequence: a trampoline placed in the low magic region (above `mImgSize`) is not
relocated. It sits gigabytes away from the relocated hook, far outside a `B`'s
+/-128 MB range, and calling it by absolute address would hit a stale low copy
with stale globals.

So the trampoline must live inside the copied payload (`0 .. mImgSize`). Write it
via a patch-table multi-word entry over a dead region of the payload (there is
ample inter-function zero padding; validate the chosen region against the
relocation table so no `R_AARCH64_RELATIVE` fixup lands in it), and have it call
u-boot functions with PC-relative `bl` (target link address minus trampoline link
address; everything is within the ~1 MB image, so it is in `bl` range). Then hook
and trampoline relocate together and every relative offset stays valid. The final
`br 0xb5000000` is absolute and correct: that is the fixed physical entry of the
uboot_b we just wrote there, and the low region is dead and free after
relocation.

## Trampoline

```asm
tramp:
    stp x29, x30, [sp, #-160]!    ; save (stash any x0-x18 you rely on)
    ; --- decide ---
    bl  0xb50767f0               ; read_volkeys()            (PC-relative bl)
    cmp w0, #0x73                ; VOLUME-UP held?
    b.ne .normal
    ; --- held: load uboot_b payload to 0xb5000000 ---
    adr x0, name_ubootb          ; "uboot_b\0" (PC-relative literal in tramp)
    mov x1, #0x2ff000            ; count (function caps to partition remainder)
    mov x2, #0x200               ; skip uboot_b DHTB header
    mov x3, #0xb5000000          ; dst
    bl  0xb503e184               ; read_partition_by_name
    cbnz w0, .normal             ; read failed -> fall back to normal boot (fail-safe)
    ; --- coherency + teardown + jump (stay at EL3) ---
    mov x0, #0xb5000000
    mov x1, #0xb5000000
    add x1, x1, #0x2ff000        ; end of written range
    bl  0xb500417c               ; flush_dcache_range(start, end)
    bl  0xb500b414               ; cleanup_before_linux (icache/dcache off, tlbi alle3)
    mov x0, #0xb5000000
    dsb sy
    isb
    br  x0                       ; enter uboot_b at EL3, MMU/caches off (cold-handoff env)
.normal:
    ldp x29, x30, [sp], #160     ; restore
    bl  0xb5005eec               ; replay the displaced slot-log call (PC-relative)
    b   0xb5005f94               ; return to normal boot
name_ubootb:
    .asciz "uboot_b"
```

u-boot runs at **EL3** here (every cache/SCTLR helper falls through to the EL3
register, and the `armv8_switch_to_el2`/`el1` machinery only makes sense from
EL3). Do not switch EL: uboot_b must be entered at EL3 exactly as the SPL
cold-hands it off, and it re-enables the MMU and caches and relocates itself.

## Cache flush and jump

Verified primitives (runtime vaddrs, load base `0xb5000000`):

| function | vaddr | what it does |
|----------|-------|--------------|
| `flush_dcache_range(start, end)` | `0xb500417c` | `dc civac` loop + `dsb sy` (clean+inval to PoC) |
| `cleanup_before_linux()` | `0xb500b414` | `daifset`, `icache_disable`, `invalidate_icache_all`, `dcache_disable` (which does `tlbi alle3`), `invalidate_dcache_all` |
| `icache_disable()` | `0xb5004688` | clears `SCTLR.I` |
| `invalidate_icache_all()` | `0xb50045f4` | `ic ialluis; isb` |
| `dcache_disable()` | `0xb5004510` | clears `SCTLR.C`/`M`, `__asm_flush_dcache_all`, `tlbi alle3` |
| `invalidate_dcache_all()` | `0xb5004148` | set/way invalidate |

Sequence: clean the freshly written uboot_b range while D-cache is still on
(`flush_dcache_range`), then tear down our own state (`cleanup_before_linux`),
then `dsb sy; isb; br 0xb5000000`. Do not touch `scr_el3`/`spsr_el3`/`hcr_el2` and
do not `eret`.

## Extending `magic_pack_ums9620.py`

Two small changes; the mechanics already support the rest:

1. Make `ADD_LENGTH` dynamic. It is fixed `0x100` today with the patch table
   capped at `0x80`. Compute `ADD_LENGTH = round_up_page(0x80 + len(patch_data))`
   (about `0x200` here). The shellcode reads the patch table at `size + 0x80`
   until the zero terminator, so a longer table needs no shellcode change; only
   the header `mImgSize += ADD_LENGTH`, the jump-stub offset, and the footer
   offset adds (already keyed off `ADD_LENGTH`) follow the new value. There is
   plenty of partition headroom (`0x108870` payload in a `0x300000` partition).
2. Add a blob patch entry. The patch format is already `[addr, len_words,
   word...]`, so emit one entry that writes the assembled trampoline words at the
   chosen dead-region runtime address, plus a single-word entry writing the `b`
   at `0xb5005f90` (immediate `((tramp_link - 0xb5005f90) >> 2)`), alongside the
   four existing unlock NOPs. Assemble the trampoline's internal `bl`s the same
   PC-relative way, in pure Python, so the output stays deterministic.

uboot_b itself is just a normal u-boot placed in the `uboot_b` partition. Because
slot A loads it, not the SPL, it needs no signing.

## Open items before building

- Pick and validate the dead region inside the payload against the relocation
  table (no `R_AARCH64_RELATIVE` fixup may target it).
- Assemble the trampoline and wire the two new patch-table entries into the
  packer.
- Prototype behind the diag path (buzz markers on "button seen" and "about to
  jump to B") and validate on an RG406H before any production image.
- Confirm the T820 SPL boots only the BCB-active slot (does not independently
  verify the other slot), which the A-default model relies on.
