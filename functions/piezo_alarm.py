#!/usr/bin/env python3
"""
Piezo alarm driver for PillSyncOS.

Wiring:
  Piezo positive -> GPIO12 (BCM)
  Piezo negative -> GND
"""

import time
import RPi.GPIO as GPIO

PIEZO_PIN = 12  # BCM numbering
_initialized = False


def _init_gpio():
    """Initialize GPIO safely with Bookworm-compatible behavior."""
    global _initialized
    if _initialized:
        return

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # Debug helpful print
        print(f"[Piezo] Initializing GPIO pin {PIEZO_PIN}")

        GPIO.setup(PIEZO_PIN, GPIO.OUT, initial=GPIO.LOW)

        _initialized = True

    except Exception as e:
        print(f"[Piezo ERROR] Failed to initialize GPIO {PIEZO_PIN}: {e}")
        raise


def _beep(on_time: float = 0.15, off_time: float = 0.1):
    """Single short beep."""
    _init_gpio()
    GPIO.output(PIEZO_PIN, GPIO.HIGH)
    time.sleep(on_time)
    GPIO.output(PIEZO_PIN, GPIO.LOW)
    time.sleep(off_time)


def alarm(
    duration: float = 30.0,
    beeps_per_group: int = 3,
    beep_on_time: float = 0.15,
    beep_off_time: float = 0.1,
    group_pause: float = 0.5,
):
    """Blocking alarm pattern for the configured duration."""
    _init_gpio()
    start = time.time()

    try:
        while (time.time() - start) < duration:
            # beep group
            for _ in range(beeps_per_group):
                GPIO.output(PIEZO_PIN, GPIO.HIGH)
                time.sleep(beep_on_time)
                GPIO.output(PIEZO_PIN, GPIO.LOW)
                time.sleep(beep_off_time)

            # pause between groups
            time.sleep(group_pause)

    finally:
        # always force piezo off
        try:
            GPIO.output(PIEZO_PIN, GPIO.LOW)
        except:
            pass


def cleanup():
    """Cleanup GPIO when shutting down."""
    global _initialized
    if _initialized:
        try:
            GPIO.output(PIEZO_PIN, GPIO.LOW)
        except:
            pass
        GPIO.cleanup(PIEZO_PIN)
        _initialized = False


if __name__ == "__main__":
    print("Starting piezo alarm test for 10 seconds...")
    alarm(duration=10.0)
    print("Done.")
    cleanup()
