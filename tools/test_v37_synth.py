import os, json, math, time

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
with open(db_path, "r", encoding="utf-8") as f:
    data = json.load(f)

def get_canonical_category(raw_tag):
    t = raw_tag.strip().lower()
    if t.startswith("#"): t = t[1:]
    if any(k in t for k in ["synth", "lead", "pad", "pluck", "arp"]): return "synth"
    return "other"

synth_items = []
for item in data.get("items", []):
    for t in item.get("tags", []):
        if get_canonical_category(t) == "synth":
            synth_items.append(item)
            break

# Sort by brightness
synth_items.sort(key=lambda it: (
    it.get("highFreqRatio", 0.0) * 0.45 + it.get("zcr", 0.0) * 2.2,
    it.get("filePath", "")
))

count = len(synth_items)
print(f"Loaded {count} synth items")

rLabel = 155.0 + (count ** 0.35) * 24.0
kAreaPackFactor = 14.65
rPack = kAreaPackFactor * math.sqrt(count)
baseRadius = max(rLabel, rPack)

waistScale = 0.66
baseStretch = 1.35
axisAngle = -0.15

cosA = math.cos(axisAngle)
sinA = math.sin(axisAngle)
capBoundaryR = baseRadius * waistScale
maxA = baseRadius * baseStretch
straightHalfW = max(0.0, maxA - capBoundaryR)

# Roberts R2 sequence
phi2 = 1.324717957244746
kPhi2Alpha1 = 1.0 / phi2
kPhi2Alpha2 = 1.0 / (phi2 * phi2)

def get_taper_at(x_local):
    absX = abs(x_local)
    if absX <= straightHalfW:
        norm = (absX / straightHalfW) if straightHalfW > 0.001 else 0.0
        return 1.28 - norm * 0.28
    dx = absX - straightHalfW
    normCap = min(1.0, max(0.0, dx / capBoundaryR)) if capBoundaryR > 0.001 else 1.0
    return 1.0 - normCap * 0.30

# Re-activated crescent spine curve:
maxAllowedBend = maxA * 0.20
T_neg = 0.28
T_pos = 0.28
T_avg = 0.5 * (T_neg * maxAllowedBend + T_pos * maxAllowedBend)
isCrescent = True

def get_spine_y(u):
    yArc = (T_neg * maxAllowedBend * ((-u) ** 1.8)) if u < 0.0 else (T_pos * maxAllowedBend * (u ** 1.8))
    yBow = (-T_avg * 0.28 * math.cos(u * 1.5707963)) if isCrescent else 0.0
    return yArc + yBow

# Generate N candidates
candidates = []
seqK = 1
while len(candidates) < count:
    u1 = (0.5 + seqK * kPhi2Alpha1) % 1.0
    u2 = (0.5 + seqK * kPhi2Alpha2) % 1.0
    seqK += 1
    
    x = -maxA + u1 * (2.0 * maxA)
    taper = get_taper_at(x)
    localCapR = capBoundaryR * taper
    
    absX = abs(x)
    if absX <= straightHalfW:
        y = (u2 * 2.0 - 1.0) * localCapR * 0.90
        candidates.append((x, y))
    else:
        dx = absX - straightHalfW
        maxYSq = localCapR * localCapR - dx * dx
        if maxYSq > 0.0:
            maxY = math.sqrt(maxYSq)
            y = (u2 * 2.0 - 1.0) * maxY * 0.92
            candidates.append((x, y))

# Sort by X
candidates.sort(key=lambda pt: pt[0])

# Map to nodes
pos2D_x = [0.0] * count
pos2D_y = [0.0] * count
orig2D_x = [0.0] * count
orig2D_y = [0.0] * count

