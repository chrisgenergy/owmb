import math, time

# Roberts R2 quasi-random 2D sequence constants:
# The generalized golden ratio for 2D is the root of x^3 = x + 1: phi_2 = 1.324717957244746
# alpha_1 = 1 / phi_2 = 0.7548776662466927
# alpha_2 = 1 / phi_2^2 = 0.5698402909980532

phi2 = 1.324717957244746
a1 = 1.0 / phi2
a2 = 1.0 / (phi2 * phi2)

count = 25748
rLabel = 155.0 + (count ** 0.35) * 24.0
kAreaPackFactor = 14.65
rPack = kAreaPackFactor * math.sqrt(count)
baseRadius = max(rLabel, rPack)

waistScale = 0.66
baseStretch = 1.35
axisAngle = -0.15

capBoundaryR = baseRadius * waistScale
maxA = baseRadius * baseStretch
straightHalfW = max(0.0, maxA - capBoundaryR)

def get_taper_at(x_local):
    absX = abs(x_local)
    if absX <= straightHalfW:
        norm = (absX / straightHalfW) if straightHalfW > 0.001 else 0.0
        return 1.28 - norm * 0.28
    dx = absX - straightHalfW
    normCap = min(1.0, max(0.0, dx / capBoundaryR)) if capBoundaryR > 0.001 else 1.0
    return 1.0 - normCap * 0.30

# Generate N candidates using R2 sequence inside capsule envelope
# Capsule envelope: |x| <= maxA, |y| <= localCapR * sqrt(1 - (dx/capR)^2)
candidates = []
k = 1
while len(candidates) < count:
    # R2 2D coordinates in [0, 1] x [0, 1]
    u1 = (0.5 + k * a1) % 1.0
    u2 = (0.5 + k * a2) % 1.0
    k += 1
    
    # Map u1 to x in [-maxA, maxA]
    x = -maxA + u1 * (2.0 * maxA)
    taper = get_taper_at(x)
    localCapR = capBoundaryR * taper
    
    # Check if inside capsule
    absX = abs(x)
    if absX <= straightHalfW:
        # Central rectangle: y in [-localCapR, localCapR]
        # Map u2 with Sersic-like mild core concentration
        y = (u2 * 2.0 - 1.0) * localCapR * 0.88
        candidates.append((x, y))
    else:
        # Cap: semicircular cap
        dx = absX - straightHalfW
        max_y_sq = localCapR * localCapR - dx * dx
        if max_y_sq > 0:
            max_y = math.sqrt(max_y_sq)
            y = (u2 * 2.0 - 1.0) * max_y * 0.90
            candidates.append((x, y))

print(f"Generated {len(candidates)} candidates in {k} iterations (efficiency: {len(candidates)/k*100:.1f}%)")

# Sort candidates by x coordinate!
candidates.sort(key=lambda pt: pt[0])

# Now candidate i corresponds to acoustic rank i!
# Let's check spacing and distribution
xs = [pt[0] for pt in candidates]
ys = [pt[1] for pt in candidates]

# Run 28 relaxation iterations on this R2 distribution
pos2D_x = list(xs)
pos2D_y = list(ys)
minNodeDist2D = 24.5
minNodeDistSq2D = minNodeDist2D * minNodeDist2D

indices = list(range(count))
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

print(f"R2 Relaxation finished in {time.time() - t0:.1f}s")

# Check remaining collisions
collisions = 0
for i in range(count):
    for j in range(i + 1, count):
        dx = pos2D_x[j] - pos2D_x[i]
        if dx >= minNodeDist2D: break
        dy = pos2D_y[j] - pos2D_y[i]
        if dx * dx + dy * dy < (minNodeDist2D - 0.5) ** 2:
            collisions += 1

print(f"R2 Remaining collisions: {collisions}")

with open("tools/vis_r2_relaxed.html", "w") as f:
    f.write(f"""<!DOCTYPE html><html><body>
<h2>R2 Blue-Noise Relaxed Synth Cluster ({count} nodes)</h2>
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
print("Wrote tools/vis_r2_relaxed.html")

