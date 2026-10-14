"""
Alexa Button Box case - NodeMCU ESP-12E on a "GPIO 1 into 2" breakout board + five 12x12 mm tact switches.
Top row: plug ON / OFF / power-cycle.  Bottom row: lights ON / OFF.

v3 changes: snap-in button pockets (no glue), screw-down board standoffs, screwed-on lid,
tall USB window for the NodeMCU's own micro-USB, wall keyholes moved clear of the board.

Generates base.stl and lid.stl. All dimensions in mm; tweak the parameters below and re-run:
    pip install manifold3d trimesh numpy
    python make_case.py

Screws: 8 x M2.5 self-tapping - 4 x 6 mm (board), 4 x 8 mm countersunk (lid).
"""
import math
from manifold3d import Manifold
import trimesh
import numpy as np

# ---------------- parameters ----------------
WALL = 2.4          # side wall thickness
FLOOR = 2.0         # base floor thickness
IN_L, IN_W, IN_H = 80.0, 80.0, 40.0   # inside length, width, height of base

# breakout board ("GPIO 1 into 2", listed as 6.35 x 6.3 cm)
BOARD_L, BOARD_W = 63.5, 63.0
PCB_T = 1.6
END_GAP = 1.0                   # gap between the USB edge of the board and the inside wall
POST_H = 4.0                    # standoff height (room for solder joints under the board)
POST_R = 3.0
# mounting holes: centre-to-centre spacing, centred on the board. MEASURE YOURS before printing.
HOLE_DX, HOLE_DY = 57.5, 57.0
SCREW_PILOT_R = 1.05            # pilot hole for M2.5 self-tapping screws

# access window in the -X wall for the NodeMCU's micro-USB cable (put that end of the board here)
WIN_W = 50.0                    # window width along the wall
WIN_FROM_PCB = -1.0             # window bottom relative to the top of the breakout PCB
WIN_TOP_MARGIN = 5.0            # solid wall left above the window (under the lid)

LID_T = 2.4         # lid plate thickness
LIP_H = 3.0         # lip that drops inside the base
LIP_W = 1.6
FIT = 0.3           # clearance between lid lip and base walls (raise if too tight)
BOSS_R = 3.5        # corner bosses for the lid screws
BOSS_INSET = 3.4    # boss centre distance from the inside walls
LID_HOLE_R = 1.5    # clearance hole in the lid for M2.5
CSK_R = 2.6         # countersink radius at the lid surface

BTN = 12.0          # tact switch body
BTN_CLEAR = 0.4
BODY_H = 3.7        # switch body height (without the stem) - snap tabs sit just past this
CAP_HOLE = 13.0     # square hole for the cap (fits 12 mm square or round caps)
CLIP_T = 1.4        # snap finger thickness
CLIP_W = 5.0        # snap finger width
TAB = 0.6           # how far the snap tab hooks over the switch
POST_ARM = 3.0      # length of the corner locating posts' arms
POST_T = 1.6
BTN_PITCH = 22.0    # centre-to-centre spacing
ROW_PITCH = 30.0
SYMBOL_DEPTH = 0.6

def box(x, y, z):
    return Manifold.cube([x, y, z])

def cyl(h, r, seg=64):
    return Manifold.cylinder(h, r, r, seg)

def cone(h, r1, r2, seg=64):
    return Manifold.cylinder(h, r1, r2, seg)

# ---------------- base ----------------
OUT_L, OUT_W = IN_L + 2 * WALL, IN_W + 2 * WALL
OUT_H = FLOOR + IN_H

base = box(OUT_L, OUT_W, OUT_H) - box(IN_L, IN_W, IN_H + 1).translate([WALL, WALL, FLOOR])

# board position (USB end against the -X wall), centred across the width
bx0 = WALL + END_GAP
by0 = WALL + (IN_W - BOARD_W) / 2
bcx, bcy = bx0 + BOARD_L / 2, by0 + BOARD_W / 2
board_holes = [(bcx + sx * HOLE_DX / 2, bcy + sy * HOLE_DY / 2) for sx in (-1, 1) for sy in (-1, 1)]
for (hx, hy) in board_holes:
    base += cyl(POST_H + 0.5, POST_R).translate([hx, hy, FLOOR - 0.5])
    base -= cyl(POST_H + 1.0, SCREW_PILOT_R, 32).translate([hx, hy, FLOOR - 1.0])   # stops 1 mm above the bottom

