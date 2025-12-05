#!/usr/bin/env python3
"""
Motor Array Controller for PillSyncOS
Controls 28BYJ-48 stepper motors using one or two MCP23017 expanders.

Auto-detects which expanders are present:
 - Board 1 → I2C addr 0x20
 - Board 2 → I2C addr 0x21 (only used if physically present)

Each motor uses one nibble (4 bits):
  GPA0–3, GPA4–7, GPB0–3 per board.

Each dispense call:
 • Rotates exactly 320 "whole steps"
 • One whole step = 2 half-steps
 • Limit of 7 calls per motor (reset after homing)

MODIFIED:
 • Global motor direction reversed (CW → CCW)
"""

import time
from smbus2 import SMBus

# MCP23017 registers
IODIRA = 0x00
IODIRB = 0x01
OLATA  = 0x14
OLATB  = 0x15

# Two expanders (board 2 optional)
ADDR_BOARD1 = 0x20
ADDR_BOARD2 = 0x21

# Half-step sequence (original from test script)
SEQ = [
    0b0001, 0b0011, 0b0010, 0b0110,
    0b0100, 0b1100, 0b1000, 0b1001
]

# Master motor map (filtered after detection)
MOTOR_MAP_TEMPLATE = {
    1: {"addr": ADDR_BOARD1, "port": "A", "shift": 0},
    2: {"addr": ADDR_BOARD1, "port": "A", "shift": 4},
    3: {"addr": ADDR_BOARD1, "port": "B", "shift": 0},
    4: {"addr": ADDR_BOARD2, "port": "A", "shift": 0},
    5: {"addr": ADDR_BOARD2, "port": "A", "shift": 4},
    6: {"addr": ADDR_BOARD2, "port": "B", "shift": 0},
}

# Step definitions
HALFSTEPS_PER_WHOLESTEP = 2
WHOLESTEPS_PER_CALL = 558
MAX_CALLS_PER_MOTOR = 7


class MotorLimitReached(Exception):
    """Raised when a motor exceeds its allowed call count."""
    pass


class MotorArray:
    def __init__(self, bus_num: int = 1):
        self.bus = SMBus(bus_num)

        # 1) Detect expanders
        self._detect_expanders()

        # 2) Filter available motors
        self.motor_map = {
            mid: cfg for mid, cfg in MOTOR_MAP_TEMPLATE.items()
            if cfg["addr"] in self.detected_addrs
        }

        # 3) Initialize call counters
        self.call_counts = {mid: 0 for mid in self.motor_map}

        # 4) Initialize expanders
        self._init_expanders()

        print(f"[MotorArray] Detected expanders: {self.detected_addrs}")
        print(f"[MotorArray] Active motors: {list(self.motor_map.keys())}")

    # -------------------------------------------------------------
    # Expander detection
    # -------------------------------------------------------------
    def _detect_expanders(self):
        self.detected_addrs = []
        for addr in [ADDR_BOARD1, ADDR_BOARD2]:
            try:
                self.bus.write_byte(addr, 0x00)  # probe
                self.detected_addrs.append(addr)
            except:
                pass

    # -------------------------------------------------------------
    # Expander setup
    # -------------------------------------------------------------
    def _init_expanders(self):
        for addr in self.detected_addrs:
            self.bus.write_byte_data(addr, IODIRA, 0x00)
            self.bus.write_byte_data(addr, IODIRB, 0x00)
            self.bus.write_byte_data(addr, OLATA, 0x00)
            self.bus.write_byte_data(addr, OLATB, 0x00)

    # -------------------------------------------------------------
    # Low-level helpers
    # -------------------------------------------------------------
    def _write_port(self, addr, port, value):
        reg = OLATA if port == "A" else OLATB
        self.bus.write_byte_data(addr, reg, value & 0xFF)

    def _write_coils_motor(self, motor_id, pattern):
        cfg = self.motor_map[motor_id]
        addr = cfg["addr"]
        port = cfg["port"]
        shift = cfg["shift"]
        nibble_val = (pattern & 0x0F) << shift
        self._write_port(addr, port, nibble_val)

    def _coils_off_motor(self, motor_id):
        self._write_coils_motor(motor_id, 0x0)

    # -------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------
    def remaining_calls(self, motor_id):
        return MAX_CALLS_PER_MOTOR - self.call_counts[motor_id]

    def reset_call_count(self, motor_id):
        self.call_counts[motor_id] = 0

    def reset_all_call_counts(self):
        for mid in self.call_counts:
            self.call_counts[mid] = 0

    # -------------------------------------------------------------
    # STEPPER MOVEMENT (PATCHED FOR REVERSED DIRECTION)
    # -------------------------------------------------------------
    def step_motor(
        self,
        motor_id: int,
        direction: int = 1,
        whole_steps: int = WHOLESTEPS_PER_CALL,
        delay: float = 0.003,
        enforce_limits: bool = True,
    ):
        if motor_id not in self.motor_map:
            raise ValueError(f"Motor {motor_id} not available on detected hardware")

        if enforce_limits and self.call_counts[motor_id] >= MAX_CALLS_PER_MOTOR:
            raise MotorLimitReached(
                f"Motor {motor_id} has reached max {MAX_CALLS_PER_MOTOR} calls."
            )

        total_halfsteps = whole_steps * HALFSTEPS_PER_WHOLESTEP

        # --------------------------------------------------------
        # PATCH: Reverse direction globally
        # CW (old direction>=0) now becomes CCW
        # --------------------------------------------------------
        if direction >= 0:
            idx = len(SEQ) - 1        # start at end
            step_fn = lambda i: (i - 1) % len(SEQ)
        else:
            idx = 0                  # start at beginning
            step_fn = lambda i: (i + 1) % len(SEQ)

        try:
            for _ in range(total_halfsteps):
                pattern = SEQ[idx]
                self._write_coils_motor(motor_id, pattern)
                time.sleep(delay)
                idx = step_fn(idx)

        finally:
            self._coils_off_motor(motor_id)

        if enforce_limits:
            self.call_counts[motor_id] += 1

    # -------------------------------------------------------------
    def coils_off_all(self):
        for addr in self.detected_addrs:
            self.bus.write_byte_data(addr, OLATA, 0x00)
            self.bus.write_byte_data(addr, OLATB, 0x00)

    def close(self):
        self.coils_off_all()
        self.bus.close()


if __name__ == "__main__":
    ma = MotorArray()
    try:
        print("Testing motor 1 → 320 steps (now CCW by default)")
        ma.step_motor(1)
    finally:
        ma.close()
