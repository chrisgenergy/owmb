import re

with open("tools/vis_v37_synth.html", "r") as f:
    content = f.read()
m_x = re.search(r"const xs = (\[.*?\]);", content)
m_y = re.search(r"const ys = (\[.*?\]);", content)
import json
xs = json.loads(m_x.group(1))
ys = json.loads(m_y.group(1))

# Let's inspect a 600x600 region in the right cap
max_x = max(xs)
cap_pts = [(x, y) for x, y in zip(xs, ys) if x > max_x - 700]

min_x = min(p[0] for p in cap_pts)
max_cx = max(p[0] for p in cap_pts)
min_y = min(p[1] for p in cap_pts)
max_y = max(p[1] for p in cap_pts)

w = max_cx - min_x + 60
h = max_y - min_y + 60

with open("tools/v37_cap.svg", "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="700" viewBox="{min_x - 30} {min_y - 30} {w} {h}" style="background:#0a0a0c">\n')
    for x, y in cap_pts:
        f.write(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#e024c3" opacity="0.9"/>\n')
    f.write('</svg>')

print(f"Cap pts: {len(cap_pts)}, SVG written to tools/v37_cap.svg")

