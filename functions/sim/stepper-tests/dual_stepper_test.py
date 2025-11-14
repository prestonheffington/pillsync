#!/usr/bin/env python3
"""
MCP23017 Dual Stepper Sequential Test
-------------------------------------
Drives two 28BYJ-48 steppers (via ULN2003 boards) on a single MCP23017 (addr 0x20).

Mapping:
  Motor 1 → GPA0..GPA3
  Motor 2 → GPB0..GPB3

Sequence:
  - Motor 1 CW one revolution
  - Pause 5s
  - Motor 2 CW one revolution
  - Pause 5s
  - Motor 1 CCW one revolution
  - Pause 5s
  - Motor 2 CCW one revolution

Use:  python3 stepper_dual_seq_test.py
"""

import time
from smbus2 import SMBus

# MCP23017 (BANK=0 default) registers
IODIRA, IODIRB = 0x00, 0x01
OLATA,  OLATB  = 0x14, 0x15

ADDR = 0x20
HALFSTEPS_PER_REV = 4096  # ~1 rev for 28BYJ-48
DELAY = 0.003  # seconds between half-steps

# Half-step pattern
SEQ = [
    0b0001, 0b0011, 0b0010, 0b0110,
    0b0100, 0b1100, 0b1000, 0b1001
]

def set_outputs(bus, addr, port):
    """Configure port pins as outputs."""
    reg = IODIRA if port == 'A' else IODIRB
    bus.write_byte_data(addr, reg, 0x00)

def write_coils(bus, addr, port, val):
    """Send pattern to ULN2003 input nibble."""
    reg = OLATA if port == 'A' else OLATB
    bus.write_byte_data(addr, reg, val & 0x0F)

def coils_off(bus, addr, port):
    """De-energize all coils."""
    write_coils(bus, addr, port, 0x00)

def step(bus, addr, port, steps, delay, direction=1):
    """Perform step sequence in given direction."""
    idx = 0 if direction > 0 else len(SEQ) - 1
    for _ in range(steps):
        write_coils(bus, addr, port, SEQ[idx])
        time.sleep(delay)
        idx = (idx + 1) % len(SEQ) if direction > 0 else (idx - 1) % len(SEQ)
    coils_off(bus, addr, port)

def main():
    with SMBus(1) as bus:
        print("[Init] Configuring MCP23017 outputs")
        set_outputs(bus, ADDR, 'A')
        set_outputs(bus, ADDR, 'B')
        coils_off(bus, ADDR, 'A')
        coils_off(bus, ADDR, 'B')

        print("[Run] Motor 1 CW 1 rev")
        step(bus, ADDR, 'A', HALFSTEPS_PER_REV, DELAY, +1)
        time.sleep(5)

        print("[Run] Motor 2 CW 1 rev")
        step(bus, ADDR, 'B', HALFSTEPS_PER_REV, DELAY, +1)
        time.sleep(5)

        print("[Run] Motor 1 CCW 1 rev")
        step(bus, ADDR, 'A', HALFSTEPS_PER_REV, DELAY, -1)
        time.sleep(5)

        print("[Run] Motor 2 CCW 1 rev")
        step(bus, ADDR, 'B', HALFSTEPS_PER_REV, DELAY, -1)

        print("[Done] All motors off")
        coils_off(bus, ADDR, 'A')
        coils_off(bus, ADDR, 'B')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        with SMBus(1) as bus:
            coils_off(bus, ADDR, 'A')
            coils_off(bus, ADDR, 'B')
        print("\n[Interrupted] Coils off.")
