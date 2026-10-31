# Future Feature Proposal: Centroidal Voronoi / Power Tessellation Sound Map Mode

## Overview
This document preserves the architectural specification and mathematical formulation for **Proposal B (Centroidal Voronoi / Power Tessellation)** evaluated during the Sound Map design phase. It is saved here as a blueprint for a future alternative visualization mode in OpenWav (e.g. "Mosaic Mode" or "Tessellation Mode" toggled alongside 2D/3D).

---

## Architectural Principles

1. **Space Partitioning**:
   - Rather than floating organic star clusters in empty cosmic space, the entire 2D canvas is partitioned into contiguous mathematical polygons using Centroidal Voronoi Tessellation (Lloyd's relaxation) or Power Diagrams.
   - Each category receives a Voronoi seed $\vec{S}_i = (x_i, y_i)$ with weight $w_i = R(N_i)^2$.

2. **Area-Proportional Cell Sizing**:
   - The area of cell $V_i$ is constrained to:
     $$\text{Area}(V_i) \propto N_i^{0.35}$$
   - Massive categories (e.g. 19,000 synths) receive large expansive polygonal territories.
   - Tiny categories (e.g. 20 woodwinds) receive small, tight cells nestled between neighbors.

3. **Zero-Area Handling for Missing Categories ($N = 0$)**:
   - When a category has 0 samples, no seed is registered.
   - Neighboring active cells expand mathematically to fill 100% of the canvas area, with zero empty holes.

4. **Sample Embedding Within Cells**:
   - Within each polygonal cell $V_i$, audio samples are distributed using a Lloyd density distribution or Poisson disk sampling, clipped strictly to the cell's convex polygon hull.
   - Boundary walls between cells can be rendered as glowing neon constellation vectors or soft glass edges.

---

## Mode Toggle Concept (Future UI)
- In the Map Overlay toolbar, alongside the `2D` / `3D` toggle button:
  - Mode 1: **Galaxy** (Dynamic 4-Force Celestial Nebula - Active Default)
  - Mode 2: **Mosaic** (Centroidal Voronoi Tessellation - Future Expansion)

