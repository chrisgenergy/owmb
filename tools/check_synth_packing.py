import json, os, math

p = os.path.expandvars(r'%APPDATA%\OpenWav\library_index.json')
data = json.load(open(p, encoding='utf-8'))
synth_items = [it for it in data.get('items', []) if any('synth' in t.lower() or 'lead' in t.lower() or 'pad' in t.lower() for t in it.get('tags', []))]
print(f"Total synth items: {len(synth_items)}")

count = len(synth_items)
base_radius = 155.0 + (count ** 0.35) * 30.0
base_stretch = 1.35
max_a = base_radius * base_stretch
cap_boundary_r = base_radius * 0.66
straight_half_w = max(0.0, max_a - cap_boundary_r)

# Capsule Area
capsule_area = (2.0 * straight_half_w) * (2.0 * cap_boundary_r) + math.pi * (cap_boundary_r ** 2)
# Required area for 'count' dots with minimum distance min_d = 24.5px
min_d = 24.5
dot_packing_area = count * (math.pi * (min_d * 0.5) ** 2) / 0.9069 # Hexagonal close-packing limit

print(f"Cluster Radius: {base_radius:.1f} px")
print(f"Capsule Dimensions: Length = {max_a * 2:.1f} px, Width = {cap_boundary_r * 2:.1f} px")
print(f"Available Capsule Area: {capsule_area:,.0f} px^2")
print(f"Required Area for {count} non-overlapping dots (min_d={min_d}px): {dot_packing_area:,.0f} px^2")
print(f"Area Deficit Ratio: {dot_packing_area / capsule_area:.2f}x (Required / Available)")

