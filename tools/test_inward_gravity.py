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

active = [c for c in counts if counts[c] > 0]
K = len(active)
radii = { c: 160.0 + (counts[c] ** 0.35) * 32.0 for c in active }

# Start with initial positions from musical vectors
clusters = []
for c in active:
    F, T, P = acoustic_tax.get(c, (0, 0, 0.5))
    angle = math.atan2(F, T)
    # Target radius: tight initial pack
    init_dist = P * 1800.0
    px = math.cos(angle) * init_dist * 1.35 # Widescreen 1.35x
    py = math.sin(angle) * init_dist
    clusters.append({ "cat": c, "pos": [px, py], "r": radii[c], "target_angle": angle })

# Physics relaxation: Inward Gravity + Hard Dynamic Contact Repulsion + Compass Restoration
# Max 3 forces!
for step in range(80):
    for i in range(K):
        # 1. Inward Centripetal Gravity: pulls everything gently towards (0,0)
        px, py = clusters[i]["pos"]
        d_center = math.hypot(px, py)
        if d_center > 10.0:
            clusters[i]["pos"][0] -= (px / d_center) * 18.0
            clusters[i]["pos"][1] -= (py / d_center) * 18.0

        # 2. Angular Compass restoration: keeps them in musical sector
        cur_angle = math.atan2(py, px / 1.35)
        angle_diff = math.remainder(clusters[i]["target_angle"] - cur_angle, 2.0 * math.pi)
        # Apply tangential nudge
        tan_x = -math.sin(cur_angle) * angle_diff * 12.0 * 1.35
        tan_y =  math.cos(cur_angle) * angle_diff * 12.0
        clusters[i]["pos"][0] += tan_x
        clusters[i]["pos"][1] += tan_y

    # 3. Dynamic Contact Repulsion (Hard Non-Overlap)
    for i in range(K):
        for j in range(i + 1, K):
            dx = clusters[j]["pos"][0] - clusters[i]["pos"][0]
            dy = clusters[j]["pos"][1] - clusters[i]["pos"][1]
            dist = math.hypot(dx, dy)
            min_dist = clusters[i]["r"] + clusters[j]["r"] + 72.0
            if 0.01 < dist < min_dist:
                overlap = (min_dist - dist) * 0.5
                nx, ny = dx / dist, dy / dist
                clusters[i]["pos"][0] -= nx * overlap
                clusters[i]["pos"][1] -= ny * overlap
                clusters[j]["pos"][0] += nx * overlap
                clusters[j]["pos"][1] += ny * overlap

            # Label box clearance
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

# Measure metrics
min_x = min(c["pos"][0] - c["r"] for c in clusters)
max_x = max(c["pos"][0] + c["r"] for c in clusters)
min_y = min(c["pos"][1] - c["r"] for c in clusters)
max_y = max(c["pos"][1] + c["r"] for c in clusters)
bb_w, bb_h = max_x - min_x, max_y - min_y
ar = bb_w / max(1.0, bb_h)

min_edge_gap = min(
    math.hypot(clusters[j]["pos"][0] - clusters[i]["pos"][0], clusters[j]["pos"][1] - clusters[i]["pos"][1]) - (clusters[i]["r"] + clusters[j]["r"])
    for i in range(K) for j in range(i + 1, K)
)

max_void = 0.0
for gy in range(25):
    py = (-0.5 + gy / 24.0) * bb_h * 0.85
    for gx in range(40):
        px = (-0.5 + gx / 39.0) * bb_w * 0.85
        md = min(math.hypot(px - c["pos"][0], py - c["pos"][1]) - c["r"] for c in clusters)
        if md > max_void:
            max_void = md

core_gap = min(math.hypot(c["pos"][0], c["pos"][1]) - c["r"] for c in clusters)

print("=== INWARD GRAVITY + CONTACT CLEARANCE RESULT ===")
print(f"Bounding Box       : {bb_w:.1f} x {bb_h:.1f} px")
print(f"Aspect Ratio       : {ar:.2f} : 1")
print(f"Min Inter-Cluster  : {min_edge_gap:.1f} px (Target >= 60px)")
print(f"Max Cosmic Void    : {max_void:.1f} px (was 1693px!)")
print(f"Core Gap           : {core_gap:.1f} px")

print("\nCluster positions around center (sorted by dist to 0,0):")
for c in sorted(clusters, key=lambda x: math.hypot(x['pos'][0], x['pos'][1]))[:8]:
    d = math.hypot(c['pos'][0], c['pos'][1])
    print(f"  {c['cat']:<20}: dist={d:6.1f}px, pos=({c['pos'][0]:7.1f}, {c['pos'][1]:7.1f}), r={c['r']:5.1f}")

