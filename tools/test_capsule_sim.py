import math, sys, os, json
sys.path.insert(0, ".")
import simulate_library as sim

db_path = os.path.expandvars(r"%APPDATA%\OpenWav\library_index.json")
with open(db_path, "r", encoding="utf-8") as f:
    data = json.load(f)

cat_counts = {}
for item in data.get("items", []):
    chosen = "other"
    for t in item.get("tags", []):
        c = sim.get_canonical_category(t)
        if c != "other":
            chosen = c
            break
    cat_counts[chosen] = cat_counts.get(chosen, 0) + 1

clusters, bb_w, bb_h, ar, _, _, _, _ = sim.run_hybrid_simulation(cat_counts)

print(f"Loaded {len(clusters)} clusters from simulation")

def get_capsule_endpoints(pos, r, stretch, angle):
    # Half-length of capsule major axis
    half_L = r * stretch
    cosA = math.cos(angle)
    sinA = math.sin(angle)
    p1 = (pos[0] - half_L * cosA, pos[1] - half_L * sinA)
    p2 = (pos[0] + half_L * cosA, pos[1] + half_L * sinA)
    return p1, p2

def dist_segment_to_segment(p1, p2, q1, q2):
    # Approximate minimum distance between two line segments
    # Sample 10 points along each segment
    min_d = float("inf")
    for s in range(11):
        t1 = s / 10.0
        ax = p1[0] + (p2[0] - p1[0]) * t1
        ay = p1[1] + (p2[1] - p1[1]) * t1
        for u in range(11):
            t2 = u / 10.0
            bx = q1[0] + (q2[0] - q1[0]) * t2
            by = q1[1] + (q2[1] - q1[1]) * t2
            d = math.hypot(ax - bx, ay - by)
            if d < min_d: min_d = d
    return min_d

anchors = {
    "vocal": (0.05, 0.00, 0.15, 0.00, 1.35),
    "loop": (-0.12, -0.05, 0.05, -0.20, 1.40),
    "clap": (-0.05, -0.25, 0.12, 0.85, 1.35),
    "snare": (0.05, -0.45, 0.05, 0.80, 1.40),
    "strings": (0.12, 0.25, 0.20, 0.30, 1.35),
    "keys": (-0.15, 0.28, 0.12, 0.60, 1.35),
    "snap": (0.15, -0.15, -0.08, 0.70, 1.30),
    "percussion": (-0.25, -0.30, -0.05, 0.35, 1.30),
    "tambourine shaker": (0.50, -0.15, -0.10, -0.25, 1.30),
    "cowbell": (0.30, -0.38, 0.10, 0.20, 1.30),
    "clave/rim": (0.25, -0.55, 0.05, 0.20, 1.35),
    "guitar": (-0.30, 0.45, -0.10, -0.45, 1.35),
    "orchestral": (0.35, 0.40, 0.15, 0.35, 1.35),
    "brass": (0.20, 0.55, -0.05, -0.25, 1.35),
    "bongo/conga": (-0.35, -0.45, -0.05, 0.40, 1.30),
    "tom": (-0.45, -0.65, 0.10, 0.25, 1.35),
    "kick": (-0.68, -0.55, -0.20, -0.30, 1.40),
    "bass": (-0.65, 0.60, -0.22, 0.30, 1.40),
    "synth": (-0.05, 0.70, 0.22, 0.70, 1.45),
    "other": (-0.40, 0.10, 0.00, -0.15, 1.30),
    "oneshot": (-0.40, 0.10, 0.00, -0.15, 1.30),
    "woodwinds": (0.55, 0.48, 0.10, 0.40, 1.30),
    "fx": (0.50, 0.65, -0.18, -0.40, 1.40),
    "crash": (0.65, 0.35, -0.10, 0.30, 1.35),
    "cymbal": (0.68, 0.18, 0.05, 0.40, 1.35),
    "ride": (0.70, 0.02, 0.00, 0.60, 1.35),
    "hihat open": (0.70, -0.25, 0.14, 0.25, 1.35),
    "hihat": (0.65, -0.48, 0.16, 0.35, 1.35),
    "hihat closed": (0.55, -0.68, 0.18, 0.40, 1.35),
}
def test_all_capsules(stretch_mode="v38"):
    min_gap = float("inf")
    worst_pair = None
    
    for i in range(len(clusters)):
        ci = clusters[i]
        tag_i = ci["cat"]
        r_i = ci["r"]
        anc_i = anchors.get(tag_i, (0, 0, 0, 0, 1.35))
        angle_i = anc_i[3]
        
        if stretch_mode == "v38":
            cnt_i = cat_counts.get(tag_i, 100)
            sqrtN = math.sqrt(cnt_i)
            stretch_i = min(1.80, max(1.35, (1.35 + 0.38 * (sqrtN / (sqrtN + 35.0))) * (anc_i[4] / 1.35)))
            cap_r_i = r_i * 0.60
        else: # clean v36
            stretch_i = 1.0 + (anc_i[4] - 1.0) * 0.40 if anc_i[4] > 0.01 else 1.35
            cap_r_i = r_i * 0.66
            
        p1, p2 = get_capsule_endpoints(ci["pos"], r_i, stretch_i, angle_i)
        
        for j in range(i + 1, len(clusters)):
            cj = clusters[j]
            tag_j = cj["cat"]
            r_j = cj["r"]
            anc_j = anchors.get(tag_j, (0, 0, 0, 0, 1.35))
            angle_j = anc_j[3]
            
            if stretch_mode == "v38":
                cnt_j = cat_counts.get(tag_j, 100)
                sqrtN = math.sqrt(cnt_j)
                stretch_j = min(1.80, max(1.35, (1.35 + 0.38 * (sqrtN / (sqrtN + 35.0))) * (anc_j[4] / 1.35)))
                cap_r_j = r_j * 0.60
            else: # clean v36
                stretch_j = 1.0 + (anc_j[4] - 1.0) * 0.40 if anc_j[4] > 0.01 else 1.35
                cap_r_j = r_j * 0.66
                
            q1, q2 = get_capsule_endpoints(cj["pos"], r_j, stretch_j, angle_j)
            
            # Distance between capsule spine segments minus their cap radii
            seg_dist = dist_segment_to_segment(p1, p2, q1, q2)
            gap = seg_dist - (cap_r_i + cap_r_j)
            if gap < min_gap:
                min_gap = gap
                worst_pair = (tag_i, tag_j)
                
    print(f"[{stretch_mode}] Min capsule-to-capsule gap: {min_gap:.1f} px between {worst_pair}")
    return min_gap, worst_pair

test_all_capsules("v38")
test_all_capsules("clean_v36")
