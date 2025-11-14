from fingerprint_round import RoundFingerprint
import time

fp = RoundFingerprint()

print("Turning LED on...")
fp.led_on()
time.sleep(0.2)

print("Entering capture mode...")
fp.enter_capture_mode()

print("Place finger...")
while not fp.get_image():
    time.sleep(0.05)

print("Image 1 OK")
fp.image_to_char(1)

print("Remove finger...")
time.sleep(1)

print("Place same finger again...")
while not fp.get_image():
    time.sleep(0.05)

print("Image 2 OK")
fp.image_to_char(2)

print("Creating model...")
if fp.create_model():
    print("Model OK!")
else:
    print("Model failed.")
    exit()

slot = 5
print("Storing model...")
if fp.store_model(slot):
    print("Stored!")
else:
    print("Store failed!")

print("Turning LED off...")
fp.led_off()
