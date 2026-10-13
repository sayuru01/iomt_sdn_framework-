import csv, sys, glob, os, statistics
cut = float(sys.argv[1])
F = max(glob.glob("baseline_raw_*.csv"), key=os.path.getmtime)
data, stamps = {}, []
with open(F) as f:
    r = csv.reader(f); next(r)
    for row in r:
        try:
            ts = float(row[0]); h = row[2]; d = int(row[3])
        except (ValueError, IndexError):
            continue
        if ts < cut or h == 'h10':
            continue
        data.setdefault(h, []).append(d); stamps.append(ts)
print(f"File: {F}")
print(f"Window: {(max(stamps)-min(stamps))/60:.1f} min\n")
print(f"{'Host':<6}{'N':<7}{'Mean':<9}{'SD':<9}{'2SD':<9}{'2.5SD':<9}{'3SD':<9}{'Max'}")
for h in sorted(data, key=lambda x: int(x[1:])):
    v = data[h]; m = statistics.mean(v); s = statistics.stdev(v)
    print(f"{h:<6}{len(v):<7}{m:<9.3f}{s:<9.3f}{m+2*s:<9.2f}{m+2.5*s:<9.2f}{m+3*s:<9.2f}{max(v)}")
