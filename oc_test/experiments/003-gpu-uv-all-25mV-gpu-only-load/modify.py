#!/usr/bin/env python3
"""Experiment 003: same DTB as 002, different test harness (GPU-only load)."""
# The DTB modification is identical to experiment 002.
# Use ../002-gpu-uv-all-25mV/modify.py to generate the DTB.
# The difference is the test: run ./gpu_only_test.sh not ./torture_test.sh
from pathlib import Path
import subprocess, sys

exp002 = Path(__file__).parent.parent / '002-gpu-uv-all-25mV' / 'modify.py'
subprocess.check_call([sys.executable, str(exp002)])
