from flask import Flask, render_template, request, redirect, url_for, session, g
from core import core
from functions.fingerprint_sensor import (
    enroll_fingerprint_at_location,
    delete_fingerprint_at_location,
)
import json
import os
import hashlib
import time
import sqlite3
import subprocess
import threading
from datetime import datetime

IDLE_LIMIT = 900  # 15 minutes (in seconds)

app = Flask(__name__)
app.secret_key = "your_secret_key"
SESSION_TIMEOUT = 900  # Auto logout after 15 minutes of inactivity
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,   # HTTP on LAN
    SESSION_COOKIE_HTTPONLY=True,
)

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
def enforce_session_timeout():
    if "user" not in session:
        return

    now = time.time()
    last = session.get("last_activity", now)
    idle = now - last

    if idle > IDLE_LIMIT:
        app.logger.info(f"[SESSION] Timeout: idle={idle:.1f}s > {IDLE_LIMIT}s. Logging out.")
        session.clear()
        return redirect(url_for("login"))

    session["last_activity"] = now



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
                # Current time as string and datetime
                now_str = datetime.now().strftime("%H:%M")
                now_dt = datetime.strptime(now_str, "%H:%M")
                print(f"⏳ Checking for scheduled medications at {now_str}")

                # Open a database connection
                db = sqlite3.connect("data/pillsync.db")
                db.row_factory = sqlite3.Row  # Allows dictionary-like row access

                # TODO: adjust status filter if your schema uses a different value
                medications = db.execute(
                    "SELECT prescription_id, name, time_of_day "
                    "FROM prescriptions "
                    "WHERE status = 'Active'"
                ).fetchall()

                triggered = False  # Track if any alert should trigger

                for med in medications:
                    med_time_str = med["time_of_day"]
                    med_time_dt = datetime.strptime(med_time_str, "%H:%M")
                    time_difference = abs((now_dt - med_time_dt).total_seconds() / 60)

                    print(
                        f"🧐 Checking medication: {med['name']} "
                        f"scheduled for {med_time_str} (Δ={time_difference:.1f} min)"
                    )

                    if time_difference <= 15:
                        print(f"✅ Triggering alert for {med['name']} at {now_str}")

                        # 🔔 Use core.py to run real alarms (piezo + neopixel)
                        core.trigger_alarms(duration=30.0)
                        triggered = True

                        # 🔹 Mark the medication as "Dispensed" so it does not trigger again
                        db.execute(
                            "UPDATE prescriptions "
                            "SET status = ?, last_dispensed = ? "
                            "WHERE prescription_id = ?",
                            ("Dispensed", datetime.now().isoformat(timespec="seconds"), med["prescription_id"]),
                        )
                        db.commit()

                if not triggered:
                    print("❌ No medications matched the time window.")

                db.close()  # Close database connection
                time.sleep(60)  # Check every 60 seconds

            except Exception as e:
                print(f"⚠ ERROR in background thread: {e}")
                time.sleep(10)  # Prevent the thread from dying immediately


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

