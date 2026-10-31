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

acoustic_tax = {
    "vocal":             ( 0.05,  0.00, 0.05),
    "clap":              (-0.05, -0.30, 0.22),
    "snare":             ( 0.08, -0.55, 0.40),
    "clave/rim":         ( 0.25, -0.65, 0.55),
    "cowbell":           ( 0.30, -0.45, 0.45),
    "snap":              ( 0.18, -0.20, 0.25),
    "hihat closed":      ( 0.58, -0.75, 0.75),
    "hihat":             ( 0.70, -0.55, 0.75),
    "hihat open":        ( 0.75, -0.35, 0.70),
    "tambourine shaker": ( 0.68, -0.15, 0.60),
    "ride":              ( 0.75,  0.05, 0.65),
    "cymbal":            ( 0.72,  0.25, 0.65),
    "crash":             ( 0.70,  0.45, 0.72),
    "woodwinds":         ( 0.60,  0.60, 0.68),
    "fx":                ( 0.55,  0.75, 0.78),
    "orchestral":        ( 0.38,  0.52, 0.52),
    "strings":           ( 0.18,  0.32, 0.28),
    "brass":             ( 0.22,  0.65, 0.58),
    "synth":             (-0.05,  0.78, 0.68),
    "keys":              (-0.18,  0.35, 0.32),
    "guitar":            (-0.30,  0.58, 0.52),
    "bass":              (-0.65,  0.72, 0.78),
    "other":             (-0.45,  0.15, 0.45),
    "loop":              (-0.15, -0.05, 0.18),
    "percussion":        (-0.30, -0.35, 0.38),
    "bongo/conga":       (-0.38, -0.55, 0.55),
    "tom":               (-0.42, -0.72, 0.72),
    "kick":              (-0.70, -0.68, 0.78),
}

active = [c for c in counts if counts[c] > 0]
K = len(active)
radii = { c: 160.0 + (counts[c] ** 0.35) * 32.0 for c in active }

GRID_W, GRID_H = 120, 75
cx, cy = GRID_W * 0.5, GRID_H * 0.5
a, b = cx * 1.06, cy * 0.92

seeds = []
for c in active:
    F, T, P = acoustic_tax.get(c, (0, 0, 0.5))
    angle = math.atan2(F, T)
    dist = P * 0.75
    ax = math.cos(angle) * dist
    ay = math.sin(angle) * dist
    gx = (ax + 1.0) * 0.5 * GRID_W
    gy = (ay + 1.0) * 0.5 * GRID_H
    w = radii[c] ** 0.35
    seeds.append({ "cat": c, "x": gx, "y": gy, "w": w })

loop_idx = [i for i, s in enumerate(seeds) if s['cat'] == 'loop'][0]
print(f"Init: loop at gx={seeds[loop_idx]['x']:.2f}, gy={seeds[loop_idx]['y']:.2f}, relY={seeds[loop_idx]['y'] - cy:.2f}")

for p in range(4):
    sum_x = [0.0] * K
    sum_y = [0.0] * K
    cell_count = [0] * K
    for gy in range(GRID_H):
        dy_norm = (gy - cy) / b
        for gx in range(GRID_W):
            dx_norm = (gx - cx) / a
            if dx_norm*dx_norm + dy_norm*dy_norm > 1.0:
                continue
            best_i = 0
            min_dist = float("inf")
            for i in range(K):
                d = ((gx - seeds[i]["x"])**2 + (gy - seeds[i]["y"])**2) / seeds[i]["w"]
                if d < min_dist:
                    min_dist = d
                    best_i = i
            sum_x[best_i] += gx
            sum_y[best_i] += gy
            cell_count[best_i] += 1
    for i in range(K):
        if cell_count[i] > 0:
            seeds[i]["x"] = sum_x[i] / cell_count[i]
            seeds[i]["y"] = sum_y[i] / cell_count[i]
    print(f"Pass {p+1}: loop at gx={seeds[loop_idx]['x']:.2f}, gy={seeds[loop_idx]['y']:.2f}, cell_count={cell_count[loop_idx]}, relY={seeds[loop_idx]['y'] - cy:.2f}")

