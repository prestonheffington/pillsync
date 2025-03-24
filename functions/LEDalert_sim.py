# Import necessary libraries
import RPi.GPIO as GPIO
import time

# Set up
LED_PIN = 17  # Use pin 17 as requested

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN, GPIO.OUT)

# SOS pattern function
def sos_signal():
    for _ in range(2):  # Run the SOS sequence twice
        # Three short blinks (S)
        for _ in range(3):
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.2)  # Short blink
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.2)

        # Three long blinks (O)
        for _ in range(3):
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.6)  # Long blink
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.2)

        # Three short blinks (S)
        for _ in range(3):
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.2)  # Short blink
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(0.2)

        time.sleep(2)  # Pause before repeating the sequence

if __name__ == "__main__":
    sos_signal()
    GPIO.cleanup()  # Ensure GPIO pins are reset after execution