# lid screw bosses in the four inside corners
boss_xy = [(x, y) for x in (WALL + BOSS_INSET, WALL + IN_L - BOSS_INSET)
                  for y in (WALL + BOSS_INSET, WALL + IN_W - BOSS_INSET)]
for (x, y) in boss_xy:
    base += cyl(IN_H + 0.5, BOSS_R).translate([x, y, FLOOR - 0.5])
    # fill the gap between boss and the two walls so it's one solid corner
    base += box(BOSS_INSET + 0.5, 2 * BOSS_R, IN_H + 0.5).translate([x - BOSS_INSET - 0.5 if x < OUT_L / 2 else x, y - BOSS_R, FLOOR - 0.5])
    base += box(2 * BOSS_R, BOSS_INSET + 0.5, IN_H + 0.5).translate([x - BOSS_R, y - BOSS_INSET - 0.5 if y < OUT_W / 2 else y, FLOOR - 0.5])
    base -= cyl(13, SCREW_PILOT_R, 32).translate([x, y, OUT_H - 12])

# tall access window for the NodeMCU's micro-USB plug + cable
pcb_top = FLOOR + POST_H + PCB_T
win_z0 = pcb_top + WIN_FROM_PCB
win_z1 = OUT_H - WIN_TOP_MARGIN
base -= box(WALL + 2, WIN_W, win_z1 - win_z0).translate([-1, bcy - WIN_W / 2, win_z0])

# wall-mount keyholes in the floor strip beside the board (+Y is up on the wall: slot above the head hole)
key_x = (bx0 + BOARD_L + POST_R + WALL + IN_L - BOSS_INSET - BOSS_R) / 2
for ky in (OUT_W * 0.28, OUT_W * 0.62):
    base -= cyl(FLOOR + 2, 4.0).translate([key_x, ky, -1])
    base -= box(4.0, 8.0, FLOOR + 2).translate([key_x - 2, ky, -1])
    base -= cyl(FLOOR + 2, 2.0).translate([key_x, ky + 8, -1])

# ---------------- lid (modelled upside-down: printed outside-face on the bed) ----------------
# installed position of a lid point (x, y) is (x, OUT_W - y)
lid = box(OUT_L, OUT_W, LID_T)
lx0, ly0 = WALL + FIT, WALL + FIT
lip_l, lip_w = IN_L - 2 * FIT, IN_W - 2 * FIT
lip = box(lip_l, lip_w, LIP_H) - box(lip_l - 2 * LIP_W, lip_w - 2 * LIP_W, LIP_H + 1).translate([LIP_W, LIP_W, -0.5])
lid += lip.translate([lx0, ly0, LID_T])
for (x, y) in boss_xy:
    ly = OUT_W - y
    # notch the lip around each corner boss
    lid -= cyl(LIP_H + 1, BOSS_R + 0.5).translate([x, ly, LID_T])
    lid -= box(BOSS_INSET + BOSS_R + 1, BOSS_INSET + BOSS_R + 1, LIP_H + 1).translate(
        [x - BOSS_INSET - 0.5 if x < OUT_L / 2 else x - BOSS_R - 0.5,
         ly - BOSS_INSET - 0.5 if ly < OUT_W / 2 else ly - BOSS_R - 0.5, LID_T])
    # countersunk clearance hole
    lid -= cyl(LID_T + 2, LID_HOLE_R, 32).translate([x, ly, -1])
    lid -= cone(CSK_R - LID_HOLE_R + 0.5, CSK_R + 0.5, LID_HOLE_R, 48).translate([x, ly, -0.5])

top_y = OUT_W / 2 - ROW_PITCH / 2      # plug row (top on the wall)
bot_y = OUT_W / 2 + ROW_PITCH / 2      # lights row (bottom on the wall)
centres = [(OUT_L / 2 + (i - 1) * BTN_PITCH, top_y) for i in range(3)] + \
          [(OUT_L / 2 + d * BTN_PITCH / 2, bot_y) for d in (-1, 1)]

