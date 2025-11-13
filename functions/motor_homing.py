#!/usr/bin/env python3
"""
Motor homing utilities for PillSyncOS.

Homing behavior (software-based):
- Each motor has 7 dispense positions per full rotation.
- Each dispense call = 320 whole steps.
- Homing = rotate 7 × 320 whole steps in a fixed direction,
  then reset the call counter for that motor.

This does NOT use a physical home switch; it assumes
mechanical alignment has been done previously and
one full revolution returns to the logical "home" slot.
"""

from .motor_array import WHOLESTEPS_PER_CALL

# 7 × 320 whole steps per full homing move
SLOTS_PER_REV = 7
HOME_WHOLESTEPS = SLOTS_PER_REV * WHOLESTEPS_PER_CALL


def home_motor(
    motor_array,
    motor_id: int,
    direction: int = -1,
    delay: float = 0.003,
) -> bool:
    """
    Home a single motor by rotating it 7 × 320 whole steps.

    :param motor_array: an instance of MotorArray to operate on
    :param motor_id: Motor number (1–6)
    :param direction: -1 or +1, direction toward "home"
    :param delay: delay between half-steps (seconds)
    :return: True if homing completed without error
    """
    # Ignore per-motor call limits during homing
    motor_array.step_motor(
        motor_id=motor_id,
        direction=direction,
        whole_steps=HOME_WHOLESTEPS,
        delay=delay,
        enforce_limits=False,
    )

    # After a successful homing move, reset the call counter
    motor_array.reset_call_count(motor_id)
    return True


def home_all_motors(
    motor_array,
    direction: int = -1,
    delay: float = 0.003,
) -> dict:
    """
    Home motors 1–6 sequentially.

    :param motor_array: an instance of MotorArray to operate on
    :param direction: homing direction for all motors
    :param delay: delay between half-steps
    :return: dict of {motor_id: True} for now (placeholder for future error handling)
    """
    results = {}
    for mid in range(1, 7):
        ok = home_motor(
            motor_array=motor_array,
            motor_id=mid,
            direction=direction,
            delay=delay,
        )
        results[mid] = ok
    return results


if __name__ == "__main__":
    # This module is normally used via core.py. Direct running would need
    # manual wiring of MotorArray, so we don't do that here.
    print("motor_homing.py is intended to be used via core.CoreController.")

