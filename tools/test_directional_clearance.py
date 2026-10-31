import os, json, math

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
with open(db_path, "r", encoding="utf-8") as f:
    data = json.load(f)
items = data.get("items", [])

import simulate_library
prio_list = [
    "subkick", "kick", "rimshot", "snare", "clap", "snap",
    "hihat open", "hihat closed", "hihat", "tom", "crash", "ride", "cymbal",
    "cowbell", "bongo/conga", "tambourine shaker", "percussion",
    "bass", "keys", "guitar", "strings", "brass", "woodwinds", "orchestral",
    "vocal", "synth", "fx", "loop"
]
real_counts = {}
for item in items:
    cats = [simulate_library.get_canonical_category(t) for t in item.get("tags", [])]
    chosen = "other"
    for p in prio_list:
        if p in cats:
            chosen = p
            break
    real_counts[chosen] = real_counts.get(chosen, 0) + 1

acoustic_continuum = {
    "vocal":             ( 0.05,  0.00,  0.15,  0.00, 1.35),
    "loop":              (-0.12, -0.05,  0.05, -0.20, 1.40),
    "clap":              (-0.05, -0.25,  0.12,  0.85, 1.35),
    "snare":             ( 0.05, -0.45,  0.05,  0.80, 1.40),
    "strings":           ( 0.12,  0.25,  0.20,  0.30, 1.35),
    "keys":              (-0.15,  0.28,  0.12,  0.60, 1.35),
    "snap":              ( 0.15, -0.15, -0.08,  0.70, 1.30),
    "percussion":        (-0.25, -0.30, -0.05,  0.35, 1.30),
    "tambourine shaker": ( 0.50, -0.15, -0.10, -0.25, 1.30),
    "cowbell":           ( 0.30, -0.38,  0.10,  0.20, 1.30),
    "clave/rim":         ( 0.25, -0.55,  0.05,  0.20, 1.35),
    "guitar":            (-0.30,  0.45, -0.10, -0.45, 1.35),
    "orchestral":        ( 0.35,  0.40,  0.15,  0.35, 1.35),
    "brass":             ( 0.20,  0.55, -0.05, -0.25, 1.35),
    "bongo/conga":       (-0.35, -0.45, -0.05,  0.40, 1.30),
    "tom":               (-0.45, -0.65,  0.10,  0.25, 1.35),
    "kick":              (-0.68, -0.55, -0.20, -0.30, 1.40),
    "bass":              (-0.65,  0.60, -0.22,  0.30, 1.40),
    "synth":             (-0.05,  0.70,  0.22,  0.70, 1.45),
    "woodwinds":         ( 0.55,  0.48,  0.10,  0.40, 1.30),
    "fx":                ( 0.50,  0.65, -0.18, -0.40, 1.40),
    "crash":             ( 0.65,  0.35, -0.10,  0.30, 1.35),
    "cymbal":            ( 0.68,  0.18,  0.05,  0.40, 1.35),
    "ride":              ( 0.70,  0.02,  0.00,  0.60, 1.35),
    "hihat open":        ( 0.70, -0.25,  0.14,  0.25, 1.35),
    "hihat":             ( 0.65, -0.48,  0.16,  0.35, 1.35),
    "hihat closed":      ( 0.55, -0.68,  0.18,  0.40, 1.35),
    "other":             (-0.40,  0.10,  0.00, -0.15, 1.30),
}

# Segment-to-segment closest points distance
def seg_seg_dist(p1, p2, p3, p4):
    d1 = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = (p4[0] - p3[0], p4[1] - p3[1])
    r = (p1[0] - p3[0], p1[1] - p3[1])
    a = d1[0]*d1[0] + d1[1]*d1[1]
    e = d2[0]*d2[0] + d2[1]*d2[1]
    f = d2[0]*r[0] + d2[1]*r[1]

    if a <= 1e-6 and e <= 1e-6:
        return math.hypot(r[0], r[1]), p1, p3
    if a <= 1e-6:
        s = 0.0
        t = max(0.0, min(1.0, f / e))
    else:
        c = d1[0]*r[0] + d1[1]*r[1]
        if e <= 1e-6:
            t = 0.0
            s = max(0.0, min(1.0, -c / a))
        else:
            b = d1[0]*d2[0] + d1[1]*d2[1]
            denom = a*e - b*b
            if denom != 0.0:
                s = max(0.0, min(1.0, (b*f - c*e) / denom))
            else:
                s = 0.0
            t = (b*s + f) / e
            if t < 0.0:
                t = 0.0
                s = max(0.0, min(1.0, -c / a))
            elif t > 1.0:
                t = 1.0
                s = max(0.0, min(1.0, (b - c) / a))

    c1 = (p1[0] + d1[0]*s, p1[1] + d1[1]*s)
    c2 = (p3[0] + d2[0]*t, p3[1] + d2[1]*t)
    return math.hypot(c2[0] - c1[0], c2[1] - c1[1]), c1, c2

