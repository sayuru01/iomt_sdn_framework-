

# simulators/traffic_sim.py
import socket
import json
import time
import argparse
from datetime import datetime
import sys
import os

# Add project root to path so 'database' package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clinical_ranges import generate_vitals, get_interval, CLINICAL_RANGES
from database.db_manager import safe_write

SERVER_PORT = 5005


def get_target_ip(host_id):
    """Send to the NEXT device in the ring (h1->h2 ... h9->h1), never to self.
    This avoids the loopback issue where a host sending to its own IP
    never actually leaves its eth0 interface, making it invisible to
    switch-level flow stats."""
    n = int(host_id[1:])
    next_n = (n % 9) + 1
    return f'10.0.0.{next_n}'


def save_to_database(host_id, device_type, vitals):
    """Save one reading to patient_data table via the shared db_manager."""
    try:
        safe_write("""
            INSERT INTO patient_data (
                timestamp, host_id, device_type,
                breathing_rate, tidal_volume, spo2_vent, airway_pressure, peep,
                heart_rate, blood_pressure, temperature, spo2_icu,
                flow_rate, volume_infused,
                prescription_id, drug_name, dispensed_amount,
                record_type, record_count
            ) VALUES (
                datetime('now'), ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?
            )
        """, (
            host_id, device_type,
            # Ventilator (h1)
            vitals.get('breathing_rate'), vitals.get('tidal_volume'),
            vitals.get('spo2') if device_type == 'VENTILATOR' else None,
            vitals.get('airway_pressure'), vitals.get('peep'),
            # ICU Monitor (h2) / Ward Monitor (h8)
            vitals.get('heart_rate'), vitals.get('blood_pressure'),
            vitals.get('temperature'),
            vitals.get('spo2') if device_type in ('ICU_MONITOR', 'WARD_MONITOR') else None,
            # Infusion Pump (h3)
            vitals.get('flow_rate'), vitals.get('volume_infused'),
            # Pharmacy-type devices (h4-h6)
            vitals.get('prescription_id'), vitals.get('drug_name'),
            vitals.get('dispensed_amount'),
            # Admin-type devices (h7-h9)
            vitals.get('record_type'), vitals.get('record_count')
        ))
    except Exception as e:
        print(f"[{host_id}] DB Error: {e}")


def run_simulator(host_id):
    if host_id not in CLINICAL_RANGES:
        raise ValueError(f"Unknown host_id '{host_id}' — must be h1-h9")

    device_type = CLINICAL_RANGES[host_id]['device_type']
    interval = get_interval(host_id)
    target_ip = get_target_ip(host_id)
    print(f"[*] Starting Simulator for {host_id} ({device_type}) — every {interval}s -> sending to {target_ip}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        while True:
            vitals = generate_vitals(host_id)

            payload = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "host_id": host_id,
                "device_type": device_type,
                "data": vitals
            }

            # UDP send is OPTIONAL — never let it crash the simulator
            try:
                message = json.dumps(payload).encode('utf-8')
                sock.sendto(message, (target_ip, SERVER_PORT))
            except Exception as e:
                print(f"[{host_id}] UDP send skipped: {e}")

            print(f"[{host_id}] Sent: {vitals}")

            save_to_database(host_id, device_type, vitals)

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n[*] Stopping simulator for {host_id}")
    finally:
        sock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IoMT Device Simulator')
    parser.add_argument('--host', type=str, required=True,
                         help='Host ID (h1-h9)')
    args = parser.parse_args()
    run_simulator(args.host)
