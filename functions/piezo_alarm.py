#!/usr/bin/env python3
"""
Piezo alarm driver for PillSyncOS.

Wiring:
  Piezo positive -> GPIO12 (BCM)
  Piezo negative -> GND
"""

import time
import RPi.GPIO as GPIO

PIEZO_PIN = 12  # BCM numbering (PWM-capable)
_initialized = False
_pwm = None


def _init_gpio():
    """Initialize GPIO safely with Bookworm-compatible behavior."""
    global _initialized
    if _initialized:
        return

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        print(f"[Piezo] Initializing GPIO pin {PIEZO_PIN}")

        GPIO.setup(PIEZO_PIN, GPIO.OUT, initial=GPIO.LOW)

        _initialized = True

    except Exception as e:
        print(f"[Piezo ERROR] Failed to initialize GPIO {PIEZO_PIN}: {e}")
        raise


def _beep(
    on_time: float = 0.15,
    off_time: float = 0.1,
    freq: int = 3000,
    duty: float = 50.0,
):
    """
    Loud beep using PWM tone.
    freq ~3000 Hz works for most passive piezos.
    duty 50% is usually the loudest.
    """
    global _pwm
    _init_gpio()

    if _pwm is None:
        _pwm = GPIO.PWM(PIEZO_PIN, freq)

    _pwm.start(duty)   # TURN ON TONE
    time.sleep(on_time)
    _pwm.stop()        # TURN OFF TONE
    time.sleep(off_time)


def alarm(
    duration: float = 30.0,
    beeps_per_group: int = 3,
    beep_on_time: float = 0.2,      # slightly longer for more volume
    beep_off_time: float = 0.12,
    group_pause: float = 0.45,
    freq: int = 3000,               # loudest tone frequency
    duty: float = 50.0,             # loudest duty cycle
):
    """
    Blocking alarm pattern using loud PWM tone.
    """
    _init_gpio()
    start = time.time()

    try:
        while (time.time() - start) < duration:
            for _ in range(beeps_per_group):
                _beep(beep_on_time, beep_off_time, freq=freq, duty=duty)

            time.sleep(group_pause)

    finally:
        # ensure pin is silent
        try:
            GPIO.output(PIEZO_PIN, GPIO.LOW)
        except:
            pass


def cleanup():
    """Cleanup GPIO when shutting down."""
    global _initialized, _pwm
    if _pwm is not None:
        try:
            _pwm.stop()
        except:
            pass
        _pwm = None

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
