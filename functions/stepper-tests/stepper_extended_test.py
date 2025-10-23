#!/usr/bin/env python3
"""
Stepper Extended Test (28BYJ-48 + ULN2003)
Pins (BCM): IN1=24, IN2=25, IN3=8 (CE0), IN4=7 (CE1)

Modes:
  longrun   -> run for N revolutions or N steps (default: 5 revs, half-step)
  wobble    -> small back-and-forth cycles to check backlash/rocking
  smoke     -> quick coil walk to verify channels and power
  slowfast  -> sweep delay from slow->fast->slow to observe stall limits

Live controls (read from stdin during run):
  p = pause/resume   q = quit now   s = stop at next safe point

Examples:
  python3 stepper_extended_test.py longrun --revs 5
  python3 stepper_extended_test.py longrun --steps 4096 --dir ccw
  python3 stepper_extended_test.py wobble --amplitude 64 --cycles 20
  python3 stepper_extended_test.py slowfast --slow 0.008 --fast 0.002 --cycles 3
  python3 stepper_extended_test.py smoke
"""

import sys
import time
import argparse
import threading
import queue
import RPi.GPIO as GPIO

# ---- pin map (BCM) ----
IN1 = 24
IN2 = 25
IN3 = 8   # CE0
IN4 = 7   # CE1
PINS = [IN1, IN2, IN3, IN4]

# ---- step sequences ----
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
FULLSTEP = [
    [1,1,0,0],
    [0,1,1,0],
    [0,0,1,1],
    [1,0,0,1],
]
WAVE = [
    [1,0,0,0],
    [0,1,0,0],
    [0,0,1,0],
    [0,0,0,1],
]

MODES = {"half": HALFSTEP, "full": FULLSTEP, "wave": WAVE}

# For 28BYJ-48 gearbox:
HALFSTEPS_PER_REV = 4096   # ~exact enough for testing
FULLSTEPS_PER_REV = 2038

class Control:
    """Thread-safe control flags via stdin (p pause/resume, q quit, s stop)."""
    def __init__(self):
        self._paused = threading.Event()
        self._paused.clear()
        self._quit_now = threading.Event()
        self._stop_req = threading.Event()
        self._msgq = queue.Queue()

    @property
    def paused(self):
        return self._paused.is_set()

    def toggle_pause(self):
        if self._paused.is_set():
            self._paused.clear()
            self._msgq.put("RESUME")
        else:
            self._paused.set()
            self._msgq.put("PAUSE")

    def wait_if_paused(self):
        while self._paused.is_set() and not self._quit_now.is_set():
            time.sleep(0.05)

    def request_quit(self):
        self._quit_now.set()
        self._msgq.put("QUIT")

    def request_stop(self):
        self._stop_req.set()
        self._msgq.put("STOP")

    def should_quit(self):
        return self._quit_now.is_set()

    def should_stop(self):
        return self._stop_req.is_set()

    def drain_msgs(self):
        msgs = []
        try:
            while True:
                msgs.append(self._msgq.get_nowait())
        except queue.Empty:
            pass
        return msgs

def stdin_listener(ctrl: Control):
    try:
        print("[controls] press: p=pause/resume  s=stop  q=quit")
        for line in sys.stdin:
            key = line.strip().lower()
            if key == 'p':
                ctrl.toggle_pause()
            elif key == 's':
                ctrl.request_stop()
            elif key == 'q':
                ctrl.request_quit()
                break
    except Exception:
        pass

def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    for p in PINS:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

def energize(pattern):
    for pin, val in zip(PINS, pattern):
        GPIO.output(pin, GPIO.HIGH if val else GPIO.LOW)

def deenergize():
    for p in PINS:
        GPIO.output(p, GPIO.LOW)

def step_stream(total_steps, delay, seq, direction, ctrl: Control):
    """Run a fixed number of sequence steps with controls."""
    idx = 0 if direction == "cw" else len(seq) - 1
    for i in range(total_steps):
        if ctrl.should_quit():
            break
        if ctrl.should_stop():
            # stop at next safe point (deenergize between steps)
            break
        ctrl.wait_if_paused()

        energize(seq[idx])
        time.sleep(delay)
        deenergize()  # cooler, slightly less torque but safer for long tests

        if direction == "cw":
            idx = (idx + 1) % len(seq)
        else:
            idx = (idx - 1) % len(seq)

def step_continuous(duration_s, delay, seq, direction, ctrl: Control):
    """Run continuously for duration (seconds) honoring controls."""
    idx = 0 if direction == "cw" else len(seq) - 1
    t0 = time.time()
    while (time.time() - t0) < duration_s:
        if ctrl.should_quit() or ctrl.should_stop():
            break
        ctrl.wait_if_paused()

        energize(seq[idx])
        time.sleep(delay)
        deenergize()

        if direction == "cw":
            idx = (idx + 1) % len(seq)
        else:
            idx = (idx - 1) % len(seq)

def longrun(args, ctrl):
    seq = MODES[args.mode]
    if args.steps is not None:
        total = int(args.steps)
        print(f"[longrun] steps={total} delay={args.delay}s mode={args.mode} dir={args.direction}")
        step_stream(total, args.delay, seq, args.direction, ctrl)
    else:
        # compute steps from revs
        if args.mode == "half":
            steps_per_rev = HALFSTEPS_PER_REV
        else:
            steps_per_rev = FULLSTEPS_PER_REV if args.mode == "full" else 4 * FULLSTEPS_PER_REV // 4
            # wave uses 4 states too; keep its rev metric close to full-step
        total = int(args.revs * steps_per_rev)
        print(f"[longrun] revs={args.revs} (~{total} steps) delay={args.delay}s mode={args.mode} dir={args.direction}")
        step_stream(total, args.delay, seq, args.direction, ctrl)

