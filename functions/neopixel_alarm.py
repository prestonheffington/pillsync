#!/usr/bin/env python3
"""
NeoPixel alarm visual driver for PillSyncOS.

This version does NOT talk directly to the hardware.
It calls the privileged root helper:
    /usr/local/bin/neopixel_driver.py

This keeps PillSync running as a normal user
while still allowing LED control via sudo.
"""

import time
import subprocess

# How many chirps per group (match piezo)
CHIRPS_PER_GROUP = 2

# Timings that match your piezo chirp behavior:
CHIRP_ON = 0.22      # piezo rising sweep duration
CHIRP_OFF = 0.12     # pause between chirps
GROUP_PAUSE = 0.6    # pause after two chirps


def _flash_on():
    """Trigger root helper to flash NeoPixels ON."""
    subprocess.Popen(
        ["sudo", "/usr/local/bin/neopixel_driver.py", "alert"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _flash_off():
    """Turn NeoPixels OFF."""
    subprocess.Popen(
        ["sudo", "/usr/local/bin/neopixel_driver.py", "off"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def alarm_flash(duration: float = 30.0):
    """
    Visual alarm pattern that syncs with the Piezo's chirp pattern:

    chirp:
        - light on during chirp sweep
        - off during chirp gap
    group:
        - pause between groups
    """

    print("Starting Neopixel alarm flash (synced to piezo)...")
    start = time.time()

    try:
        while (time.time() - start) < duration:

            # Two chirps in a row (same as piezo)
            for _ in range(CHIRPS_PER_GROUP):
                _flash_on()
                time.sleep(CHIRP_ON)
                _flash_off()
                time.sleep(CHIRP_OFF)

            # Group pause (same as piezo)
            time.sleep(GROUP_PAUSE)

    finally:
        # Make sure LEDs turn off at end
        _flash_off()
        print("Neopixel alarm finished.")


if __name__ == "__main__":
    print("Starting Neopixel alarm test for 10 seconds...")
    alarm_flash(duration=10.0)
    print("Done.")
