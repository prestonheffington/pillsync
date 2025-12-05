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


def _play_tone(freq: int, duration: float, duty: float = 70.0):
    """
    Play a tone at the given frequency and duty cycle.
    Higher duty = louder output while maintaining tone integrity.
    """
    global _pwm
    _init_gpio()

    if _pwm is None:
        _pwm = GPIO.PWM(PIEZO_PIN, freq)
    else:
        _pwm.ChangeFrequency(freq)

    _pwm.start(duty)
    time.sleep(duration)
    _pwm.stop()

def _chirp(on_time=0.22, off_time=0.12):
    """
    Louder medical-style chirp with increased duty cycle.
    Sweep: 1500 → 2600 Hz
    Duty cycle: 65% → 80%
    """
    _init_gpio()

    sweep_start = 1500
    sweep_end = 2600
    steps = 8
    step_size = (sweep_end - sweep_start) // steps
    tone_length = on_time / steps

    for i in range(steps):
        freq = sweep_start + (i * step_size)
        duty = 65 + (i * 2)  # Sweep from ~65% to ~80%
        if duty > 80:
            duty = 80  # Cap safely
        _play_tone(freq, tone_length, duty=duty)

    time.sleep(off_time)


def alarm(
    duration: float = 30.0,
    beeps_per_group: int = 2,
    group_pause: float = 0.6,
):
    """
    Friendly medical-device alarm using blended tone/chirp pattern.
    """
    _init_gpio()
    start = time.time()

    try:
        while (time.time() - start) < duration:
            for _ in range(beeps_per_group):
                _chirp()

            time.sleep(group_pause)

    finally:
        # ensure silence
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
