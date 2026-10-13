"""
Alexa 5-button wall box for a NodeMCU ESP-12E on a "GPIO 1 into 2" breakout board + five 12x12 mm tact switches.
Top row: plug ON / OFF / power-cycle.  Bottom row: lights ON / OFF.
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
IN_L, IN_W, IN_H = 80.0, 74.0, 40.0   # inside length, width, height of base

# NodeMCU sits plugged into a "GPIO 1 into 2" expansion/breakout board; the case holds the breakout.
BOARD_L, BOARD_W = 63.5, 63.0   # breakout PCB (listed as 6.35 x 6.3 cm) - measure yours
BOARD_CLEAR = 1.0               # extra room on each side of the PCB
POST_H = 7.0                    # board rests on corner pads this high (room for solder pins + keyhole screw heads)
PCB_T = 1.6
END_GAP = 1.0                   # gap between the jack/USB edge of the board and the inside wall
# access window in the -X wall for DC jack / power switch / NodeMCU USB (put that edge of the board here)
WIN_W = 50.0                    # window width along the wall
WIN_BELOW = 0.5                 # window starts this far below the top of the breakout PCB
WIN_ABOVE = 15.0                # and goes this far above it (covers DC jack and the NodeMCU's USB)

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

# board position (jack / USB edge against the -X wall), centred across the width
g = BOARD_CLEAR
bx0 = WALL + END_GAP + g
by0 = WALL + (IN_W - BOARD_W) / 2
PAD = 6.0      # corner pad size under the PCB
FENCE = 1.6    # corner fence thickness
FENCE_UP = 3.0 # fence rises this far above the pad top to locate the board
for cx, sx in ((bx0, -1), (bx0 + BOARD_L, 1)):
    for cy, sy in ((by0, -1), (by0 + BOARD_W, 1)):
        px = cx if sx < 0 else cx - PAD          # pad under the corner
        py = cy if sy < 0 else cy - PAD
        base += box(PAD, PAD, POST_H).translate([px, py, FLOOR])
        fx = cx - g - FENCE if sx < 0 else cx + g  # L-shaped fence just outside the corner
        fy = cy - g - FENCE if sy < 0 else cy + g
        lx = px - (g + FENCE if sx < 0 else 0)
        ly = py - (g + FENCE if sy < 0 else 0)
        base += box(FENCE, PAD + g + FENCE, POST_H + FENCE_UP).translate([fx, ly, FLOOR])
        base += box(PAD + g + FENCE, FENCE, POST_H + FENCE_UP).translate([lx, fy, FLOOR])

# access window through the -X wall for the DC jack, power switch and USB
pcb_top = FLOOR + POST_H + PCB_T
base -= box(WALL + 2, WIN_W, WIN_BELOW + WIN_ABOVE).translate(
    [-1, by0 + BOARD_W / 2 - WIN_W / 2, pcb_top - WIN_BELOW])

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
ROW_PITCH = 30.0
top_y = OUT_W / 2 - ROW_PITCH / 2      # plug row (top on the wall)
bot_y = OUT_W / 2 + ROW_PITCH / 2      # lights row (bottom on the wall)
centres = [(OUT_L / 2 + (i - 1) * BTN_PITCH, top_y) for i in range(3)] + \
          [(OUT_L / 2 + d * BTN_PITCH / 2, bot_y) for d in (-1, 1)]
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

def sun():   # lights ON: dot with 8 rays
    s = cyl(SYMBOL_DEPTH + 1, 2.2)
    for k in range(8):
        s += box(1.2, 1.8, SYMBOL_DEPTH + 1).translate([-0.6, 3.2, 0]).rotate([0, 0, k * 45])
    return s

def moon():  # lights OFF: crescent (opening faces right when installed)
    return cyl(SYMBOL_DEPTH + 1, 4.2) - cyl(SYMBOL_DEPTH + 3, 3.6).translate([1.9, -0.9, -1])

symbols = [
    bar(1.6, 8.0),                                            # | = ON
    ring(4.0, 2.6),                                           # O = OFF
    ring(4.0, 2.6, gap_deg=70) + bar(1.6, 5.0).translate([0, -2.8, 0]),  # power symbol = power-cycle
    sun(),                                                    # lights ON
    moon(),                                                   # lights OFF
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
