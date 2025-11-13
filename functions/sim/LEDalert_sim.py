# sos_neopixel.py
# Flashes an 8-LED NeoPixel stick in orange (... --- ...) SOS pattern.

import time
import board
import neopixel

# --- Configuration ---
PIXEL_PIN = board.D13      # GPIO 13 (BCM)
NUM_PIXELS = 8
COLOR = (255, 80, 0)       # orange
BRIGHTNESS = 0.3

# Morse timing (seconds)
DOT = 0.2
DASH = DOT * 3
INTRA = DOT
LETTER_GAP = DOT * 3
WORD_GAP = DOT * 7

pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)

def flash(duration):
    """Turn on all pixels in orange for <duration> seconds."""
    pixels.fill(COLOR)
    pixels.show()
    time.sleep(duration)
    pixels.fill((0, 0, 0))
    pixels.show()
    time.sleep(INTRA)

def sos_signal(repeats=2):
    """Play SOS (... --- ...) <repeats> times."""
    for _ in range(repeats):
        # S = ...
        for _ in range(3):
            flash(DOT)
        time.sleep(LETTER_GAP)

        # O = ---
        for _ in range(3):
            flash(DASH)
        time.sleep(LETTER_GAP)

        # S = ...
        for _ in range(3):
            flash(DOT)
        time.sleep(WORD_GAP)

if __name__ == "__main__":
    try:
        sos_signal()
    except KeyboardInterrupt:
        pass
    finally:
        pixels.fill((0, 0, 0))
        pixels.show()
