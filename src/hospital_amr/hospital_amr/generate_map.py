#!/usr/bin/env python3
"""Generate hospital_ward.pgm map — centered at origin."""

import os

# Map parameters
RESOLUTION = 0.05  # meters per pixel
ORIGIN_X = -8.0    # 1m border around hospital (-7..7)
ORIGIN_Y = -6.0    # 1m border around hospital (-5..5)
MAP_WIDTH_M = 16.0
MAP_HEIGHT_M = 12.0

WIDTH = int(MAP_WIDTH_M / RESOLUTION)   # 320
HEIGHT = int(MAP_HEIGHT_M / RESOLUTION)  # 240

def m2px(x, y):
    px = int((x - ORIGIN_X) / RESOLUTION)
    py = int((y - ORIGIN_Y) / RESOLUTION)
    return px, py

def draw_rect(grid, x1, y1, x2, y2, val):
    px1, py1 = m2px(x1, y1)
    px2, py2 = m2px(x2, y2)
    px1, px2 = min(px1, px2), max(px1, px2)
    py1, py2 = min(py1, py2), max(py1, py2)
    for y in range(max(0, py1), min(HEIGHT, py2)):
        for x in range(max(0, px1), min(WIDTH, px2)):
            grid[y][x] = val

grid = [[205 for _ in range(WIDTH)] for _ in range(HEIGHT)]

# Outside boundaries → unknown
draw_rect(grid, -8, -6, 8, -5, 128)
draw_rect(grid, -8,  5, 8,  6, 128)
draw_rect(grid, -8, -6, -7, 6, 128)
draw_rect(grid,  7, -6,  8, 6, 128)

W = 0  # wall color (black)
H = 0.075  # half wall thickness

# Outer walls
draw_rect(grid, -7-H, -5-H, 7+H, -5+H, W)   # south
draw_rect(grid, -7-H,  5-H, 7+H,  5+H, W)   # north
draw_rect(grid, -7-H, -5, -7+H,  5, W)        # west
draw_rect(grid,  7-H, -5,  7+H,  5, W)        # east

# Corridor walls y=-1 (south side)
draw_rect(grid, -7, -1-H, -5.6, -1+H, W)
# gap -5.6 to -4.4 (pharmacy door)
draw_rect(grid, -4.4, -1-H, -3.5, -1+H, W)
draw_rect(grid, -3.5, -1-H, -1.75, -1+H, W)
# gap -1.75 to -0.6 (room 4 door)
draw_rect(grid, -0.6, -1-H, 1.75, -1+H, W)
draw_rect(grid, 1.75, -1-H, 3.5, -1+H, W)
draw_rect(grid, 3.5, -1-H, 7, -1+H, W)

# Corridor walls y=1 (north side)
draw_rect(grid, -7, 1-H, -5.6, 1+H, W)
# gap -5.6 to -4.4 (room 1 door)
draw_rect(grid, -4.4, 1-H, -3.5, 1+H, W)
draw_rect(grid, -3.5, 1-H, -1.75, 1+H, W)
# gap -1.75 to -0.6 (room 2 door)
draw_rect(grid, -0.6, 1-H, 1.75, 1+H, W)
draw_rect(grid, 1.75, 1-H, 3.5, 1+H, W)
# gap 3.5 to 4.7 (room 3 door)
draw_rect(grid, 4.7, 1-H, 7, 1+H, W)

# Room dividers (vertical)
# Upper
draw_rect(grid, -3.5-H, 1, -3.5+H, 5, W)
draw_rect(grid, -1.75-H, 1, -1.75+H, 5, W)
draw_rect(grid, 1.75-H, 1, 1.75+H, 5, W)
draw_rect(grid, 3.5-H, 1, 3.5+H, 5, W)
# Lower
draw_rect(grid, -3.5-H, -5, -3.5+H, -1, W)
draw_rect(grid, -1.75-H, -5, -1.75+H, -1, W)
draw_rect(grid, 1.75-H, -5, 1.75+H, -1, W)
draw_rect(grid, 3.5-H, -5, 3.5+H, -1, W)

# Furniture
draw_rect(grid, -6.25, 3.0, -4.25, 4.0, W)   # bed 01
draw_rect(grid, -1.0,  3.0,  1.0,  4.0, W)   # bed 02
draw_rect(grid,  4.25, 3.0,  6.25, 4.0, W)   # bed 03
draw_rect(grid, -1.0, -4.0,  1.0, -3.0, W)   # bed 04
draw_rect(grid, -6.5, -4.3, -4.0, -3.7, W)   # pharmacy counter
draw_rect(grid,  4.35, -3.4, 6.15, -2.6, W)   # nurse desk
draw_rect(grid, -6.75, 3.25, -6.25, 3.75, W)  # table 01
draw_rect(grid, -1.75, 3.25, -1.25, 3.75, W)  # table 02
draw_rect(grid, 3.55, 3.25, 4.05, 3.75, W)    # table 03

# Write PGM
script_dir = os.path.dirname(os.path.abspath(__file__))
out = os.path.normpath(os.path.join(script_dir, '..', 'maps', 'hospital_ward.pgm'))
with open(out, 'wb') as f:
    f.write(f"P5\n{WIDTH} {HEIGHT}\n255\n".encode())
    for row in reversed(grid):
        f.write(bytes(row))
print(f"Generated {out} ({WIDTH}x{HEIGHT})")
