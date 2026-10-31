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

active = [c for c in prio_list if c in real_counts]
if "other" in real_counts and "other" not in active: active.append("other")
tagCount = len(active)

from tools.test_directional_clearance import acoustic_continuum, seg_seg_dist

def getClusterPackedRadius(c):
    cnt = real_counts[c]
    rLabel = 155.0 + (cnt ** 0.35) * 24.0
    rPack = 14.65 * math.sqrt(cnt)
    return max(rLabel, rPack) * 1.10

totalClusterArea = sum(math.pi * getClusterPackedRadius(c)**2 for c in active)
kMacroGridWidth = 120
kMacroGridHeight = 75
cx = kMacroGridWidth * 0.5
cy = kMacroGridHeight * 0.5
a = cx * 1.10
b = cy * 0.90
domainGridArea = math.pi * a * b

minP = min(acoustic_continuum[c][0] for c in active)
maxP = max(acoustic_continuum[c][0] for c in active)
minT = min(acoustic_continuum[c][1] for c in active)
maxT = max(acoustic_continuum[c][1] for c in active)
midP = (minP + maxP) * 0.5
midT = (minT + maxT) * 0.5
spanP = max(0.60, maxP - minP)
spanT = max(0.60, maxT - minT)

kMacroPackDensity = 0.74
cellSize = max(25.0, math.sqrt((totalClusterArea / kMacroPackDensity) / domainGridArea))

seeds = []
for c in active:
    P, T = acoustic_continuum[c][0], acoustic_continuum[c][1]
    normP = (P - midP) / (spanP * 0.5)
    normT = (T - midT) / (spanT * 0.5)
    angle = math.atan2(normP, normT)
    rawR = math.hypot(normT, normP)
    dist = min(0.70, (rawR ** 0.80) * 0.56)
    ax = math.cos(angle) * dist
    ay = math.sin(angle) * dist
    gx = (ax + 1.0) * 0.5 * kMacroGridWidth
    gy = (ay + 1.0) * 0.5 * kMacroGridHeight
    r = getClusterPackedRadius(c)
    weight = r ** 1.85
    seeds.append({"cat": c, "gx": gx, "gy": gy, "weight": weight})

for _ in range(4):
    sumX = [0.0] * len(active)
    sumY = [0.0] * len(active)
    cellCount = [0] * len(active)
    for gy in range(kMacroGridHeight):
        dy_norm = (gy - cy) / b
        for gx in range(kMacroGridWidth):
            dx_norm = (gx - cx) / a
            if dx_norm * dx_norm + dy_norm * dy_norm > 1.0: continue
            bestIdx = 0
            minDist = float("inf")
            for i in range(len(active)):
                dx = gx - seeds[i]["gx"]
                dy = gy - seeds[i]["gy"]
                d = (dx * dx + dy * dy) / max(1.0, seeds[i]["weight"])
                if d < minDist:
                    minDist = d
                    bestIdx = i
            sumX[bestIdx] += gx
            sumY[bestIdx] += gy
            cellCount[bestIdx] += 1
    for i in range(len(active)):
        if cellCount[i] > 0:
            seeds[i]["gx"] = sumX[i] / cellCount[i]
            seeds[i]["gy"] = sumY[i] / cellCount[i]

outClusters = []
for i in range(len(active)):
    c = active[i]
    gridRelX = seeds[i]["gx"] - cx
    gridRelY = seeds[i]["gy"] - cy
    outClusters.append({"tag": c, "count": real_counts[c], "x": gridRelX * cellSize, "y": gridRelY * cellSize})

maxDistFromCenter = 100.0
for i in range(tagCount):
    d = math.hypot(outClusters[i]["x"], outClusters[i]["y"])
    maxDistFromCenter = max(maxDistFromCenter, d)

