#!/usr/bin/env python3
# Drives six 28BYJ-48 steppers via two MCP23017 expanders, one motor at a time.

import time
import board
import busio

# pip install adafruit-circuitpython-mcp230xx
from adafruit_mcp230xx.mcp23017 import MCP23017

# -------------------- CONFIG (edit if your wiring changes) --------------------
# I2C addresses (A2..A0 strap pins). From your schematic:
#  - Expander 1: "initial state" = 0x20 (A0 open)
#  - Expander 2: "A0 soldered closed" = 0x21
I2C_ADDRS = { "EXP1": 0x20, "EXP2": 0x21 }

# Map each motor to four pins on the MCP23017: (expander_key, pin_number)
# Pin numbers are MCP23017 0..15 (A0..A7 = 0..7, B0..B7 = 8..15).
# This mapping assumes each ULN2003 IN1..IN4 is wired in order to consecutive pins.
# If your board swapped IN order, just permute the 4-tuple for that motor.
MOTOR_PINS = {
    # Left cluster (EXP1 = 0x20)
    "M1": [("EXP1", 0), ("EXP1", 1), ("EXP1", 2), ("EXP1", 3)],   # IN1..IN4
    "M2": [("EXP1", 4), ("EXP1", 5), ("EXP1", 6), ("EXP1", 7)],
    "M3": [("EXP1", 8), ("EXP1", 9), ("EXP1",10), ("EXP1",11)],

    # Right cluster (EXP2 = 0x21)
    "M4": [("EXP2", 0), ("EXP2", 1), ("EXP2", 2), ("EXP2", 3)],
    "M5": [("EXP2", 4), ("EXP2", 5), ("EXP2", 6), ("EXP2", 7)],
    "M6": [("EXP2", 8), ("EXP2", 9), ("EXP2",10), ("EXP2",11)],
}

# Motion tuning
HALF_STEPS_PER_REV = 4096      # typical for 28BYJ-48 gearbox (tune if needed)
STEP_DELAY = 0.0018            # half-step dwell (sec). Increase for more torque.
PAUSE_BETWEEN = 2.0            # seconds between motors
# -----------------------------------------------------------------------------

# 8-state half-step sequence (28BYJ-48 via ULN2003)
HALFSEQ = [
    (1,0,0,0),
    (1,1,0,0),
    (0,1,0,0),
    (0,1,1,0),
    (0,0,1,0),
    (0,0,1,1),
    (0,0,0,1),
    (1,0,0,1),
]

class StepperViaMCP:
    def __init__(self, pins):
        # pins: list of 4 adafruit_mcp230xx digital pin objects
        self.pins = pins
        for p in self.pins:
            p.switch_to_output(value=False)

    def _write(self, a,b,c,d):
        for p, v in zip(self.pins, (a,b,c,d)):
            p.value = bool(v)

    def release(self):
        for p in self.pins:
            p.value = False

    def step(self, steps, delay=STEP_DELAY):
        seq = HALFSEQ if steps >= 0 else list(reversed(HALFSEQ))
        steps = abs(int(steps))
        for i in range(steps):
            self._write(*seq[i % 8])
            time.sleep(delay)
        self.release()

    def rotate_degrees(self, deg, delay=STEP_DELAY):
        steps = int(HALF_STEPS_PER_REV * (deg / 360.0))
        self.step(steps, delay=delay)

def get_mcps():
    i2c = busio.I2C(board.SCL, board.SDA)
    return {k: MCP23017(i2c, address=a) for k, a in I2C_ADDRS.items()}

def mcp_pin(mcp, n):
    if not (0 <= n <= 15):
        raise ValueError("MCP23017 pin index must be 0..15")
    return mcp.get_pin(n)

def build_motors(mcps):
    motors = []
    for name, mapping in MOTOR_PINS.items():
        pin_objs = [mcp_pin(mcps[exp], pin_n) for (exp, pin_n) in mapping]
        motors.append((name, StepperViaMCP(pin_objs)))
    return motors

def sequence_half_turn_each(direction="CW"):
    """Turn each motor half a revolution in order, pausing in between."""
    mcps = get_mcps()
    motors = build_motors(mcps)

    print("Detected expanders:", {k: hex(v) for k, v in I2C_ADDRS.items()})
    print("Starting sequence: half-turn each, 2s pause.")

    sign = 1 if direction.upper() == "CW" else -1
    half_turn_deg = 180.0 * sign

    for name, motor in motors:
        print(f"-> {name}: rotating {half_turn_deg:+.0f}°")
        motor.rotate_degrees(half_turn_deg)
        motor.release()
        time.sleep(PAUSE_BETWEEN)

    print("Done.")

if __name__ == "__main__":
    try:
        sequence_half_turn_each("CW")   # change to "CCW" if needed
    except KeyboardInterrupt:
        pass
