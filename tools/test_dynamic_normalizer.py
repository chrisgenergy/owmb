import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json, math
import simulate_library as sim

archetypes = {
    "1. Real Library (87k general)": None, # loaded from db
    "2. Pure Drum Pack (0 tonal)": {
        "kick": 2500, "snare": 3000, "clap": 800, "hihat closed": 2000, 
        "hihat open": 1200, "tambourine shaker": 600, "tom": 500, "percussion": 1500
    },
    "3. Pure Orchestral (0 drums)": {
        "strings": 4000, "brass": 2500, "woodwinds": 1800, "orchestral": 3200, "fx": 900
    },
    "4. Micro-Pack (150 samples)": {
        "kick": 30, "snare": 30, "hihat": 40, "bass": 25, "synth": 25
    }
}

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
archetypes["1. Real Library (87k general)"] = counts

# Continuous acoustic properties from §5
# Frequency (-1 to +1), Timbre (-1 to +1), Radial Tier / Center Affinity (0 to 1)
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
    "loop":              (-0.20, -0.05, 0.20),
    "percussion":        (-0.30, -0.35, 0.38),
    "bongo/conga":       (-0.38, -0.55, 0.55),
    "tom":               (-0.42, -0.72, 0.72),
    "kick":              (-0.70, -0.68, 0.78),
}

for name, arch_counts in archetypes.items():
    active = [c for c in arch_counts if arch_counts[c] > 0]
    K = len(active)
    radii = { c: 160.0 + (arch_counts[c] ** 0.35) * 32.0 for c in active }

    # DYNAMIC NORMALIZATION across active categories (Resilience Rule §3)
    # If drums only, min-max normalize F and T so the library dynamically scales to the entire disc!
    all_F = [acoustic_tax[c][0] for c in active if c in acoustic_tax]
    all_T = [acoustic_tax[c][1] for c in active if c in acoustic_tax]
    all_P = [acoustic_tax[c][2] for c in active if c in acoustic_tax]
    
    # Dynamic expansion factor: if span is narrow, expand organically
    span_F = max(all_F) - min(all_F) if all_F else 1.0
    span_T = max(all_T) - min(all_T) if all_T else 1.0
    scale_F = 1.6 / max(0.6, span_F)
    scale_T = 1.6 / max(0.6, span_T)

    mid_F = (max(all_F) + min(all_F)) * 0.5 if all_F else 0.0
    mid_T = (max(all_T) + min(all_T)) * 0.5 if all_T else 0.0

    GRID_W, GRID_H = 120, 75
    cx, cy = GRID_W * 0.5, GRID_H * 0.5
    a, b = cx * 1.06, cy * 0.92
    domain_grid_area = math.pi * a * b

    seeds = []
    for c in active:
        F, T, P = acoustic_tax.get(c, (0, 0, 0.5))
        # Center relative to active library distribution (Dynamic Centroid)
        dF = (F - mid_F) * min(1.3, scale_F)
        dT = (T - mid_T) * min(1.3, scale_T)
        angle = math.atan2(dF, dT)
        dist = math.hypot(dT, dF) * 0.65
        # Clamp within unit disc
        dist = min(0.78, dist)
        ax = math.cos(angle) * dist
        ay = math.sin(angle) * dist

        gx = (ax + 1.0) * 0.5 * GRID_W
        gy = (ay + 1.0) * 0.5 * GRID_H
        w = radii[c] ** 0.35 # Damped sub-linear Voronoi weight!
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

    # Layer B Local clearance
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
    print(f"[{name}]")
    print(f"  AR: {ar:.2f}, Core Gap: {core_gap:6.1f}px, Max Void: {max_void:6.1f}px")

