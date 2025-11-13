#!/usr/bin/env python3
"""
Neopixel alarm flash for PillSyncOS.

Wiring:
  Neopixel DIN  -> GPIO18 (BCM) / board.D18
  Neopixel VCC  -> 5V
  Neopixel GND  -> GND

Assumes an 8-LED stick (8x5050).
"""

import time
import board
import neopixel

PIXEL_PIN = board.D18
NUM_PIXELS = 8
BRIGHTNESS = 0.4

_pixels = None


def _init_pixels():
    global _pixels
    if _pixels is None:
        _pixels = neopixel.NeoPixel(
            PIXEL_PIN,
            NUM_PIXELS,
            brightness=BRIGHTNESS,
            auto_write=False,
        )
        _pixels.fill((0, 0, 0))
        _pixels.show()
    return _pixels


def _set_all(color):
    pixels = _init_pixels()
    pixels.fill(color)
    pixels.show()


def alarm_flash(
    duration: float = 30.0,
    flash_on_time: float = 0.15,
    flash_off_time: float = 0.15,
    group_flashes: int = 3,
    group_pause: float = 0.5,
    color=(255, 0, 0),
):
    """
    Blocking Neopixel alarm flash.

    Pattern:
      - 3 quick red flashes
      - pause
      - repeat until duration elapsed

    :param duration: total alarm time in seconds (default 30s)
    """
    start = time.time()
    _init_pixels()

    try:
        while (time.time() - start) < duration:
            # group of flashes
            for _ in range(group_flashes):
                _set_all(color)
                time.sleep(flash_on_time)
                _set_all((0, 0, 0))
                time.sleep(flash_off_time)

            # pause between groups
            time.sleep(group_pause)
    finally:
        # ensure LEDs are off at the end
        _set_all((0, 0, 0))


def cleanup():
    """Turn off LEDs; neopixel doesn't need a 'cleanup', just black them out."""
    if _init_pixels() is not None:
        _set_all((0, 0, 0))


if __name__ == "__main__":
    print("Starting Neopixel alarm flash test for 10 seconds...")
    alarm_flash(duration=10.0)
    print("Done.")
    cleanup()
