PillSyncOS

Smart Medication Management System for Raspberry Pi

PillSyncOS is a Raspberry Pi–based medication management platform that integrates a secure web interface with hardware components such as stepper motors, LED indicators, piezo alarms, and optional fingerprint authentication. The system allows users to schedule, dispense, and track medication doses while providing a modular, hardware-driven backend.

Features
Secure Access

First-time credential update workflow

Session-based authentication

Automatic logout after inactivity

Dashboard

Dynamic welcome message

User list

Manual dispense controls

Upcoming medication list

Prescription Management

Add, edit, and delete prescriptions

Time-based scheduling

Refill tracking

User association for multi-patient use

Hardware Integration

Stepper motor control via MCP23017 expanders

NeoPixel alert lighting

Piezo alarm notifications

Fingerprint authentication support (planned)

Complete simulation layer for development environments

Background Services

Independent scheduler thread

Triggers alerts and handles timed dispensing

Logs dispense outcomes

Project Structure
pillsync/
├── app.py                   # Main Flask application
├── core.py                  # Core logic (dispense workflow, scheduling engine)
├── config.py                # System configuration flags
│
├── data/
│   ├── pillsync.db          # SQLite database
│   ├── pillsync_backup.db   # Automatic backup
│   ├── credentials.json     # Stored hashed credentials
│   └── schema.sql           # Database schema
│
├── functions/
│   ├── motor_array.py       # Stepper motor driver (auto I2C detection)
│   ├── motor_homing.py      # Homing logic (future)
│   ├── fingerprint.py       # Hardware fingerprint wrapper
│   ├── neopixel_alarm.py    # NeoPixel alert control
│   ├── piezo_alarm.py       # Piezo tone generator
│   ├── notification.py      # Internal logging and notifications
│   ├── ui.py                # UI helpers
│   └── sim/                 # Simulation modules
│       ├── buzzer_sim.py
│       ├── LEDalert_sim.py
│       ├── servermotor_sim.py
│       └── stepper_sim.py
│
├── templates/               # Jinja2 templates
│   ├── login.html
│   ├── update_credentials.html
│   ├── dashboard.html
│   ├── prescriptions.html
│   ├── prescription_form.html
│   ├── users.html
│   └── demo.html
│
├── static/
│   └── background.png
│
├── requirements.txt
├── liscense.txt
└── README.md

Installation
1. Clone the repository
git clone https://github.com/prestonheffington/pillsync.git
cd pillsync

2. Install dependencies
sudo pip3 install -r requirements.txt --break-system-packages

3. Enable I2C (required for hardware operation)
sudo raspi-config


Interface Options → I2C → Enable

4. Run the application
python3 app.py


Access the web interface via:

http://<raspberry_pi_ip>:5000

Default Credentials

Username: admin
Password: password

The system will require a credential update on first login.

Dispense Workflow Overview

The dispensing process is coordinated through core.py:

A scheduled time triggers, or the user initiates a manual dispense.

Fingerprint authentication is applied if enabled.

MotorArray sends coil patterns to the MCP23017 expander.

Stepper motors rotate the appropriate number of steps.

Logs are recorded in the database.

NeoPixel and/or piezo alerts are triggered when appropriate.

If hardware is unavailable, simulation modules provide safe fallback behavior.

Hardware Support
Supported Devices

MCP23017 GPIO expanders

28BYJ-48 stepper motors with ULN2003 drivers

NeoPixel LED strips/sticks

UART fingerprint sensors

Piezo buzzers

Physical dispense buttons

Auto-Detection

motor_array.py automatically scans for expanders at addresses 0x20 and 0x21, enabling only motors mapped to detected hardware.

Development Notes

All authentication credentials are hashed.

The scheduler runs in a background thread independent of the Flask server.

SQLite is used for local persistence and supports hot-swap backups.

The system is structured to allow hardware modules to be added, removed, or simulated without breaking core functionality.

Roadmap

Full fingerprint-based dispense authorization

Remote access via VPN/tunnel solutions

Refill notifications via SMS or email

Logging dashboard for system events

Multi-profile support for larger installations

Optional MQTT or BLE connectivity

Contributing

Fork the repository

Create a feature branch

Submit a pull request to the main branch

Ensure hardware-related changes are tested on device

License

This project is licensed under the MIT License.
See liscense.txt for licensing details.