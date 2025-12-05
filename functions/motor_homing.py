#!/usr/bin/env python3
"""
Motor homing utilities for PillSyncOS.

Homing behavior (software-based):
- Each motor has 7 dispense positions per full rotation.
- Each dispense call = 320 whole steps.
- Homing = rotate 7 × 320 whole steps in a fixed direction,
  then reset the call counter for that motor.

PATCHES:
- Default homing direction changed to +1 (CW),
  because global motor direction in MotorArray was reversed.
- Home only motors 1–3 (motors 4–6 disabled for demo day).
"""

from .motor_array import WHOLESTEPS_PER_CALL

# 7 × 320 whole steps per full homing move
SLOTS_PER_REV = 7
HOME_WHOLESTEPS = SLOTS_PER_REV * WHOLESTEPS_PER_CALL


def home_motor(
    motor_array,
    motor_id: int,
    direction: int = +1,   # PATCH: home now moves CW by default
    delay: float = 0.003,
) -> bool:
    """Home a single motor by rotating it 7 × 320 whole steps."""

    # Ignore per-motor call limits during homing
    motor_array.step_motor(
        motor_id=motor_id,
        direction=direction,
        whole_steps=HOME_WHOLESTEPS,
        delay=delay,
        enforce_limits=False,
    )

    motor_array.reset_call_count(motor_id)
    return True


def home_all_motors(
    motor_array,
    direction: int = +1,   # PATCH: default homing direction now CW
    delay: float = 0.003,
) -> dict:
    """
    Home motors 1–3 only.
    Motors 4–6 are disabled for demo day.
    """
    results = {}

    for mid in [1, 2, 3]:   # PATCH: demo-safe motor list
        ok = home_motor(
            motor_array=motor_array,
            motor_id=mid,
            direction=direction,
            delay=delay,
        )
        results[mid] = ok

    # Optional: mark disabled motors in results
    # results[4] = "disabled"
    # results[5] = "disabled"
    # results[6] = "disabled"

    return results


if __name__ == "__main__":
    print("motor_homing.py is intended to be used via core.CoreController.")
