"""Helpers for reproducible DTB modifications on RG Vita (UMS512).

Usage pattern from an experiment's modify.py:

    from pathlib import Path
    from oc_test.tools.modify_dtb import DtbPatcher, pack_multidtb, pack_into_editor

    p = DtbPatcher('/tmp/editor.dts')
    p.replace_gpu_opp_voltage(850, old_mv=800, new_mv=787.5)
    p.save('/tmp/editor_modified.dts')
    p.compile('/tmp/editor_modified.dtb')
    pack_multidtb('/tmp/editor_modified.dtb', '/tmp/modified_multidtb.bin')
    pack_into_editor('/tmp/modified_multidtb.bin',
                     '/work/vita/android_boot_image_editor')
"""
import struct
import subprocess
import sys
from pathlib import Path

UV_TO_HEX = {  # common voltages in microvolts -> hex
    700000: '0xaae60', 750000: '0xb71b0', 800000: '0xc3500',
    787500: '0xc042c', 775000: '0xbd358', 762500: '0xba284',
    725000: '0xb1008', 712500: '0xadf30', 687500: '0xa7f8c',
    1050000: '0x100590', 1075000: '0x1066b8', 1100000: '0x10c8e0',
    1012500: '0xf7214',
}

class DtbPatcher:
    def __init__(self, dts_path):
        self.dts_path = dts_path
        self.dts = Path(dts_path).read_text()
        self.changes = []

    def replace(self, old, new, tag='generic'):
        n = self.dts.count(old)
        if n == 0:
            raise ValueError(f'pattern not found: {old!r}')
        self.dts = self.dts.replace(old, new)
        self.changes.append((tag, n, old, new))
        return n

    def save(self, dst):
        Path(dst).write_text(self.dts)

    def compile(self, dst_dtb):
        r = subprocess.run(['dtc', '-q', '-I', 'dts', '-O', 'dtb', '-o', dst_dtb, self.dts_path],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f'dtc failed: {r.stderr}')


def pack_multidtb(inner_dtb_path, out_path):
    inner = Path(inner_dtb_path).read_bytes()
    hdr = struct.pack('>IIIIIIII', 0xd7b7ab1e, 64 + len(inner), 32, 32, 1, 32, 4096, 1)
    entry = struct.pack('>IIIIIIII', len(inner), 64, 0, 0, 0, 0, 0, 0)
    Path(out_path).write_bytes(hdr + entry + inner)


def pack_into_editor(multidtb_path, editor_root):
    import shutil
    dst = Path(editor_root) / 'build' / 'unzip_boot' / 'dtb'
    shutil.copy(multidtb_path, dst)