spineGeoms = []
for i in range(tagCount):
    c = outClusters[i]["tag"]
    anc_pitch, anc_timbre, anc_z, anc_angle, anc_stretch = acoustic_continuum[c]
    rLabel = 155.0 + (outClusters[i]["count"] ** 0.35) * 24.0
    rPack = 14.65 * math.sqrt(outClusters[i]["count"])
    baseRadius = max(rLabel, rPack)

    distFromCenter = math.hypot(outClusters[i]["x"], outClusters[i]["y"])
    distNorm = max(0.0, min(1.0, distFromCenter / maxDistFromCenter))

    baseStretch = anc_stretch if anc_stretch > 0.01 else 1.70
    activeStretch = 1.05 + (baseStretch - 1.05) * (distNorm ** 1.2)
    widthRatio = 0.95 - 0.52 * (distNorm ** 1.2)
    localBend = 0.32 * (distNorm ** 1.3)

    perimAngle = math.atan2(outClusters[i]["y"], outClusters[i]["x"])
    tangentAngle = perimAngle + math.pi * 0.5

    spineAngle = anc_angle
    if distNorm > 0.15:
        blendT = max(0.0, min(1.0, (distNorm - 0.15) / 0.65))
        diff = tangentAngle - anc_angle
        while diff > math.pi: diff -= 2 * math.pi
        while diff < -math.pi: diff += 2 * math.pi
        spineAngle = anc_angle + diff * blendT

    cosT = math.cos(spineAngle)
    sinT = math.sin(spineAngle)
    cosIn = -sinT
    sinIn = cosT
    if cosIn * (-outClusters[i]["x"]) + sinIn * (-outClusters[i]["y"]) < 0.0:
        cosIn = -cosIn
        sinIn = -sinIn

    maxA = baseRadius * math.sqrt(activeStretch)
    capR = maxA * widthRatio
    spineL = max(0.0, maxA - capR)
    normU = spineL / max(1.0, maxA)
    bendOffset = (normU * normU) * (maxA * localBend)

    spineGeoms.append({
        "cosT": cosT, "sinT": sinT, "cosIn": cosIn, "sinIn": sinIn,
        "maxA": maxA, "capR": capR, "spineL": spineL, "localBend": localBend,
        "bendOffset": bendOffset
    })

def bent_boomerang_dist(i, j):
    sg1 = spineGeoms[i]
    c1x, c1y = outClusters[i]["x"], outClusters[i]["y"]
    # Point 0: Center (c1x, c1y)
    # Point 1: Tip 1
    t1_x = c1x + sg1["cosT"] * sg1["spineL"] + sg1["cosIn"] * sg1["bendOffset"]
    t1_y = c1y + sg1["sinT"] * sg1["spineL"] + sg1["sinIn"] * sg1["bendOffset"]
    # Point 2: Tip 2
    t2_x = c1x - sg1["cosT"] * sg1["spineL"] + sg1["cosIn"] * sg1["bendOffset"]
    t2_y = c1y - sg1["sinT"] * sg1["spineL"] + sg1["sinIn"] * sg1["bendOffset"]
    segs1 = [((c1x, c1y), (t1_x, t1_y)), ((c1x, c1y), (t2_x, t2_y))]

    sg2 = spineGeoms[j]
    c2x, c2y = outClusters[j]["x"], outClusters[j]["y"]
    u1_x = c2x + sg2["cosT"] * sg2["spineL"] + sg2["cosIn"] * sg2["bendOffset"]
    u1_y = c2y + sg2["sinT"] * sg2["spineL"] + sg2["sinIn"] * sg2["bendOffset"]
    u2_x = c2x - sg2["cosT"] * sg2["spineL"] + sg2["cosIn"] * sg2["bendOffset"]
    u2_y = c2y - sg2["sinT"] * sg2["spineL"] + sg2["sinIn"] * sg2["bendOffset"]
    segs2 = [((c2x, c2y), (u1_x, u1_y)), ((c2x, c2y), (u2_x, u2_y))]

    min_d = float("inf")
    best_pt1, best_pt2 = None, None
    for s1a, s1b in segs1:
        for s2a, s2b in segs2:
            d, p1, p2 = seg_seg_dist(s1a, s1b, s2a, s2b)
            if d < min_d:
                min_d = d
                best_pt1 = p1
                best_pt2 = p2
    return min_d, best_pt1, best_pt2

kMinInterClusterGapPx = 55.0
kMinLabelWidthPx = 150.0
kMinLabelHeightPx = 42.0

