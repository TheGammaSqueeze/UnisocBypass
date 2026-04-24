#!/usr/bin/env python3
"""Generate modified.dts for exp 021: GPU 900 MHz with operating-points voltage 850 mV.

Hypothesis: operating-points voltage IS applied to vddgpu via regulator_set_voltage()
in kbase_devfreq_target. Exp 020 kept OP voltage at 800 mV (stock); exp 021 raises it
to 850 mV to verify and stabilize 900 MHz.
"""
import subprocess, pathlib
here = pathlib.Path(__file__).parent
out = here / 'modified.dts'
tools = here.parent.parent / 'tools'
subprocess.check_call(['python3', str(tools / 'gen_gpu_oc_dts.py'),
                       '900', '--volt-mv', '850', str(out)])
