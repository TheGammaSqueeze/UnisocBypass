# 010 - CPU UV -62.5 mV (GPU stock)

Deeper CPU UV. GPU DT left unchanged since DTB GPU UV doesn't reach hardware.

DT targets:
- CPU LITTLE 2002 MHz: 1050 mV -> 987.5 mV
- CPU BIG 2002 MHz: 1050 mV -> 987.5 mV

Previous runtime voltage floor observed at 1009 mV in cpu-only mode. Testing
whether going deeper in DT still yields any further drop at runtime.
