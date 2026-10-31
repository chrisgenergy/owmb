import os, json, math, time

# Let's run the exact simulation with 28 iterations of relaxation on synth items
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

synth_items.sort(key=lambda it: (
    it.get("highFreqRatio", 0.0) * 0.45 + it.get("zcr", 0.0) * 2.2,
    it.get("filePath", "")
))

count = len(synth_items)
print(f"Items: {count}")

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

capR = capBoundaryR * 1.06
aRect = 4.0 * straightHalfW * capR
aCap = 0.5 * math.pi * capR * capR
aTotal = max(1.0, aRect + 2.0 * aCap)
fLeft = aCap / aTotal
fRect = aRect / aTotal
fRight = fLeft

def get_taper_at(x_local):
    absX = abs(x_local)
    if absX <= straightHalfW:
        norm = (absX / straightHalfW) if straightHalfW > 0.001 else 0.0
        return 1.28 - norm * 0.28
    dx = absX - straightHalfW
    normCap = min(1.0, max(0.0, dx / capBoundaryR)) if capBoundaryR > 0.001 else 1.0
    return 1.0 - normCap * 0.30

def apply_boundary_force(x_local, y_local, strength):
    taper = get_taper_at(x_local)
    localCapR = capBoundaryR * taper
    if localCapR < 0.001: return x_local, y_local
    
    if abs(x_local) <= straightHalfW:
        r = abs(y_local) / localCapR
        if r > 0.75:
            norm = min(1.5, (r - 0.75) / 0.25)
            excess = (norm ** 3) * localCapR * strength * 0.35
            y_local = (y_local - excess) if y_local > 0.0 else (y_local + excess)
    else:
        dx = abs(x_local) - straightHalfW
        distCapSq = dx * dx + y_local * y_local
        distCap = math.sqrt(distCapSq)
        r = distCap / localCapR
        if r > 0.75 and distCap > 0.0001:
            norm = min(1.5, (r - 0.75) / 0.25)
            excess = (norm ** 3) * localCapR * strength * 0.35
            targetDist = max(0.0, distCap - excess)
            s = targetDist / distCap
            dx *= s
            x_local = (straightHalfW + dx) if x_local > 0.0 else (-straightHalfW - dx)
            y_local *= s
    return x_local, y_local

pos2D_x = [0.0] * count
pos2D_y = [0.0] * count
orig2D_x = [0.0] * count
orig2D_y = [0.0] * count

