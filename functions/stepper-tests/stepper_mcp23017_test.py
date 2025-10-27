#!/usr/bin/env python3
"""
MCP23017 Stepper Test (Adafruit GPIO Expander Bonnet)
Default mapping: GPA0..GPA3 -> ULN2003 IN1..IN4
Performs 1 rev CW, pause 5s, then 1 rev CCW.

Usage examples:
  python3 stepper_mcp23017_test.py                 # addr 0x20, Port A
  python3 stepper_mcp23017_test.py --addr 0x21     # second bonnet
  python3 stepper_mcp23017_test.py --port B        # use GPB0..GPB3
  python3 stepper_mcp23017_test.py --delay 0.004   # slower (more torque)
"""

import time
import argparse
from smbus2 import SMBus

# MCP23017 (BANK=0 default) registers
IODIRA = 0x00
IODIRB = 0x01
OLATA  = 0x14
OLATB  = 0x15

HALFSTEPS_PER_REV = 4096  # 28BYJ-48 approx

# Half-step sequence, LSB is Ax0 (A0/B0)
HALFSTEP_SEQ = [
    0b0001,  # x0
    0b0011,  # x0,x1
    0b0010,  # x1
    0b0110,  # x1,x2
    0b0100,  # x2
    0b1100,  # x2,x3
    0b1000,  # x3
    0b1001,  # x3,x0
]

def set_outputs(bus, addr, port):
    if port == 'A':
        bus.write_i2c_block_data(addr, IODIRA, [0x00])  # all A pins output
    else:
        bus.write_i2c_block_data(addr, IODIRB, [0x00])  # all B pins output

def write_coils(bus, addr, port, val):
    reg = OLATA if port == 'A' else OLATB
    bus.write_i2c_block_data(addr, reg, [val & 0x0F])  # only lower 4 bits used

def coils_off(bus, addr, port):
    write_coils(bus, addr, port, 0x00)

def step(bus, addr, port, steps, delay, direction=1):
    idx = 0 if direction > 0 else len(HALFSTEP_SEQ) - 1
    for _ in range(steps):
        write_coils(bus, addr, port, HALFSTEP_SEQ[idx])
        time.sleep(delay)
        idx = (idx + 1) % len(HALFSTEP_SEQ) if direction > 0 else (idx - 1) % len(HALFSTEP_SEQ)
    coils_off(bus, addr, port)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addr", type=lambda x: int(x, 0), default=0x20, help="I2C address (e.g., 0x20, 0x21)")
    ap.add_argument("--port", choices=['A','B'], default='A', help="Use MCP23017 Port A or B")
    ap.add_argument("--delay", type=float, default=0.003, help="Seconds between half-steps")
    args = ap.parse_args()

    print(f"[MCP23017 test] addr=0x{args.addr:02X} port={args.port} delay={args.delay}s")
    with SMBus(1) as bus:
        set_outputs(bus, args.addr, args.port)

        print("Rotate CW 1 rev…")
        step(bus, args.addr, args.port, HALFSTEPS_PER_REV, args.delay, direction=1)

        print("Pause 5s…")
        time.sleep(5)

        print("Rotate CCW 1 rev…")
        step(bus, args.addr, args.port, HALFSTEPS_PER_REV, args.delay, direction=-1)

        coils_off(bus, args.addr, args.port)
        print("Done.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        with SMBus(1) as bus:
            # best-effort coil off on common addresses
            for a in (0x20, 0x21, 0x22, 0x23):
                try:
                    write_coils(bus, a, 'A', 0x00)
                    write_coils(bus, a, 'B', 0x00)
                except Exception:
                    pass
        print("\nInterrupted; coils de-energized.")
