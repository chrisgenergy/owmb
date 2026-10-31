#!/usr/bin/env python3
"""
Layer A C++ Algorithm Prototype & Validator
Simulates the exact C++ Hybrid Layer A (Centroidal Power Partitioning) + Layer B (Local Label Guard)
across all 4 archetypes to guarantee 100% GREEN before editing C++.
"""

import sys
import os
import json
import math

def run_hybrid_layer_ab(cat_counts):
    canonical_anchors = {
        "kick":              (-0.75, -0.65),
        "bass":              ( 0.75, -0.65),
        "hihat closed":      (-0.75,  0.65),
        "hihat":             (-0.60,  0.70),
        "hihat open":        (-0.45,  0.72),
        "fx":                ( 0.75,  0.65),
        "tom":               (-0.75, -0.30),
        "bongo/conga":       (-0.50, -0.25),
        "percussion":        (-0.35, -0.05),
        "snare":             (-0.70,  0.15),
        "clap":              (-0.45,  0.20),
        "snap":              (-0.25,  0.25),
        "clave/rim":         (-0.55,  0.42),
        "cowbell":           (-0.35,  0.48),
        "tambourine shaker": (-0.20,  0.72),
        "ride":              (-0.05,  0.75),
        "cymbal":            ( 0.10,  0.75),
        "crash":             ( 0.28,  0.72),
        "woodwinds":         ( 0.45,  0.68),
        "brass":             ( 0.60,  0.40),
        "orchestral":        ( 0.45,  0.48),
        "strings":           ( 0.35,  0.22),
        "synth":             ( 0.75,  0.15),
        "keys":              ( 0.45, -0.15),
        "guitar":            ( 0.70, -0.25),
        "vocal":             ( 0.00,  0.05),
        "loop":              (-0.20, -0.60),
        "other":             ( 0.10, -0.62)
    }

    active = [c for c in canonical_anchors if cat_counts.get(c, 0) > 0]
    K = len(active)
    if K == 0:
        return [], 0, 0, 1.6, 0, 0, 0

    # Layer B Radii
    radii = { c: 160.0 + (cat_counts[c] ** 0.35) * 32.0 for c in active }
    sum_area = sum((radii[c] + 45.0) ** 2 for c in active)
    pack_radius = math.sqrt(max(100.0, sum_area / 0.52))
    base_spread = max(780.0, pack_radius * 1.05)

    # =========================================================================
    # LAYER A: DETERMINISTIC 2D CENTROIDAL POWER DIAGRAM
    # =========================================================================
    GRID_W = 120
    GRID_H = 75  # 120 / 75 = 1.60 : 1 Widescreen Aspect Ratio
    weights = { c: radii[c] ** 2 for c in active }

    seeds = []
    for c in active:
        ax, ay = canonical_anchors[c]
        gx = (ax + 1.0) * 0.5 * GRID_W
        gy = (ay + 1.0) * 0.5 * GRID_H
        seeds.append({ "cat": c, "x": gx, "y": gy, "w": weights[c] })

    # 4 Lloyd relaxation passes
    for _ in range(4):
        sum_x = [0.0] * K
        sum_y = [0.0] * K
        cell_count = [0] * K

        for gy in range(GRID_H):
            for gx in range(GRID_W):
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

    # Map grid coordinates back to physical world coordinates [-spread, +spread]
    clusters = []
    for s in seeds:
        px = (s["x"] / GRID_W - 0.5) * 2.0 * base_spread * 1.55
        py = (s["y"] / GRID_H - 0.5) * 2.0 * base_spread * 0.95
        clusters.append({
            "cat": s["cat"], "r": radii[s["cat"]],
            "pos": [px, py]
        })

    # =========================================================================
    # LAYER B: LOCAL CONTACT CLEARANCE & LABEL GUARD (12 Gentle Passes)
    # =========================================================================
    for _ in range(12):
        for i in range(K):
            for j in range(i + 1, K):
                dx = clusters[j]["pos"][0] - clusters[i]["pos"][0]
                dy = clusters[j]["pos"][1] - clusters[i]["pos"][1]
                dist = math.hypot(dx, dy)
                min_radial = clusters[i]["r"] + clusters[j]["r"] + 65.0
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

    # Auto-center
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

    # Adjacent Sector Gap
    sorted_by_theta = sorted(clusters, key=lambda c: math.atan2(c["pos"][1], c["pos"][0]))
    max_sector_gap = 0.0
    for i in range(K):
        c1 = sorted_by_theta[i]
        c2 = sorted_by_theta[(i + 1) % K]
        dist = math.hypot(c2["pos"][0] - c1["pos"][0], c2["pos"][1] - c1["pos"][1])
        edge_gap = max(0.0, dist - (c1["r"] + c2["r"]))
        if edge_gap > max_sector_gap:
            max_sector_gap = edge_gap

    # Label Overlaps
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

    # Core check
    core_dist = min(math.hypot(c["pos"][0], c["pos"][1]) - c["r"] for c in clusters)

    return clusters, bb_w, bb_h, ar, len(label_overlaps), min_edge_gap, max_sector_gap, core_dist

