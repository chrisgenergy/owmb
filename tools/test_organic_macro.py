import os, json, math

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
with open(db_path, "r", encoding="utf-8") as f:
    data = json.load(f)

items = data.get("items", [])

def get_canonical_category(raw_tag):
    t = raw_tag.strip().lower()
    if t.startswith("#"): t = t[1:]
    if not t or t == "untagged": return "other"
    if t in ["subkick", "kick"]: return "kick"
    if t == "snare": return "snare"
    if t in ["rimshot", "rim", "clave"]: return "clave/rim"
    if t == "clap": return "clap"
    if t == "snap": return "snap"
    if t in ["closedhat", "closed_hat", "closed-hat"]: return "hihat closed"
    if t in ["openhat", "open_hat", "open-hat"]: return "hihat open"
    if t in ["hihat", "hat"]: return "hihat"
    if t == "tom": return "tom"
    if t in ["crash", "ride", "cymbal"]: return "cymbal"
    if t in ["shaker", "tambourine", "tamb"]: return "tambourine shaker"
    if t == "cowbell": return "cowbell"
    if t in ["conga", "bongo"]: return "bongo/conga"
    if t in ["percussion", "perc", "percloop", "toploop"]: return "percussion"
    if t in ["subbass", "synthbass", "reesebass", "slapbass", "808bass", "bass", "bassloop", "808"]: return "bass"
    if t in ["piano", "rhodes", "organ", "keys", "chord", "chords"]: return "keys"
    if t in ["acousticguitar", "electricguitar", "guitar", "gtr"]: return "guitar"
    if t in ["violin", "viola", "cello", "contrabass", "strings", "string"]: return "strings"
    if t in ["frenchhorn", "trumpet", "trombone", "tuba", "brass", "horn"]: return "brass"
    if t in ["piccolo", "flute", "oboe", "englishhorn", "clarinet", "bassoon", "sax", "woodwinds", "woodwind"]: return "woodwinds"
    if t in ["timpani", "tubularbells", "glockenspiel", "xylophone", "marimba", "bell", "gong", "harp", "ensemble", "orchestral"]: return "orchestral"
    if t in ["acapella", "vocalchop", "chant", "speech", "vocal", "vox", "vocalloop", "choir"]: return "vocal"
    if t in ["lead", "pad", "pluck", "arp", "synth", "melodicloop"]: return "synth"
    if t in ["subdrop", "impact", "riser", "downlifter", "sweep", "glitch", "vinyl", "foley", "atmosphere", "texture", "fx", "sfx"]: return "fx"
    if t in ["drumloop", "loop", "909", "beat", "beats", "drumkit", "kit", "kits", "breakbeat", "groove"]: return "loop"
    return "other"

# Group items
clusters = {}
for it in items:
    cat = "other"
    for t in it.get("tags", []):
        c = get_canonical_category(t)
        if c != "other":
            cat = c
            break
    if cat not in clusters: clusters[cat] = []
    clusters[cat].append(it)

print(f"Total categories: {len(clusters)}")

# Let's run simulate_library to get category centers (tagCenters2D)
import sys
sys.path.insert(0, ".")
import simulate_library as sim
cat_counts = {c: len(itms) for c, itms in clusters.items()}
sim_clusters, bb_w, bb_h, ar, colls, min_gap, max_void, core_gap = sim.run_hybrid_simulation(cat_counts)

centers = {c["cat"]: c["pos"] for c in sim_clusters}
radii = {c["cat"]: c["r"] for c in sim_clusters}
print(f"Computed centers for {len(centers)} clusters")

# Category colors
colors = {
    "vocal": "#ff4d6d", "bass": "#7b2cbf", "keys": "#00b4d8", "guitar": "#2ec4b6",
    "brass": "#ff9f1c", "orchestral": "#e63946", "kick": "#ff007f", "strings": "#e056fd",
    "synth": "#d90429", "snare": "#48cae4", "hihat closed": "#ffd166", "tom": "#f77f00",
    "clap": "#b5179e", "percussion": "#06d6a0", "loop": "#118ab2", "fx": "#00f5d4",
    "cowbell": "#a7c957", "bongo/conga": "#6a994e", "tambourine shaker": "#e9d8a6",
    "clave/rim": "#90e0ef", "hihat open": "#ffea00", "hihat": "#ffd60a", "cymbal": "#38b000",
    "ride": "#0077b6", "crash": "#0096c7", "snap": "#ccff33", "woodwinds": "#52b788", "other": "#888888"
}

