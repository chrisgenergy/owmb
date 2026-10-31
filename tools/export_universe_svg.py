import re

with open("tools/vis_organic_universe.html", "r") as f:
    content = f.read()

import ast
m_nodes = re.search(r"const nodes = (\[.*?\]);\nconst centers", content, re.DOTALL)
m_centers = re.search(r"const centers = (\[.*?\]);", content, re.DOTALL)
nodes = ast.literal_eval(m_nodes.group(1))
centers = ast.literal_eval(m_centers.group(1))

min_x = min(n[0] for n in nodes)
max_x = max(n[0] for n in nodes)
min_y = min(n[1] for n in nodes)
max_y = max(n[1] for n in nodes)

bw = max_x - min_x + 200
bh = max_y - min_y + 200

with open("tools/vis_organic_universe.svg", "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="{min_x - 100} {min_y - 100} {bw} {bh}" style="background:#0a0a0d">\n')
    for x, y, col, cat in nodes:
        f.write(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{col}" opacity="0.85"/>\n')
    for cat, pos in centers:
        f.write(f'<rect x="{pos[0]-40:.1f}" y="{pos[1]-12:.1f}" width="80" height="24" rx="4" fill="rgba(0,0,0,0.7)"/>\n')
        f.write(f'<text x="{pos[0]:.1f}" y="{pos[1]+5:.1f}" fill="#ffffff" font-size="16" font-family="sans-serif" font-weight="bold" text-anchor="middle">{cat}</text>\n')
    f.write('</svg>')

print(f"Wrote tools/vis_organic_universe.svg ({len(nodes)} nodes)")