def button_holder():
    """Snap-in holder for a 12x12 tact switch, built upward from z=0 (the lid's inner face).
    Legs exit toward +/-Y (open sides); snap fingers are on the +/-X sides."""
    s = (BTN + BTN_CLEAR) / 2
    h = Manifold()
    # four L-shaped corner posts (locate the body, stay clear of the legs)
    for sx in (-1, 1):
        for sy in (-1, 1):
            arm_x = box(POST_ARM + POST_T, POST_T, BODY_H)          # along X, on the +/-Y side
            arm_y = box(POST_T, POST_ARM + POST_T, BODY_H)          # along Y, on the +/-X side
            ax = s - POST_ARM if sx > 0 else -s - POST_T
            ay = s if sy > 0 else -s - POST_T
            h += arm_x.translate([ax, ay, 0])
            bx = s if sx > 0 else -s - POST_T
            by = s - POST_ARM if sy > 0 else -s - POST_T
            h += arm_y.translate([bx, by, 0])
    # two flexible snap fingers with hooks
    fh = BODY_H + 2 * TAB
    for sx in (-1, 1):
        fx = s if sx > 0 else -s - CLIP_T
        h += box(CLIP_T, CLIP_W, fh).translate([fx, -CLIP_W / 2, 0])
        hook_x = s - TAB if sx > 0 else -s
        h += box(TAB, CLIP_W, TAB).translate([hook_x, -CLIP_W / 2, BODY_H])                 # retaining ledge
        hook2 = s - TAB / 2 if sx > 0 else -s
        h += box(TAB / 2, CLIP_W, TAB).translate([hook2, -CLIP_W / 2, BODY_H + TAB])        # lead-in step
    return h

holder = button_holder()
for (x, y) in centres:
    lid += holder.translate([x, y, LID_T])
    lid -= box(CAP_HOLE, CAP_HOLE, LID_T + 2).translate([x - CAP_HOLE / 2, y - CAP_HOLE / 2, -1])

# debossed symbols below each button (on the outside face, z=0 here)
def ring(r_out, r_in, gap_deg=0):
    c = cyl(SYMBOL_DEPTH + 1, r_out) - cyl(SYMBOL_DEPTH + 3, r_in).translate([0, 0, -1])
    if gap_deg:
        w = 2 * r_out * math.sin(math.radians(gap_deg / 2)) + 0.01
        c -= box(w, r_out + 1, SYMBOL_DEPTH + 3).translate([-w / 2, -(r_out + 1), -1])
    return c

def bar(w, h):
    return box(w, h, SYMBOL_DEPTH + 1).translate([-w / 2, -h / 2, 0])

def sun():   # lights ON: dot with 8 rays
    s = cyl(SYMBOL_DEPTH + 1, 2.2)
    for k in range(8):
        s += box(1.2, 1.8, SYMBOL_DEPTH + 1).translate([-0.6, 3.2, 0]).rotate([0, 0, k * 45])
    return s

def moon():  # lights OFF: crescent
    return cyl(SYMBOL_DEPTH + 1, 4.2) - cyl(SYMBOL_DEPTH + 3, 3.6).translate([1.9, -0.9, -1])

# +Y in lid coordinates = down on the wall
sym_dy = CAP_HOLE / 2 + 7.5
symbols = [
    bar(1.6, 8.0),                                                       # | = plug ON
    ring(4.0, 2.6),                                                      # O = plug OFF
    ring(4.0, 2.6, gap_deg=70) + bar(1.6, 5.0).translate([0, -2.8, 0]),  # power symbol = power-cycle
    sun(),                                                               # lights ON
    moon(),                                                              # lights OFF
]
for (x, y), s in zip(centres, symbols):
    lid -= s.translate([x, y + sym_dy, -1])

def save(m, path):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    t.export(path)
    print(path, "watertight:", t.is_watertight, "bounds:", np.round(t.bounds, 1).tolist())

if __name__ == "__main__":
    save(base, "base.stl")
    save(lid, "lid.stl")
