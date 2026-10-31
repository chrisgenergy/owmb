import math
import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))
import simulate_library
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
with open(db_path, "r", encoding="utf-8") as f:
    d = json.load(f)
items = d.get("items", [])
real_counts = {}
for it in items:
    cat = "other"
    for t in it.get("tags", []):
        c = get_canonical_category(t)
        if c != "other":
            cat = c
            break
    real_counts[cat] = real_counts.get(cat, 0) + 1

# Archetypes
archetypes = {
    "1. Real Library (87k general)": real_counts,
    "2. Pure Drum Pack (0 tonal)": {
        "kick": 850, "snare": 720, "clap": 410, "hihat closed": 980,
        "hihat open": 310, "tom": 260, "percussion": 540, "crash": 180
    },
    "3. Pure Orchestral (0 drums)": {
        "strings": 1450, "brass": 620, "woodwinds": 480, "orchestral": 890, "keys": 310
    },
    "4. Micro-Pack (150 samples)": {
        "kick": 40, "snare": 35, "hihat": 45, "bass": 20, "synth": 10
    }
}

def run_sim_with_dynamic_radii(cat_counts, packing_efficiency=0.80):
    active = [c for c in acoustic_continuum if cat_counts.get(c, 0) > 0]
    K = len(active)
    if K == 0:
        return [], 0, 0, 1.6, 0, 0, 0, 0

    k_area = 3.1901
    A_hex = (24.5 ** 2) * (math.sqrt(3) / 2.0)
    pack_factor = math.sqrt(A_hex / (packing_efficiency * k_area))

    # Dynamic radius: guarantees legible label for small N and physical area for large N
    radii = {}
    for c in active:
        cnt = cat_counts[c]
        r_label = 155.0 + (cnt ** 0.35) * 26.0
        r_pack = pack_factor * math.sqrt(cnt)
        radii[c] = max(r_label, r_pack)

    kMacroPackDensity = 0.74
    kRadialCompressionExponent = 0.80
    kRadialBaseScale = 0.56
    kMaxRadialFactor = 0.70

    active_P = [acoustic_continuum[c][0] for c in active]
    active_T = [acoustic_continuum[c][1] for c in active]
    min_P, max_P = min(active_P), max(active_P)
    min_T, max_T = min(active_T), max(active_T)
    mid_P = (min_P + max_P) * 0.5
    mid_T = (min_T + max_T) * 0.5
    span_P = max(0.60, max_P - min_P)
    span_T = max(0.60, max_T - min_T)

    GRID_W = 120
    GRID_H = 75
    total_area_needed = sum(math.pi * (radii[c] + 68.0) ** 2 for c in active)
    domain_area = total_area_needed / kMacroPackDensity
    cy = math.sqrt(domain_area / (math.pi * 1.60))
    cx = cy * 1.60 * 1.08

    target_anchors = {}
    for c in active:
        norm_P = (acoustic_continuum[c][0] - mid_P) / span_P
        norm_T = (acoustic_continuum[c][1] - mid_T) / span_T
        raw_r = math.hypot(norm_T, norm_P)
        theta = math.atan2(norm_P, norm_T)
        comp_r = min(kMaxRadialFactor, (raw_r ** kRadialCompressionExponent) * kRadialBaseScale)
        anchor_x = cx * comp_r * math.cos(theta)
        anchor_y = cy * comp_r * math.sin(theta)
        target_anchors[c] = (anchor_x, anchor_y)

    # Centroidal Power Diagram: weight proportional to target area (radius squared)
    # Damped power weight prevents massive categories from crushing smaller ones while allocating required area
    weights = {c: (radii[c] ** 1.85) for c in active}
    clusters = [{"cat": c, "pos": list(target_anchors[c]), "r": radii[c]} for c in active]

    # Iterative Lloyd-Power Relaxation
    for iteration in range(40):
        cell_sums = {c: [0.0, 0.0] for c in active}
        cell_counts = {c: 0 for c in active}

        for gy in range(GRID_H):
            py = (-0.5 + (gy + 0.5) / GRID_H) * 2.0 * cy
            for gx in range(GRID_W):
                px = (-0.5 + (gx + 0.5) / GRID_W) * 2.0 * cx
                if (px / cx) ** 2 + (py / cy) ** 2 > 1.0:
                    continue
                best_cat = None
                min_pwr = float("inf")
                for c in clusters:
                    d_sq = (px - c["pos"][0]) ** 2 + (py - c["pos"][1]) ** 2
                    pwr = d_sq - weights[c["cat"]]
                    if pwr < min_pwr:
                        min_pwr = pwr
                        best_cat = c["cat"]
                if best_cat:
                    cell_sums[best_cat][0] += px
                    cell_sums[best_cat][1] += py
                    cell_counts[best_cat] += 1

        for c in clusters:
            cat = c["cat"]
            cnt = cell_counts[cat]
            if cnt > 0:
                cent_x = cell_sums[cat][0] / cnt
                cent_y = cell_sums[cat][1] / cnt
                blend = 0.65 if iteration < 20 else 0.40
                c["pos"][0] = c["pos"][0] * (1.0 - blend) + cent_x * blend
                c["pos"][1] = c["pos"][1] * (1.0 - blend) + cent_y * blend

    # Layer B: Dynamic Node Contact Repulsion (Hard Clearance Guard)
    kMinInterClusterGapPx = 68.0
    for pass_idx in range(120):
        for i in range(K):
            for j in range(i + 1, K):
                dx = clusters[j]["pos"][0] - clusters[i]["pos"][0]
                dy = clusters[j]["pos"][1] - clusters[i]["pos"][1]
                dist = math.hypot(dx, dy)
                min_dist = clusters[i]["r"] + clusters[j]["r"] + kMinInterClusterGapPx
                if dist < min_dist and dist > 0.001:
                    overlap = min_dist - dist
                    push_x = (dx / dist) * (overlap * 0.52)
                    push_y = (dy / dist) * (overlap * 0.52)
                    clusters[i]["pos"][0] -= push_x
                    clusters[i]["pos"][1] -= push_y
                    clusters[j]["pos"][0] += push_x
                    clusters[j]["pos"][1] += push_y

    # Centroid Auto-Centering
    mx = sum(c["pos"][0] for c in clusters) / K
    my = sum(c["pos"][1] for c in clusters) / K
    for c in clusters:
        c["pos"][0] -= mx
        c["pos"][1] -= my

    # Metrics
    min_edge_gap = float("inf")
    closest_pair = None
    for i in range(K):
        for j in range(i + 1, K):
            dist = math.hypot(clusters[j]["pos"][0] - clusters[i]["pos"][0],
                              clusters[j]["pos"][1] - clusters[i]["pos"][1])
            edge_gap = dist - (clusters[i]["r"] + clusters[j]["r"])
            if edge_gap < min_edge_gap:
                min_edge_gap = edge_gap
                closest_pair = (clusters[i]["cat"], clusters[j]["cat"])

    label_overlaps = []
    for i in range(K):
        for j in range(i + 1, K):
            dx = abs(clusters[j]["pos"][0] - clusters[i]["pos"][0])
            dy = abs(clusters[j]["pos"][1] - clusters[i]["pos"][1])
            if dx < 145.0 and dy < 38.0:
                label_overlaps.append((clusters[i]["cat"], clusters[j]["cat"]))

    min_x = min(c["pos"][0] - c["r"] for c in clusters)
    max_x = max(c["pos"][0] + c["r"] for c in clusters)
    min_y = min(c["pos"][1] - c["r"] for c in clusters)
    max_y = max(c["pos"][1] + c["r"] for c in clusters)
    bb_w = max_x - min_x
    bb_h = max_y - min_y
    ar = bb_w / max(1.0, bb_h)

    max_void_radius = 0.0
    for gy in range(25):
        py = (-0.5 + gy / 24.0) * bb_h * 0.85
        for gx in range(40):
            px = (-0.5 + gx / 39.0) * bb_w * 0.85
            min_dist_edge = min(math.hypot(px - c["pos"][0], py - c["pos"][1]) - c["r"] for c in clusters)
            if min_dist_edge > max_void_radius:
                max_void_radius = min_dist_edge

    core_gap = min(math.hypot(c["pos"][0], c["pos"][1]) - c["r"] for c in clusters)

    return clusters, bb_w, bb_h, ar, len(label_overlaps), min_edge_gap, max_void_radius, core_gap

print("Testing Dynamic Radii across Archetypes:")
for name, counts in archetypes.items():
    clusters, bb_w, bb_h, ar, label_ov, min_gap, max_void, core_gap = run_sim_with_dynamic_radii(counts)
    synth_r = next((c["r"] for c in clusters if c["cat"] == "synth"), None)
    print(f"\nArchetype: {name}")
    if synth_r:
        print(f"  Synth Radius: {synth_r:.1f} px")
    print(f"  Aspect Ratio         : {ar:.2f} : 1")
    print(f"  Min Inter-Cluster Gap: {min_gap:.1f} px")
    print(f"  Max 2D Cosmic Void   : {max_void:.1f} px")
    print(f"  Core Gap             : {core_gap:.1f} px")
    print(f"  Label Collisions     : {label_ov}")
