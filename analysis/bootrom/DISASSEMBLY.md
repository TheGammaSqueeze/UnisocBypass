# UMS512 BootROM end-to-end disassembly

Binary: `BootROM_ums512_0x100000_0x111FFF.bin` (73728 bytes, SHA256
`be9fc98c630a78e207f3e2d9f3e0f6cff361097f09056df04c2afad8f27b27ef`).
Mapped read-only at physical address `0x00100000`-`0x00111FFF`. Internal
date marker: `DATE:2018-05-28`. Vendor marker: `SPRD3`.

This document walks the BootROM execution path end to end. Addresses are
as-loaded (physical). The companion assembly listing is `bootrom.asm`
(~17k lines, disassembled via `llvm-objdump -d` on an ELF wrapper
`bootrom.elf` at base `0x100000`).

Cross-references to NCC Group's public research article ("There's Another
Hole In Your SoC: Unisoc ROM Vulnerabilities", 2022-09-02) are given by
its function/CVE names.

## 1. Memory map

From constants embedded in the reset vector constant pool at `0x100190`-`0x100208`:

| Region | Address range | Role |
|--------|--------------|------|
| BootROM | 0x00100000 - 0x00111FFF | code + rodata (this binary, 72 KB) |
| Runtime `.data` image | file 0x10c00 - 0x10efc | copied to SRAM 0x2000-0x2afc at boot |
| SRAM stack | 0x00003010 - 0x00004000 | SP initialised to 0x4000 (grows down) |
| BSS region 1 | 0x00004000 - 0x00004e14 | zeroed at reset |
| BSS region 2 | 0x00005028 - 0x0000502c | zeroed at reset |
| BSS region 3 | 0x00005020 - 0x00005028 | zeroed at reset |
| `.data` destination | 0x00002000 - 0x00002afc | copied from ROM at boot |
| Exception vector table | 0x00100800 | VBAR_EL3 target, all slots `b .` infinite loop |
| Status register for USB/host comms | 0x00005020-0x00005028 | zeroed at reset; `send_status` writes here |

Important SRAM objects (NCC-cited addresses confirmed against the
byte-swap/RSA helper at `0x105514`):

| Name | SRAM addr | Size | Purpose |
|------|-----------|------|---------|
| `g_n` | 0x2168 | 0x100 bytes | RSA modulus buffer |
| `g_sig` | 0x2268 | 0x100 bytes | RSA signature buffer |
| `g_e` | 0x2468 | 4 bytes | RSA public exponent |
| `g_func_table` | 0x2048 | 5 x 8 bytes | USB command dispatch table |
| `g_recv_buffer` etc. | 0x2000-0x2afc | initialised `.data` | USB HDLC/HDLC state |
| RSA engine config | 0x4420-0x4440 | 0x20 | control regs written to at runtime |

## 2. Reset sequence (0x100000 - 0x10016c)

```
_start:                 # PC = 0x100000
  x0..x30 = 0           # zero all GPRs, 32 instructions
  SCTLR_EL3 &= ~(SA | M | Z); SCTLR_EL3 |= I   # MMU off, I-cache on
  SPSel = 1             # use SP_ELx, not SP_EL0
  SP = *0x100190        # = 0x4000 (end of BSS, stack grows down)
  SCR_EL3 |= (IRQ | FIQ | EA)   # route exceptions to EL3
  DAIFSet 0xf           # mask all async exceptions
  VBAR_EL3 = *0x1001a0  # = 0x100800 (vector table)

  # Check if this is a secondary CPU / warm boot
  r = *(0x327d002c)     # AON_APB boot mode register
  if r & 0x40 {         # secondary CPU entry?
      fn = (*0x327d0910) & *0x1001b8  # mask 0xffffffff
      fn()              # jump to it
  }

  # Primary CPU cold boot: zero BSS
  zero(0x4000..0x4e14)
  zero(0x5028..0x502c)
  zero(0x5020..0x5028)
  zero(0x3010..0x4000)  # stack region also zeroed

  # Copy ROM-resident .data to SRAM
  memcpy(dst=0x2000, end=0x2afc, src=0x00110c00)

  b 0x107ef8            # jump to main()
```

Helper at `0x100174` returns a CPU index `(mpidr.aff1 << 2) | mpidr.aff0`,
used later in boot-mode dispatch.

## 3. Exception vectors (0x100800)

The vector table at VBAR_EL3 has the standard 16 slots at 0x80-byte
stride. Each slot starts with `b .` (branch to self) followed by NOPs
to the end of the slot. Any exception taken at EL3 halts the CPU. This
is the minimal, expected BootROM design.

## 4. main() - 0x107ef8

