import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json, simulate_library as sim

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
print(f"Bounding box: {bb_w:.1f} x {bb_h:.1f}, AR: {ar:.2f}")
print(f"Min gap: {mg:.1f}, Max void: {mv:.1f}, Core gap: {cg:.1f}")
print("Clusters sorted by Y descending (North to South):")
for c in sorted(cl, key=lambda x: -x['pos'][1]):
    print(f"{c['cat']:<20}: pos=({c['pos'][0]:7.1f}, {c['pos'][1]:7.1f}), r={c['r']:5.1f}, count={counts.get(c['cat'], 0)}")