# Generate node positions with true organic stretch, crescent spine, and tidal bridges
output_nodes = []
for c in sim_clusters:
    cat = c["cat"]
    cpos = centers[cat]
    base_r = radii[cat]
    itms = clusters.get(cat, [])
    cnt = len(itms)
    if cnt == 0: continue
    
    # Celestial stretch: 1.55x to 1.85x
    stretch = 1.65
    waist = 0.60
    maxA = base_r * stretch
    capR = base_r * waist
    straightHalfW = max(0.0, maxA - capR)
    
    # Affinity neighbors
    aff_partners = []
    if cat == "synth": aff_partners = ["bass", "keys"]
    elif cat == "bass": aff_partners = ["kick", "synth"]
    elif cat == "kick": aff_partners = ["bass", "tom"]
    elif cat == "keys": aff_partners = ["synth", "guitar"]
    elif cat == "strings": aff_partners = ["orchestral", "vocal"]
    elif cat == "orchestral": aff_partners = ["strings", "brass"]
    elif cat == "vocal": aff_partners = ["strings", "loop"]
    
    # Compute primary pull direction
    primary_dir = [0.0, 0.0]
    for p in aff_partners:
        if p in centers:
            dx = centers[p][0] - cpos[0]
            dy = centers[p][1] - cpos[1]
            d = math.hypot(dx, dy)
            if d > 1.0:
                primary_dir[0] += (dx / d)
                primary_dir[1] += (dy / d)
    pd_len = math.hypot(primary_dir[0], primary_dir[1])
    if pd_len > 0.01:
        primary_dir[0] /= pd_len
        primary_dir[1] /= pd_len
        
    axisAngle = math.atan2(primary_dir[1], primary_dir[0]) if pd_len > 0.01 else 0.0
    cosA = math.cos(axisAngle)
    sinA = math.sin(axisAngle)
    
    # Parabolic crescent bow towards primary attractor
    bow_bend = maxA * 0.22
    
    phi2 = 1.324717957244746
    a1, a2 = 1.0 / phi2, 1.0 / (phi2 * phi2)
    
    # Sample nodes (take up to 1500 for fast visual preview of entire universe)
    sample_stride = max(1, cnt // 600)
    sampled_itms = itms[::sample_stride]
    N = len(sampled_itms)
    
    cands = []
    seqK = 1
    while len(cands) < N:
        u1 = (0.5 + seqK * a1) % 1.0
        u2 = (0.5 + seqK * a2) % 1.0
        seqK += 1
        x = -maxA + u1 * (2.0 * maxA)
        absX = abs(x)
        taper = 1.25 - 0.25 * (absX / maxA)
        localR = capR * taper
        if absX <= straightHalfW:
            y = (u2 * 2.0 - 1.0) * localR * 0.90
            cands.append((x, y))
        else:
            dx = absX - straightHalfW
            my_sq = localR * localR - dx * dx
            if my_sq > 0:
                cands.append((x, (u2 * 2.0 - 1.0) * math.sqrt(my_sq) * 0.92))
                
    cands.sort(key=lambda pt: pt[0])
    
    for i, itm in enumerate(sampled_itms):
        cand_x, cand_y = cands[i]
        
        # Parabolic crescent bow: center bows outward by bow_bend
        u = cand_x / maxA
        cand_y += bow_bend * (1.0 - u * u)
        
        # Check secondary tags for tidal reaches
        tags = itm.get("tags", [])
        secondary_pull = [0.0, 0.0]
        for t in tags:
            c_tag = get_canonical_category(t)
            if c_tag != "other" and c_tag != cat and c_tag in centers:
                dx = centers[c_tag][0] - cpos[0]
                dy = centers[c_tag][1] - cpos[1]
                dist = math.hypot(dx, dy)
                gap = max(0.0, dist - base_r - radii[c_tag])
                # Outlier can reach up to 35% of the clearance corridor!
                reach = min(base_r * 0.35, gap * 0.35)
                secondary_pull[0] += (dx / dist) * reach
                secondary_pull[1] += (dy / dist) * reach
                break
                
        # World coordinate
        wx = cpos[0] + (cand_x * cosA - cand_y * sinA) + secondary_pull[0]
        wy = cpos[1] + (cand_x * sinA + cand_y * cosA) + secondary_pull[1]
        
        output_nodes.append((wx, wy, colors.get(cat, "#e024c3"), cat))

print(f"Generated {len(output_nodes)} preview nodes across all clusters")

# Output full map HTML visualizer
with open("tools/vis_organic_universe.html", "w") as f:
    f.write(f"""<!DOCTYPE html><html><body style="background:#0a0a0d; color:#fff; font-family:sans-serif; margin:0; overflow:hidden">
<div style="position:absolute; top:10px; left:10px; z-index:10; background:rgba(0,0,0,0.7); padding:8px 12px; border-radius:6px">
<b>Organic Celestial Universe Preview</b>: Crescent Spines + Inter-Cluster Tidal Outlier Filaments
</div>
<canvas id="c" width="1920" height="1080" style="width:100vw; height:100vh"></canvas>
<script>
const cvs = document.getElementById('c');
const ctx = cvs.getContext('2d');
const w = cvs.width, h = cvs.height;

// Find bounding box
const nodes = {output_nodes};
const centers = {list(centers.items())};

let minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9;
for (const [x, y, col, cat] of nodes) {{
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
}}

const bw = maxX - minX, bh = maxY - minY;
const scale = Math.min((w * 0.85) / bw, (h * 0.85) / bh);
const cx = w / 2, cy = h / 2;
const midX = (minX + maxX) / 2, midY = (minY + maxY) / 2;

function toScreen(x, y) {{
    return [cx + (x - midX) * scale, cy + (y - midY) * scale];
}}

// Draw nodes
for (const [x, y, col, cat] of nodes) {{
    const [sx, sy] = toScreen(x, y);
    ctx.fillStyle = col;
    ctx.beginPath();
    ctx.arc(sx, sy, 2.8, 0, Math.PI * 2);
    ctx.fill();
}}

// Draw category labels
ctx.font = "bold 13px sans-serif";
ctx.textAlign = "center";
for (const [cat, pos] of centers) {{
    const [sx, sy] = toScreen(pos[0], pos[1]);
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.fillRect(sx - 40, sy - 9, 80, 18);
    ctx.fillStyle = "#ffffff";
    ctx.fillText(cat, sx, sy + 4);
}}
</script></body></html>""")

print("Wrote tools/vis_organic_universe.html")
