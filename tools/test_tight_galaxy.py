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

acoustic_continuum = {
    # Frequency Pitch (-1 to +1), Timbre (-1 to +1)
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

active = [c for c in acoustic_continuum if counts.get(c, 0) > 0]
K = len(active)
radii = { c: 160.0 + (counts[c] ** 0.35) * 32.0 for c in active }

# Active Normalization
active_P = [acoustic_continuum[c][0] for c in active]
active_T = [acoustic_continuum[c][1] for c in active]
min_P, max_P = min(active_P), max(active_P)
min_T, max_T = min(active_T), max(active_T)
mid_P = (min_P + max_P) * 0.5
mid_T = (min_T + max_T) * 0.5
span_P = max(0.60, max_P - min_P)
span_T = max(0.60, max_T - min_T)

GRID_W, GRID_H = 120, 75
cx, cy = GRID_W * 0.5, GRID_H * 0.5

# Test tighter elliptical boundary + centripetal damping in Lloyd relaxation
for domain_scale in [1.0, 0.85, 0.75]:
    a = cx * 1.06 * domain_scale
    b = cy * 0.92 * domain_scale
    domain_grid_area = math.pi * a * b

    for pack_density in [0.65, 0.72]:
        seeds = []
        for c in active:
            P, T = acoustic_continuum[c]
            norm_P = (P - mid_P) / (span_P * 0.5)
            norm_T = (T - mid_T) / (span_T * 0.5)
            angle = math.atan2(norm_P, norm_T)
            # Continuous radial compression: smooth sqrt taper towards core
            raw_r = math.hypot(norm_T, norm_P)
            dist = min(0.72, (raw_r ** 0.75) * 0.55) * domain_scale

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
        cell_size = math.sqrt((total_cluster_area / pack_density) / domain_grid_area)

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
                    min_radial = clusters[i]["r"] + clusters[j]["r"] + 64.0
                    if 0.01 < dist < min_radial:
                        overlap = (min_radial - dist) * 0.5
                        nx, ny = dx / dist, dy / dist
                        clusters[i]["pos"][0] -= nx * overlap
                        clusters[i]["pos"][1] -= ny * overlap
                        clusters[j]["pos"][0] += nx * overlap
                        clusters[j]["pos"][1] += ny * overlap
                    abs_dx, abs_dy = abs(dx), abs(dy)
                    min_lw, min_lh = 145.0, 38.0
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

        min_x = min(c["pos"][0] - c["r"] for c in clusters)
        max_x = max(c["pos"][0] + c["r"] for c in clusters)
        min_y = min(c["pos"][1] - c["r"] for c in clusters)
        max_y = max(c["pos"][1] + c["r"] for c in clusters)
        bb_w, bb_h = max_x - min_x, max_y - min_y
        ar = bb_w / max(1.0, bb_h)

        max_nn_gap = max(
            min(math.hypot(clusters[j]["pos"][0] - clusters[i]["pos"][0],
                           clusters[j]["pos"][1] - clusters[i]["pos"][1]) - (clusters[i]["r"] + clusters[j]["r"])
                for j in range(K) if i != j)
            for i in range(K)
        )
        avg_nn_gap = sum(
            min(math.hypot(clusters[j]["pos"][0] - clusters[i]["pos"][0],
                           clusters[j]["pos"][1] - clusters[i]["pos"][1]) - (clusters[i]["r"] + clusters[j]["r"])
                for j in range(K) if i != j)
            for i in range(K)
        ) / K

        max_void = 0.0
        for gy in range(25):
            py = (-0.5 + gy / 24.0) * bb_h * 0.85
            for gx in range(40):
                px = (-0.5 + gx / 39.0) * bb_w * 0.85
                md = min(math.hypot(px - c["pos"][0], py - c["pos"][1]) - c["r"] for c in clusters)
                if md > max_void:
                    max_void = md

        core_gap = min(math.hypot(c["pos"][0], c["pos"][1]) - c["r"] for c in clusters)
        print(f"scale={domain_scale:.2f}, pack={pack_density:.2f} -> BB: {bb_w:.0f}x{bb_h:.0f}, AR: {ar:.2f}, AvgGap: {avg_nn_gap:5.1f}px, MaxNNGap: {max_nn_gap:5.1f}px, MaxVoid: {max_void:6.1f}px, Core: {core_gap:5.1f}px")

