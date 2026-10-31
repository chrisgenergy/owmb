import math
import json
import os
import sys
sys.path.insert(0, os.path.abspath("."))
from simulate_library import get_canonical_category

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
with open(db_path, "r", encoding="utf-8") as f:
    d = json.load(f)
items = d.get("items", [])
counts = {}
for it in items:
    cat = "other"
    for t in it.get("tags", []):
        c = get_canonical_category(t)
        if c != "other":
            cat = c
            break
    counts[cat] = counts.get(cat, 0) + 1

print(f"{'Category':<18} | {'Count':>6} | {'BaseR':>7} | {'Area Mpx2':>10} | {'Max d_hex':>9} | {'Target d':>8}")
print("-" * 70)
for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
    if count == 0: continue
    baseR = 155.0 + (count ** 0.35) * 30.0
    capBoundaryR = baseR * 0.66
    maxA = baseR * 1.35
    straightHalfW = max(0.0, maxA - capBoundaryR)
    area = 2 * straightHalfW * 2 * capBoundaryR + math.pi * (capBoundaryR ** 2)
    d_hex = 1.0745 * math.sqrt(area / count)
    print(f"{cat:<18} | {count:>6} | {baseR:>7.1f} | {area/1e6:>10.2f} | {d_hex:>9.1f} | 24.5")
