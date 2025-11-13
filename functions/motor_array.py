#!/usr/bin/env python3
"""
Motor Array Controller for PillSyncOS
Controls 6x 28BYJ-48 stepper motors using two MCP23017 expanders.

BOARD 1 (I2C addr 0x20)
  Motor 1 → GPA0–GPA3
  Motor 2 → GPA4–GPA7
  Motor 3 → GPB0–GPB3

BOARD 2 (I2C addr 0x21)
  Motor 4 → GPA0–GPA3
  Motor 5 → GPA4–GPA7
  Motor 6 → GPB0–GPB3

Each dispense call:
 • Rotates exactly 320 "whole steps"
 • One whole step = 2 half-steps
 • Limit of 7 calls per motor (reset after homing)
"""

import time
from smbus2 import SMBus

# MCP23017 registers
IODIRA = 0x00
IODIRB = 0x01
OLATA  = 0x14
OLATB  = 0x15

# Two expanders
ADDR_BOARD1 = 0x20
ADDR_BOARD2 = 0x21

# Half-step sequence (same as your working test script)
SEQ = [
    0b0001, 0b0011, 0b0010, 0b0110,
    0b0100, 0b1100, 0b1000, 0b1001
]

# Motor mapping (logical motor → board/port/nibble)
MOTOR_MAP = {
    1: {"addr": ADDR_BOARD1, "port": "A", "shift": 0},
    2: {"addr": ADDR_BOARD1, "port": "A", "shift": 4},
    3: {"addr": ADDR_BOARD1, "port": "B", "shift": 0},
    4: {"addr": ADDR_BOARD2, "port": "A", "shift": 0},
    5: {"addr": ADDR_BOARD2, "port": "A", "shift": 4},
    6: {"addr": ADDR_BOARD2, "port": "B", "shift": 0},
}

# Step definitions
HALFSTEPS_PER_WHOLESTEP = 2
WHOLESTEPS_PER_CALL = 320
MAX_CALLS_PER_MOTOR = 7


class MotorLimitReached(Exception):
    """Raised when a motor exceeds its allowed call count."""
    pass


class MotorArray:
    def __init__(self, bus_num: int = 1):
        self.bus = SMBus(bus_num)
        self.call_counts = {mid: 0 for mid in MOTOR_MAP}
        self._init_expanders()

    # -------------------------
    # Expander setup
    # -------------------------
    def _init_expanders(self):
        used_addrs = {cfg["addr"] for cfg in MOTOR_MAP.values()}
        for addr in used_addrs:
            # Set both ports as outputs
            self.bus.write_byte_data(addr, IODIRA, 0x00)
            self.bus.write_byte_data(addr, IODIRB, 0x00)
            # Coils off
            self.bus.write_byte_data(addr, OLATA, 0x00)
            self.bus.write_byte_data(addr, OLATB, 0x00)

    # -------------------------
    # Internal low-level helpers
    # -------------------------
    def _write_port(self, addr, port, value):
        reg = OLATA if port == "A" else OLATB
        self.bus.write_byte_data(addr, reg, value & 0xFF)

    def _write_coils_motor(self, motor_id, pattern):
        cfg = MOTOR_MAP[motor_id]
        addr = cfg["addr"]
        port = cfg["port"]
        shift = cfg["shift"]

        # Place the 4-bit pattern into the correct nibble
        nibble_val = (pattern & 0x0F) << shift

        # Only one motor runs at a time → safe to zero other nibble
        self._write_port(addr, port, nibble_val)

    def _coils_off_motor(self, motor_id):
        self._write_coils_motor(motor_id, 0x0)

    # -------------------------
    # Public API
    # -------------------------
    def remaining_calls(self, motor_id):
        return MAX_CALLS_PER_MOTOR - self.call_counts[motor_id]

    def reset_call_count(self, motor_id):
        self.call_counts[motor_id] = 0

    def reset_all_call_counts(self):
        for mid in self.call_counts:
            self.call_counts[mid] = 0

    def step_motor(
        self,
        motor_id: int,
        direction: int = 1,
        whole_steps: int = WHOLESTEPS_PER_CALL,
        delay: float = 0.003,
        enforce_limits: bool = True,
    ):
        if enforce_limits and self.call_counts[motor_id] >= MAX_CALLS_PER_MOTOR:
            raise MotorLimitReached(
                f"Motor {motor_id} has reached max {MAX_CALLS_PER_MOTOR} calls."
            )

        total_halfsteps = whole_steps * HALFSTEPS_PER_WHOLESTEP
        idx = 0 if direction >= 0 else len(SEQ) - 1

        try:
            for _ in range(total_halfsteps):
                pattern = SEQ[idx]
                self._write_coils_motor(motor_id, pattern)
                time.sleep(delay)

                idx = (idx + 1) % len(SEQ) if direction >= 0 else (idx - 1) % len(SEQ)

        finally:
            self._coils_off_motor(motor_id)

        if enforce_limits:
            self.call_counts[motor_id] += 1

    def coils_off_all(self):
        addrs = {cfg["addr"] for cfg in MOTOR_MAP.values()}
        for addr in addrs:
            self.bus.write_byte_data(addr, OLATA, 0x00)
            self.bus.write_byte_data(addr, OLATB, 0x00)

    def close(self):
        self.coils_off_all()
        self.bus.close()


if __name__ == "__main__":
    ma = MotorArray()
    try:
        print("Testing motor 1 → 320 steps CW")
        ma.step_motor(1)
    finally:
        ma.close()