for rank_i in range(count):
    item = synth_items[rank_i]
    cand_x, cand_y = candidates[rank_i]
    
    x_local = cand_x
    y_local = cand_y
    
    decay_ratio = item.get("decayRatio", 0.0)
    if decay_ratio > 0.001:
        decay_u = math.tanh((decay_ratio - 0.25) * 2.2) * 0.12
        taper = get_taper_at(x_local)
        y_local += decay_u * (capBoundaryR * taper)
        
    rank_u = min(1.0, max(-1.0, x_local / maxA)) if maxA > 0.001 else 0.0
    y_local += get_spine_y(rank_u)
    
    # Jitter
    fp_hash = 0
    for ch in item.get("filePath", ""):
        fp_hash = ((31 * fp_hash + ord(ch)) & 0xFFFFFFFF)
    if fp_hash >= 0x80000000: fp_hash -= 0x100000000
    h3 = ((fp_hash ^ (rank_i * 2654435761 & 0xFFFFFFFF)) * 1664525 + 1013904223) ^ 0x3c6ef372
    h4 = (h3 * 1664525 + 1013904223) ^ 0xa54ff53a
    jX = (((h3 % 1001) - 500) / 500.0) * 2.5
    jY = (((h4 % 1001) - 500) / 500.0) * 2.5
    x_local += jX
    y_local += jY
    
    pos2D_x[rank_i] = x_local * cosA - y_local * sinA
    pos2D_y[rank_i] = x_local * sinA + y_local * cosA
    orig2D_x[rank_i] = pos2D_x[rank_i]
    orig2D_y[rank_i] = pos2D_y[rank_i]

print("Running 28 iterations of relaxation...")
indices = list(range(count))
minNodeDist2D = 24.5
minNodeDistSq2D = minNodeDist2D * minNodeDist2D
t0 = time.time()

for iter in range(28):
    indices.sort(key=lambda idx: pos2D_x[idx])
    for i in range(count):
        idxA = indices[i]
        posA_x = pos2D_x[idxA]
        posA_y = pos2D_y[idxA]
        for j in range(i + 1, count):
            idxB = indices[j]
            dx2 = pos2D_x[idxB] - posA_x
            if dx2 >= minNodeDist2D: break
            dy2 = pos2D_y[idxB] - posA_y
            distSq2 = dx2 * dx2 + dy2 * dy2
            if distSq2 < minNodeDistSq2D and distSq2 > 0.0001:
                dist = math.sqrt(distSq2)
                push = (minNodeDist2D - dist) * 0.50
                nx = dx2 / dist
                ny = dy2 / dist
                posA_x -= nx * push
                posA_y -= ny * push
                pos2D_x[idxB] += nx * push
                pos2D_y[idxB] += ny * push
        pos2D_x[idxA] = posA_x
        pos2D_y[idxA] = posA_y

print(f"Relaxation done in {time.time() - t0:.1f}s")

# Let's inspect cap samples to confirm NO STRIPES and NO HOLLOW CELLS
max_x = max(pos2D_x)
right_cap_pts = [(x, y) for x, y in zip(pos2D_x, pos2D_y) if x > max_x - 500]
print(f"Right cap has {len(right_cap_pts)} points")

# Write HTML for inspection
with open("tools/vis_v37_synth.html", "w") as f:
    f.write(f"""<!DOCTYPE html><html><body style="background:#0a0a0c; color:#fff; font-family:sans-serif">
<h2>V37 Synth Cluster ({count} samples) - Isotropic Blue-Noise + Crescent Spine</h2>
<canvas id="c" width="1800" height="1200" style="background:#111216; border:1px solid #333"></canvas>
<script>
const cvs = document.getElementById('c');
const ctx = cvs.getContext('2d');
const cx = 900, cy = 600, scale = 0.28;
const xs = {pos2D_x};
const ys = {pos2D_y};
ctx.fillStyle = '#e024c3';
for (let i = 0; i < xs.length; i++) {{
    ctx.beginPath();
    ctx.arc(cx + xs[i] * scale, cy + ys[i] * scale, 2.5, 0, Math.PI * 2);
    ctx.fill();
}}
</script></body></html>""")
print("Wrote tools/vis_v37_synth.html")

