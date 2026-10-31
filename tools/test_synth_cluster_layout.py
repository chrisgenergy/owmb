import math
import time

def run_intra_cluster_test():
    count = 19000
    print(f"Testing Intra-Cluster Layout for N = {count} nodes...")

    # 1. Dynamic Radius Formula with organic loose packing (eta ~ 0.70)
    rLabel = 155.0 + (count ** 0.35) * 24.0
    kAreaPackFactor = 15.80
    rPack = kAreaPackFactor * math.sqrt(count)
    baseRadius = max(rLabel, rPack)
    print(f"  baseRadius = {baseRadius:.1f} px")

    waistScale = 0.66
    baseStretch = 1.35
    capBoundaryR = baseRadius * waistScale
    maxA = baseRadius * baseStretch
    straightHalfW = max(0.0, maxA - capBoundaryR)
    print(f"  maxA = {maxA:.1f} px, capBoundaryR = {capBoundaryR:.1f} px, straightHalfW = {straightHalfW:.1f} px")

    # Halton sequence for 2D low-discrepancy (base 2 for x, base 3 for y)
    def halton(i, b):
        f, r = 1.0, 0.0
        while i > 0:
            f /= b
            r += f * (i % b)
            i //= b
        return r

    t0 = time.time()
    # Generate Halton points
    # Using area-proportional longitudinal sampling so density is uniform across body and caps:
    # 1. Total capsule area:
    rect_area = 2.0 * straightHalfW * 2.0 * capBoundaryR
    cap_area = math.pi * (capBoundaryR ** 2)
    tot_area = rect_area + cap_area
    left_cap_frac = (0.5 * cap_area) / tot_area
    rect_frac = rect_area / tot_area

    def map_area_to_x(u):
        # u in [0, 1]
        if u < left_cap_frac:
            # in left cap
            f = u / left_cap_frac
            # area of circle segment from left (-R) to dx
            # f = (theta - sin(theta))/pi where theta in [0, pi]
            # Fast approximation for circle segment inverse:
            # f ~ (1 - cos(theta_half)) or Taylor series
            # dx goes from -capBoundaryR to 0
            # f = (1 + dx/R)^1.5 approx
            dx = capBoundaryR * (math.pow(f, 0.65) * 2.0 - 1.0)
            return -straightHalfW + min(0.0, dx)
        elif u < left_cap_frac + rect_frac:
            # in rectangle: uniform
            f = (u - left_cap_frac) / rect_frac
            return -straightHalfW + f * (2.0 * straightHalfW)
        else:
            # in right cap
            f = (u - left_cap_frac - rect_frac) / left_cap_frac
            dx = capBoundaryR * (1.0 - math.pow(1.0 - f, 0.65) * 2.0)
            return straightHalfW + max(0.0, dx)

    halton_pairs = [(halton(i + 1, 2), halton(i + 1, 3) * 2.0 - 1.0) for i in range(count)]
    halton_pairs.sort(key=lambda p: p[0])

    nodes = []
    for rank_i in range(count):
        u_area = halton_pairs[rank_i][0]
        u_y = halton_pairs[rank_i][1]

        x_0 = map_area_to_x(u_area)
        absX = abs(x_0)
        taper = 1.25 - (absX / straightHalfW) * 0.25 if absX <= straightHalfW else 1.0 - min(1.0, (absX - straightHalfW) / capBoundaryR) * 0.25
        localCapR = capBoundaryR * taper
        allowedY = localCapR
        if absX > straightHalfW:
            dx = absX - straightHalfW
            allowedY = math.sqrt(max(0.01, localCapR * localCapR - dx * dx))
        
        # Smooth organic dispersion across full height
        y_0 = u_y * allowedY * 0.92

        nodes.append([x_0, y_0])

    t_gen = time.time() - t0
    print(f"  Point generation took {t_gen*1000:.1f} ms")

    # Intra-cluster repulsion with Sweep-and-Prune
    minNodeDist2D = 24.5
    minNodeDistSq2D = minNodeDist2D * minNodeDist2D

    t_rep_start = time.time()
    for iter_idx in range(28):
        # Sort nodes by X for Sweep-and-Prune
        nodes.sort(key=lambda p: p[0])

        for i in range(count):
            xi, yi = nodes[i][0], nodes[i][1]
            for j in range(i + 1, count):
                xj = nodes[j][0]
                dx = xj - xi
                if dx >= minNodeDist2D:
                    break # Early break!
                dy = nodes[j][1] - yi
                distSq = dx * dx + dy * dy
                if distSq < minNodeDistSq2D and distSq > 0.0001:
                    dist = math.sqrt(distSq)
                    push = (minNodeDist2D - dist) * 0.50
                    nx = dx / dist
                    ny = dy / dist
                    nodes[i][0] -= nx * push
                    nodes[i][1] -= ny * push
                    nodes[j][0] += nx * push
                    nodes[j][1] += ny * push

        # Soft boundary restoring force
        cushionStrength = 0.18 + 0.14 * (iter_idx / 28.0)
        for i in range(count):
            x = nodes[i][0]
            y = nodes[i][1]
            absX = abs(x)
            taper = 1.28 - (absX / straightHalfW) * 0.28 if absX <= straightHalfW else 1.0 - min(1.0, (absX - straightHalfW) / capBoundaryR) * 0.30
            localCapR = capBoundaryR * taper
            if absX <= straightHalfW:
                r = abs(y) / max(0.01, localCapR)
                if r > 0.75:
                    norm = min(2.0, (r - 0.75) / 0.25)
                    excess = (norm ** 3) * localCapR * cushionStrength * 0.40
                    nodes[i][1] = (y - excess) if y > 0 else (y + excess)
            else:
                dx = absX - straightHalfW
                distCap = math.hypot(dx, y)
                r = distCap / max(0.01, localCapR)
                if r > 0.75 and distCap > 0.001:
                    norm = min(2.0, (r - 0.75) / 0.25)
                    excess = (norm ** 3) * localCapR * cushionStrength * 0.40
                    targetDist = max(0.0, distCap - excess)
                    s = targetDist / distCap
                    nodes[i][0] = (straightHalfW + dx * s) if x > 0 else (-straightHalfW - dx * s)
                    nodes[i][1] = y * s

    t_rep = time.time() - t_rep_start
    print(f"  28-iteration Sweep-and-Prune Repulsion took {t_rep*1000:.1f} ms")

    # Evaluate overlap metric
    nodes.sort(key=lambda p: p[0])
    overlaps = 0
    min_dist = float("inf")
    for i in range(count):
        xi, yi = nodes[i][0], nodes[i][1]
        for j in range(i + 1, count):
            dx = nodes[j][0] - xi
            if dx >= minNodeDist2D:
                break
            dy = nodes[j][1] - yi
            d = math.hypot(dx, dy)
            if d < min_dist:
                min_dist = d
            if d < minNodeDist2D - 0.01:
                overlaps += 1

    print(f"  RESULTS:")
    print(f"    Min Node Distance: {min_dist:.2f} px (Target: >= 24.5 px)")
    print(f"    Total Overlaps   : {overlaps} (Target: 0)")
    if overlaps == 0 and min_dist >= 24.0:
        print("    >>> 100% PASS: PERFECT MOSAIC STARFIELD! <<<")
    else:
        print("    >>> FAILED <<<")

if __name__ == "__main__":
    run_intra_cluster_test()
