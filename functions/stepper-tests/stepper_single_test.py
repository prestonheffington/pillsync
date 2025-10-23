#!/usr/bin/env python3
"""
Stepper single-motor test (28BYJ-48 + ULN2003)
Pins (BCM): IN1=24, IN2=25, IN3=8 (CE0), IN4=7 (CE1)

Usage examples:
  python3 stepper_single_test.py --steps 1024        # ~quarter turn (roughly)
  python3 stepper_single_test.py --steps 2048 --dir ccw
  python3 stepper_single_test.py --mode wave --delay 0.004

Tip: If it chatters or stalls, increase --delay (slower), e.g. 0.006–0.010.
"""

import argparse
import sys
import time
import RPi.GPIO as GPIO

# ---- pin map (BCM) ----
IN1 = 24
IN2 = 25
IN3 = 8   # CE0
IN4 = 7   # CE1
PINS = [IN1, IN2, IN3, IN4]

# Sequences
HALFSTEP = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1],
]

WAVE = [
    [1,0,0,0],
    [0,1,0,0],
    [0,0,1,0],
    [0,0,0,1],
]

FULLSTEP = [
    [1,1,0,0],
    [0,1,1,0],
    [0,0,1,1],
    [1,0,0,1],
]

MODES = {
    "half": HALFSTEP,   # smoothest, most torque (effective), more steps/rev
    "wave": WAVE,       # lower torque, fewer steps/rev
    "full": FULLSTEP,   # more torque than wave, fewer steps than half
}

def setup():
    GPIO.setmode(GPIO.BCM)
    for p in PINS:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

def energize(pattern):
    for pin, val in zip(PINS, pattern):
        GPIO.output(pin, GPIO.HIGH if val else GPIO.LOW)

def deenergize():
    for p in PINS:
        GPIO.output(p, GPIO.LOW)

def step_motor(steps, delay, mode, direction):
    seq = MODES[mode]
    seq_len = len(seq)
    index = 0 if direction == "cw" else seq_len - 1
    step_count = 0

    try:
        while step_count < steps:
            energize(seq[index])
            time.sleep(delay)
            # advance or reverse
            if direction == "cw":
                index = (index + 1) % seq_len
            else:
                index = (index - 1) % seq_len
            step_count += 1
    finally:
        deenergize()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1024,
                    help="Number of sequence steps (not shaft degrees).")
    ap.add_argument("--delay", type=float, default=0.003,
                    help="Seconds between sequence steps (higher = slower).")
    ap.add_argument("--mode", choices=list(MODES.keys()), default="half",
                    help="Drive mode: half, full, or wave.")
    ap.add_argument("--dir", dest="direction", choices=["cw","ccw"], default="cw",
                    help="Rotation direction.")
    args = ap.parse_args()

    print(f"Pins (BCM): {PINS} | mode={args.mode} | dir={args.direction} | "
          f"steps={args.steps} | delay={args.delay}s")

    try:
        setup()
        step_motor(args.steps, args.delay, args.mode, args.direction)
        print("Done.")
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
