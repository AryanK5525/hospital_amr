#!/usr/bin/env python3
"""Generate hospital_ward.pgm map matching the SDF world."""

import struct
import os

# Map parameters (must match hospital_ward.yaml)
RESOLUTION = 0.05  # meters per pixel
ORIGIN_X = -1.0
ORIGIN_Y = -1.0
MAP_WIDTH_M = 16.0   # world extends 0..14m + 1m border each side
MAP_HEIGHT_M = 12.0

WIDTH = int(MAP_WIDTH_M / RESOLUTION)   # 320
HEIGHT = int(MAP_HEIGHT_M / RESOLUTION)  # 240

# Convert world coords (meters) to pixel coords
def m2px(x, y):
    px = int((x - ORIGIN_X) / RESOLUTION)
    py = int((y - ORIGIN_Y) / RESOLUTION)
    return px, py

def draw_filled_rect(grid, x1_m, y1_m, x2_m, y2_m, value):
    """Draw a filled rectangle in world coordinates."""
    px1, py1 = m2px(x1_m, y1_m)
    px2, py2 = m2px(x2_m, y2_m)
    px1, px2 = min(px1, px2), max(px1, px2)
    py1, py2 = min(py1, py2), max(py1, py2)
    for y in range(max(0, py1), min(HEIGHT, py2)):
        for x in range(max(0, px1), min(WIDTH, px2)):
            grid[y][x] = value

# Initialize grid: 205 = free space (light gray in PGM)
grid = [[205 for _ in range(WIDTH)] for _ in range(HEIGHT)]

# Mark outside boundaries as unknown (128)
# Everything outside [0,14] x [0,10] is unknown
draw_filled_rect(grid, -1.0, -1.0, 16.0, 0.0, 128)   # below south wall
draw_filled_rect(grid, -1.0, 10.0, 16.0, 12.0, 128)   # above north wall
draw_filled_rect(grid, -1.0, -1.0, 0.0, 12.0, 128)    # left of west wall
draw_filled_rect(grid, 14.0, -1.0, 16.0, 12.0, 128)   # right of east wall

WALL = 0  # black = occupied
THICK = 0.15  # wall thickness

# Outer walls
draw_filled_rect(grid, 0 - THICK/2, 0 - THICK/2, 14 + THICK/2, 0 + THICK/2, WALL)   # south
draw_filled_rect(grid, 0 - THICK/2, 10 - THICK/2, 14 + THICK/2, 10 + THICK/2, WALL)  # north
draw_filled_rect(grid, 0 - THICK/2, 0, 0 + THICK/2, 10, WALL)                         # west
draw_filled_rect(grid, 14 - THICK/2, 0, 14 + THICK/2, 10, WALL)                       # east

# Corridor walls at y=4 (south side of corridor)
H = THICK / 2
# Segments with gaps for doors
# Segment 1: x=0 to x=1.4
draw_filled_rect(grid, 0, 4-H, 1.4, 4+H, WALL)
# GAP: 1.4 to 2.6 (pharmacy door)
# Segment 2: x=2.6 to x=3.5
draw_filled_rect(grid, 2.6, 4-H, 3.5, 4+H, WALL)
# Segment 3: x=3.5 to x=5.25
draw_filled_rect(grid, 3.5, 4-H, 5.25, 4+H, WALL)
# GAP: 5.25 to 6.4 (room 4 door)
# Segment 4: x=6.4 to x=8.75
draw_filled_rect(grid, 6.4, 4-H, 8.75, 4+H, WALL)
# Segment 5: x=8.75 to x=10.5
draw_filled_rect(grid, 8.75, 4-H, 10.5, 4+H, WALL)
# Segment 6: x=10.5 to x=14
draw_filled_rect(grid, 10.5, 4-H, 14, 4+H, WALL)

# Corridor walls at y=6 (north side of corridor)
draw_filled_rect(grid, 0, 6-H, 1.4, 6+H, WALL)
# GAP: 1.4 to 2.6 (room 1 door)
draw_filled_rect(grid, 2.6, 6-H, 3.5, 6+H, WALL)
draw_filled_rect(grid, 3.5, 6-H, 5.25, 6+H, WALL)
# GAP: 5.25 to 6.4 (room 2 door)
draw_filled_rect(grid, 6.4, 6-H, 8.75, 6+H, WALL)
draw_filled_rect(grid, 8.75, 6-H, 10.5, 6+H, WALL)
# GAP: 10.5 to 11.7 (room 3 door)
draw_filled_rect(grid, 11.7, 6-H, 14, 6+H, WALL)

# Room divider walls (vertical)
# Upper rooms
draw_filled_rect(grid, 3.5-H, 6, 3.5+H, 10, WALL)    # between room1 area
draw_filled_rect(grid, 5.25-H, 6, 5.25+H, 10, WALL)   # room1/room2
draw_filled_rect(grid, 8.75-H, 6, 8.75+H, 10, WALL)   # room2/room3
draw_filled_rect(grid, 10.5-H, 6, 10.5+H, 10, WALL)   # room3 left

# Lower rooms
draw_filled_rect(grid, 3.5-H, 0, 3.5+H, 4, WALL)      # pharmacy right
draw_filled_rect(grid, 5.25-H, 0, 5.25+H, 4, WALL)     # room4 left
draw_filled_rect(grid, 8.75-H, 0, 8.75+H, 4, WALL)     # room4 right
draw_filled_rect(grid, 10.5-H, 0, 10.5+H, 4, WALL)     # nurse station left

# Furniture as obstacles (slightly inflated)
# Beds (simplified as rectangles)
draw_filled_rect(grid, 0.75, 8.0, 2.75, 9.0, WALL)   # bed_01
draw_filled_rect(grid, 6.0, 8.0, 8.0, 9.0, WALL)     # bed_02
draw_filled_rect(grid, 11.25, 8.0, 13.25, 9.0, WALL)  # bed_03
draw_filled_rect(grid, 6.0, 1.0, 8.0, 2.0, WALL)     # bed_04

# Pharmacy counter
draw_filled_rect(grid, 0.5, 0.7, 3.0, 1.3, WALL)

# Nurse desk
draw_filled_rect(grid, 11.35, 1.6, 13.15, 2.4, WALL)

# Bedside tables
draw_filled_rect(grid, 0.25, 8.25, 0.75, 8.75, WALL)  # table 01
draw_filled_rect(grid, 5.25, 8.25, 5.75, 8.75, WALL)  # table 02
draw_filled_rect(grid, 10.55, 8.25, 11.05, 8.75, WALL) # table 03

# Write PGM file
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, '..', 'maps', 'hospital_ward.pgm')
output_path = os.path.normpath(output_path)

with open(output_path, 'wb') as f:
    header = f"P5\n{WIDTH} {HEIGHT}\n255\n"
    f.write(header.encode())
    # PGM stores top row first; our grid[0] = bottom of map (low y)
    # So we need to flip vertically
    for row in reversed(grid):
        f.write(bytes(row))

print(f"Generated {output_path}")
print(f"  Size: {WIDTH}x{HEIGHT} pixels")
print(f"  Resolution: {RESOLUTION} m/px")
print(f"  Origin: ({ORIGIN_X}, {ORIGIN_Y})")

