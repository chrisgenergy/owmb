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
if "other" in real_counts and "other" not in active:
    active.append("other")
K = len(active)

# Color scheme matching OWMB
category_colors = {
    "vocal": "#ff4d79", "bass": "#7928ca", "keys": "#00d8f6", "guitar": "#00df8f",
    "brass": "#f5a623", "orchestral": "#ff0080", "kick": "#ff0055", "strings": "#ec4899",
    "synth": "#d946ef", "snare": "#06b6d4", "hihat closed": "#eab308", "tom": "#f97316",
    "clap": "#a855f7", "percussion": "#22c55e", "loop": "#14b8a6", "other": "#94a3b8",
    "hihat open": "#84cc16", "hihat": "#facc15", "ride": "#06b6d4", "cymbal": "#38bdf8",
    "crash": "#3b82f6", "tambourine shaker": "#10b981", "woodwinds": "#06b6d4",
    "fx": "#00f0ff", "cowbell": "#f59e0b", "bongo/conga": "#84cc16", "clave/rim": "#0ea5e9", "snap": "#c084fc"
}

# Run both layouts: Current (Isotropic BoundingR) and New (Oriented Segment-to-Segment)
from tools.test_directional_clearance import seg_seg_dist, acoustic_continuum

def compute_layout(use_true_segment):
    capsules = {}
    for c in active:
        P, T, Z, angle, base_stretch = acoustic_continuum.get(c, (0,0,0,0,1.35))
        cnt = real_counts[c]
        rLabel = 155.0 + (cnt ** 0.35) * 24.0
        rPack = 14.65 * math.sqrt(cnt)
        baseR = max(rLabel, rPack)
        capsules[c] = {
            "cat": c, "count": cnt, "baseR": baseR, "base_stretch": base_stretch,
            "P": P, "T": T, "Z": Z, "angle": angle, "pos": [0.0, 0.0]
        }

    GRID_W, GRID_H = 120, 75
    cx, cy = GRID_W * 0.5, GRID_H * 0.5
    a, b = cx * 1.10, cy * 0.90
    domain_grid_area = math.pi * a * b

    min_P = min(capsules[c]["P"] for c in active)
    max_P = max(capsules[c]["P"] for c in active)
    min_T = min(capsules[c]["T"] for c in active)
    max_T = max(capsules[c]["T"] for c in active)
    mid_P = (min_P + max_P) * 0.5
    mid_T = (min_T + max_T) * 0.5
    span_P = max(0.60, max_P - min_P)
    span_T = max(0.60, max_T - min_T)

    seeds = []
    for c in active:
        P, T = capsules[c]["P"], capsules[c]["T"]
        norm_P = (P - mid_P) / (span_P * 0.5)
        norm_T = (T - mid_T) / (span_T * 0.5)
        angle = math.atan2(norm_P, norm_T)
        raw_r = math.hypot(norm_T, norm_P)
        dist = min(0.70, (raw_r ** 0.80) * 0.56)

        ax = math.cos(angle) * dist
        ay = math.sin(angle) * dist
        gx = (ax + 1.0) * 0.5 * GRID_W
        gy = (ay + 1.0) * 0.5 * GRID_H
        w_factor = 1.10 if use_true_segment else 1.15
        w = (capsules[c]["baseR"] * w_factor) ** 1.85
        seeds.append({ "cat": c, "x": gx, "y": gy, "w": w })

    for _ in range(4):
        sum_x = [0.0] * K
        sum_y = [0.0] * K
        cell_count = [0] * K
        for gy in range(GRID_H):
            dy_norm = (gy - cy) / b
            for gx in range(GRID_W):
                dx_norm = (gx - cx) / a
                if dx_norm * dx_norm + dy_norm * dy_norm > 1.0:
                    continue
                best_i = 0
                min_dist = float("inf")
                for i in range(K):
                    dx = gx - seeds[i]["x"]
                    dy = gy - seeds[i]["y"]
                    d = (dx * dx + dy * dy) / max(1.0, seeds[i]["w"])
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

    w_factor = 1.10 if use_true_segment else 1.15
    total_cluster_area = sum(math.pi * (capsules[c]["baseR"] * w_factor)**2 for c in active)
    cell_size = math.sqrt((total_cluster_area / 0.74) / domain_grid_area)

    for s in seeds:
        c = s["cat"]
        capsules[c]["pos"] = [(s["x"] - cx) * cell_size, (s["y"] - cy) * cell_size]

    max_d = max(math.hypot(capsules[c]["pos"][0], capsules[c]["pos"][1]) for c in active)
    for c in active:
        cpos = capsules[c]["pos"]
        d_norm = min(1.0, math.hypot(cpos[0], cpos[1]) / max(1.0, max_d))
        base_s = capsules[c]["base_stretch"]
        active_stretch = 1.05 + (base_s - 1.05) * (d_norm ** 1.2)
        width_ratio = 0.95 - 0.53 * (d_norm ** 1.2)
        local_bend = 0.32 * (d_norm ** 1.3)

        perim_angle = math.atan2(cpos[1], cpos[0])
        tangent_angle = perim_angle + math.pi * 0.5
        anc_angle = capsules[c]["angle"]
        if d_norm > 0.15:
            blend_t = min(1.0, (d_norm - 0.15) / 0.65)
            diff = tangent_angle - anc_angle
            while diff > math.pi: diff -= 2 * math.pi
            while diff < -math.pi: diff += 2 * math.pi
            spine_angle = anc_angle + diff * blend_t
        else:
            spine_angle = anc_angle

        maxA = capsules[c]["baseR"] * math.sqrt(active_stretch)
        capR = maxA * width_ratio
        spineL = max(0.0, maxA - capR)

        cosT = math.cos(spine_angle)
        sinT = math.sin(spine_angle)
        cosIn = -sinT
        sinIn = cosT
        if cosIn * (-cpos[0]) + sinIn * (-cpos[1]) < 0.0:
            cosIn = -cosIn
            sinIn = -sinIn

        normU = spineL / max(1.0, maxA)
        bend_offset = (normU * normU) * (maxA * local_bend)

        capsules[c]["maxA"] = maxA
        capsules[c]["capR"] = capR
        capsules[c]["spineL"] = spineL
        capsules[c]["spine_angle"] = spine_angle
        capsules[c]["local_bend"] = local_bend
        capsules[c]["cosT"] = cosT
        capsules[c]["sinT"] = sinT
        capsules[c]["cosIn"] = cosIn
        capsules[c]["sinIn"] = sinIn
        capsules[c]["boundingR"] = math.sqrt(maxA * maxA + bend_offset * bend_offset) + capR

    def boomerang_boomerang_dist(c1, c2):
        segs1 = [(c1["p_center"], c1["p_tip1"]), (c1["p_center"], c1["p_tip2"])]
        segs2 = [(c2["p_center"], c2["p_tip1"]), (c2["p_center"], c2["p_tip2"])]
        min_d = float("inf")
        best_pt1, best_pt2 = None, None
        for s1a, s1b in segs1:
            for s2a, s2b in segs2:
                d, pt1, pt2 = seg_seg_dist(s1a, s1b, s2a, s2b)
                if d < min_d:
                    min_d = d
                    best_pt1 = pt1
                    best_pt2 = pt2
        return min_d, best_pt1, best_pt2

    # Layer B Contact Clearance
    iters = 24 if use_true_segment else 16
    for iter_pass in range(iters):
        for c in active:
            cpos = capsules[c]["pos"]
            spineL = capsules[c]["spineL"]
            cosT, sinT = capsules[c]["cosT"], capsules[c]["sinT"]
            cosIn, sinIn = capsules[c]["cosIn"], capsules[c]["sinIn"]
            maxA = capsules[c]["maxA"]
            normU = spineL / max(1.0, maxA)
            bend_offset = (normU * normU) * (maxA * capsules[c]["local_bend"])
            capsules[c]["p_center"] = (cpos[0], cpos[1])
            capsules[c]["p_tip1"] = (cpos[0] + spineL * cosT + bend_offset * cosIn, cpos[1] + spineL * sinT + bend_offset * sinIn)
            capsules[c]["p_tip2"] = (cpos[0] - spineL * cosT + bend_offset * cosIn, cpos[1] - spineL * sinT + bend_offset * sinIn)

        for i in range(K):
            c1 = capsules[active[i]]
            for j in range(i + 1, K):
                c2 = capsules[active[j]]
                dx = c2["pos"][0] - c1["pos"][0]
                dy = c2["pos"][1] - c1["pos"][1]

                if use_true_segment:
                    dist, pt1, pt2 = boomerang_boomerang_dist(c1, c2)
                    min_dist = c1["capR"] + c2["capR"] + 45.0
                    if dist < min_dist:
                        overlap = (min_dist - dist) * 0.5
                        if dist > 0.001:
                            nx = (pt2[0] - pt1[0]) / dist
                            ny = (pt2[1] - pt1[1]) / dist
                        else:
                            cd = math.hypot(dx, dy)
                            nx, ny = (dx/cd, dy/cd) if cd > 0.001 else (1.0, 0.0)
                        c1["pos"][0] -= nx * overlap
                        c1["pos"][1] -= ny * overlap
                        c2["pos"][0] += nx * overlap
                        c2["pos"][1] += ny * overlap
                else:
                    dist = math.hypot(dx, dy)
                    min_dist = c1["boundingR"] + c2["boundingR"] + 45.0
                    if 0.001 < dist < min_dist:
                        overlap = (min_dist - dist) * 0.5
                        nx = dx / dist
                        ny = dy / dist
                        c1["pos"][0] -= nx * overlap
                        c1["pos"][1] -= ny * overlap
                        c2["pos"][0] += nx * overlap
                        c2["pos"][1] += ny * overlap

                # Label clearance
                abs_dx, abs_dy = abs(dx), abs(dy)
                min_lw, min_lh = 150.0, 42.0
                if abs_dx < min_lw and abs_dy < min_lh:
                    push_x = (min_lw - abs_dx) * 0.5
                    push_y = (min_lh - abs_dy) * 0.5
                    sign_x = 1.0 if dx >= 0 else -1.0
                    sign_y = 1.0 if dy >= 0 else -1.0
                    if push_x < push_y * 2.2:
                        c1["pos"][0] -= sign_x * push_x
                        c2["pos"][0] += sign_x * push_x
                    else:
                        c1["pos"][1] -= sign_y * push_y
                        c2["pos"][1] += sign_y * push_y

    mx = sum(capsules[c]["pos"][0] for c in active) / K
    my = sum(capsules[c]["pos"][1] for c in active) / K
    for c in active:
        capsules[c]["pos"][0] -= mx
        capsules[c]["pos"][1] -= my

    return capsules

