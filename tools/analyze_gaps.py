import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json, math
import simulate_library as sim

p = os.path.expandvars(r'%APPDATA%\OpenWav\library_index.json')
data = json.load(open(p, encoding='utf-8'))
counts = {}
for it in data.get('items', []):
    chosen = "other"
    for t in it.get('tags', []):
        c = sim.get_canonical_category(t)
        if c != "other":
            chosen = c
            break
    counts[chosen] = counts.get(chosen, 0) + 1

cl, bb_w, bb_h, ar, lo, mg, mv, cg = sim.run_hybrid_simulation(counts)

print(f"Total clusters: {len(cl)}")
print(f"Bounding Box: {bb_w:.1f} x {bb_h:.1f}, Aspect Ratio: {ar:.2f}")
print(f"Min inter-cluster gap: {mg:.1f} px")
print(f"Max cosmic void: {mv:.1f} px")
print(f"Center occupancy (core gap): {cg:.1f} px")

# Find the nearest neighbor and edge gap for EVERY cluster
print("\n--- NEAREST NEIGHBOR EDGE GAP FOR EACH CLUSTER ---")
gaps = []
for i, c1 in enumerate(cl):
    min_gap = float('inf')
    nearest = None
    for j, c2 in enumerate(cl):
        if i == j: continue
        dx = c2["pos"][0] - c1["pos"][0]
        dy = c2["pos"][1] - c1["pos"][1]
        dist = math.hypot(dx, dy)
        gap = dist - (c1["r"] + c2["r"])
        if gap < min_gap:
            min_gap = gap
            nearest = c2["cat"]
    gaps.append((c1["cat"], nearest, min_gap, c1["r"]))
    print(f"  {c1['cat']:<20} -> nearest: {nearest:<20} | edge gap: {min_gap:6.1f} px | r: {c1['r']:5.1f} px")

avg_gap = sum(g[2] for g in gaps) / len(gaps)
max_gap = max(g[2] for g in gaps)
min_gap = min(g[2] for g in gaps)
print(f"\nAverage nearest-neighbor edge gap: {avg_gap:.1f} px (Min: {min_gap:.1f} px, Max: {max_gap:.1f} px)")

