# test_db.py
import os
import sys
import time

# db_manager එක import කරගැනීම
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'database'))
import db_manager

def run_full_database_test():
    print("\n[*] Starting Full Database Verification Test...\n")
    current_time_ms = time.time() * 1000

    # ---------------------------------------------------------
    # TABLE 1: device_status
    # ---------------------------------------------------------
    print("[1] Testing Table: device_status")
    query_write_1 = """
        INSERT INTO device_status 
        (timestamp, host_id, host_name, ip_address, department, status) 
        VALUES (datetime('now'), ?, ?, ?, ?, ?)
    """
    try:
        row_id = db_manager.safe_write(query_write_1, ("h1", "Ventilator", "10.0.0.1", "ICU", "ONLINE"))
        res1 = db_manager.safe_read(f"SELECT * FROM device_status WHERE id={row_id}", fetch_one=True)
        print(f"  ✅ SUCCESS -> Host: {res1['host_id']} | Dept: {res1['department']} | Status: {res1['status']}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")

    # ---------------------------------------------------------
    # TABLE 2: patient_data
    # ---------------------------------------------------------
    print("\n[2] Testing Table: patient_data")
    query_write_2 = """
        INSERT INTO patient_data 
        (timestamp, host_id, device_type, breathing_rate, tidal_volume) 
        VALUES (datetime('now'), ?, ?, ?, ?)
    """
    try:
        row_id = db_manager.safe_write(query_write_2, ("h1", "VENTILATOR", 15.5, 450.0))
        res2 = db_manager.safe_read(f"SELECT * FROM patient_data WHERE id={row_id}", fetch_one=True)
        print(f"  ✅ SUCCESS -> Host: {res2['host_id']} | Rate: {res2['breathing_rate']} | Vol: {res2['tidal_volume']}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")

    # ---------------------------------------------------------
    # TABLE 3: attack_events
    # ---------------------------------------------------------
    print("\n[3] Testing Table: attack_events")
    query_write_3 = """
        INSERT INTO attack_events 
        (timestamp, timestamp_ms, attacker_ip, attacker_mac, target_ip, attack_type, detection_time_ms) 
        VALUES (datetime('now'), ?, ?, ?, ?, ?, ?)
    """
    try:
        row_id = db_manager.safe_write(query_write_3, (current_time_ms, "10.0.0.10", "00:00:00:00:00:10", "10.0.0.1", "PACKET_BURST", 65.5))
        res3 = db_manager.safe_read(f"SELECT * FROM attack_events WHERE id={row_id}", fetch_one=True)
        print(f"  ✅ SUCCESS -> Attacker: {res3['attacker_ip']} | Type: {res3['attack_type']} | Detect: {res3['detection_time_ms']}ms")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")

    # ---------------------------------------------------------
    # TABLE 4: forensic_logs
    # ---------------------------------------------------------
    print("\n[4] Testing Table: forensic_logs")
    query_write_4 = """
        INSERT INTO forensic_logs 
        (timestamp, timestamp_ms, capture_stage, attacker_ip, attacker_mac, evidence_json, sha256_hash) 
        VALUES (datetime('now'), ?, ?, ?, ?, ?, ?)
    """
    evidence_dummy = '{"event": "test"}'
    try:
        row_id = db_manager.safe_write(query_write_4, (current_time_ms, "PRE_CONTAINMENT", "10.0.0.10", "00:00:00:00:00:10", evidence_dummy, "abc123def456hash"))
        res4 = db_manager.safe_read(f"SELECT * FROM forensic_logs WHERE id={row_id}", fetch_one=True)
        print(f"  ✅ SUCCESS -> Stage: {res4['capture_stage']} | Hash: {res4['sha256_hash']}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")

    print("\n[*] Full Database Verification Completed!\n")

if __name__ == '__main__':
    run_full_database_test()