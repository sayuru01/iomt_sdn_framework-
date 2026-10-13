# simulators/clinical_ranges.py
import random

CLINICAL_RANGES = {
    'h1': {
        'device_type':     'VENTILATOR',
        'breathing_rate':  (12, 20),      # breaths/min (WHO)
        'tidal_volume':    (400, 600),     # mL (ARDS Network)
        'spo2':            (95, 100),      # % (BTS)
        'airway_pressure': (15, 25),       # cmH2O
        'peep':            (5, 8),         # cmH2O
        'send_interval':   1               # seconds
    },
    'h2': {
        'device_type':    'ICU_MONITOR',
        'heart_rate':     (60, 100),       # bpm (AHA)
        'blood_pressure': (90, 140),       # mmHg (JNC 8)
        'temperature':    (36.1, 37.2),    # Celsius (WHO)
        'spo2':           (95, 100),       # %
        'send_interval':  1
    },
    'h3': {
        'device_type':    'INFUSION_PUMP',
        'flow_rate':      (1, 500),        # mL/hour
        'volume_infused': (0, 1000),       # mL
        'send_interval':  5
    },
    'h4': {
        'device_type':      'PHARMACY_PC',
        'dispensed_amount': (1, 100),
        'record_count':     (1, 20),
        'send_interval':    300            # 5 minutes
    },
    'h5': {
        'device_type':      'DRUG_DISPENSER',
        'dispensed_amount': (1, 50),
        'send_interval':    300
    },
    'h6': {
        'device_type':   'PHARMACY_DB',
        'record_count':  (1, 30),
        'send_interval': 300
    },
    'h7': {
        'device_type':   'ADMIN_PC',
        'record_count':  (1, 15),
        'send_interval': 300
    },
    'h8': {
        'device_type':   'WARD_MONITOR',
        'heart_rate':    (60, 100),
        'spo2':          (95, 100),
        'send_interval': 1
    },
    'h9': {
        'device_type':   'NURSES_STATION',
        'record_count':  (1, 10),
        'send_interval': 300
    },
}


def generate_vitals(device_key):
    """Returns only the randomized tuple-range fields (no device_type, no send_interval)."""
    ranges = CLINICAL_RANGES[device_key]
    vitals = {}
    for key, value in ranges.items():
        if isinstance(value, tuple):
            vitals[key] = round(random.uniform(value[0], value[1]), 2)
    return vitals


def get_interval(device_key):
    """Returns send interval in seconds for this device."""
    return CLINICAL_RANGES[device_key]['send_interval']


if __name__ == '__main__':
    for h in CLINICAL_RANGES:
        print(h, CLINICAL_RANGES[h]['device_type'], generate_vitals(h), get_interval(h))