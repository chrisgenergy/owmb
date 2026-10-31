import os, json, math, time, array

# Load data
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
print(f"Loaded and sorted {count} synth items")

rLabel = 155.0 + (count ** 0.35) * 24.0
kAreaPackFactor = 14.65
rPack = kAreaPackFactor * math.sqrt(count)
baseRadius = max(rLabel, rPack)

waistScale = 0.66
baseStretch = 1.35
axisAngle = -0.15 # typical synth angle

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

# Initial placement
pos_x = [0.0] * count
pos_y = [0.0] * count

for rank_i in range(count):
    item = synth_items[rank_i]
    u_norm = rank_i / (count - 1) if count > 1 else 0.5
    
    # 64-bit splitmix hash
    fp_hash = 0
    for ch in item.get("filePath", ""):
        fp_hash = ((31 * fp_hash + ord(ch)) & 0xFFFFFFFF)
    if fp_hash >= 0x80000000:
        fp_hash -= 0x100000000 # 32-bit signed juce String::hashCode
        
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
        
    # Jitter
    h3 = ((fp_hash ^ (rank_i * 2654435761 & 0xFFFFFFFF)) * 1664525 + 1013904223) ^ 0x3c6ef372
    h4 = (h3 * 1664525 + 1013904223) ^ 0xa54ff53a
    jX = (((h3 % 1001) - 500) / 500.0) * 3.5
    jY = (((h4 % 1001) - 500) / 500.0) * 3.5
    
    x_local = x_0 + jX
    y_local = y_0 + jY
    
    # Rotate to 2D
    pos_x[rank_i] = x_local * cosA - y_local * sinA
    pos_y[rank_i] = x_local * sinA + y_local * cosA

print(f"X range: [{min(pos_x):.1f}, {max(pos_x):.1f}], Y range: [{min(pos_y):.1f}, {max(pos_y):.1f}]")

# Let's save a slice to HTML canvas to visualize initial state vs relaxed state
with open("tools/vis_initial.html", "w") as f:
    f.write(f"""<!DOCTYPE html><html><body>
<canvas id="c" width="1600" height="1200" style="background:#111"></canvas>
<script>
const cvs = document.getElementById('c');
const ctx = cvs.getContext('2d');
const cx = 800, cy = 600, scale = 0.25;
const xs = {list(pos_x[::2])};
const ys = {list(pos_y[::2])};
ctx.fillStyle = '#ff00ff';
for (let i = 0; i < xs.length; i++) {{
    ctx.fillRect(cx + xs[i] * scale, cy + ys[i] * scale, 2, 2);
}}
</script></body></html>""")
print("Wrote tools/vis_initial.html")