"""@app.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    # only admin can edit
    if session.get("user") != 'admin':
        return "Unauthorized", 403

    db = get_db()
    if request.method == "POST":
        new_name = request.form["name"]
        new_birthdate = request.form["birthdate"]
        db.execute(
            "UPDATE users SET name = ?, birthdate = ? WHERE user_id = ?",
            (new_name, new_birthdate, user_id)
        )
        db.commit()
        return redirect(url_for("get_users"))

    user_to_edit = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return render_template("edit_user.html", user=user_to_edit)"""


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()

    # ✅ use session["user_id"], not session["user"]
    user = db.execute(
        "SELECT name FROM users WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()

    prescriptions = db.execute(
        "SELECT name, dosage, time_of_day FROM prescriptions WHERE status='Active' AND user_id = ?",
        (session["user_id"],)
    ).fetchall()

    return render_template(
        "dashboard.html",
        user_name=user["name"] if user else "User",
        prescriptions=prescriptions
    )


@app.route("/users")
def get_users():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    rows = db.execute("SELECT * FROM users ORDER BY user_id ASC;").fetchall()

    users = []
    for row in rows:
        users.append({
            "id": row["user_id"],
            "name": row["name"],
            "birthdate": row["birthdate"],
            "fingerprint": "Yes" if row["fingerprint_data"] else "No",
        })

    return render_template("users.html", users=users)


@app.route("/users/<int:user_id>/fingerprint/enroll", methods=["POST"])
def enroll_fingerprint(user_id):
    """
    Enroll a fingerprint for the given user.

    - Uses user_id as the fingerprint template location (slot).
      This assumes user_id <= 127 (sensor capacity).
    - On success, stores the slot in users.fingerprint_data.
    """
    if "user" not in session:
        return redirect(url_for("login"))

    # Map user_id to a sensor slot. For our 2-user demo this is safe.
    location = user_id
    if not (1 <= location <= 127):
        print(f"[ERROR] user_id {user_id} is out of valid fingerprint slot range (1–127).")
        return redirect(url_for("get_users"))

    print(f"[INFO] Enrolling fingerprint for user_id={user_id} at slot={location}...")

    success = False
    try:
        success = enroll_fingerprint_at_location(location)
    except Exception as e:
        print(f"[ERROR] enroll_fingerprint_at_location crashed for user {user_id}: {e}")

    db = get_db()

    if success:
        try:
            db.execute(
                "UPDATE users SET fingerprint_data = ? WHERE user_id = ?;",
                (location, user_id),
            )
            db.commit()
            print(f"[INFO] Stored fingerprint slot {location} in DB for user_id={user_id}")
        except Exception as e:
            print(f"[ERROR] Failed to update fingerprint_data in DB for user_id={user_id}: {e}")
    else:
        print(f"[WARN] Fingerprint enrollment failed for user_id={user_id}")

    return redirect(url_for("get_users"))


@app.route("/users/<int:user_id>/fingerprint/delete", methods=["POST"])
def delete_fingerprint(user_id):
    """
    Delete the fingerprint associated with a user.

    - Reads users.fingerprint_data as the sensor slot.
    - Deletes from the sensor and clears the DB field.
    """
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    row = db.execute(
        "SELECT fingerprint_data FROM users WHERE user_id = ?;",
        (user_id,),
    ).fetchone()

    if not row or row["fingerprint_data"] is None:
        print(f"[INFO] No fingerprint to delete for user_id={user_id}")
        return redirect(url_for("get_users"))

    location = int(row["fingerprint_data"])
    print(f"[INFO] Deleting fingerprint for user_id={user_id} from slot={location}...")

    success = False
    try:
        success = delete_fingerprint_at_location(location)
    except Exception as e:
        print(f"[ERROR] delete_fingerprint_at_location crashed for user {user_id}: {e}")

    if success:
        try:
            db.execute(
                "UPDATE users SET fingerprint_data = NULL WHERE user_id = ?;",
                (user_id,),
            )
            db.commit()
            print(f"[INFO] Cleared fingerprint_data in DB for user_id={user_id}")
        except Exception as e:
            print(f"[ERROR] Failed to clear fingerprint_data in DB for user_id={user_id}: {e}")
    else:
        print(f"[WARN] Fingerprint delete failed for user_id={user_id}")

    return redirect(url_for("get_users"))


@app.route("/users/add", methods=["POST"])
def add_user():
    if "user" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    birthdate = request.form.get("birthdate", "").strip()

    if not name or not birthdate:
        print("[ERROR] Missing required fields for new user")
        return redirect(url_for("get_users"))

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (name, birthdate) VALUES (?, ?);",
            (name, birthdate),
        )
        db.commit()
        print(f"[INFO] User added: {name}, {birthdate}")
    except Exception as e:
        print(f"[ERROR] add_user failed: {e}")

    return redirect(url_for("get_users"))


@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    try:
        db.execute("DELETE FROM users WHERE user_id = ?;", (user_id,))
        db.commit()
        print(f"[INFO] User deleted: {user_id}")
    except Exception as e:
        print(f"[ERROR] delete_user failed: {e}")

    return redirect(url_for("get_users"))


@app.route("/demo")
def demo():
    """
    Demo Day page.

    - Protected by normal app login (session["user"])
    - Will eventually expose:
        - Trigger alarms on command
        - Dispense on command (bypass fingerprint)
        - Home all motors
    """
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("demo.html")


@app.route("/debug_session")
def debug_session():
    # ONLY for debugging; remove later
    return {
        "has_user": "user" in session,
        "has_user_id": "user_id" in session,
        "user": session.get("user"),
        "user_id": session.get("user_id"),
        "last_active": session.get("last_active"),
    }, 200


