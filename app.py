from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import hashlib

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Temporary storage instead of a database
CREDENTIALS_FILE = "data/credentials.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

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

@app.route("/", methods=["GET", "POST"])
def login():
    credentials = load_credentials()
    
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_input_password = hash_password(password)

        print(f"DEBUG: Entered Username: {username}")
        print(f"DEBUG: Entered Password (hashed): {hashed_input_password}")
        print(f"DEBUG: Stored Username: {credentials['username']}")
        print(f"DEBUG: Stored Password: {credentials['password']}")

        if username == credentials["username"] and hashed_input_password == credentials["password"]:
            print("DEBUG: Login successful!")
            session["user"] = username
            
            # **Redirect to password update page if default credentials are still used**
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

        # Update stored credentials
        save_credentials(new_username, new_password)

        session["user"] = new_username  # Keep user logged in
        print("DEBUG: Credentials updated successfully!")

        return redirect(url_for("dashboard"))

    return render_template("update_credentials.html")


@app.route("/dashboard")
def dashboard():
    """Dashboard page (No database, just a placeholder)."""
    if "user" not in session:
        return redirect(url_for("login"))
    
    return render_template("dashboard.html", username=session["user"], medications=[])

@app.route("/logout")
def logout():
    """Logout the user and clear the session."""
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
