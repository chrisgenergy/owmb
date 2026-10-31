import math
import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))
from simulate_library import get_canonical_category

acoustic_continuum = {
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

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
real_counts = {}
if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])
    for item in items:
        chosen = "other"
        for t in item.get("tags", []):
            c = get_canonical_category(t)
            if c != "other":
                chosen = c
                break
        real_counts[chosen] = real_counts.get(chosen, 0) + 1

archetypes = {
    "Real 87k": real_counts,
    "Pure Drums": {
        "kick": 2500, "snare": 3000, "clap": 800, "hihat closed": 2000, 
        "hihat open": 1200, "tambourine shaker": 600, "tom": 500, "percussion": 1500
    },
    "Pure Orch": {
        "strings": 4000, "brass": 2500, "woodwinds": 1800, "orchestral": 3200, "fx": 900
    },
    "Micro-Pack": {
        "kick": 30, "snare": 30, "hihat": 40, "bass": 25, "synth": 25
    }
}

def test_gap(gap_px, pack_density=0.74):
    results = {}
    for name, counts in archetypes.items():
        active = [c for c in acoustic_continuum if counts.get(c, 0) > 0]
        K = len(active)
        k_area = 3.1901
        A_hex = (24.5 ** 2) * (math.sqrt(3) / 2.0)
        pack_factor = math.sqrt(A_hex / (0.76 * k_area))

        radii = {}
        for c in active:
            cnt = counts[c]
            r_label = 155.0 + (cnt ** 0.35) * 24.0
            r_pack = pack_factor * math.sqrt(cnt)
            radii[c] = max(r_label, r_pack)

        GRID_W = 120
        GRID_H = 75
        cx, cy = GRID_W * 0.5, GRID_H * 0.5
        a, b = cx * 1.10, cy * 0.90
        domain_grid_area = math.pi * a * b

        active_P = [acoustic_continuum[c][0] for c in active]
        active_T = [acoustic_continuum[c][1] for c in active]
        min_P, max_P = min(active_P), max(active_P)
        min_T, max_T = min(active_T), max(active_T)
        mid_P = (min_P + max_P) * 0.5
        mid_T = (min_T + max_T) * 0.5
        span_P = max(0.60, max_P - min_P)
        span_T = max(0.60, max_T - min_T)

        seeds = []
        for c in active:
            P, T = acoustic_continuum[c]
            norm_P = (P - mid_P) / (span_P * 0.5)
            norm_T = (T - mid_T) / (span_T * 0.5)
            angle = math.atan2(norm_P, norm_T)
            raw_r = math.hypot(norm_T, norm_P)
            dist = min(0.70, (raw_r ** 0.80) * 0.56)
            ax = math.cos(angle) * dist
            ay = math.sin(angle) * dist
            gx = (ax + 1.0) * 0.5 * GRID_W
            gy = (ay + 1.0) * 0.5 * GRID_H
            w = radii[c] ** 1.85
            seeds.append({ "cat": c, "x": gx, "y": gy, "w": w })

        for _ in range(4):
            sum_x = [0.0] * K
            sum_y = [0.0] * K
            cell_count = [0] * K
            for gy in range(GRID_H):
                dy_norm = (gy - cy) / b
                for gx in range(GRID_W):
                    dx_norm = (gx - cx) / a
                    if dx_norm * dx_norm + dy_norm * dy_norm > 1.0: continue
                    best_i = 0
                    min_dist = float("inf")
                    for i in range(K):
                        dx = gx - seeds[i]["x"]
                        dy = gy - seeds[i]["y"]
                        d = (dx * dx + dy * dy) / max(1.0, seeds[i]["w"])
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
        cell_size = math.sqrt((total_cluster_area / pack_density) / domain_grid_area)

        clusters = []
        for s in seeds:
            px = (s["x"] - cx) * cell_size
            py = (s["y"] - cy) * cell_size
            clusters.append({ "cat": s["cat"], "r": radii[s["cat"]], "pos": [px, py] })

        for _ in range(16):
            for i in range(K):
                for j in range(i + 1, K):
                    dx = clusters[j]["pos"][0] - clusters[i]["pos"][0]
                    dy = clusters[j]["pos"][1] - clusters[i]["pos"][1]
                    dist = math.hypot(dx, dy)
                    min_radial = clusters[i]["r"] + clusters[j]["r"] + gap_px
                    if 0.01 < dist < min_radial:
                        overlap = (min_radial - dist) * 0.5
                        nx, ny = dx / dist, dy / dist
                        clusters[i]["pos"][0] -= nx * overlap
                        clusters[i]["pos"][1] -= ny * overlap
                        clusters[j]["pos"][0] += nx * overlap
                        clusters[j]["pos"][1] += ny * overlap

                    abs_dx, abs_dy = abs(dx), abs(dy)
                    min_lw, min_lh = 150.0, 42.0
                    if abs_dx < min_lw and abs_dy < min_lh:
                        push_x = (min_lw - abs_dx) * 0.5
                        push_y = (min_lh - abs_dy) * 0.5
                        sign_x = 1.0 if dx >= 0 else -1.0
                        sign_y = 1.0 if dy >= 0 else -1.0
                        if push_x < push_y * 2.2:
                            clusters[i]["pos"][0] -= sign_x * push_x
                            clusters[j]["pos"][0] += sign_x * push_x
                        else:
                            clusters[i]["pos"][1] -= sign_y * push_y
                            clusters[j]["pos"][1] += sign_y * push_y

        min_edge_gap = float("inf")
        for i in range(K):
            for j in range(i + 1, K):
                dist = math.hypot(clusters[j]["pos"][0] - clusters[i]["pos"][0],
                                  clusters[j]["pos"][1] - clusters[i]["pos"][1])
                edge_gap = dist - (clusters[i]["r"] + clusters[j]["r"])
                if edge_gap < min_edge_gap: min_edge_gap = edge_gap

        label_colls = 0
        for i in range(K):
            for j in range(i + 1, K):
                dx = abs(clusters[j]["pos"][0] - clusters[i]["pos"][0])
                dy = abs(clusters[j]["pos"][1] - clusters[i]["pos"][1])
                if dx < 145.0 and dy < 38.0: label_colls += 1

        min_x = min(c["pos"][0] - c["r"] for c in clusters)
        max_x = max(c["pos"][0] + c["r"] for c in clusters)
        min_y = min(c["pos"][1] - c["r"] for c in clusters)
        max_y = max(c["pos"][1] + c["r"] for c in clusters)
        ar = (max_x - min_x) / max(1.0, max_y - min_y)

        results[name] = { "min_gap": min_edge_gap, "ar": ar, "labels": label_colls }
    return results

print(f"{'Gap (px)':<10} | {'Archetype':<12} | {'Min Edge Gap':>12} | {'Aspect Ratio':>12} | {'Label Collisions':>16}")
print("-" * 75)
for test_g in [68.0, 50.0, 40.0, 35.0, 25.0]:
    res = test_gap(test_g)
    for arch, r in res.items():
        print(f"{test_g:<10.1f} | {arch:<12} | {r['min_gap']:>11.1f} px | {r['ar']:>11.2f} : 1 | {r['labels']:>16d}")
    print("-" * 75)
