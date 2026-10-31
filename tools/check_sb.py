import sys, math
sys.path.insert(0, ".")
import tools.test_capsule_sim as tcs

ci = [c for c in tcs.clusters if c['cat'] == 'synth'][0]
cj = [c for c in tcs.clusters if c['cat'] == 'bass'][0]
print("Synth: pos =", ci["pos"], "r =", ci["r"])
print("Bass:  pos =", cj["pos"], "r =", cj["r"])
dist = math.hypot(ci["pos"][0] - cj["pos"][0], ci["pos"][1] - cj["pos"][1])
print(f"Center dist: {dist:.1f} px")
print(f"Sum of radii: {ci['r'] + cj['r']:.1f} px")
print(f"Circular gap: {dist - (ci['r'] + cj['r']):.1f} px")