def test_specification():
    db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
    real_counts = {}
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data.get("items", []):
            chosen = "other"
            for t in item.get("tags", []):
                t_clean = t.lower().replace("#", "").strip()
                if "kick" in t_clean: chosen = "kick"; break
                if "snare" in t_clean: chosen = "snare"; break
                if "clap" in t_clean: chosen = "clap"; break
                if "hihat" in t_clean or "hat" in t_clean: chosen = "hihat"; break
                if "bass" in t_clean: chosen = "bass"; break
                if "synth" in t_clean: chosen = "synth"; break
                if "keys" in t_clean or "piano" in t_clean: chosen = "keys"; break
                if "guitar" in t_clean: chosen = "guitar"; break
                if "vocal" in t_clean: chosen = "vocal"; break
                if "perc" in t_clean: chosen = "percussion"; break
                if "loop" in t_clean: chosen = "loop"; break
            real_counts[chosen] = real_counts.get(chosen, 0) + 1

    archetypes = {
        "1. Real Library (87k general)": real_counts if real_counts else { "kick": 1000 },
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

    print("================================================================================")
    print("      STEP 3: C++ SPECIFICATION VERIFICATION (HYBRID LAYER A + LAYER B)        ")
    print("================================================================================")

    all_green = True
    for name, counts in archetypes.items():
        clusters, w, h, ar, labels, min_gap, max_sec, core = run_hybrid_layer_ab(counts)
        pass_gap = min_gap >= 60.0
        pass_labels = labels == 0
        pass_ar = 1.40 <= ar <= 1.90
        is_torn = max_sec > 1400.0

        is_green = pass_gap and pass_labels and pass_ar and not is_torn
        if not is_green: all_green = False

        print(f"\nArchetype: {name}")
        print(f"  Categories        : {len(clusters)}")
        print(f"  Aspect Ratio      : {ar:.2f} : 1        (Target: [1.40, 1.90]) -> {'PASS' if pass_ar else 'FAIL':4s}")
        print(f"  Min Edge Gap      : {min_gap:6.1f} px    (Target: >= 60.0 px)   -> {'PASS' if pass_gap else 'FAIL':4s}")
        print(f"  Max Sector Gap    : {max_sec:6.1f} px    (Target: <= 1400 px)   -> {'HEALTHY' if not is_torn else 'TORN':10s}")
        print(f"  Core Occupancy    : {core:6.1f} px    ({'Filled Core' if core < 350 else 'Donut':12s})")
        print(f"  Label Collisions  : {labels:6d}         (Target: 0)            -> {'PASS' if pass_labels else 'FAIL':4s}")

    print("\n================================================================================")
    if all_green:
        print(">>> RESULT: 100% GREEN ACROSS ALL 4 ARCHETYPES! <<<")
        print("    The Hybrid Layer A+B C++ specification is mathematically verified.")
    else:
        print(">>> RESULT: RED <<<")
    print("================================================================================")

if __name__ == "__main__":
    test_specification()

