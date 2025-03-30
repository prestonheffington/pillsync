# 💊 PillSync

PillSync is a web-based smart medication management system designed to run on a Raspberry Pi. It provides a user-friendly interface to schedule, dispense, and track medication doses while integrating with hardware peripherals like LEDs, buzzers, and fingerprint sensors.

---

## 🚀 Features

- Secure login system with credential setup on first use
- Session-based authentication with auto logout
- Dashboard with:
  - Dynamic welcome message
  - Upcoming medication list
  - Manual dispense button
- Prescription management:
  - Add, view, and delete prescriptions
  - Time-based scheduling support with dosage and refill tracking
- Simulated peripheral control (LEDs, buzzers, stepper motors)
- Background alert system for scheduled medication notifications
- Styled responsive interface with glass UI and background image

---

## 📁 Project Structure

pillsync/
├── app.py                   # Main Flask server
├── data/                    # Contains SQLite DB and credentials file
│   ├── pillsync.db
│   └── credentials.json
├── functions/               # Simulated hardware control scripts
│   ├── servermotor_sim.py
│   ├── buzzer_sim.py
│   └── LEDalert_sim.py
├── static/                  # Static assets (e.g., background.png)
│   └── background.png
├── templates/               # HTML templates (Flask Jinja2)
│   ├── login.html
│   ├── update_credentials.html
│   ├── dashboard.html
│   ├── prescriptions.html
│   └── prescription_form.html
├── requirements.txt         # Python dependencies
├── README.md                # Project overview and instructions
└── license.txt              # Project license

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/prestonheffington/pillsync.git
cd pillsync
```

### 2. Install Dependencies

```bash
sudo pip3 install -r requirements.txt --break-system-packages
```

### 3. Run the Server

```bash
python3 app.py
```

Then visit:

```
http://<your_pi_ip>:5000
```

Example:
```
http://192.168.1.50:5000
```

---

## 🔐 Default Credentials

- **Username:** `admin`
- **Password:** `password`

> You will be prompted to change these on first login.

---

## 🔧 Hardware Integration

This project supports GPIO peripherals such as:

- **LEDs** – Represent various alerts and actions.
- **Buzzers** – Audio alerts for scheduled doses.
- **Stepper motors** – Simulate or control medication dispensing.
- **Fingerprint sensor** (planned) – For secure identity verification before dispensing.

> For prototyping, LEDs are used to simulate all peripheral outputs.

---

## 💡 Development Notes

- All UI is dynamically updated based on database content.
- Routes and functions are modular to allow future hardware integration.
- Background tasks run in a thread to check medication schedules every minute.

---

## 🛡️ Planned Features

- Remote secure access via Tailscale or Cloudflare Tunnel
- Fingerprint-based dispense authorization
- Refill alerts via email/text
- Activity logs and usage analytics

---

## 🤝 Contribution

To contribute, fork the repo and submit a pull request. The current structure must be followed. All changes must be tested before merging into `main`.

---

## 📄 License

This project is licensed under the terms of the MIT License. See `license.txt` for details.

---

## 👨‍💻 Maintainer

**Preston Heffington**  
GitHub: [@prestonheffington](https://github.com/prestonheffington)
