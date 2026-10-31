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

active = [c for c in counts if counts[c] > 0]
K = len(active)
radii = { c: 160.0 + (counts[c] ** 0.35) * 32.0 for c in active }

# Acoustic continuous attributes (§5)
# Pitch: -1 (Sub/Bass) to +1 (Air/Cymbals)
# Timbre: -1 (Transient/Percussive) to +1 (Harmonic/Tonal)
# Core: 0 (Central Melodic/Groove Anchor) to 1 (Extreme Perimeter)
acoustic_tax = {
    # Frequency F (-1 to +1), Timbre T (-1 to +1), Perimeter P (0 to 1)
    "vocal":             ( 0.05,  0.00, 0.08),
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
    "loop":              (-0.20, -0.05, 0.22), # Central groove bridge!
    "percussion":        (-0.30, -0.35, 0.38),
    "bongo/conga":       (-0.38, -0.55, 0.55),
    "tom":               (-0.42, -0.72, 0.72),
    "kick":              (-0.70, -0.68, 0.78),
}

for exp in [2.0, 1.0, 0.5, 0.2]:
    # Test Voronoi with different weight exponents: w = r^exp
    GRID_W, GRID_H = 120, 75
    cx, cy = GRID_W * 0.5, GRID_H * 0.5
    a, b = cx * 1.06, cy * 0.92
    domain_grid_area = math.pi * a * b

    seeds = []
    for c in active:
        F, T, P = acoustic_tax.get(c, (0, 0, 0.5))
        # Continuous polar-elliptical placement from musical axes
        angle = math.atan2(F, T)
        # R is bounded by perimeter affinity P
        dist = P * 0.75
        ax = math.cos(angle) * dist
        ay = math.sin(angle) * dist
        gx = (ax + 1.0) * 0.5 * GRID_W
        gy = (ay + 1.0) * 0.5 * GRID_H
        w = radii[c] ** exp
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

    # Measure core void and max void
    min_x = min(c["pos"][0] - c["r"] for c in clusters)
    max_x = max(c["pos"][0] + c["r"] for c in clusters)
    min_y = min(c["pos"][1] - c["r"] for c in clusters)
    max_y = max(c["pos"][1] + c["r"] for c in clusters)
    bb_w, bb_h = max_x - min_x, max_y - min_y
    ar = bb_w / max(1.0, bb_h)

    max_void = 0.0
    for gy in range(25):
        py = (-0.5 + gy / 24.0) * bb_h * 0.85
        for gx in range(40):
            px = (-0.5 + gx / 39.0) * bb_w * 0.85
            md = min(math.hypot(px - c["pos"][0], py - c["pos"][1]) - c["r"] for c in clusters)
            if md > max_void:
                max_void = md
    core_gap = min(math.hypot(c["pos"][0], c["pos"][1]) - c["r"] for c in clusters)
    print(f"Weight Exp r^{exp:.1f} -> Max Void: {max_void:6.1f}px, Core Gap: {core_gap:6.1f}px, AR: {ar:.2f}")

