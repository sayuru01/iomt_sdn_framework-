import csv
import statistics
import sys
import glob

F = sorted(glob.glob("baseline_raw_*.csv"))[-1]
print(f"Reading: {F}\n")

data = {}  # host -> list of packet_delta
with open(F) as f:
    reader = csv.DictReader(f)
    for row in reader:
        host = row['host']
        if host == 'h10':
            continue  # h10 is the attacker, never baseline it
        try:
            delta = int(row['packet_delta'])
        except (ValueError, KeyError):
            continue
        data.setdefault(host, []).append(delta)

print(f"{'Host':<6}{'N':<8}{'Mean':<10}{'SD':<10}{'Thr(2SD)':<10}{'Thr(2.5SD)':<12}{'Thr(3SD)':<10}")
print("-" * 66)

results = {}
for host in sorted(data.keys(), key=lambda h: int(h[1:])):
    vals = data[host]
    n = len(vals)
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals) if n > 1 else 0.0
    t2 = mean + 2 * sd
    t25 = mean + 2.5 * sd
    t3 = mean + 3 * sd
    results[host] = {"n": n, "mean": mean, "sd": sd,
                      "threshold_2sd": t2, "threshold_2_5sd": t25, "threshold_3sd": t3}
    print(f"{host:<6}{n:<8}{mean:<10.3f}{sd:<10.3f}{t2:<10.3f}{t25:<12.3f}{t3:<10.3f}")

import json
with open("baseline_thresholds.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved: baseline_thresholds.json")
