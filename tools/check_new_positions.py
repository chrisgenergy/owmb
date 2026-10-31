import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json, math
import simulate_library as sim

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
with open(db_path, "r", encoding="utf-8") as f:
    data = json.load(f)
counts = {}
for it in data.get("items", []):
    chosen = "other"
    for t in it.get("tags", []):
        c = sim.get_canonical_category(t)
        if c != "other":
            chosen = c
            break
    counts[chosen] = counts.get(chosen, 0) + 1

acoustic_taxonomy = {
    "vocal":             ( 0.05,  0.00),
    "loop":              (-0.12, -0.05),
    "clap":              (-0.05, -0.25),
    "snare":             ( 0.05, -0.45),
    "strings":           ( 0.12,  0.25),
    "keys":              (-0.15,  0.28),
    "snap":              ( 0.15, -0.15),
    "percussion":        (-0.25, -0.30),
    "tambourine shaker": ( 0.50, -0.15),
    "cowbell":           ( 0.30, -0.38),
    "clave/rim":         ( 0.25, -0.55),
    "guitar":            (-0.30,  0.45),
    "orchestral":        ( 0.35,  0.40),
    "brass":             ( 0.20,  0.55),
    "bongo/conga":       (-0.35, -0.45),
    "tom":               (-0.45, -0.65),
    "kick":              (-0.68, -0.55),
    "bass":              (-0.65,  0.60),
    "synth":             (-0.05,  0.70),
    "other":             (-0.40,  0.10),
    "woodwinds":         ( 0.55,  0.48),
    "fx":                ( 0.50,  0.65),
    "crash":             ( 0.65,  0.35),
    "cymbal":            ( 0.68,  0.18),
    "ride":              ( 0.70,  0.02),
    "hihat open":        ( 0.70, -0.25),
    "hihat":             ( 0.65, -0.48),
    "hihat closed":      ( 0.55, -0.68),
}

active = [c for c in acoustic_taxonomy if counts.get(c, 0) > 0]
K = len(active)
radii = { c: 160.0 + (counts[c] ** 0.35) * 32.0 for c in active }

active_P = [acoustic_taxonomy[c][0] for c in active]
active_T = [acoustic_taxonomy[c][1] for c in active]
min_P, max_P = min(active_P), max(active_P)
min_T, max_T = min(active_T), max(active_T)
mid_P = (min_P + max_P) * 0.5
mid_T = (min_T + max_T) * 0.5
span_P = max(0.6, max_P - min_P)
span_T = max(0.6, max_T - min_T)

GRID_W, GRID_H = 120, 75
cx, cy = GRID_W * 0.5, GRID_H * 0.5
a, b = cx * 1.06, cy * 0.92
domain_grid_area = math.pi * a * b

seeds = []
for c in active:
    P, T = acoustic_taxonomy[c]
    norm_P = (P - mid_P) / (span_P * 0.5)
    norm_T = (T - mid_T) / (span_T * 0.5)
    angle = math.atan2(norm_P, norm_T)
    dist = math.hypot(norm_T, norm_P) * 0.62
    dist = min(0.78, dist)
    
    ax = math.cos(angle) * dist
    ay = math.sin(angle) * dist
    gx = (ax + 1.0) * 0.5 * GRID_W
    gy = (ay + 1.0) * 0.5 * GRID_H
    w = radii[c] ** 0.35
    seeds.append({ "cat": c, "x": gx, "y": gy, "w": w })

for _ in range(4):
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

total_cluster_area = sum(math.pi * radii[c]**2 for c in active)
cell_size = math.sqrt((total_cluster_area / 0.55) / domain_grid_area)

clusters = []
for s in seeds:
    px = (s["x"] - cx) * cell_size
    py = (s["y"] - cy) * cell_size
    clusters.append({ "cat": s["cat"], "pos": [px, py], "r": radii[s["cat"]] })

for _ in range(16):
    for i in range(K):
        for j in range(i + 1, K):
            dx = clusters[j]["pos"][0] - clusters[i]["pos"][0]
            dy = clusters[j]["pos"][1] - clusters[i]["pos"][1]
            dist = math.hypot(dx, dy)
            min_radial = clusters[i]["r"] + clusters[j]["r"] + 72.0
            if 0.01 < dist < min_radial:
                overlap = (min_radial - dist) * 0.5
                nx, ny = dx / dist, dy / dist
                clusters[i]["pos"][0] -= nx * overlap
                clusters[i]["pos"][1] -= ny * overlap
                clusters[j]["pos"][0] += nx * overlap
                clusters[j]["pos"][1] += ny * overlap

print("Clusters sorted by distance to center (0,0):")
for c in sorted(clusters, key=lambda x: math.hypot(x['pos'][0], x['pos'][1])):
    d = math.hypot(c['pos'][0], c['pos'][1])
    print(f"  {c['cat']:<20}: dist={d:6.1f}px, pos=({c['pos'][0]:7.1f}, {c['pos'][1]:7.1f}), r={c['r']:5.1f}")

