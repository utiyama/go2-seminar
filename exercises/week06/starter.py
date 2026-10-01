"""week06: Path Planning：グリッド探索. See README.md for the exercise."""
from collections import deque
import json
from pathlib import Path

# 0: free, 1: occupied. Coordinates are (row, column), not world x/y.
grid = [[0, 0, 0, 1, 0], [0, 1, 0, 1, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0]]
start, goal = (0, 0), (3, 4)

def plan(grid, start, goal):
    # TODO: Replace FIFO with a priority queue: g + Manhattan distance to goal.
    queue = deque([start])
    parent = {start: None}
    expanded = 0
    while queue:
        cell = queue.popleft()
        expanded += 1
        if cell == goal:
            path = []
            while cell is not None:
                path.append(cell)
                cell = parent[cell]
            return path[::-1], expanded
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nxt = (cell[0] + dr, cell[1] + dc)
            r, c = nxt
            if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] == 0 and nxt not in parent:
                parent[nxt] = cell
                queue.append(nxt)
    return [], expanded

if __name__ == "__main__":
    path, expanded = plan(grid, start, goal)
    result = {"baseline": "BFS", "path_row_col": path, "expanded": expanded}
    print(result)
    Path("results").mkdir(exist_ok=True)
    Path("results/week06.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