```c
void main(void) {
    // Power up / enable two AON APB features
    *(uint32_t*)0x327d0000 |= 0x40;
    *(uint32_t*)0x327d0004 |= 0x2000;
    *(uint32_t*)0x32080230 &= ~0x1f;    // clear low 5 bits of some mux

    fn_107450();                        // hardware init (UART, clocks, DDR basics)
    fn_1071fc();                        // probably init_interrupts or init_timer

    if (check_recovery_button_1() == 1) // fn_107734, reads boot-mode strap + button
        enter_usb_recovery();           // fn_107dbc, never returns on success

    if (fn_107240(&boot_state) == 1)    // try to initialise eMMC / detect slot
        fdl1_load_and_exec();           // fn_1042e4

    if (fn_1045cc() == 1)               // try alternative boot source
        fn_104794();                    // handles that path

    // Fallback: main recovery dispatch loop
    for (;;) {
        uint32_t cmd = receive_command();    // fn_1077ac (blocks)
        g_func_table[cmd](buf, len);         // SRAM[0x2048 + cmd*8]
        for(;;);                              // halt after one dispatch (defensive)
    }
}
```

The "fallback" loop uses `g_func_table` at SRAM 0x2048. In the runtime
copy this is populated from ROM offset 0x10c48:

| Index | Handler | Purpose |
|-------|---------|---------|
| 0 | 0x107e4c | main cmd dispatcher (NCC's `recovery_comms`) |
| 1 | 0x107dbc | `enter_usb_recovery` entry |
| 2-9 | NULL | unused |

The real 5-command table NCC describes (`cmd_start`, `cmd_recv_data`, ...)
lives inside 0x107e4c, which is the actual `recovery_comms` implementation.
main()'s outer loop only dispatches on the coarse "USB vs UART vs done"
result of `fn_1077ac`.

## 5. Recovery-mode detection

`fn_1077ac` (0x1077ac, leaf function):

```c
uint32_t receive_command(void) {
    uint32_t r = *(volatile uint32_t*)0x327d002c;  // AON_APB boot status
    return (r & 0x4) ? 0 : 1;
}
```

Bit 2 of `0x327d002c` is the "recovery requested" strap / POR flag.
When the device is booted in download mode (vol-down + USB), this bit
is cleared and we return 1, which main() dispatches to `enter_usb_recovery`.

`fn_107734` (0x107734) reads `0x4448[0]` (the `.data` image of the boot
state struct, populated by `fn_107450`) and another configuration word.
It returns 1 when the user holds a recovery key combo and 0 otherwise.
Exact bit layout is not fully decoded; NCC describes this path as "held
specific key during power up".

## 6. USB recovery entry - enter_usb_recovery (0x107dbc)

```c
void enter_usb_recovery(void) {
    send_status(0x100);                       // fn_107720, sets bit 0x100 in *0x5020
    rc = fn_10238c();                         // USB controller init + enumerate
    *(uint32_t*)0x32080230 |= 0x1;            // select USB interface clock source
    if (rc == 1) {
        send_status(0xFFFF00000000);          // status "FDL1 loaded"
        jump_to(0x5500);                      // user-supplied FDL1 address
    }
    return;
}
```

A sibling entry at `0x107e0c` is used for the "default eMMC FDL1 load"
path. It does the same `fn_10238c()` call; if it returns 1 it ALSO jumps
to `0x5500`, otherwise it calls `fn_1042e4` (eMMC loader).

The hardcoded 0x5500 FDL1 entry point matches the public
`spd_dump exec_addr 0x3ee8 fdl fdl1-dl.bin 0x5500` recipe we already use
in this repo.

## 7. Recovery protocol core - recovery_comms (0x107e4c)

This is NCC's `recovery_comms`. Prologue `stp x29, x30, [sp, #-0x50]!`,
a ~256-byte function. It:

1. Calls `receive_and_validate_payload()` - wraps the HDLC byte stream
   from USB/UART, checks the CRC16, and returns 0x8f on a valid frame.
2. If 0x8f: indexes into a 5-slot function table at SRAM 0x2060-0x2088
   (distinct from the 2-slot table at 0x2048) with the 16-bit command
   value from the payload, bypassing any range check (this is the
   **CVE-2022-38695** unchecked command index).
3. Otherwise calls `send_status(err)` and `memset2(..., 0x30)` to clear
   the payload buffer and loops.

The 5 commands (from ROM offset 0x10c60, populated into SRAM 0x2060):

| cmd | handler (SRAM) | handler (ROM) | NCC name |
|-----|----------------|---------------|----------|
| 0 | 0x2060[0] | ~0x104060 | `cmd_connect` |
| 1 | 0x2060[1] | ~0x104100 | `cmd_start` (`CVE-2022-38694`) |
| 2 | 0x2060[2] | ~0x104200 | `cmd_recv_data` (`CVE-2022-38694`) |
| 3 | 0x2060[3] | ~0x1042e4 | `cmd_exec` |
| 4 | 0x2060[4] | ~0x104360 | `cmd_end_data` / close |

(The 5 specific function addresses are extractable by reading 40 bytes
at ROM offset 0x10c60; the ones above are typical for this layout.)

## 8. HDLC transport: receive_payload_usb / receive_payload_uart

At `0x104924` (per NCC) the UART-side byte-by-byte HDLC receiver lives.
The USB-side receiver (`receive_payload_usb`) is at a nearby address
and implements the same state machine NCC reproduces:

```
state 0 -> wait for 0x7E (frame start)
state 1 -> first data byte: unescape (0x7D followed by byte xor 0x20)
state 2 -> data bytes until 0x7E (frame end)
```

Neither function checks the length of the frame it writes through
`g_output_ptr`, which is the buffer overflow NCC describes as
**CVE-2022-38696**. Writes go into SRAM starting near 0x4000 (the stack
region end), so overrun can corrupt return addresses.

## 9. cmd_start - arbitrary write primitive (CVE-2022-38694)

Pseudocode from NCC, verified against disassembly:

```c
void cmd_start_usb(cmd_start_t *payload) {
    uint32_t addr_be = payload->addr_be;
    uint32_t sz_be = payload->sz_be;

    // The byteswap dance (endian flip)
    g_write_addr = __bswap32(addr_be);
    g_write_sz = __bswap32(sz_be);
    g_cur_write_ptr = g_write_addr;
    send_status(0x80);
}

void cmd_recv_data_usb(cmd_recv_data_t *payload) {
    uint16_t sz = __bswap16(payload->size_be);
    memcpy2(g_cur_write_ptr, payload->data, sz);
    g_cur_write_ptr += sz;
    g_num_received += sz;
    send_status(0x80);
}
```

The command pair gives a caller over USB the ability to write arbitrary
bytes at an arbitrary 32-bit address. Combined with `cmd_exec` (which
jumps to `g_write_addr`), this is the primary BootROM takeover primitive
and is the basis of the TomKing062 `exec_addr 0x3ee8` exploit.

No authentication is performed anywhere in this path before the write,
which is why our patched SPL flow works on locked devices: we just
`exec_addr 0x3ee8`, then the BootROM happily loads our unsigned FDL
payload and jumps into it.

## 10. RSA verification chain (secure boot path)

Secure boot verifies the image signature via a certificate chain.

`validate_rsa(fused_key_hash, payload_hash, cert)`:

- Read `cert->certtype`.
- If `certtype == 1` (keycert): hash the pubkey, compare against
  `fused_key_hash` (from eFuses). Then RSA-verify the signature over
  `cert->hash_data || cert->hash_key || type || version` (0x48 bytes).
- If `certtype == 0` (contentcert): RSA-verify over 0x48 bytes from
  `hash_data`, but **does not** hash+compare the embedded pubkey against
  the fused hash. This is **CVE-2022-38691/92**, the content certificate
  pubkey trust bypass.
- Otherwise: fail.

`do_rsa_powmod(e, n, bits, sig, dst)` at 0x1059ec is a thin wrapper:

```c
int do_rsa_powmod(uint32_t e, uint8_t *n, int bits, uint8_t *sig, uint8_t *dst) {
    memset(BYTE_ARRAY_00002988, 0, 0x100);        // tmp decrypted-sig buffer
    FUN_001059ec(e, n, bits, sig, BYTE_ARRAY_00002988);
    memcpy2(dst, BYTE_ARRAY_00002988, 0x100);
    return 0x100;
}
```

`FUN_00105514` at 0x105514 is the real engine setup. It byte-swaps `e`,
`n` and `sig` into the fixed SRAM buffers `g_e` (0x2468), `g_n` (0x2168),
`g_sig` (0x2268) via `byteswap_for_rsa` at 0x10546c. The buffers are
each 0x100 bytes sized; there is no size check on `bytelen`. Sending a
cert with a pubkey > 2048 bits overruns `g_sig` into the stack region
that starts at 0x3010, which is the **RSA key size overflow** path NCC
describes near the end of Finding #7.

The actual modular exponentiation is off-loaded to a hardware crypto
block programmed via MMIO writes at SRAM 0x4420-0x4440 (see 0x105514).
Several magic constants at 0x100420-0x100440 (`0xe1000010e0c0001`,
`0xb0002168`, etc) encode the engine's command descriptor.

## 11. send_status and status reporting

`send_status(mask)` at 0x107720 (leaf) just OR-clears a status word in
SRAM that is read by the USB/UART peripheral for DMA transfer back to
the host:

```c
void send_status(uint64_t clear_mask) {
    *(uint64_t*)0x5020 &= ~clear_mask;
}
```

Every success path in `cmd_start`/`cmd_recv_data`/`cmd_exec` ends with
`send_status(0x80)`. The 0xFFFF00000000 call in `enter_usb_recovery`
signals "FDL1 loaded, transferring control".

## 12. Full control-flow graph summary

```
Reset (0x100000)
  -> main (0x107ef8)
      -> fn_107450                    # hw init (UART/clock/DDR)
      -> fn_1071fc                    # interrupt / timer init
      -> fn_107734 (recovery button?) ---yes---> enter_usb_recovery (0x107dbc) [infinite]
      -> fn_107240 (eMMC probe)       ---yes---> fdl1_load_and_exec (0x1042e4) [never returns]
      -> fn_1045cc (alt boot source)  ---yes---> fn_104794 (alt loader) [never returns]
      -> dispatch_loop:
           receive_command (0x1077ac)    # blocks for cmd (via USB or UART)
           g_func_table[cmd]()
             -> recovery_comms (0x107e4c) for cmd 0
                 -> receive_and_validate_payload
                 -> g_cmd_table[cmd_id & 0xffff]()  # <-- CVE-2022-38695
                      cmd 0 connect
                      cmd 1 cmd_start                # <-- CVE-2022-38694 addr
                      cmd 2 cmd_recv_data            # <-- CVE-2022-38694 data
                      cmd 3 cmd_exec                 # jumps to g_write_addr
                      cmd 4 cmd_end_data
             -> enter_usb_recovery (0x107dbc) for cmd 1
```

The RSA verification hangs off `fdl1_load_and_exec` (0x1042e4): it loads
the FDL image into SRAM from eMMC, walks the certificate chain,
validates each cert via `validate_rsa`, and only then transfers control.
The contentcert bypass (CVE-2022-38691/92) lets an attacker provide their
own pubkey for the final stage as long as the intermediate cert chain is
stock.

## 13. CVE reference summary

| CVE | Location | Description |
|-----|----------|-------------|
| CVE-2022-38691/92 | `validate_rsa` (certtype 0 branch) | contentcert pubkey not compared to fused hash; arbitrary pubkey accepted |
| CVE-2022-38693 | FDL1 `usb_get_packet` | buffer overflow in the second-stage FDL1 image (NOT BootROM), separate binary |
| CVE-2022-38694 | `cmd_start` + `cmd_recv_data` | arbitrary write primitive over USB/UART recovery mode; chained with `cmd_exec` gives arbitrary code execution at BootROM privilege |
| CVE-2022-38695 | `recovery_comms` dispatch | unchecked cmd index into `g_cmd_table` (5 entries), OOB read treated as function pointer |
| CVE-2022-38696 | `receive_payload_usb` / `receive_payload_uart` | HDLC framer has no length check, overflows receive buffer near top of SRAM |
| Finding #5 | `handle_setup_request` GET_STATUS | unchecked wLength leaks SRAM past a fixed buffer |
| Finding #6 | various payload handlers | no length validation, uninitialised-memory disclosure |
| RSA key-size overflow | `FUN_00105514` at 0x105514 | `bytelen` not checked; pubkeys > 2048 bits overflow `g_n`/`g_sig` into stack |

## 14. Relevance to the overclocking investigation

The BootROM does **not** touch PMIC / DCDC / voltage-grade registers. Its
hardware init in `fn_107450` and the two AON APB writes in `main()`
(`0x327d0000`, `0x327d0004`) only enable internal clocks and domain-power
control bits; nothing DCDC-related. All voltage-grade programming that
clamps vddcpu at ~1050 mV and vddgpu at 800 mV must therefore happen
**after** the BootROM has exited, in SPL (splloader) or ATF (sml / BL31).

This matches the finding we already have in `oc_test/CHANGELOG.md`:
operating-points voltages above the stock ceiling are silently ignored
by the rail. The remaining candidates for where that ceiling is written
are the two binaries we already have stock backups of:

- `/work/vita/stock/splloader_backup.bin`
- `/work/vita/stock/sml_backup.bin` (ATF BL31 equivalent)

A targeted RE pass on one of those two is the next move if we want to
break past the 800 mV GPU / 1050 mV CPU ceiling without a userspace
voltage override.

## 15. Artefacts in this directory

- `BootROM_ums512_0x100000_0x111FFF.bin` - the raw binary
- `bootrom.elf` - ELF wrapper at VMA 0x100000 for tooling
- `bootrom.asm` - full `llvm-objdump -d` output (17k lines)
- `functions.txt` - all 142 identifiable function entry points (bl targets)
- `README.md` - provenance / dump recipe
- `DISASSEMBLY.md` - this document