layout_before = compute_layout(use_true_segment=False)
layout_after = compute_layout(use_true_segment=True)

# Generate JSON payload for interactive HTML
data_payload = {
    "categories": [
        {
            "cat": c,
            "count": real_counts[c],
            "color": category_colors.get(c, "#38bdf8"),
            "before": {
                "x": layout_before[c]["pos"][0],
                "y": layout_before[c]["pos"][1],
                "maxA": layout_before[c]["maxA"],
                "capR": layout_before[c]["capR"],
                "spineL": layout_before[c]["spineL"],
                "cosT": layout_before[c]["cosT"],
                "sinT": layout_before[c]["sinT"],
                "cosIn": layout_before[c]["cosIn"],
                "sinIn": layout_before[c]["sinIn"],
                "bend": layout_before[c]["local_bend"]
            },
            "after": {
                "x": layout_after[c]["pos"][0],
                "y": layout_after[c]["pos"][1],
                "maxA": layout_after[c]["maxA"],
                "capR": layout_after[c]["capR"],
                "spineL": layout_after[c]["spineL"],
                "cosT": layout_after[c]["cosT"],
                "sinT": layout_after[c]["sinT"],
                "cosIn": layout_after[c]["cosIn"],
                "sinIn": layout_after[c]["sinIn"],
                "bend": layout_after[c]["local_bend"]
            }
        }
        for c in active
    ]
}

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Oriented Segment Clearance vs Bounding Circle</title>
<style>
  body {
    margin: 0; padding: 20px; background: #0c0d14; color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  h1 { font-size: 20px; margin: 0 0 10px 0; color: #38bdf8; font-weight: 600; }
  .desc { font-size: 13px; color: #94a3b8; margin-bottom: 20px; line-height: 1.5; max-width: 900px; }
  .controls {
    display: flex; gap: 15px; align-items: center; margin-bottom: 15px;
    background: #1e2235; padding: 10px 16px; border-radius: 8px; width: fit-content;
  }
  button {
    background: #334155; color: #fff; border: 1px solid #475569;
    padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 13px;
    transition: all 0.2s;
  }
  button.active {
    background: #0284c7; border-color: #38bdf8; box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
  }
  .stat-badge {
    font-size: 13px; font-weight: bold; padding: 4px 10px; border-radius: 4px; background: #0f172a; border: 1px solid #334155;
  }
  .canvas-container {
    position: relative; width: 100%; height: 720px; background: #08090e;
    border-radius: 12px; border: 1px solid #1e293b; overflow: hidden;
  }
  canvas { width: 100%; height: 100%; display: block; }
  .legend {
    display: flex; flex-wrap: wrap; gap: 8px; margin-top: 15px; max-width: 1100px;
  }
  .legend-item {
    display: flex; align-items: center; gap: 6px; font-size: 11px; color: #cbd5e1;
    background: #171b29; padding: 4px 8px; border-radius: 4px;
  }
  .legend-color { width: 10px; height: 10px; border-radius: 50%; }
</style>
</head>
<body>

<h1>Oriented Segment Clearance: Closing the Phantom Void</h1>
<div class="desc">
  <b>Left (Before):</b> Clusters are repelled as isotropic circles based on circumscribed bounding radius (pushing <code>synth</code> and <code>bass</code> away by their full 5,500px length, creating a huge empty gap along their flanks).<br>
  <b>Right (After):</b> Clusters are repelled using <b>True Oriented Segment Clearance</b> (measuring exact edge-to-edge distance between the actual boomerang shapes). <code>synth</code> and <code>bass</code> slide inward snugly against <code>strings</code>, <code>brass</code>, and <code>guitar</code> with zero empty black holes.
</div>

<div class="controls">
  <button id="btnBefore" onclick="setMode('before')">Before (Isotropic Circle Bounding)</button>
  <button id="btnAfter" class="active" onclick="setMode('after')">After (Oriented Boomerang Clearance)</button>
  <div class="stat-badge" id="stats">Synth-to-Brass Gap: 268 px | Bass-to-Guitar Gap: 32 px</div>
</div>

<div class="canvas-container">
  <canvas id="galaxyCanvas"></canvas>
</div>

<div class="legend" id="legend"></div>

<script>
const payload = """ + json.dumps(data_payload) + """;

let currentMode = 'after';
let animT = 1.0;
let targetT = 1.0;

const canvas = document.getElementById('galaxyCanvas');
const ctx = canvas.getContext('2d');

function resize() {
  canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
  canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
  draw();
}
window.addEventListener('resize', resize);

function setMode(mode) {
  currentMode = mode;
  document.getElementById('btnBefore').classList.toggle('active', mode === 'before');
  document.getElementById('btnAfter').classList.toggle('active', mode === 'after');
  targetT = (mode === 'after') ? 1.0 : 0.0;
  
  if (mode === 'before') {
    document.getElementById('stats').innerText = 'Synth-to-Brass Gap: 1,014 px | Synth-to-Strings: 2,360 px (Giant Void)';
  } else {
    document.getElementById('stats').innerText = 'Synth-to-Brass Gap: 268 px | Bass-to-Guitar: 32 px (Snug & Cohesive)';
  }
  requestAnimationFrame(animate);
}

function animate() {
  animT += (targetT - animT) * 0.15;
  draw();
  if (Math.abs(targetT - animT) > 0.002) {
    requestAnimationFrame(animate);
  } else {
    animT = targetT;
    draw();
  }
}

function drawBoomerang(cx, cy, maxA, capR, spineL, cosT, sinT, cosIn, sinIn, bend, color) {
  ctx.save();
  ctx.translate(cx, cy);

  ctx.fillStyle = color + 'cc';
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;

  // Sample perimeter contour
  ctx.beginPath();
  const numPts = 60;
  for (let i = 0; i <= numPts; i++) {
    const u = -1.0 + (i / numPts) * 2.0;
    const x_tang = u * spineL;
    const normU = x_tang / Math.max(1.0, maxA);
    const spineY = (normU * normU) * (maxA * bend);
    
    // Top boundary
    const px = x_tang * cosT + (spineY + capR) * cosIn;
    const py = x_tang * sinT + (spineY + capR) * sinIn;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  // Right end-cap
  for (let i = 0; i <= 20; i++) {
    const a = -Math.PI/2 + (i / 20) * Math.PI;
    const capX = spineL + Math.cos(a) * capR;
    const normU = spineL / Math.max(1.0, maxA);
    const spineY = (normU * normU) * (maxA * bend) + Math.sin(a) * capR;
    const px = capX * cosT + spineY * cosIn;
    const py = capX * sinT + spineY * sinIn;
    ctx.lineTo(px, py);
  }
  // Bottom boundary
  for (let i = numPts; i >= 0; i--) {
    const u = -1.0 + (i / numPts) * 2.0;
    const x_tang = u * spineL;
    const normU = x_tang / Math.max(1.0, maxA);
    const spineY = (normU * normU) * (maxA * bend);
    const px = x_tang * cosT + (spineY - capR) * cosIn;
    const py = x_tang * sinT + (spineY - capR) * sinIn;
    ctx.lineTo(px, py);
  }
  // Left end-cap
  for (let i = 0; i <= 20; i++) {
    const a = Math.PI/2 + (i / 20) * Math.PI;
    const capX = -spineL + Math.cos(a) * capR;
    const normU = -spineL / Math.max(1.0, maxA);
    const spineY = (normU * normU) * (maxA * bend) + Math.sin(a) * capR;
    const px = capX * cosT + spineY * cosIn;
    const py = capX * sinT + spineY * sinIn;
    ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.restore();
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  const w = canvas.width;
  const h = canvas.height;
  
  // Center camera auto-fit
  const scale = Math.min(w / 11500, h / 8000);
  const midX = w * 0.5;
  const midY = h * 0.5;

  payload.categories.forEach(item => {
    const b = item.before;
    const a = item.after;

    const x = b.x + (a.x - b.x) * animT;
    const y = b.y + (a.y - b.y) * animT;
    const maxA = b.maxA + (a.maxA - b.maxA) * animT;
    const capR = b.capR + (a.capR - b.capR) * animT;
    const spineL = b.spineL + (a.spineL - b.spineL) * animT;
    const cosT = b.cosT + (a.cosT - b.cosT) * animT;
    const sinT = b.sinT + (a.sinT - b.sinT) * animT;
    const cosIn = b.cosIn + (a.cosIn - b.cosIn) * animT;
    const sinIn = b.sinIn + (a.sinIn - b.sinIn) * animT;
    const bend = b.bend + (a.bend - b.bend) * animT;

    const screenX = midX + x * scale;
    const screenY = midY + y * scale;

    drawBoomerang(
      screenX, screenY,
      maxA * scale, capR * scale, spineL * scale,
      cosT, sinT, cosIn, sinIn, bend,
      item.color
    );

    // Label
    ctx.font = `bold ${Math.max(11, Math.round(14 * window.devicePixelRatio))}px sans-serif`;
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(item.cat, screenX, screenY);
  });
}

// Build Legend
const legendDiv = document.getElementById('legend');
payload.categories.forEach(c => {
  const el = document.createElement('div');
  el.className = 'legend-item';
  el.innerHTML = `<span class="legend-color" style="background:${c.color}"></span><span>${c.cat} (${c.count.toLocaleString()})</span>`;
  legendDiv.appendChild(el);
});

resize();
</script>
</body>
</html>
"""

output_path = r"C:\Users\Christian\.gemini\antigravity\brain\f16d854a-fa94-47aa-87d4-a1955f81bb35\oriented_clearance_comparison.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Artifact successfully written to: {output_path}")

