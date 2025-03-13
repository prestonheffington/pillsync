# PillSync Project

## Project Overview
PillSync is a Raspberry Pi-based local server designed for medication scheduling and dispensing. The system allows users to create, store, and manage medication schedules through a web-based UI. The Flask server acts as the central hub, handling authentication, scheduling, and peripheral control (e.g., stepper motor for dispensing and fingerprint verification for authentication).

## Repository Structure
```
PillSync/
│-- app.py                # Main Flask application
│-- requirements.txt      # Dependencies for the project
│-- config.json           # Stores user credentials (temporary solution)
│-- database/
│   ├── pillsync.db       # SQLite database storing user & prescription data
│-- templates/
│   ├── index.html        # Main UI page
│   ├── login.html        # Login page
│-- static/
│   ├── style.css         # CSS for UI design
│-- functions/
│   ├── LEDtest.py        # Test function for LED control
│   ├── dispense.py       # Medication dispensing logic
│-- data/
│   ├── user_data.json    # User and prescription data (if applicable)
│-- scripts/
│   ├── setup.sh          # Script for initial setup
│-- README.md             # Project documentation
```

## Installation & Setup
1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/pillsync.git
   cd pillsync
   ```

2. **Install Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Run the Flask Server**
   ```bash
   python3 app.py
   ```
   Access the UI by entering `http://pillsync.local` in a web browser.

## Database Information
- The SQLite database (`pillsync.db`) stores:
  - **User Data:** Name, User ID (auto-generated), Fingerprint data, Birthdate
  - **Prescription Data:** Name, Amount (in days), Frequency, Refill Date
- Future enhancements include secure authentication and multi-user support.

## Development Guidelines
- Maintain the existing directory structure.
- Store new features in appropriately named files within the `functions/` or `templates/` directories.
- Ensure all dependencies are added to `requirements.txt`.
- Document major changes in the `README.md` or a dedicated `CHANGELOG.md`.
- Code should follow Python best practices and be well-commented for team collaboration.

## Future Development
- Implement persistent login functionality.
- Improve UI design and accessibility.
- Integrate notifications and alerts.
- Expand peripheral device integration.

For any questions, please coordinate via the project's communication channel.

---
**Maintainers:** PillSync Development Team

Project PillSync - Medication Scheduling Web Interface

Description:
This project is a web-based local server UI prototype designed to help manage medication schedules.
It allows users to input prescription details, view schedules, and track when medication refills are needed based on a 30-day supply.

Features:
- View existing medication schedules.
- Add new medication details and set start dates.
- Calculate refill date based on a 30-day supply.
- User-friendly UI accessible via 'pillsync.local' on local network.

Requirements:
- Raspberry Pi (or other Linux-based system)
- Flask (Python web framework)
- Python 3
- Network access to reach 'pillsync.local'

Installation:
1. Install Python 3 and pip (if not already installed).
2. Install Flask via `sudo apt install python3-flask` or `pip3 install flask`.
3. Clone or download this repository to your Raspberry Pi.
4. Navigate to the project directory and run the Flask app:
   python3 app.py
5. Access the UI by entering 'pillsync.local:5000' in a web browser.

Usage:
- Go to the home page to view existing medication schedules.
- Use the form to add new prescriptions and view refill dates.

License:
This project is open-source. Feel free to contribute or modify as needed.

Instalation Guide and Requirements:
After cloning the repository onto your device, navigate to the pillsync folder and run
the folloing command:

pip3 install -r requirements.txt

This will install all required dependencies and packages used so far. 

