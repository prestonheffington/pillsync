from flask import Flask, render_template, request, redirect, url_for, session, g
import json
import os
import hashlib
import time
import sqlite3
import subprocess
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"
SESSION_TIMEOUT = 900  # Auto logout after 15 minutes of inactivity

# External database for user/meds data
DATABASE = "data/pillsync.db"

# Temporary storage instead of a database
CREDENTIALS_FILE = "data/credentials.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# 🔹 Database Connection Function
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Allows dictionary-like access to rows
    return db


def hash_password(password):
    """Hash a password using MD5 to match the stored format."""
    return hashlib.md5(password.encode()).hexdigest()


def load_credentials():
    """Load username and hashed password from the JSON file."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as file:
            return json.load(file)
    return {"username": "admin", "password": hash_password("password")}  # Default login


def save_credentials(username, password):
    """Save new credentials to JSON file."""
    with open(CREDENTIALS_FILE, "w") as file:
        json.dump({"username": username, "password": hash_password(password)}, file)


@app.before_request
def check_session_timeout():
    """Check if the session has expired due to inactivity."""
    if "user" in session:
        last_active = session.get("last_active", time.time())
        if time.time() - last_active > SESSION_TIMEOUT:
            session.pop("user", None)      # Logout the user
            session.pop("user_id", None)   # Also drop user_id
            return redirect(url_for("login"))
        session["last_active"] = time.time()  # Update activity timestamp


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def check_medication_schedule():
    print("🔄 Background alert system started...")

    with app.app_context():  # Ensures Flask context for DB access
        while True:
            try:
                now = datetime.now().strftime("%H:%M")  # Current time
                now_dt = datetime.strptime(now, "%H:%M")  # Convert to datetime
                print(f"⏳ Checking for scheduled medications at {now}")

                # Open a database connection
                db = sqlite3.connect("data/pillsync.db")
                db.row_factory = sqlite3.Row  # Allows dictionary-like row access

                medications = db.execute(
                    "SELECT prescription_id, name, time_of_day FROM prescriptions WHERE status='Active'"
                ).fetchall()

                triggered = False  # Track if any alert should trigger

                for med in medications:
                    med_time_dt = datetime.strptime(med["time_of_day"], "%H:%M")  # Convert DB time
                    time_difference = abs((now_dt - med_time_dt).total_seconds() / 60)

                    print(f"🧐 Checking medication: {med['name']} scheduled for {med['time_of_day']} (Time difference: {time_difference} minutes)")

                    if time_difference <= 15:
                        print(f"✅ Triggering alert for {med['name']} at {now}")

                        # Run alert scripts
                        subprocess.run(["python3", "functions/buzzer_sim.py"])
                        subprocess.run(["python3", "/home/pneil/pillsync/functions/buzzer_sim.py"], check=True)
                        triggered = True

                        # 🔹 Mark the medication as "Dispensed" so it does not trigger again
                        db.execute(
                            "UPDATE prescriptions SET status='Dispensed', last_dispensed=? WHERE prescription_id=?",
                            (now, med["prescription_id"])
                        )
                        db.commit()

                if not triggered:
                    print("❌ No medications matched the time window.")

                db.close()  # Close database connection
                time.sleep(60)  # Check every 60 seconds

            except Exception as e:
                print(f"⚠ ERROR in background thread: {e}")
                time.sleep(10)  # Prevent the thread from dying immediately


# Start the alert thread
alert_thread = threading.Thread(target=check_medication_schedule, daemon=True)
alert_thread.start()


@app.route("/", methods=["GET", "POST"])
def login():
    credentials = load_credentials()

    # Already logged in? go to dashboard
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        hashed_input_password = hash_password(password)

        print(f"DEBUG: Entered Username: {username}")
        print(f"DEBUG: Entered Password (hashed): {hashed_input_password}")
        print(f"DEBUG: Stored Username: {credentials['username']}")
        print(f"DEBUG: Stored Password: {credentials['password']}")

        if username == credentials["username"] and hashed_input_password == credentials["password"]:
            print("DEBUG: Login successful!")
            session["user"] = username

            # Fetch or create a DB user row and store user_id in session
            db = get_db()

            # Try to find by name (since users.name exists; there's no 'username' column)
            user = db.execute(
                "SELECT user_id FROM users WHERE name = ?",
                (username,)
            ).fetchone()

            if user is None:
                # Create a minimal user record; adjust birthdate default if you like
                db.execute(
                    "INSERT INTO users (name, birthdate) VALUES (?, ?)",
                    (username, "1990-01-01")
                )
                db.commit()
                user = db.execute(
                    "SELECT user_id FROM users WHERE name = ?",
                    (username,)
                ).fetchone()

            session["user_id"] = user["user_id"]

            # Keep your default-credentials redirect
            if username == "admin" and hashed_input_password == hash_password("password"):
                print("DEBUG: Default credentials detected, redirecting to update page.")
                return redirect(url_for("update_credentials"))

            return redirect(url_for("dashboard"))
        else:
            print("DEBUG: Invalid login attempt")
            return "Invalid credentials", 401

    return render_template("login.html")


@app.route("/update_credentials", methods=["GET", "POST"])
def update_credentials():
    """Force the user to update credentials if using default login."""
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_username = request.form.get("username")
        new_password = request.form.get("password")

        # Update stored credentials (JSON file)
        save_credentials(new_username, new_password)

        # 🔹 NEW: also update the user's name in the database
        db = get_db()
        db.execute(
            "UPDATE users SET name = ? WHERE user_id = ?",
            (new_username, session["user_id"])
        )
        db.commit()

        # Keep user logged in under the new name
        session["user"] = new_username
        print("DEBUG: Credentials updated successfully!")

        return redirect(url_for("dashboard"))

    return render_template("update_credentials.html")


@app.route("/logout")
def logout():
    """Manually log out the user."""
    session.pop("user", None)
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/users")
def get_users():
    db = get_db()
    cursor = db.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template("users.html", users=users)


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()

    # Fetch the logged-in user's name from the database
    user = db.execute("SELECT name FROM users WHERE user_id = ?", (session["user"],)).fetchone()

    # Fetch upcoming medications from the prescriptions table
    prescriptions = db.execute("SELECT name, dosage, time_of_day FROM prescriptions WHERE status='Active'").fetchall()

    return render_template("dashboard.html", user_name=user["name"] if user else "User", prescriptions=prescriptions)


@app.route("/prescriptions")
def get_prescriptions():
    db = get_db()
    cursor = db.execute("SELECT * FROM prescriptions")
    prescriptions = cursor.fetchall()
    return render_template("prescriptions.html", prescriptions=prescriptions)


@app.route("/delete_prescription/<int:prescription_id>", methods=["POST"])
def delete_prescription(prescription_id):
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    db.execute("DELETE FROM prescriptions WHERE prescription_id = ?", (prescription_id,))
    db.commit()

    return {"success": True}


@app.route("/prescription_form")
def prescription_form():
    """Render the prescription entry form."""
    return render_template("prescription_form.html")


@app.route("/add_prescription", methods=["POST"])
def add_prescription():
    """Handle form submission and add prescription to database."""
    db = get_db()
    user_id = 1  # Placeholder for now (future: assign dynamically)
    name = request.form["name"]
    amount = request.form["amount"]
    frequency = request.form["frequency"]
    refill_date = request.form["refill_date"]
    dosage = request.form.get("dosage", "")
    time_of_day = request.form.get("time_of_day", "")

    db.execute("""
        INSERT INTO prescriptions (user_id, name, amount, frequency, refill_date, dosage, time_of_day, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')
    """, (user_id, name, amount, frequency, refill_date, dosage, time_of_day))
    db.commit()

    return redirect(url_for("get_prescriptions"))


@app.route("/dispense", methods=["POST"])
def dispense():
    if "user" not in session:
        return {"success": False, "error": "Unauthorized"}, 401

    try:
        result = subprocess.run(["python3", "functions/servermotor_sim.py"], check=True, capture_output=True, text=True)
        print("DEBUG: Dispense Output ->", result.stdout)  # Log output
        return {"success": True, "message": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        print("ERROR: Dispense failed ->", e.stderr)  # Log error
        return {"success": False, "error": "Failed to dispense"}


if __name__ == "__main__":
    print("🚀 Starting PillSync server...")

    # Prevent multiple threads from starting
    if not any(t.name == "MedicationScheduler" for t in threading.enumerate()):
        alert_thread = threading.Thread(target=check_medication_schedule, daemon=True, name="MedicationScheduler")
        alert_thread.start()
        print("🔄 Background thread for medication alerts started.")

    app.run(host="0.0.0.0", port=5000, debug=False)  # Disable auto-reload to prevent duplicate threads
