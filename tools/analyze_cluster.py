import json, math

with open("tools/simulate_relaxation.py", "r") as f:
    # let's write a script that inspects vis_relaxed.html data
    pass

import re
with open("tools/vis_relaxed.html", "r") as f:
    content = f.read()

m_x = re.search(r"const xs = (\[.*?\]);", content)
m_y = re.search(r"const ys = (\[.*?\]);", content)
xs = json.loads(m_x.group(1))
ys = json.loads(m_y.group(1))

W, H = 2000, 1200
# Canvas bounds
min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)
print(f"X range: [{min_x:.1f}, {max_x:.1f}], Y range: [{min_y:.1f}, {max_y:.1f}]")

# Let's inspect nearest neighbor distance histogram
dists = []
# sample 2000 points
sample_indices = list(range(0, len(xs), 10))
for i in sample_indices:
    xi, yi = xs[i], ys[i]
    min_d = 1e9
    for j in range(len(xs)):
        if i == j: continue
        dx = xs[j] - xi
        if abs(dx) > min_d: continue
        dy = ys[j] - yi
        d = math.hypot(dx, dy)
        if d < min_d:
            min_d = d
    dists.append(min_d)

print(f"NN min dist: min={min(dists):.2f}, median={sorted(dists)[len(dists)//2]:.2f}, max={max(dists):.2f}")

# Let's inspect density variations or stripes
# Let's write an SVG of a zoomed-in section (e.g. 500x500 window) where we see stripes or loops
# Pick a window where there is interesting structure
cx = (min_x + max_x) / 2
cy = (min_y + max_y) / 2

# Let's generate an SVG of the whole cluster and a zoomed-in patch
with open("tools/cluster_view.svg", "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="background:#111">\n')
    scale = 0.28
    ox, oy = W / 2, H / 2
    for x, y in zip(xs, ys):
        px = ox + x * scale
        py = oy + y * scale
        f.write(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2" fill="#e024c3" opacity="0.8"/>\n')
    f.write('</svg>')

print("Wrote tools/cluster_view.svg")

