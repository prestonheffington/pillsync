-- Create Users table
CREATE TABLE users (
	user_id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	birthdate TEXT NOT NULL,
	fingerprint_data BLOB
);

-- Create Prescriptions table
CREATE TABLE prescriptions (
    prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    amount INTEGER NOT NULL,
    frequency TEXT NOT NULL,
    refill_date TEXT NOT NULL,
    dosage TEXT,
    time_of_day TEXT,
    status TEXT DEFAULT 'Active',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
