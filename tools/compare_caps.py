import re, json, math

def inspect_cap(html_file, name):
    with open(html_file, "r") as f:
        content = f.read()
    m_x = re.search(r"const xs = (\[.*?\]);", content)
    m_y = re.search(r"const ys = (\[.*?\]);", content)
    xs = json.loads(m_x.group(1))
    ys = json.loads(m_y.group(1))
    
    max_x = max(xs)
    # Right cap: points with x > max_x - 600
    cap_pts = [(x, y) for x, y in zip(xs, ys) if x > max_x - 600]
    print(f"[{name}] Right cap points: {len(cap_pts)}")
    
    # Generate SVG of right cap
    min_cx = min(p[0] for p in cap_pts)
    max_cx = max(p[0] for p in cap_pts)
    min_cy = min(p[1] for p in cap_pts)
    max_cy = max(p[1] for p in cap_pts)
    
    w = max_cx - min_cx + 40
    h = max_cy - min_cy + 40
    with open(f"tools/cap_{name}.svg", "w") as out:
        out.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="{min_cx - 20} {min_cy - 20} {w} {h}" style="background:#111">\n')
        for x, y in cap_pts:
            out.write(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="#e024c3" opacity="0.85"/>\n')
        out.write('</svg>')
    print(f"Wrote tools/cap_{name}.svg")

inspect_cap("tools/vis_relaxed.html", "original")
inspect_cap("tools/vis_r2_relaxed.html", "r2")