for rank_i in range(count):
    item = synth_items[rank_i]
    u_norm = rank_i / (count - 1) if count > 1 else 0.5
    
    fp_hash = 0
    for ch in item.get("filePath", ""):
        fp_hash = ((31 * fp_hash + ord(ch)) & 0xFFFFFFFF)
    if fp_hash >= 0x80000000:
        fp_hash -= 0x100000000
        
    z = ((rank_i * 2654435761) ^ (fp_hash & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFFFFFFFFFF
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9 & 0xFFFFFFFFFFFFFFFF
    z = (z ^ (z >> 27)) * 0x94d049bb133111eb & 0xFFFFFFFFFFFFFFFF
    z ^= (z >> 31)
    
    u_r = (z & 0xFFFFFF) / 16777215.0
    u_v = (((z >> 24) & 0xFFFFFF) / 16777215.0) * 2.0 - 1.0
    
    decay_ratio = item.get("decayRatio", 0.0)
    decay_u = 0.0
    if decay_ratio > 0.001:
        decay_u = math.tanh((decay_ratio - 0.25) * 2.2) * 0.65
        
    combined_cross = min(1.0, max(-1.0, u_v * 0.75 + decay_u * 0.25))
    sersic_cross = math.copysign(abs(combined_cross) ** 1.10, combined_cross)
    
    if u_norm < fLeft:
        frac = u_norm / max(0.001, fLeft)
        angle = math.pi * 0.5 + frac * math.pi
        rDist = capR * math.sqrt(max(0.01, u_r * 0.92))
        x_0 = -straightHalfW + rDist * math.cos(angle)
        y_0 = rDist * math.sin(angle)
    elif u_norm < fLeft + fRect:
        frac = (u_norm - fLeft) / max(0.001, fRect)
        x_0 = -straightHalfW + frac * (2.0 * straightHalfW)
        taper = get_taper_at(x_0)
        localCapR = capBoundaryR * taper
        y_0 = sersic_cross * localCapR * 0.88
    else:
        frac = (u_norm - fLeft - fRect) / max(0.001, fRight)
        angle = -math.pi * 0.5 + frac * math.pi
        rDist = capR * math.sqrt(max(0.01, u_r * 0.92))
        x_0 = straightHalfW + rDist * math.cos(angle)
        y_0 = rDist * math.sin(angle)
        
    h3 = ((fp_hash ^ (rank_i * 2654435761 & 0xFFFFFFFF)) * 1664525 + 1013904223) ^ 0x3c6ef372
    h4 = (h3 * 1664525 + 1013904223) ^ 0xa54ff53a
    jX = (((h3 % 1001) - 500) / 500.0) * 3.5
    jY = (((h4 % 1001) - 500) / 500.0) * 3.5
    
    x_local = x_0 + jX
    y_local = y_0 + jY
    
    pos2D_x[rank_i] = x_local * cosA - y_local * sinA
    pos2D_y[rank_i] = x_local * sinA + y_local * cosA
    orig2D_x[rank_i] = pos2D_x[rank_i]
    orig2D_y[rank_i] = pos2D_y[rank_i]

indices = list(range(count))
minNodeDist2D = 24.5
minNodeDistSq2D = minNodeDist2D * minNodeDist2D

print("Starting relaxation simulation...")
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
            if dx2 >= minNodeDist2D:
                break
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
        
    if iter < 8:
        springNode = 0.03 * (1.0 - (iter / 8.0))
        for idx in range(count):
            pos2D_x[idx] += (orig2D_x[idx] - pos2D_x[idx]) * springNode
            pos2D_y[idx] += (orig2D_y[idx] - pos2D_y[idx]) * springNode
            
    if iter < 24:
        cushionStrength = 0.18 + 0.14 * (iter / 24.0)
        for idx in range(count):
            relX = pos2D_x[idx]
            relY = pos2D_y[idx]
            x_local = relX * cosA + relY * sinA
            y_local = -relX * sinA + relY * cosA
            x_local, y_local = apply_boundary_force(x_local, y_local, cushionStrength)
            pos2D_x[idx] = x_local * cosA - y_local * sinA
            pos2D_y[idx] = x_local * sinA + y_local * cosA

print(f"Relaxation finished in {time.time() - t0:.1f}s")

# Check collisions
collisions = 0
for i in range(count):
    for j in range(i + 1, count):
        dx = pos2D_x[j] - pos2D_x[i]
        if dx >= minNodeDist2D: break
        dy = pos2D_y[j] - pos2D_y[i]
        if dx * dx + dy * dy < (minNodeDist2D - 0.5) ** 2:
            collisions += 1

print(f"Remaining collisions: {collisions}")

# Output HTML visualizer
with open("tools/vis_relaxed.html", "w") as f:
    f.write(f"""<!DOCTYPE html><html><body>
<h2>Relaxed Synth Cluster ({count} nodes)</h2>
<canvas id="c" width="1800" height="1200" style="background:#111"></canvas>
<script>
const cvs = document.getElementById('c');
const ctx = cvs.getContext('2d');
const cx = 900, cy = 600, scale = 0.28;
const xs = {pos2D_x};
const ys = {pos2D_y};
ctx.fillStyle = '#ff00ff';
for (let i = 0; i < xs.length; i++) {{
    ctx.beginPath();
    ctx.arc(cx + xs[i] * scale, cy + ys[i] * scale, 2.5, 0, Math.PI * 2);
    ctx.fill();
}}
</script></body></html>""")
print("Wrote tools/vis_relaxed.html")