for it in range(24):
    for i in range(tagCount):
        for j in range(i + 1, tagCount):
            dist, pt1, pt2 = bent_boomerang_dist(i, j)
            minClearance = spineGeoms[i]["capR"] + spineGeoms[j]["capR"] + kMinInterClusterGapPx

            if dist < minClearance:
                overlap = (minClearance - dist) * 0.5
                if dist > 0.001:
                    nx = (pt2[0] - pt1[0]) / dist
                    ny = (pt2[1] - pt1[1]) / dist
                else:
                    cdx = outClusters[j]["x"] - outClusters[i]["x"]
                    cdy = outClusters[j]["y"] - outClusters[i]["y"]
                    cd = math.hypot(cdx, cdy)
                    nx = cdx / cd if cd > 0.001 else 1.0
                    ny = cdy / cd if cd > 0.001 else 0.0

                outClusters[i]["x"] -= nx * overlap
                outClusters[i]["y"] -= ny * overlap
                outClusters[j]["x"] += nx * overlap
                outClusters[j]["y"] += ny * overlap

            dx = outClusters[j]["x"] - outClusters[i]["x"]
            dy = outClusters[j]["y"] - outClusters[i]["y"]
            absDx = abs(dx)
            absDy = abs(dy)
            if absDx < kMinLabelWidthPx and absDy < kMinLabelHeightPx:
                pushX = (kMinLabelWidthPx - absDx) * 0.5
                pushY = (kMinLabelHeightPx - absDy) * 0.5
                signX = 1.0 if dx >= 0.0 else -1.0
                signY = 1.0 if dy >= 0.0 else -1.0
                if pushX < pushY * 2.2:
                    outClusters[i]["x"] -= signX * pushX
                    outClusters[j]["x"] += signX * pushX
                else:
                    outClusters[i]["y"] -= signY * pushY
                    outClusters[j]["y"] += signY * pushY

kPhi2Alpha1 = 0.7548776662
kPhi2Alpha2 = 0.5698402910

def generate_stars(tag, c_info, sg):
    count = c_info["count"]
    maxA = sg["maxA"]
    capR = sg["capR"]
    spineL = sg["spineL"]
    cosT, sinT = sg["cosT"], sg["sinT"]
    cosIn, sinIn = sg["cosIn"], sg["sinIn"]
    localBend = sg["localBend"]

    pts = []
    seqK = 1
    while len(pts) < count:
        u1 = (0.5 + seqK * kPhi2Alpha1) % 1.0
        u2 = (0.5 + seqK * kPhi2Alpha2) % 1.0
        seqK += 1
        candX = (u1 * 2.0 - 1.0) * maxA
        candY = (u2 * 2.0 - 1.0) * capR
        projX = max(-spineL, min(spineL, candX))
        dx = candX - projX
        dy = candY
        if dx*dx + dy*dy <= (capR * 0.94)**2:
            normU = candX / maxA
            spineY = (normU * normU) * (maxA * localBend)
            y_local = spineY + candY
            posX = c_info["x"] + candX * cosT + y_local * cosIn
            posY = c_info["y"] + candX * sinT + y_local * sinIn
            pts.append((posX, posY))
    return pts

c_map = {outClusters[i]["tag"]: (outClusters[i], spineGeoms[i]) for i in range(tagCount)}
bass_pts = generate_stars("bass", c_map["bass"][0], c_map["bass"][1])
synth_pts = generate_stars("synth", c_map["synth"][0], c_map["synth"][1])
guitar_pts = generate_stars("guitar", c_map["guitar"][0], c_map["guitar"][1])

def check_pair(nameA, ptsA, nameB, ptsB):
    min_d = float("inf")
    colls = 0
    for pa in ptsA[::10]:
        for pb in ptsB[::20]:
            d = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
            if d < min_d: min_d = d
            if d < 24.5: colls += 1
    print(f"[{nameA} <-> {nameB}] Min Star Dist: {min_d:.1f} px | Collisions: {colls}")

check_pair("bass", bass_pts, "synth", synth_pts)
check_pair("bass", bass_pts, "guitar", guitar_pts)
check_pair("guitar", guitar_pts, "synth", synth_pts)
