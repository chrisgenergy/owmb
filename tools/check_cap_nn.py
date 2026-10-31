import re, math

with open('tools/v37_cap.svg', 'r') as f:
    content = f.read()
pts = re.findall(r'cx="([0-9\.-]+)" cy="([0-9\.-]+)"', content)
pts = [(float(x), float(y)) for x, y in pts]

nn_dists = []
for i in range(0, len(pts), 5):
    xi, yi = pts[i]
    min_d = 1e9
    for j in range(len(pts)):
        if i == j: continue
        d = math.hypot(pts[j][0] - xi, pts[j][1] - yi)
        if d < min_d: min_d = d
    nn_dists.append(min_d)

print(f'NN distances in cap: min={min(nn_dists):.2f}, median={sorted(nn_dists)[len(nn_dists)//2]:.2f}, max={max(nn_dists):.2f}')

