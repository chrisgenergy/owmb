import math

# Let's test capsule-to-capsule clearance with area preservation vs unconstrained stretch
def test_capsule_clearance():
    # Synth and Bass centers and radii from real simulation
    # Synth: r ~ 2020px, pos ~ (1950, -100)
    # Bass:  r ~ 1600px, pos ~ (900, -1400)
    c_synth = (1950.0, -100.0)
    r_synth = 2020.0
    c_bass  = (900.0, -1400.0)
    r_bass  = 1600.0
    
    dx = c_synth[0] - c_bass[0]
    dy = c_synth[1] - c_bass[1]
    dist = math.hypot(dx, dy)
    print(f"Center distance: {dist:.1f} px")
    print(f"Sum of circular radii: {r_synth + r_bass:.1f} px")
    print(f"Circular gap: {dist - (r_synth + r_bass):.1f} px")
    
    # In v38:
    # Synth stretch = 1.80, maxA = 2020 * 1.80 = 3636 px!
    # Axis angle of synth is ~ 0.70 rad (pointing towards lower-left/bass!)
    angle_synth = 0.70
    # Vector from synth center along its axis towards bass:
    # If the major axis points towards bass:
    reach_synth_axis = r_synth * 1.80 # 3636 px!
    reach_bass_axis = r_bass * 1.40  # 2240 px!
    print(f"v38 Synth maxA: {reach_synth_axis:.1f} px")
    print(f"v38 Bass maxA:  {reach_bass_axis:.1f} px")
    print(f"Overlap along axis: {(reach_synth_axis + reach_bass_axis) - dist:.1f} px (CATASTROPHIC COLLISION!)")

test_capsule_clearance()

