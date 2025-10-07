#!/usr/bin/env python3
"""
app_sim_test.py
Runs all simulation modules in sequence with 30-second intervals.

Sequence:
1. LEDalert_sim.py  (NeoPixel alert simulation)
2. buzzer_sim.py    (buzzer SOS test)
3. stepper_sim.py   (motor test sequence)

Modules are located in pillsync/functions/.
"""

import time
import importlib
import sys
from pathlib import Path

# Ensure the functions directory is importable
BASE_DIR = Path(__file__).resolve().parent
FUNCTIONS_DIR = BASE_DIR / "functions"
if str(FUNCTIONS_DIR) not in sys.path:
    sys.path.append(str(FUNCTIONS_DIR))

# Ordered list of module names (without .py extension)
MODULES = ["LEDalert_sim", "buzzer_sim", "stepper_sim"]
PAUSE_BETWEEN = 30  # seconds between tests

def run_module(mod_name):
    print(f"\n=== Running {mod_name}.py ===")
    try:
        module = importlib.import_module(mod_name)
        if hasattr(module, "main"):
            module.main()  # preferred explicit entry point
        else:
            # If script executes on import
            print(f"(No main() found — executed on import.)")
        print(f"=== Finished {mod_name}.py ===\n")
    except Exception as e:
        print(f"❌ Error running {mod_name}: {e}")

def main():
    print("🚀 Starting PillSync simulation test sequence...")
    for i, mod_name in enumerate(MODULES):
        run_module(mod_name)
        if i < len(MODULES) - 1:
            print(f"⏳ Waiting {PAUSE_BETWEEN} seconds before next test...\n")
            time.sleep(PAUSE_BETWEEN)
    print("✅ All simulation tests complete.")

if __name__ == "__main__":
    main()