def test_true_segment_clearance(gap_px=45.0):
    active = [c for c in prio_list if c in real_counts]
    if "other" in real_counts and "other" not in active:
        active.append("other")
    K = len(active)

    capsules = {}
    for c in active:
        P, T, Z, angle, base_stretch = acoustic_continuum.get(c, (0,0,0,0,1.35))
        cnt = real_counts[c]
        rLabel = 155.0 + (cnt ** 0.35) * 24.0
        rPack = 14.65 * math.sqrt(cnt)
        baseR = max(rLabel, rPack)
        capsules[c] = {
            "cat": c, "count": cnt, "baseR": baseR, "base_stretch": base_stretch,
            "P": P, "T": T, "Z": Z, "angle": angle, "pos": [0.0, 0.0]
        }

    GRID_W, GRID_H = 120, 75
    cx, cy = GRID_W * 0.5, GRID_H * 0.5
    a, b = cx * 1.10, cy * 0.90
    domain_grid_area = math.pi * a * b

    min_P = min(capsules[c]["P"] for c in active)
    max_P = max(capsules[c]["P"] for c in active)
    min_T = min(capsules[c]["T"] for c in active)
    max_T = max(capsules[c]["T"] for c in active)
    mid_P = (min_P + max_P) * 0.5
    mid_T = (min_T + max_T) * 0.5
    span_P = max(0.60, max_P - min_P)
    span_T = max(0.60, max_T - min_T)

    seeds = []
    for c in active:
        P, T = capsules[c]["P"], capsules[c]["T"]
        norm_P = (P - mid_P) / (span_P * 0.5)
        norm_T = (T - mid_T) / (span_T * 0.5)
        angle = math.atan2(norm_P, norm_T)
        raw_r = math.hypot(norm_T, norm_P)
        dist = min(0.70, (raw_r ** 0.80) * 0.56)

        ax = math.cos(angle) * dist
        ay = math.sin(angle) * dist
        gx = (ax + 1.0) * 0.5 * GRID_W
        gy = (ay + 1.0) * 0.5 * GRID_H
        # Power diagram weight: area equivalent
        w = (capsules[c]["baseR"] * 1.10) ** 1.85
        seeds.append({ "cat": c, "x": gx, "y": gy, "w": w })

    for _ in range(4):
        sum_x = [0.0] * K
        sum_y = [0.0] * K
        cell_count = [0] * K

        for gy in range(GRID_H):
            dy_norm = (gy - cy) / b
            for gx in range(GRID_W):
                dx_norm = (gx - cx) / a
                if dx_norm * dx_norm + dy_norm * dy_norm > 1.0:
                    continue

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

    total_cluster_area = sum(math.pi * (capsules[c]["baseR"] * 1.10)**2 for c in active)
    cell_size = math.sqrt((total_cluster_area / 0.74) / domain_grid_area)

    for s in seeds:
        c = s["cat"]
        capsules[c]["pos"] = [(s["x"] - cx) * cell_size, (s["y"] - cy) * cell_size]

    max_d = max(math.hypot(capsules[c]["pos"][0], capsules[c]["pos"][1]) for c in active)
    for c in active:
        cpos = capsules[c]["pos"]
        d_norm = min(1.0, math.hypot(cpos[0], cpos[1]) / max(1.0, max_d))
        base_s = capsules[c]["base_stretch"]
        active_stretch = 1.05 + (base_s - 1.05) * (d_norm ** 1.2)
        width_ratio = 0.95 - 0.53 * (d_norm ** 1.2)
        local_bend = 0.32 * (d_norm ** 1.3)

        perim_angle = math.atan2(cpos[1], cpos[0])
        tangent_angle = perim_angle + math.pi * 0.5
        anc_angle = capsules[c]["angle"]
        if d_norm > 0.15:
            blend_t = min(1.0, (d_norm - 0.15) / 0.65)
            diff = tangent_angle - anc_angle
            while diff > math.pi: diff -= 2 * math.pi
            while diff < -math.pi: diff += 2 * math.pi
            spine_angle = anc_angle + diff * blend_t
        else:
            spine_angle = anc_angle

        maxA = capsules[c]["baseR"] * math.sqrt(active_stretch)
        capR = maxA * width_ratio
        spineL = max(0.0, maxA - capR)

        cosT = math.cos(spine_angle)
        sinT = math.sin(spine_angle)
        cosIn = -sinT
        sinIn = cosT
        if cosIn * (-cpos[0]) + sinIn * (-cpos[1]) < 0.0:
            cosIn = -cosIn
            sinIn = -sinIn

        normU = spineL / max(1.0, maxA)
        bend_offset = (normU * normU) * (maxA * local_bend)

        # 2 spine segments for boomerang: from center to tip1, and from center to tip2
        p_center = (cpos[0], cpos[1])
        p_tip1 = (cpos[0] + spineL * cosT + bend_offset * cosIn, cpos[1] + spineL * sinT + bend_offset * sinIn)
        p_tip2 = (cpos[0] - spineL * cosT + bend_offset * cosIn, cpos[1] - spineL * sinT + bend_offset * sinIn)

        capsules[c]["maxA"] = maxA
        capsules[c]["capR"] = capR
        capsules[c]["spineL"] = spineL
        capsules[c]["spine_angle"] = spine_angle
        capsules[c]["cosT"] = cosT
        capsules[c]["sinT"] = sinT
        capsules[c]["cosIn"] = cosIn
        capsules[c]["sinIn"] = sinIn
        capsules[c]["p_center"] = p_center
        capsules[c]["p_tip1"] = p_tip1
        capsules[c]["p_tip2"] = p_tip2
        capsules[c]["boundingR"] = maxA + capR

    # Distance between two 2-segment boomerangs
    def boomerang_boomerang_dist(c1, c2):
        # 4 segment pairs: (c1.tip1, c1.center) vs (c2.tip1, c2.center), etc.
        segs1 = [(c1["p_center"], c1["p_tip1"]), (c1["p_center"], c1["p_tip2"])]
        segs2 = [(c2["p_center"], c2["p_tip1"]), (c2["p_center"], c2["p_tip2"])]
        min_d = float("inf")
        best_pt1, best_pt2 = None, None
        for s1a, s1b in segs1:
            for s2a, s2b in segs2:
                d, pt1, pt2 = seg_seg_dist(s1a, s1b, s2a, s2b)
                if d < min_d:
                    min_d = d
                    best_pt1 = pt1
                    best_pt2 = pt2
        return min_d, best_pt1, best_pt2

    # Layer B Contact Clearance (24 Passes)
    for iter_pass in range(24):
        # Update point coordinates from pos
        for c in active:
            cpos = capsules[c]["pos"]
            spineL = capsules[c]["spineL"]
            cosT, sinT = capsules[c]["cosT"], capsules[c]["sinT"]
            cosIn, sinIn = capsules[c]["cosIn"], capsules[c]["sinIn"]
            maxA = capsules[c]["maxA"]
            normU = spineL / max(1.0, maxA)
            bend_offset = (normU * normU) * (maxA * 0.32 * (min(1.0, math.hypot(cpos[0], cpos[1]) / max(1.0, max_d)) ** 1.3))
            capsules[c]["p_center"] = (cpos[0], cpos[1])
            capsules[c]["p_tip1"] = (cpos[0] + spineL * cosT + bend_offset * cosIn, cpos[1] + spineL * sinT + bend_offset * sinIn)
            capsules[c]["p_tip2"] = (cpos[0] - spineL * cosT + bend_offset * cosIn, cpos[1] - spineL * sinT + bend_offset * sinIn)

        for i in range(K):
            c1 = capsules[active[i]]
            for j in range(i + 1, K):
                c2 = capsules[active[j]]
                dist, pt1, pt2 = boomerang_boomerang_dist(c1, c2)
                min_dist = c1["capR"] + c2["capR"] + gap_px

                if dist < min_dist:
                    overlap = (min_dist - dist) * 0.5
                    if dist > 0.001:
                        nx = (pt2[0] - pt1[0]) / dist
                        ny = (pt2[1] - pt1[1]) / dist
                    else:
                        dx = c2["pos"][0] - c1["pos"][0]
                        dy = c2["pos"][1] - c1["pos"][1]
                        cd = math.hypot(dx, dy)
                        nx, ny = (dx/cd, dy/cd) if cd > 0.001 else (1.0, 0.0)

                    c1["pos"][0] -= nx * overlap
                    c1["pos"][1] -= ny * overlap
                    c2["pos"][0] += nx * overlap
                    c2["pos"][1] += ny * overlap

                # Label clearance
                dx = c2["pos"][0] - c1["pos"][0]
                dy = c2["pos"][1] - c1["pos"][1]
                abs_dx, abs_dy = abs(dx), abs(dy)
                min_lw, min_lh = 150.0, 42.0
                if abs_dx < min_lw and abs_dy < min_lh:
                    push_x = (min_lw - abs_dx) * 0.5
                    push_y = (min_lh - abs_dy) * 0.5
                    sign_x = 1.0 if dx >= 0 else -1.0
                    sign_y = 1.0 if dy >= 0 else -1.0
                    if push_x < push_y * 2.2:
                        c1["pos"][0] -= sign_x * push_x
                        c2["pos"][0] += sign_x * push_x
                    else:
                        c1["pos"][1] -= sign_y * push_y
                        c2["pos"][1] += sign_y * push_y

    mx = sum(capsules[c]["pos"][0] for c in active) / K
    my = sum(capsules[c]["pos"][1] for c in active) / K
    for c in active:
        capsules[c]["pos"][0] -= mx
        capsules[c]["pos"][1] -= my

    # Update final point coordinates
    for c in active:
        cpos = capsules[c]["pos"]
        spineL = capsules[c]["spineL"]
        cosT, sinT = capsules[c]["cosT"], capsules[c]["sinT"]
        cosIn, sinIn = capsules[c]["cosIn"], capsules[c]["sinIn"]
        maxA = capsules[c]["maxA"]
        normU = spineL / max(1.0, maxA)
        bend_offset = (normU * normU) * (maxA * 0.32 * (min(1.0, math.hypot(cpos[0], cpos[1]) / max(1.0, max_d)) ** 1.3))
        capsules[c]["p_center"] = (cpos[0], cpos[1])
        capsules[c]["p_tip1"] = (cpos[0] + spineL * cosT + bend_offset * cosIn, cpos[1] + spineL * sinT + bend_offset * sinIn)
        capsules[c]["p_tip2"] = (cpos[0] - spineL * cosT + bend_offset * cosIn, cpos[1] - spineL * sinT + bend_offset * sinIn)

    # Compute Acceptance Metrics
    min_clearance = float("inf")
    closest_pair = None
    for i in range(K):
        c1 = capsules[active[i]]
        for j in range(i + 1, K):
            c2 = capsules[active[j]]
            dist, _, _ = boomerang_boomerang_dist(c1, c2)
            clr = dist - (c1["capR"] + c2["capR"])
            if clr < min_clearance:
                min_clearance = clr
                closest_pair = (c1["cat"], c2["cat"])

    label_colls = 0
    for i in range(K):
        for j in range(i + 1, K):
            dx = abs(capsules[active[j]]["pos"][0] - capsules[active[i]]["pos"][0])
            dy = abs(capsules[active[j]]["pos"][1] - capsules[active[i]]["pos"][1])
            if dx < 145.0 and dy < 38.0:
                label_colls += 1

    min_x = min(capsules[c]["pos"][0] - capsules[c]["boundingR"] for c in active)
    max_x = max(capsules[c]["pos"][0] + capsules[c]["boundingR"] for c in active)
    min_y = min(capsules[c]["pos"][1] - capsules[c]["boundingR"] for c in active)
    max_y = max(capsules[c]["pos"][1] + capsules[c]["boundingR"] for c in active)
    ar = (max_x - min_x) / max(1.0, max_y - min_y)

    print(f"Min True Edge Clearance: {min_clearance:6.1f} px ({closest_pair[0]} <-> {closest_pair[1]})")
    print(f"Label Collisions        : {label_colls}")
    print(f"Aspect Ratio            : {ar:.2f} : 1")
    
    def pair_stat(a, b):
        c1, c2 = capsules[a], capsules[b]
        cd = math.hypot(c2["pos"][0]-c1["pos"][0], c2["pos"][1]-c1["pos"][1])
        dist, _, _ = boomerang_boomerang_dist(c1, c2)
        clr = dist - (c1["capR"] + c2["capR"])
        print(f"  {a:8s} <-> {b:8s}: CenterDist={cd:6.1f} px | True Edge Clearance={clr:6.1f} px")

    print("\nDistances for Synth & Bass:")
    pair_stat("synth", "strings")
    pair_stat("synth", "brass")
    pair_stat("synth", "guitar")
    pair_stat("bass", "keys")
    pair_stat("bass", "guitar")
    pair_stat("snare", "clap")
    pair_stat("vocal", "ride")

test_true_segment_clearance(gap_px=45.0)