def wobble(args, ctrl):
    """Rock back/forth by small amplitude to expose backlash & wiring order."""
    seq = MODES[args.mode]
    amp = int(args.amplitude)
    cycles = int(args.cycles)
    print(f"[wobble] amplitude={amp} steps, cycles={cycles}, delay={args.delay}s, mode={args.mode}")
    for c in range(cycles):
        if ctrl.should_quit() or ctrl.should_stop():
            break
        # forward amp
        step_stream(amp, args.delay, seq, "cw", ctrl)
        # brief settle
        time.sleep(args.settle)
        # backward amp
        step_stream(amp, args.delay, seq, "ccw", ctrl)
        time.sleep(args.settle)

def smoke(args, ctrl):
    """Quick coil walk to verify each channel drives correctly."""
    print("[smoke] coil walk on IN1..IN4, then a short 32-step spin.")
    # one-hot pulses
    onehots = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
    for i, pat in enumerate(onehots, start=1):
        print(f"  coil {i} ON")
        energize(pat); time.sleep(0.15); deenergize(); time.sleep(0.1)
    # short spin
    step_stream(32, 0.006, HALFSTEP, "cw", ctrl)
    print("[smoke] done.")

def slowfast(args, ctrl):
    """Ramp delay slow->fast->slow for several cycles (watch for stalls)."""
    seq = MODES[args.mode]
    slow = float(args.slow)
    fast = float(args.fast)
    steps_each = int(args.steps_each)
    cycles = int(args.cycles)
    print(f"[slowfast] slow={slow}s ➜ fast={fast}s, steps_each={steps_each}, cycles={cycles}, mode={args.mode}")
    if fast <= 0 or slow <= 0 or fast > slow:
        print("ERROR: require 0 < fast < slow", file=sys.stderr)
        return

    # create a monotonic list of delays
    def delay_sweep(n=20):
        # linear in delay-domain (simple & fine for this motor)
        up = [slow - (slow-fast)*i/(n-1) for i in range(n)]
        down = up[::-1]
        return up + down[1:-1]

    sweep = delay_sweep(24)
    for cy in range(cycles):
        if ctrl.should_quit() or ctrl.should_stop():
            break
        print(f"  cycle {cy+1}/{cycles}")
        for d in sweep:
            if ctrl.should_quit() or ctrl.should_stop():
                break
            step_stream(steps_each, d, seq, args.direction, ctrl)

def run_with_controls(fn, *fn_args):
    ctrl = Control()
    listener = threading.Thread(target=stdin_listener, args=(ctrl,), daemon=True)
    listener.start()
    try:
        gpio_setup()
        fn(*fn_args, ctrl)
    except KeyboardInterrupt:
        print("\n[ctrl] KeyboardInterrupt")
    finally:
        deenergize()
        GPIO.cleanup()
        # drain last control messages
        for m in ctrl.drain_msgs():
            print(f"[ctrl] {m}")

def build_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    common = dict(
        add_mode=True,
        add_dir=True,
        add_delay=True
    )

    def add_common(sp, **opts):
        if opts.get("add_mode", False):
            sp.add_argument("--mode", choices=list(MODES.keys()), default="half",
                            help="Drive mode sequence.")
        if opts.get("add_dir", False):
            sp.add_argument("--dir", dest="direction", choices=["cw","ccw"], default="cw",
                            help="Rotation direction.")
        if opts.get("add_delay", False):
            sp.add_argument("--delay", type=float, default=0.003,
                            help="Seconds between steps (higher=slower).")

    sp = sub.add_parser("longrun", help="Run for N revs or steps")
    add_common(sp, **common)
    group = sp.add_mutually_exclusive_group()
    group.add_argument("--revs", type=float, default=5.0, help="Revolutions (ignored if --steps given).")
    group.add_argument("--steps", type=int, help="Exact sequence steps.")
    sp.set_defaults(handler=longrun)

    sp = sub.add_parser("wobble", help="Back-and-forth small amplitude")
    add_common(sp, **common)
    sp.add_argument("--amplitude", type=int, default=64, help="Steps forward/back each wobble.")
    sp.add_argument("--cycles", type=int, default=30, help="Number of wobble cycles.")
    sp.add_argument("--settle", type=float, default=0.05, help="Pause between direction changes.")
    sp.set_defaults(handler=wobble)

    sp = sub.add_parser("smoke", help="Coil walk + tiny spin")
    sp.set_defaults(handler=smoke)

    sp = sub.add_parser("slowfast", help="Speed sweep slow->fast->slow")
    add_common(sp, **common)
    sp.add_argument("--slow", type=float, default=0.008, help="Slow delay (seconds).")
    sp.add_argument("--fast", type=float, default=0.002, help="Fast delay (seconds).")
    sp.add_argument("--steps-each", type=int, default=64, help="Steps per delay setting.")
    sp.add_argument("--cycles", type=int, default=2, help="Number of sweep cycles.")
    sp.set_defaults(handler=slowfast)

    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    print(f"Pins (BCM): {PINS}")
    run_with_controls(args.handler, args)

if __name__ == "__main__":
    main()