@app.route("/prescriptions")
def get_prescriptions():
    db = get_db()

    # JSON feed (for device/screen client)
    if request.args.get("format") == "json":
        cursor = db.execute("SELECT * FROM prescriptions")
        prescriptions = cursor.fetchall()
        return [
            {
                "prescription_id": p["prescription_id"],
                "user_id": p["user_id"],
                "name": p["name"],
                "amount": p["amount"],
                "frequency": p["frequency"],
                "refill_date": p["refill_date"],
                "dosage": p["dosage"],
                "time_of_day": p["time_of_day"],
                "status": p["status"],
            }
            for p in prescriptions
        ]

    # Web page → login required
    if "user" not in session:
        return redirect(url_for("login"))

    # Optional user context from query string: /prescriptions?user_id=1
    selected_user_id = request.args.get("user_id", type=int)

    # Build SQL conditionally based on whether a user was selected
    sql = "SELECT * FROM prescriptions"
    params = []

    if selected_user_id is not None:
        sql += " WHERE user_id = ?"
        params.append(selected_user_id)

    cur = db.execute(sql, params)
    prescriptions = cur.fetchall()

    return render_template(
        "prescriptions.html",
        prescriptions=prescriptions,
        selected_user_id=selected_user_id,
    )


@app.route("/prescriptions/new", methods=["GET", "POST"])
def add_prescription():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        user_id = int(user_id) if user_id else None

        name = request.form.get("name")
        amount = request.form.get("amount")
        frequency = request.form.get("frequency")
        refill_date = request.form.get("refill_date")
        dosage = request.form.get("dosage")
        time_of_day = request.form.get("time_of_day")
        status = "Active"

        if not name or not amount or not frequency or not refill_date:
            print("[ERROR] Missing required fields in Add Prescription")
            return redirect(url_for("add_prescription", user_id=user_id))

        db.execute(
            """
            INSERT INTO prescriptions
                (user_id, name, amount, frequency, refill_date, dosage, time_of_day, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, amount, frequency, refill_date, dosage, time_of_day, status),
        )
        db.commit()

        if user_id:
            return redirect(url_for("get_prescriptions", user_id=user_id))
        return redirect(url_for("get_prescriptions"))

    # GET
    selected_user_id = request.args.get("user_id", type=int)
    return render_template("prescription_form.html", selected_user_id=selected_user_id)


@app.route("/prescriptions/<int:prescription_id>/delete", methods=["POST"])
def delete_prescription(prescription_id):
    if "user" not in session:
        return redirect(url_for("login"))

    selected_user_id = request.args.get("user_id", type=int)

    db = get_db()
    try:
        db.execute("DELETE FROM prescriptions WHERE prescription_id = ?;", (prescription_id,))
        db.commit()
    except Exception as e:
        print(f"[ERROR] delete_prescription failed: {e}")

    if selected_user_id:
        return redirect(url_for("get_prescriptions", user_id=selected_user_id))
    return redirect(url_for("get_prescriptions"))


@app.route("/prescription_form")
def prescription_form():
    if "user" not in session:
        return redirect(url_for("login"))
    db = get_db()
    users = db.execute("SELECT user_id, name FROM users WHERE name != ?", ('admin',)).fetchall()
    return render_template("prescription_form.html", users=users)


@app.route("/dispense", methods=["POST"])
def dispense():
    if "user" not in session:
        return {"success": False, "error": "Unauthorized"}, 401

    user_id = session.get("user_id")

    # Optional motor_id from JSON body, default to 1 for now
    payload = request.get_json(silent=True) or {}
    try:
        motor_id = int(payload.get("motor_id", 1))
    except (TypeError, ValueError):
        motor_id = 1

    try:
        result = core.dispense_slot(user_id=user_id, motor_id=motor_id)

        if result.get("success"):
            print(
                f"DEBUG: Dispense successful for user_id={user_id}, motor_id={motor_id}"
            )
            return {
                "success": True,
                "message": "Dispense completed successfully.",
            }, 200
        else:
            error_msg = result.get("error") or "Dispense failed at hardware level."
            print(f"ERROR: Dispense failed -> {error_msg}")
            return {
                "success": False,
                "error": error_msg,
            }, 500

    except Exception as e:
        print("ERROR: /dispense route crashed ->", e)
        return {
            "success": False,
            "error": f"Exception occurred: {e}",
        }, 500

@app.route("/home_motors", methods=["POST"])
def home_motors():
    """
    Home all motors (7 x 320 steps in reverse) and reset call counters.

    This will eventually be triggered by a 'Reset / Home All' button on
    the dashboard or Demo Day page.
    """
    if "user" not in session:
        return {"success": False, "error": "Unauthorized"}, 401

    try:
        results = core.home_all_motors(direction=-1)

        # results is expected to be a dict like {1: True, 2: True, ...}
        print(f"DEBUG: Home all motors results: {results}")

        if all(results.values()):
            return {
                "success": True,
                "message": "All motors homed successfully.",
                "results": results,
            }, 200
        else:
            return {
                "success": False,
                "error": "One or more motors failed to home.",
                "results": results,
            }, 500

    except Exception as e:
        print("ERROR: /home_motors route crashed ->", e)
        return {
            "success": False,
            "error": f"Exception occurred: {e}",
        }, 500

@app.route("/demo_alarms", methods=["POST"])
def demo_alarms():
    """
    Demo-only endpoint to trigger alarms on command.
    Uses core.trigger_alarms and bypasses fingerprint.
    """
    if "user" not in session:
        return {"success": False, "error": "Unauthorized"}, 401

    try:
        core.trigger_alarms(duration=30.0)
        return {
            "success": True,
            "message": "Demo alarms triggered successfully.",
        }, 200

    except Exception as e:
        print("ERROR: /demo_alarms route crashed ->", e)
        return {
            "success": False,
            "error": f"Exception occurred: {e}",
        }, 500

# --- device / screen communication endpoints ---

@app.route("/ping", methods=["GET"])
def ping():
    """Simple connectivity check for the on-device screen."""
    return {"status": "ok"}, 200


@app.route("/get_time", methods=["GET"])
def get_time():
    """Return current server time (for touchscreen clock sync)."""
    return {"time": time.time()}, 200


@app.route("/check_alert", methods=["GET"])
def check_alert():
    """Return the nearest due dose within ±15 min, including its prescription_id."""
    now = datetime.now().strftime("%H:%M")
    now_dt = datetime.strptime(now, "%H:%M")
    db = get_db()

    meds = db.execute(
        "SELECT prescription_id, user_id, name, time_of_day, status FROM prescriptions WHERE status='Active'"
    ).fetchall()

    closest = None
    closest_diff = 99999.0
    for med in meds:
        try:
            med_time_dt = datetime.strptime(med["time_of_day"], "%H:%M")
        except Exception:
            continue
        diff = abs((now_dt - med_time_dt).total_seconds() / 60.0)
        if diff <= 15 and diff < closest_diff:
            closest = med
            closest_diff = diff

    if closest:
        return {
            "alert": True,
            "user_id": closest["user_id"],
            "prescription_id": closest["prescription_id"],
            "name": closest["name"],
            "message": "Scan Finger to Dispense",
            "color": "red"
        }, 200

    return {"alert": False, "message": ""}, 200


@app.route("/sync_actions", methods=["POST"])
def sync_actions():
    """
    Body: {"actions":[{"prescription_id": <int>, "action":"dispense", "success": true}]}
    """
    data = request.get_json(force=True)
    actions = data.get("actions", [])
    db = get_db()
    now = datetime.now().strftime("%H:%M")
    for action in actions:
        if action.get("action") == "dispense" and action.get("success"):
            db.execute(
                "UPDATE prescriptions SET status='Dispensed', last_dispensed=? WHERE prescription_id=?",
                (now, action["prescription_id"])
            )
    db.commit()
    return {"success": True}, 200


if __name__ == "__main__":
    print("🚀 Starting PillSync server...")

    # Prevent multiple threads from starting
    if not any(t.name == "MedicationScheduler" for t in threading.enumerate()):
        alert_thread = threading.Thread(target=check_medication_schedule, daemon=True, name="MedicationScheduler")
        alert_thread.start()
        print("🔄 Background thread for medication alerts started.")

    app.run(host="0.0.0.0", port=5000, debug=False)  # Disable auto-reload to prevent duplicate threads
