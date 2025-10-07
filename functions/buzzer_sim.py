# sos_buzzer.py
# Makes a piezo element on GPIO 4 buzz in an SOS (... --- ...) pattern.

import RPi.GPIO as GPIO
import time

BUZZER_PIN = 4  # BCM numbering

# Morse timing constants (seconds)
DOT = 0.2      # short beep
DASH = DOT * 3 # long beep
INTRA = DOT    # between elements in one letter
LETTER_GAP = DOT * 3
WORD_GAP = DOT * 7

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

def buzz(duration):
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    time.sleep(INTRA)

def sos_buzz():
    try:
        # S = ...
        for _ in range(3):
            buzz(DOT)
        time.sleep(LETTER_GAP)

        # O = ---
        for _ in range(3):
            buzz(DASH)
        time.sleep(LETTER_GAP)

        # S = ...
        for _ in range(3):
            buzz(DOT)
        time.sleep(WORD_GAP)

        return "SOS pattern played"

    finally:
        GPIO.output(BUZZER_PIN, GPIO.LOW)

if __name__ == "__main__":
    sos_buzz()
    GPIO.cleanup()

