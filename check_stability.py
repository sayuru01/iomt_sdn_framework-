import csv, glob
from collections import defaultdict

F = sorted(glob.glob("baseline_raw_*.csv"))[-1]
buckets = defaultdict(lambda: defaultdict(list))  # minute -> host -> deltas

with open(F) as f:
    reader = csv.DictReader(f)
    for row in reader:
        host = row['host']
        if host not in ('h1','h2','h3'):
            continue
        try:
            ts = float(row['timestamp'])
            delta = int(row['packet_delta'])
        except (ValueError, KeyError):
            continue
        minute = int(ts // 60) * 60
        buckets[minute][host].append(delta)

print(f"{'Minute':<14}{'h1_mean':<10}{'h2_mean':<10}{'h3_mean':<10}")
for minute in sorted(buckets.keys()):
    row = buckets[minute]
    vals = []
    for h in ('h1','h2','h3'):
        d = row.get(h, [])
        vals.append(sum(d)/len(d) if d else -1)
    print(f"{minute:<14}{vals[0]:<10.3f}{vals[1]:<10.3f}{vals[2]:<10.3f}")
