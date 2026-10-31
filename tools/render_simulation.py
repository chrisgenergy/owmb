import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json, math
import simulate_library as sim

def generate():
    db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
    if not os.path.exists(db_path):
        print("Database not found")
        return
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    counts = {}
    for it in data.get("items", []):
        chosen = "other"
        for t in it.get("tags", []):
            c = sim.get_canonical_category(t)
            if c != "other":
                chosen = c
                break
        counts[chosen] = counts.get(chosen, 0) + 1

    acoustic_continuum = {
        "vocal":             ( 0.05,  0.00),
        "loop":              (-0.12, -0.05),
        "clap":              (-0.05, -0.25),
        "snare":             ( 0.05, -0.45),
        "strings":           ( 0.12,  0.25),
        "keys":              (-0.15,  0.28),
        "snap":              ( 0.15, -0.15),
        "percussion":        (-0.25, -0.30),
        "tambourine shaker": ( 0.50, -0.15),
        "cowbell":           ( 0.30, -0.38),
        "clave/rim":         ( 0.25, -0.55),
        "guitar":            (-0.30,  0.45),
        "orchestral":        ( 0.35,  0.40),
        "brass":             ( 0.20,  0.55),
        "bongo/conga":       (-0.35, -0.45),
        "tom":               (-0.45, -0.65),
        "kick":              (-0.68, -0.55),
        "bass":              (-0.65,  0.60),
        "synth":             (-0.05,  0.70),
        "other":             (-0.40,  0.10),
        "woodwinds":         ( 0.55,  0.48),
        "fx":                ( 0.50,  0.65),
        "crash":             ( 0.65,  0.35),
        "cymbal":            ( 0.68,  0.18),
        "ride":              ( 0.70,  0.02),
        "hihat open":        ( 0.70, -0.25),
        "hihat":             ( 0.65, -0.48),
        "hihat closed":      ( 0.55, -0.68),
    }

    # Hide ghost clusters with < 5 samples
    active = [c for c in acoustic_continuum if counts.get(c, 0) >= 5]
    K = len(active)
    radii = { c: 160.0 + (counts[c] ** 0.35) * 32.0 for c in active }

    active_P = [acoustic_continuum[c][0] for c in active]
    active_T = [acoustic_continuum[c][1] for c in active]
    min_P, max_P = min(active_P), max(active_P)
    min_T, max_T = min(active_T), max(active_T)
    mid_P = (min_P + max_P) * 0.5
    mid_T = (min_T + max_T) * 0.5
    span_P = max(0.60, max_P - min_P)
    span_T = max(0.60, max_T - min_T)

    GRID_W, GRID_H = 120, 75
    cx, cy = GRID_W * 0.5, GRID_H * 0.5
    a, b = cx * 1.06, cy * 0.92
    domain_grid_area = math.pi * a * b

    seeds = []
    for c in active:
        P, T = acoustic_continuum[c]
        norm_P = (P - mid_P) / (span_P * 0.5)
        norm_T = (T - mid_T) / (span_T * 0.5)
        angle = math.atan2(norm_P, norm_T)
        raw_r = math.hypot(norm_T, norm_P)
        # Sub-linear radial compression: tight cohesive galaxy
        dist = min(0.70, (raw_r ** 0.80) * 0.56)

        ax = math.cos(angle) * dist
        ay = math.sin(angle) * dist
        gx = (ax + 1.0) * 0.5 * GRID_W
        gy = (ay + 1.0) * 0.5 * GRID_H
        w = radii[c] ** 0.35
        seeds.append({ "cat": c, "x": gx, "y": gy, "w": w })

    for _ in range(4):
        sum_x = [0.0] * K
        sum_y = [0.0] * K
        cell_count = [0] * K
        for gy in range(GRID_H):
            dy_norm = (gy - cy) / b
            for gx in range(GRID_W):
                dx_norm = (gx - cx) / a
                if dx_norm*dx_norm + dy_norm*dy_norm > 1.0:
                    continue
                best_i = 0
                min_dist = float("inf")
                for i in range(K):
                    d = ((gx - seeds[i]["x"])**2 + (gy - seeds[i]["y"])**2) / seeds[i]["w"]
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

    # Higher packing density: 0.70 instead of 0.55
    total_cluster_area = sum(math.pi * radii[c]**2 for c in active)
    cell_size = math.sqrt((total_cluster_area / 0.70) / domain_grid_area)

    clusters = []
    for s in seeds:
        px = (s["x"] - cx) * cell_size
        py = (s["y"] - cy) * cell_size
        clusters.append({ "cat": s["cat"], "pos": [px, py], "r": radii[s["cat"]] })

    for _ in range(16):
        for i in range(K):
            for j in range(i + 1, K):
                dx = clusters[j]["pos"][0] - clusters[i]["pos"][0]
                dy = clusters[j]["pos"][1] - clusters[i]["pos"][1]
                dist = math.hypot(dx, dy)
                min_radial = clusters[i]["r"] + clusters[j]["r"] + 64.0
                if 0.01 < dist < min_radial:
                    overlap = (min_radial - dist) * 0.5
                    nx, ny = dx / dist, dy / dist
                    clusters[i]["pos"][0] -= nx * overlap
                    clusters[i]["pos"][1] -= ny * overlap
                    clusters[j]["pos"][0] += nx * overlap
                    clusters[j]["pos"][1] += ny * overlap
                abs_dx, abs_dy = abs(dx), abs(dy)
                min_lw, min_lh = 145.0, 38.0
                if abs_dx < min_lw and abs_dy < min_lh:
                    push_x = (min_lw - abs_dx) * 0.5
                    push_y = (min_lh - abs_dy) * 0.5
                    sign_x = 1.0 if dx >= 0 else -1.0
                    sign_y = 1.0 if dy >= 0 else -1.0
                    if push_x < push_y * 2.2:
                        clusters[i]["pos"][0] -= sign_x * push_x
                        clusters[j]["pos"][0] += sign_x * push_x
                    else:
                        clusters[i]["pos"][1] -= sign_y * push_y
                        clusters[j]["pos"][1] += sign_y * push_y

    mx = sum(c["pos"][0] for c in clusters) / K
    my = sum(c["pos"][1] for c in clusters) / K
    for c in clusters:
        c["pos"][0] -= mx
        c["pos"][1] -= my

    min_x = min(c["pos"][0] - c["r"] for c in clusters)
    max_x = max(c["pos"][0] + c["r"] for c in clusters)
    min_y = min(c["pos"][1] - c["r"] for c in clusters)
    max_y = max(c["pos"][1] + c["r"] for c in clusters)
    bb_w = max_x - min_x
    bb_h = max_y - min_y
    ar = bb_w / max(1.0, bb_h)

    cat_colors = {
        "kick": "#ff2d75", "snare": "#00d2ff", "clap": "#bf55ec", "hihat closed": "#ffd200",
        "hihat": "#ffd200", "hihat open": "#ffd200", "tambourine shaker": "#00e676",
        "tom": "#ff7700", "crash": "#00e5ff", "ride": "#00e5ff", "cymbal": "#00e5ff",
        "cowbell": "#aeea00", "bongo/conga": "#795548", "percussion": "#00e676",
        "bass": "#9d4edd", "keys": "#00e5ff", "guitar": "#00e676", "strings": "#ff2a85",
        "brass": "#ff9100", "woodwinds": "#e040fb", "orchestral": "#ff007f",
        "vocal": "#ff3366", "synth": "#d500f9", "fx": "#00e5ff", "loop": "#00e5ff",
        "other": "#90a4ae", "clave/rim": "#00e5ff", "snap": "#bf55ec"
    }

    # Simulate camera framing at margin = 1.18 (instead of 1.30)
    view_pad = 120.0
    vx = min_x - view_pad
    vy = min_y - view_pad
    vw = bb_w + view_pad * 2.0
    vh = bb_h + view_pad * 2.0

    svg_elements = []
    svg_elements.append(f'<line x1="{vx}" y1="0" x2="{vx+vw}" y2="0" stroke="rgba(255,255,255,0.08)" stroke-dasharray="4" />')
    svg_elements.append(f'<line x1="0" y1="{vy}" x2="0" y2="{vy+vh}" stroke="rgba(255,255,255,0.08)" stroke-dasharray="4" />')

    for c in clusters:
        col = cat_colors.get(c["cat"], "#888888")
        px, py = c["pos"][0], -c["pos"][1]
        r = c["r"]
        n_samples = counts.get(c["cat"], 0)
        svg_elements.append(f'''
        <g class="cluster-node" data-cat="{c["cat"]}">
            <ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{r:.1f}" ry="{r*0.7:.1f}" fill="{col}" fill-opacity="0.25" stroke="{col}" stroke-width="2.5" />
            <circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="#ffffff" />
            <text x="{px:.1f}" y="{py - r*0.7 - 10:.1f}" fill="#ffffff" font-size="26" font-weight="bold" font-family="sans-serif" text-anchor="middle" filter="url(#shadow)">{c["cat"]}</text>
            <text x="{px:.1f}" y="{py - r*0.7 + 16:.1f}" fill="rgba(255,255,255,0.7)" font-size="16" font-family="sans-serif" text-anchor="middle">({n_samples:,})</text>
        </g>
        ''')

    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sample Cloud Layout Simulation (Cohesive Compact Disc)</title>
    <style>
        body {{
            background: #0d0f12;
            color: #e0e0e0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #262930;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: flex;
            gap: 24px;
            font-size: 14px;
        }}
        .stat-val {{
            color: #00d2ff;
            font-weight: bold;
        }}
        .canvas-container {{
            background: #090a0d;
            border: 1px solid #1c1f26;
            border-radius: 8px;
            overflow: hidden;
            display: flex;
            justify-content: center;
        }}
        svg {{
            width: 100%;
            height: 720px;
        }}
        .cluster-node:hover ellipse {{
            fill-opacity: 0.45;
            stroke-width: 4;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h2>Sound Map Simulation: Cohesive Compact Galaxy (Proposal v32)</h2>
            <div style="color: #888; font-size: 13px;">70% Packing Density • Sub-linear Radial Compression • 18% Camera Margin • Ghost-Cluster Culling</div>
        </div>
        <div class="stats">
            <div>Categories: <span class="stat-val">{K}</span></div>
            <div>Aspect Ratio: <span class="stat-val">{ar:.2f} : 1</span></div>
            <div>Bounding Box: <span class="stat-val">{bb_w:.0f} × {bb_h:.0f} px</span></div>
        </div>
    </div>
    <div class="canvas-container">
        <svg viewBox="{vx:.1f} {vy:.1f} {vw:.1f} {vh:.1f}">
            <defs>
                <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000000" flood-opacity="0.9" />
                </filter>
            </defs>
            {''.join(svg_elements)}
        </svg>
    </div>
</body>
</html>'''

    out_path = r"C:\Users\Christian\.gemini\antigravity\brain\f16d854a-fa94-47aa-87d4-a1955f81bb35\sound_map_simulation_visual.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated visual simulation: {out_path}")
    print(f"AR: {ar:.2f}, Bounding Box: {bb_w:.1f} x {bb_h:.1f}")

if __name__ == "__main__":
    generate()
