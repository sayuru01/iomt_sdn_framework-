import sqlite3
import os

def setup_database():
    print("Database setup script executed successfully")
    # 1. Create necessary folders if they don't exist
    os.makedirs('database', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    db_path = 'database/iomt_security.db'
    
    # 2. Connect to SQLite (this automatically creates the file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 3. Enable WAL mode (Crucial for preventing database locks with Ryu and Simulators)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    # 4. Create the 4 Tables
    print("Creating tables...")
    conn.executescript("""
CREATE TABLE IF NOT EXISTS attack_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL,          -- ISO format + milliseconds
    timestamp_ms    REAL NOT NULL,          -- Unix timestamp in ms
    attacker_ip     TEXT NOT NULL,          -- 10.0.0.10
    attacker_mac    TEXT NOT NULL,          -- MAC address
    target_ip       TEXT,                   -- Which device targeted
    attack_type     TEXT NOT NULL,          -- 'PACKET_BURST'/'PORT_SCAN'/'LATERAL_MOVEMENT'
    packet_rate     INTEGER,                -- packets per 5 seconds
    ports_scanned   INTEGER,                -- number of ports scanned
    devices_contacted INTEGER,              -- number of devices reached
    detection_time_ms REAL,                 -- ms from attack start to detection
    threshold_exceeded TEXT,                -- which threshold triggered
    run_number      INTEGER,                -- experiment run 1-10
    experiment_type TEXT                    -- 'ATTACK' or 'NORMAL'
);

CREATE TABLE IF NOT EXISTS forensic_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER,                -- links to attack_events.id
    timestamp       TEXT NOT NULL,          -- exact capture moment
    timestamp_ms    REAL NOT NULL,
    capture_stage   TEXT NOT NULL,          -- 'PRE_CONTAINMENT' (always)
    attacker_ip     TEXT NOT NULL,
    attacker_mac    TEXT NOT NULL,
    target_ip       TEXT,
    target_mac      TEXT,
    packet_rate     INTEGER,
    flow_table_state TEXT,                  -- JSON dump of flow table
    active_connections TEXT,               -- JSON list
    attack_type     TEXT,
    evidence_json   TEXT NOT NULL,          -- full JSON evidence string
    sha256_hash     TEXT NOT NULL,          -- SHA-256 of evidence_json
    hash_verified   INTEGER DEFAULT 1,      -- 1=verified, 0=tampered
    containment_fired_at_ms REAL,          -- when DROP rule sent
    snapshot_before_containment INTEGER,   -- always 1 (proof of order)
    FOREIGN KEY (event_id) REFERENCES attack_events(id)
);

CREATE TABLE IF NOT EXISTS device_status (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL,
    host_id         TEXT NOT NULL,          -- 'h1', 'h2', ... 'h10'
    host_name       TEXT NOT NULL,          -- 'Ventilator', 'ICU Monitor'
    ip_address      TEXT NOT NULL,          -- 10.0.0.x
    department      TEXT NOT NULL,          -- 'ICU', 'PHARMACY', 'ADMIN', 'ATTACKER'
    status          TEXT NOT NULL,          -- 'ONLINE','BLOCKED','PROTECTED','RESTORED'
    containment_time_ms REAL,              -- time to apply DROP rule
    rollback_time_ms REAL,                 -- time to remove DROP rule (FP)
    restore_time_ms REAL,                  -- time to restore from backup (Module 5)
    false_positive  INTEGER DEFAULT 0,     -- 1 if rollback was FP
    run_number      INTEGER
);

CREATE TABLE IF NOT EXISTS patient_data (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL,
    host_id         TEXT NOT NULL,          -- which device sent this
    device_type     TEXT NOT NULL,          -- 'VENTILATOR', 'ICU_MONITOR', etc.
    -- Ventilator fields
    breathing_rate  REAL,                   -- 12-20 breaths/min (WHO)
    tidal_volume    REAL,                   -- 400-600 mL (ARDS Network)
    spo2_vent       REAL,                   -- 95-100% (BTS)
    airway_pressure REAL,                   -- 15-25 cmH2O
    peep            REAL,                   -- 5-8 cmH2O
    -- ICU Monitor fields
    heart_rate      REAL,                   -- 60-100 bpm (AHA)
    blood_pressure  REAL,                   -- 90-140 mmHg (JNC 8)
    temperature     REAL,                   -- 36.1-37.2 C (WHO)
    spo2_icu        REAL,                   -- 95-100%
    -- Pharmacy fields
    prescription_id TEXT,
    drug_name       TEXT,
    dispensed_amount REAL,
    -- Admin fields
    record_type     TEXT,
    record_count    INTEGER,
    -- Infusion Pump (h3)
    flow_rate       REAL,
    volume_infused  REAL
);
                       """)

    # 5. Auto-migrate: add any new columns that CREATE TABLE IF NOT EXISTS skips
    migrations = [
        ("patient_data", "flow_rate",       "REAL"),
        ("patient_data", "volume_infused",  "REAL"),
    ]
    for table, column, col_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            print(f"  [MIGRATED] Added {table}.{column}")
        except sqlite3.OperationalError:
            pass  # column already exists — safe to ignore

    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()