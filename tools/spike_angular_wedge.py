#!/usr/bin/env python3
"""
Step 0b: 2-Tier Core-Periphery Angular Wedge Spike
Tests dense 2D acoustic disc (Core + Perimeter) macro-allocation.
Core = central body (vocal, snare, clap, keys, strings).
Perimeter = high air, transient edge, low bedrock (kicks, hats, cymbals, bass, fx).
"""

import math
import os
import json

def run_spike():
    core_categories = {"vocal", "snare", "clap", "snap", "keys", "strings", "percussion"}

    perimeter_ring = [
        "kick", "tom", "bongo/conga", "clave/rim", "cowbell", 
        "hihat closed", "hihat", "hihat open", "tambourine shaker", 
        "ride", "cymbal", "crash", "woodwinds", "fx", "brass", 
        "orchestral", "synth", "guitar", "bass", "loop", "other"
    ]

    core_ring = ["percussion", "snap", "clap", "snare", "vocal", "strings", "keys"]

    db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
    real_counts = {}
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data.get("items", []):
            cat = "other"
            for t in item.get("tags", []):
                t_clean = t.lower().replace("#", "").strip()
                for c in (perimeter_ring + core_ring):
                    if c in t_clean or t_clean in c:
                        cat = c
                        break
                if cat != "other":
                    break
            real_counts[cat] = real_counts.get(cat, 0) + 1

    archetypes = {
        "A. Real Library (87k general)": real_counts if real_counts else { c: 3000 for c in perimeter_ring + core_ring },
        "B. Pure Drum Pack (0 tonal)": {
            "kick": 2500, "snare": 3000, "clap": 800, "hihat closed": 2000, 
            "hihat open": 1200, "tambourine shaker": 600, "tom": 500, "percussion": 1500
        },
        "C. Pure Orchestral (0 drums)": {
            "strings": 4000, "brass": 2500, "woodwinds": 1800, "orchestral": 3200, "fx": 900
        },
        "D. Micro-Pack (150 samples)": {
            "kick": 30, "snare": 30, "hihat": 40, "bass": 25, "synth": 25
        }
    }

    print("================================================================================")
    print("      STEP 0b: 2-TIER CORE-PERIPHERY ANGULAR WEDGE SPIKE (DENSE 2D DISC)        ")
    print("================================================================================")

    for arch_name, counts in archetypes.items():
        # Separate active into Core and Perimeter
        active_perim = [c for c in perimeter_ring if counts.get(c, 0) > 0]
        active_core  = [c for c in core_ring if counts.get(c, 0) > 0]
        all_active   = active_perim + active_core
        K_total = len(all_active)
        if K_total == 0:
            continue

        cat_radii = { c: 160.0 + (counts[c] ** 0.35) * 32.0 for c in all_active }

        # Perimeter allocation
        K_perim = len(active_perim)
        target_gap = 75.0
        perim_arc_demands = [2.0 * cat_radii[c] + target_gap for c in active_perim]
        total_perim_arc = sum(perim_arc_demands) if perim_arc_demands else 1000.0
        # Perimeter radius
        R_perim = max(800.0, total_perim_arc / (2.0 * math.pi))
        perim_wedge_angles = [arc / R_perim for arc in perim_arc_demands]

        centers = []
        cur_angle = -math.pi * 0.5
        for i, c in enumerate(active_perim):
            th = cur_angle + perim_wedge_angles[i] * 0.5
            cx = math.cos(th) * R_perim * 1.55
            cy = math.sin(th) * R_perim * 0.95
            centers.append({
                "cat": c, "tier": "perimeter", "r": cat_radii[c],
                "theta": th, "x": cx, "y": cy
            })
            cur_angle += perim_wedge_angles[i]

        # Core allocation (sits at inner radius ~0.42 * R_perim)
        K_core = len(active_core)
        if K_core > 0:
            core_arc_demands = [2.0 * cat_radii[c] + target_gap for c in active_core]
            total_core_arc = sum(core_arc_demands)
            R_core = max(450.0, total_core_arc / (2.0 * math.pi))
            core_wedge_angles = [arc / R_core for arc in core_arc_demands]
            cur_core_angle = -math.pi * 0.5
            for i, c in enumerate(active_core):
                th = cur_core_angle + core_wedge_angles[i] * 0.5
                cx = math.cos(th) * R_core * 1.55
                cy = math.sin(th) * R_core * 0.95
                centers.append({
                    "cat": c, "tier": "core", "r": cat_radii[c],
                    "theta": th, "x": cx, "y": cy
                })
                cur_core_angle += core_wedge_angles[i]

        # Metric Evaluations
        all_edge_gaps = []
        min_inter_gap = float("inf")
        closest_pair = None
        for i in range(len(centers)):
            for j in range(i + 1, len(centers)):
                c1, c2 = centers[i], centers[j]
                dist = math.hypot(c2["x"] - c1["x"], c2["y"] - c1["y"])
                edge_gap = dist - (c1["r"] + c2["r"])
                if edge_gap < min_inter_gap:
                    min_inter_gap = edge_gap
                    closest_pair = (c1["cat"], c2["cat"])

        # Label overlaps
        label_overlaps = []
        for i in range(len(centers)):
            for j in range(i + 1, len(centers)):
                dx = abs(centers[j]["x"] - centers[i]["x"])
                dy = abs(centers[j]["y"] - centers[i]["y"])
                if dx < 145.0 and dy < 38.0:
                    label_overlaps.append((centers[i]["cat"], centers[j]["cat"]))

        # Bounding box & Aspect Ratio
        min_x = min(c["x"] - c["r"] for c in centers)
        max_x = max(c["x"] + c["r"] for c in centers)
        min_y = min(c["y"] - c["r"] for c in centers)
        max_y = max(c["y"] + c["r"] for c in centers)
        bb_ar = (max_x - min_x) / max(1.0, (max_y - min_y))

        # Core vs Perimeter Void Fill
        # Check if center (0,0) has nearby clusters (dense core vs hollow donut)
        dist_to_center = min(math.hypot(c["x"], c["y"]) - c["r"] for c in centers)
        has_dense_core = dist_to_center < 350.0

        print(f"\n--- Archetype: {arch_name} ---")
        print(f"  Total Categories (Perim/Core) : {K_total} ({K_perim} perim, {K_core} core)")
        print(f"  Perimeter Radius (R_perim)    : {R_perim:.1f} px")
        print(f"  Bounding Box AR               : {bb_ar:.2f} : 1")
        print(f"  Min Edge-to-Edge Gap          : {min_inter_gap:.1f} px -> {'PASS' if min_inter_gap >= 40.0 else 'WARN'}")
        if min_inter_gap < 40.0:
            print(f"    Closest Pair                : {closest_pair[0]} <--> {closest_pair[1]}")
        print(f"  Label Overlaps                : {len(label_overlaps)} collisions -> {'PASS' if len(label_overlaps) == 0 else 'FAIL'}")
        print(f"  Core Density (Hollow Donut?)  : {'Dense Core (No Donut Hole)' if has_dense_core else 'Hollow Center'}")

if __name__ == "__main__":
    run_spike()
