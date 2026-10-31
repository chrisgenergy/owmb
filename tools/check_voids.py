import re

def count_voids(svg_path):
    with open(svg_path, "r") as f:
        content = f.read()
    pts = re.findall(r'cx="([\d\.-]+)" cy="([\d\.-]+)"', content)
    pts = [(float(x), float(y)) for x, y in pts]
    
    # Grid occupancy
    min_x = min(p[0] for p in pts)
    max_x = max(p[0] for p in pts)
    min_y = min(p[1] for p in pts)
    max_y = max(p[1] for p in pts)
    
    # Check for empty 50x50 cells in the interior
    cell_size = 40.0
    cols = int((max_x - min_x) / cell_size) + 1
    rows = int((max_y - min_y) / cell_size) + 1
    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    
    for x, y in pts:
        c = int((x - min_x) / cell_size)
        r = int((y - min_y) / cell_size)
        if 0 <= r < rows and 0 <= c < cols:
            grid[r][c] += 1
            
    # Find interior cells (having non-empty neighbors on all 4 sides) that are completely empty
    interior_empty = 0
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] == 0:
                if grid[r-1][c] > 0 and grid[r+1][c] > 0 and grid[r][c-1] > 0 and grid[r][c+1] > 0:
                    interior_empty += 1
                    
    print(f"[{svg_path}] Interior empty void cells (hollow rooms): {interior_empty}")

count_voids("tools/cap_original.svg")
count_voids("tools/cap_r2.svg")

