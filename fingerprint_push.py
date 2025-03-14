import hashlib
from flask import Flask, request, jsonify

registered_fingerprints = {}


def send_push_notification(token, title, message):
   
    print(f"Sending notification to {token}: {title} - {message}")
    return {"status": "success", "message": "Notification simulated"}


app = Flask(__name__)


@app.route('/fingerprint/enroll', methods=['POST'])
def enroll_fingerprint():
    data = request.get_json() 
    user_id = data.get('user_id')  
    fingerprint_data = data.get('fingerprint_data')  
    
    if not user_id or not fingerprint_data:
        return jsonify({"error": "Missing user_id or fingerprint_data"}), 400

   
    fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()

    registered_fingerprints[user_id] = fingerprint_hash
    
    
    return jsonify({"message": f"Fingerprint for {user_id} enrolled."}), 200


@app.route('/fingerprint/verify', methods=['POST'])
def verify_fingerprint():
    data = request.get_json()  
    user_id = data.get('user_id')  
    fingerprint_data = data.get('fingerprint_data')  
    
    if not user_id or not fingerprint_data:
        return jsonify({"error": "Missing user_id or fingerprint_data"}), 400

    fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
    registered_hash = registered_fingerprints.get(user_id)
    
    if registered_hash and registered_hash == fingerprint_hash:
       
        send_push_notification(
            user_id, 
            "Medication Reminder", 
            "It's time to take your pills. Please take your medication now."
        )
        
        return jsonify({"message": "Authentication successful. Medication reminder sent."}), 200
    else:
       
        return jsonify({"message": "Authentication failed."}), 401


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
