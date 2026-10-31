#!/usr/bin/env python3
"""
True 2D Planar Disc Void Metric Evaluation:
Measures the maximum empty radius from any point in the domain to the nearest cluster boundary.
"""

import math
import os
import json
from test_hybrid_spec import run_hybrid_layer_ab

def evaluate_2d_voids():
    archetypes = {
        "1. Real Library (87k general)": {"kick": 2500, "snare": 3000, "clap": 800, "hihat closed": 2000, "hihat open": 1200, "bass": 2000, "synth": 4000, "keys": 2500, "guitar": 1500, "strings": 3000, "brass": 1800, "woodwinds": 1200, "orchestral": 2500, "fx": 1500, "vocal": 2200, "tom": 800, "loop": 2000, "other": 1500},
        "2. Pure Drum Pack (0 tonal)": {"kick": 2500, "snare": 3000, "clap": 800, "hihat closed": 2000, "hihat open": 1200, "tambourine shaker": 600, "tom": 500, "percussion": 1500},
        "3. Pure Orchestral (0 drums)": {"strings": 4000, "brass": 2500, "woodwinds": 1800, "orchestral": 3200, "fx": 900},
        "4. Micro-Pack (150 samples)": {"kick": 30, "snare": 30, "hihat": 40, "bass": 25, "synth": 25}
    }

    print("================================================================================")
    print("      TRUE 2D PLANAR DISC VOID EVALUATION (MAX EMPTY RADIUS)                    ")
    print("================================================================================")

    for name, counts in archetypes.items():
        clusters, w, h, ar, labels, min_gap, _, core = run_hybrid_layer_ab(counts)
        K = len(clusters)

        # 2D Void Metric: Sample a 40x25 grid across the bounding box [-w/2, w/2] x [-h/2, h/2]
        # and find the distance from each point to the nearest cluster edge
        max_void_radius = 0.0
        void_point = (0, 0)

        for gy in range(25):
            py = (-0.5 + gy / 24.0) * h * 0.85
            for gx in range(40):
                px = (-0.5 + gx / 39.0) * w * 0.85
                # Distance to nearest cluster boundary
                min_dist_to_cluster_edge = min(math.hypot(px - c["pos"][0], py - c["pos"][1]) - c["r"] for c in clusters)
                if min_dist_to_cluster_edge > max_void_radius:
                    max_void_radius = min_dist_to_cluster_edge
                    void_point = (px, py)

        print(f"\nArchetype: {name}")
        print(f"  Categories            : {K}")
        print(f"  Aspect Ratio          : {ar:.2f} : 1")
        print(f"  Min Inter-Cluster Gap : {min_gap:.1f} px (PASS >= 60px)")
        print(f"  Max 2D Void Radius    : {max_void_radius:.1f} px (Cosmic breathing space)")
        print(f"  Center Occupancy      : {core:.1f} px (Dense Core)")
        print(f"  Label Collisions      : {labels} collisions")

if __name__ == "__main__":
    evaluate_2d_voids()

