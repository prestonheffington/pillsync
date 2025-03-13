# import necessary libraries
import RPi.GPIO as GPIO
import time

# set up
LED_PIN = 18

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN,GPIO.OUT)

# callable function
def flash_led():
	GPIO.output(LED_PIN,GPIO.HIGH)
	time.sleep(1)
	GPIO.output(18,GPIO.LOW)
	return "LED flashed"

if __name__ == "__main__":
    flash_led()
    GPIO.cleanup()
