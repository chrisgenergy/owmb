import sys
import os
import json
import math
import time

sys.path.insert(0, ".")
from simulate_library import (
    get_canonical_category, run_hybrid_simulation,
    generate_cluster_stars, check_star_collisions
)

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
real_counts = {}
if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])
    prio_list = [
        "subkick", "kick", "rimshot", "snare", "clap", "snap",
        "hihat open", "hihat closed", "hihat", "tom", "crash", "ride", "cymbal",
        "cowbell", "bongo/conga", "tambourine shaker", "percussion",
        "bass", "keys", "guitar", "strings", "brass", "woodwinds", "orchestral",
        "vocal", "synth", "fx", "loop"
    ]
    for item in items:
        cats = [get_canonical_category(t) for t in item.get("tags", [])]
        chosen = "other"
        for p in prio_list:
            if p in cats:
                chosen = p
                break
        real_counts[chosen] = real_counts.get(chosen, 0) + 1

total_real = sum(real_counts.values())

targets = [10_000, 50_000, 87_177, 120_000, 200_000]

print("=" * 84)
print("     SCALE-UP STRESS TEST: 10k, 50k, 87k, 120k, 200k LIBRARIES (§3 & §7 GATES)      ")
print("=" * 84)

results = []

for target_n in targets:
    scale = target_n / float(total_real)
    scaled_counts = {}
    for c, cnt in real_counts.items():
        scaled_counts[c] = max(1, int(round(cnt * scale)))
    
    actual_n = sum(scaled_counts.values())
    
    t0 = time.time()
    (clusters, bb_w, bb_h, ar, label_colls, min_gap, max_void, core_gap,
     star_colls, min_star_dist, colliding_pairs, closest_pair) = run_hybrid_simulation(scaled_counts)
    t_elapsed_ms = (time.time() - t0) * 1000.0

    pass_gap = min_gap >= 45.0
    pass_stars = (star_colls == 0) and (min_star_dist >= 24.5)
    pass_labels = label_colls == 0
    pass_ar = 1.40 <= ar <= 1.90
    pass_core = core_gap < 500.0

    all_pass = pass_gap and pass_stars and pass_labels and pass_ar and pass_core

    results.append({
        "target": target_n,
        "actual": actual_n,
        "bb_w": bb_w,
        "bb_h": bb_h,
        "ar": ar,
        "min_gap": min_gap,
        "closest_pair": closest_pair,
        "min_star_dist": min_star_dist,
        "star_colls": star_colls,
        "colliding_pairs": colliding_pairs,
        "label_colls": label_colls,
        "core_gap": core_gap,
        "elapsed_ms": t_elapsed_ms,
        "pass": all_pass
    })

    print(f"\n--- Library Scale: {target_n:,} samples (Actual: {actual_n:,}) ---")
    print(f"  Layout Dimension        : {bb_w:6.0f} x {bb_h:6.0f} px (Aspect: {ar:.2f}:1) -> {'PASS' if pass_ar else 'FAIL':4s}")
    print(f"  Min Inter-Cluster Gap   : {min_gap:6.1f} px       (Target: >= 45.0 px)  -> {'PASS' if pass_gap else 'FAIL':4s} ({closest_pair[0]} <-> {closest_pair[1]})")
    print(f"  Min Star-to-Star Dist   : {min_star_dist:6.1f} px       (Target: >= 24.5 px)  -> {'PASS' if pass_stars else 'FAIL':4s}")
    print(f"  Cross-Cluster Overlaps  : {star_colls:6d}          (Target: 0)           -> {'PASS' if star_colls == 0 else 'FAIL':4s}")
    print(f"  Label Collisions        : {label_colls:6d}          (Target: 0)           -> {'PASS' if pass_labels else 'FAIL':4s}")
    print(f"  Center Occupancy / Core : {core_gap:6.1f} px       (Target: < 500.0 px)  -> {'PASS' if pass_core else 'FAIL':4s}")
    print(f"  Layout Generation Time  : {t_elapsed_ms:6.1f} ms")

print("\n" + "=" * 84)
print("                       CAMERA AUTO-FIT & VIEWPORT MARGINS                           ")
print("=" * 84)
viewports = {
    "Widescreen 16:9 (1920x1080)": (1920.0, 1080.0),
    "DAW Plugin 4:3  (1024x768) ": (1024.0, 768.0),
    "Ultrawide 21:9  (2560x1080)": (2560.0, 1080.0)
}

for r in results:
    w, h = r["bb_w"], r["bb_h"]
    print(f"\nScale: {r['target']:,} samples ({w:.0f}x{h:.0f} px)")
    for vp_name, (vw, vh) in viewports.items():
        scale_fit = min((vw * 0.80) / w, (vh * 0.80) / h)
        fit_w = w * scale_fit
        fit_h = h * scale_fit
        margin_x = (vw - fit_w) / (2.0 * vw) * 100.0
        margin_y = (vh - fit_h) / (2.0 * vh) * 100.0
        fill_ratio = (fit_w * fit_h) / (vw * vh)
        print(f"  {vp_name:28s} -> Margins: X={margin_x:4.1f}%, Y={margin_y:4.1f}% | Fill: {fill_ratio:.2f}")

print("\n" + "=" * 84)
all_green = all(r["pass"] for r in results)
if all_green:
    print(">>> SCALE TEST SUMMARY: 100% GREEN ACROSS ALL SCALES (10k to 200k) <<<")
else:
    print(">>> SCALE TEST SUMMARY: ISSUES DETECTED <<<")
print("=" * 84)

