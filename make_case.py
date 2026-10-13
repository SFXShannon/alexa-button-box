"""
Alexa 3-button wall box for a NodeMCU ESP-12E (CP2102) + three 12x12 mm tact switches.
Generates base.stl and lid.stl. All dimensions in mm; tweak the parameters below and re-run:
    pip install manifold3d trimesh numpy
    python make_case.py
"""
import math
from manifold3d import Manifold, CrossSection
import trimesh
import numpy as np

# ---------------- parameters ----------------
WALL = 2.4          # side wall thickness
FLOOR = 2.0         # base floor thickness
IN_L, IN_W, IN_H = 80.0, 50.0, 32.0   # inside length, width, height of base

BOARD_L, BOARD_W = 49.0, 26.0   # NodeMCU CP2102 PCB (measure yours! some are 48 x 26)
BOARD_CLEAR = 0.6               # extra room around the PCB
RAIL_H = 14.0                   # board sits this high, leaves room for header pins + dupont plugs
PCB_T = 1.6
USB_GAP = 1.5                   # gap between USB end of board and inside wall
USB_SLOT_W, USB_SLOT_H = 12.0, 8.0

LID_T = 2.4         # lid plate thickness
LIP_H = 3.0         # lip that drops inside the base
LIP_W = 1.6
FIT = 0.3           # clearance between lid lip and base walls (raise if too tight)

BTN = 12.0          # tact switch body
BTN_CLEAR = 0.4
CAP_HOLE = 13.0     # square hole for the cap (fits 12 mm square or round caps)
POCKET_WALL = 1.6
POCKET_DEPTH = 3.8  # switch body height (without stem) ~3.5-3.8
BTN_PITCH = 22.0    # centre-to-centre spacing
SYMBOL_DEPTH = 0.6

KEYHOLE = True      # wall-mount keyholes in the base floor

def box(x, y, z):
    return Manifold.cube([x, y, z])

def cyl(h, r, seg=64):
    return Manifold.cylinder(h, r, r, seg)

# ---------------- base ----------------
OUT_L, OUT_W = IN_L + 2 * WALL, IN_W + 2 * WALL
OUT_H = FLOOR + IN_H

base = box(OUT_L, OUT_W, OUT_H) - box(IN_L, IN_W, IN_H + 1).translate([WALL, WALL, FLOOR])

# board position (USB end against the -X wall)
bx0 = WALL + USB_GAP
by0 = WALL + (IN_W - BOARD_W) / 2
# end supports: only under the short ends so header pins (which run along the long edges) stay clear
for x in (bx0, bx0 + BOARD_L - 4.0):
    base += box(4.0, BOARD_W, RAIL_H).translate([x, by0, FLOOR])
# corner locating fences (rise 2.5 mm above the support so the board can't slide)
fence_h = RAIL_H + 2.5
g = BOARD_CLEAR / 2
for (fx, fy, sx, sy) in [
    (bx0 + BOARD_L - 4.0, by0 - 1.5 - g, 5.5 + g, 1.5),            # far end, -Y side
    (bx0 + BOARD_L - 4.0, by0 + BOARD_W + g, 5.5 + g, 1.5),        # far end, +Y side
    (bx0 + BOARD_L + g, by0 - 1.5 - g, 1.5, BOARD_W + 3 + 2 * g),  # far end stop
    (bx0, by0 - 1.5 - g, 4.0, 1.5),                                # USB end, -Y side
    (bx0, by0 + BOARD_W + g, 4.0, 1.5),                            # USB end, +Y side
]:
    base += box(sx, sy, fence_h).translate([fx, fy, FLOOR])

# USB slot through the -X wall, centred on the micro-USB connector (top side of PCB)
usb_z = FLOOR + RAIL_H + PCB_T + 1.4
base -= box(WALL + 2, USB_SLOT_W, USB_SLOT_H).translate(
    [-1, by0 + BOARD_W / 2 - USB_SLOT_W / 2, usb_z - USB_SLOT_H / 2])

# wall-mount keyholes (screw head 8 mm, shank slot 4 mm)
if KEYHOLE:
    for kx in (OUT_L * 0.25, OUT_L * 0.75):
        # +Y is "up" on the wall: head hole below, narrow slot above it
        ky = OUT_W - WALL - 14
        base -= cyl(FLOOR + 2, 4.0).translate([kx, ky, -1])
        base -= box(4.0, 8.0, FLOOR + 2).translate([kx - 2, ky, -1])
        base -= cyl(FLOOR + 2, 2.0).translate([kx, ky + 8, -1])

# ---------------- lid (modelled upside-down: printed top-face on the bed) ----------------
lid = box(OUT_L, OUT_W, LID_T)
lx0, ly0 = WALL + FIT, WALL + FIT
lip_l, lip_w = IN_L - 2 * FIT, IN_W - 2 * FIT
lip = box(lip_l, lip_w, LIP_H) - box(lip_l - 2 * LIP_W, lip_w - 2 * LIP_W, LIP_H + 1).translate([LIP_W, LIP_W, -0.5])
lid += lip.translate([lx0, ly0, LID_T])

# button centres (in lid coordinates, mirrored later so they line up when flipped)
cy = OUT_W / 2 - 4
centres = [(OUT_L / 2 + (i - 1) * BTN_PITCH, cy) for i in range(3)]
pocket_in = BTN + BTN_CLEAR
pocket_out = pocket_in + 2 * POCKET_WALL
for (x, y) in centres:
    p = box(pocket_out, pocket_out, POCKET_DEPTH) - box(pocket_in, pocket_in, POCKET_DEPTH + 1).translate(
        [POCKET_WALL, POCKET_WALL, -0.5])
    lid += p.translate([x - pocket_out / 2, y - pocket_out / 2, LID_T])
    lid -= box(CAP_HOLE, CAP_HOLE, LID_T + 2).translate([x - CAP_HOLE / 2, y - CAP_HOLE / 2, -1])

# debossed IEC power symbols below each button (on the outside face, z=0 here)
def ring(r_out, r_in, gap_deg=0):
    c = cyl(SYMBOL_DEPTH + 1, r_out) - cyl(SYMBOL_DEPTH + 3, r_in).translate([0, 0, -1])
    if gap_deg:
        w = 2 * r_out * math.sin(math.radians(gap_deg / 2)) + 0.01
        c -= box(w, r_out + 1, SYMBOL_DEPTH + 3).translate([-w / 2, -(r_out + 1), -1])
    return c

def bar(w, h):
    return box(w, h, SYMBOL_DEPTH + 1).translate([-w / 2, -h / 2, 0])

# lid is printed upside down: installed coords are (x, OUT_W - y), so +Y here = down on the wall
sym_dy = CAP_HOLE / 2 + 7.5
symbols = [
    bar(1.6, 8.0),                                            # | = ON
    ring(4.0, 2.6),                                           # O = OFF
    ring(4.0, 2.6, gap_deg=70) + bar(1.6, 5.0).translate([0, -2.8, 0]),  # power symbol = power-cycle
]
for (x, y), s in zip(centres, symbols):
    lid -= s.translate([x, y + sym_dy, -1])

def save(m, path):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    t.export(path)
    print(path, "watertight:", t.is_watertight, "bounds:", np.round(t.bounds, 1).tolist())

save(base, "base.stl")
save(lid, "lid.stl")
