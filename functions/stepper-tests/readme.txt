# Stepper Test Utilities

Bench validation scripts for MCP23017 → ULN2003 → 28BYJ-48 chain.

## Configuration
- MCP23017 address: `0x20`
- Motor 1: GPA0–GPA3
- Motor 2: GPB0–GPB3
- Shared 5 V (logic) and common GND with Pi
- External PSU recommended for multi-motor load

## Run
```bash
python3 stepper_dual_seq_test.py
