import bpy
import math
from mathutils import Vector

# ============================================================
# GAME OF NO LORE
# GRANDPARENTS' HOUSE - INSPIRED BLOCKOUT GENERATOR v003
# Blender 5.2+ baseline
#
# v003 CHANGES
# - Roof stairs moved completely to the BACK side.
# - Middle utility/storage block removed from courtyard.
# - Storeroom moved to the RIGHT end of the living wing,
#   attached to the house wall beside the main house door.
# - Added a proper accessible right-side roof terrace/deck.
# - Back stairs now climb to that roof terrace.
# - Added a well / kuan in the rear utility garden.
#
# DESIGN LAW
# This is a gameplay-first house inspired by Nani's house,
# NOT a literal 1:1 reconstruction.
#
# WARNING
# Running this script CLEARS the current Blender scene.
# ============================================================


# ------------------------------------------------------------
# 0. MASTER TWEAKS
# ------------------------------------------------------------

WALL_H = 2.8
WALL_T = 0.22

PROPERTY_LEFT_X = -9.0
PROPERTY_RIGHT_X = 8.5
PROPERTY_BACK_Y = 12.3

ROAD_Y = -12.0
NAALA_Y = -9.4

FRONT_YARD_FRONT_Y = -8.7
FRONT_YARD_BACK_Y = -2.0
COMPOUND_WALL_Y = -1.75

PASSING_INNER_X = 6.3
PASSING_OUTER_X = 8.2
PASSING_START_Y = -1.65
PASSING_END_Y = 5.7
PASSING_W = PASSING_OUTER_X - PASSING_INNER_X

GATE_CENTER_Y = 4.55
GATE_W = 1.75
GATE_H = 2.45

COURTYARD_FRONT_Y = -1.45
COURTYARD_BACK_Y = 6.25
COURTYARD_LEFT_X = -8.45
COURTYARD_RIGHT_X = 6.05

LIVING_CENTER_X = -3.45
LIVING_CENTER_Y = 7.55
LIVING_W = 9.3
LIVING_D = 3.8
LIVING_H = 3.0

VERANDA_DEPTH = 1.75

# Right-side attached storeroom
STORE_W = 2.25
STORE_D = 2.65
STORE_H = 2.65

# Roof terrace / service roof
ROOF_TERRACE_Z = 3.16
ROOF_PARAPET_H = 0.72

# Rear garden
REAR_FRONT_Y = 9.55
REAR_BACK_Y = 12.0

# ------------------------------------------------------------
# 1. BLOCKOUT COLORS
# ------------------------------------------------------------

COLORS = {
    "road":        (0.38, 0.27, 0.17, 1),
    "water":       (0.20, 0.40, 0.44, 1),
    "grass":       (0.43, 0.53, 0.31, 1),
    "earth":       (0.52, 0.43, 0.29, 1),
    "wall":        (0.69, 0.64, 0.54, 1),
    "house":       (0.76, 0.71, 0.62, 1),
    "wood":        (0.36, 0.24, 0.15, 1),
    "metal":       (0.20, 0.22, 0.22, 1),
    "brick":       (0.52, 0.31, 0.22, 1),
    "veranda":     (0.59, 0.50, 0.38, 1),
    "pillar":      (0.52, 0.66, 0.47, 1),
    "pillar_red":  (0.58, 0.22, 0.18, 1),
    "service":     (0.60, 0.55, 0.46, 1),
    "rear":        (0.47, 0.56, 0.36, 1),
    "roof":        (0.63, 0.59, 0.50, 1),
    "guide":       (0.95, 0.75, 0.20, 1),
    "player":      (0.22, 0.43, 0.80, 1),
    "well_inner":  (0.08, 0.10, 0.11, 1),
}

# ------------------------------------------------------------
# 2. CLEAN SCENE
# ------------------------------------------------------------

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ------------------------------------------------------------
# 3. COLLECTIONS
# ------------------------------------------------------------

def get_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

COL_WORLD     = get_collection("00_WORLD_REFERENCE")
COL_APPROACH  = get_collection("01_FRONT_APPROACH")
COL_YARD      = get_collection("02_FRONT_YARD")
COL_WALL_GATE = get_collection("03_COMPOUND_WALL_GATE")
COL_PASSING   = get_collection("04_NARROW_PASSING")
COL_COURT     = get_collection("05_COURTYARD")
COL_LIVING    = get_collection("06_LIVING_WING")
COL_VERANDA   = get_collection("07_VERANDA")
COL_SERVICE   = get_collection("08_SERVICE_AREA")
COL_ROOF      = get_collection("09_ROOF_AND_BACK_STAIRS")
COL_REAR      = get_collection("10_REAR_GARDEN_AND_WELL")
COL_PROPS     = get_collection("11_BLOCKOUT_PROPS")
COL_GUIDES    = get_collection("90_GUIDES")
COL_CAMERA    = get_collection("99_CAMERA_REVIEW")

# ------------------------------------------------------------
# 4. MATERIALS
# ------------------------------------------------------------

def make_material(name, rgba, roughness=0.88):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)

    mat.use_nodes = True
    mat.diffuse_color = rgba

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = 0.0

    return mat

MATS = {
    key: make_material(f"MAT_{key.upper()}", rgba)
    for key, rgba in COLORS.items()
}

# ------------------------------------------------------------
# 5. HELPERS
# ------------------------------------------------------------

def move_to_collection(obj, col):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    col.objects.link(obj)

def make_cube(name, loc, dims, mat, col, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(location=loc)

    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims

    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True
    )

    obj.data.materials.append(mat)

    if bevel > 0:
        modifier = obj.modifiers.new("Soft_Bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2

    move_to_collection(obj, col)
    return obj

def wall_x(name, center_x, y, length,
           col=COL_WALL_GATE,
           height=WALL_H,
           thickness=WALL_T,
           mat=None):
    return make_cube(
        name,
        (center_x, y, height / 2),
        (length, thickness, height),
        mat or MATS["wall"],
        col
    )

def wall_y(name, x, center_y, length,
           col=COL_WALL_GATE,
           height=WALL_H,
           thickness=WALL_T,
           mat=None):
    return make_cube(
        name,
        (x, center_y, height / 2),
        (thickness, length, height),
        mat or MATS["wall"],
        col
    )

def add_label(text, loc, size=0.42):
    bpy.ops.object.text_add(location=loc)

    obj = bpy.context.object
    obj.name = "GUIDE_" + text.replace(" ", "_").replace("/", "_")
    obj.data.body = text
    obj.data.align_x = 'CENTER'
    obj.data.align_y = 'CENTER'
    obj.data.size = size
    obj.data.extrude = 0.01
    obj.data.materials.append(MATS["guide"])

    move_to_collection(obj, COL_GUIDES)
    return obj

def add_pillar(name, x, y, h=2.55):
    make_cube(
        name,
        (x, y, h / 2),
        (0.44, 0.44, h),
        MATS["pillar"],
        COL_VERANDA,
        0.02
    )

    make_cube(
        name + "_RedBase",
        (x, y, 0.22),
        (0.46, 0.46, 0.44),
        MATS["pillar_red"],
        COL_VERANDA,
        0.01
    )

def add_charpai(name, x, y):
    make_cube(
        name + "_Bed",
        (x, y, 0.48),
        (1.75, 0.72, 0.11),
        MATS["wood"],
        COL_PROPS,
        0.015
    )

    for sx in (-0.76, 0.76):
        for sy in (-0.26, 0.26):
            make_cube(
                f"{name}_Leg_{sx}_{sy}",
                (x + sx, y + sy, 0.24),
                (0.10, 0.10, 0.48),
                MATS["wood"],
                COL_PROPS,
                0.01
            )

def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# ------------------------------------------------------------
# 6. WORLD REFERENCE
# ------------------------------------------------------------

make_cube(
    "Road",
    (0, ROAD_Y, -0.08),
    (23.0, 3.2, 0.16),
    MATS["road"],
    COL_WORLD,
    0.03
)

make_cube(
    "Property_Base",
    (-0.25, 1.35, -0.16),
    (18.2, 21.0, 0.16),
    MATS["earth"],
    COL_WORLD,
    0.02
)

# ------------------------------------------------------------
# 7. NAALA + WOODEN CROSSING
# ------------------------------------------------------------

make_cube(
    "Naala_Water",
    (0, NAALA_Y, -0.18),
    (19.0, 0.80, 0.28),
    MATS["water"],
    COL_APPROACH,
    0.02
)

wall_x(
    "Naala_Bank_RoadSide",
    0,
    NAALA_Y - 0.51,
    19.0,
    col=COL_APPROACH,
    height=0.38,
    thickness=0.25,
    mat=MATS["brick"]
)

wall_x(
    "Naala_Bank_YardSide",
    0,
    NAALA_Y + 0.51,
    19.0,
    col=COL_APPROACH,
    height=0.38,
    thickness=0.25,
    mat=MATS["brick"]
)

# Crossing remains deliberately separate from the narrow passing.
CROSSING_X = 1.25

for i in range(6):
    make_cube(
        f"WoodCrossing_Plank_{i+1:02d}",
        (
            CROSSING_X,
            NAALA_Y - 0.48 + i * 0.19,
            0.10
        ),
        (1.35, 0.17, 0.12),
        MATS["wood"],
        COL_APPROACH,
        0.015
    )

# ------------------------------------------------------------
# 8. FRONT GRASSY AREA + OLD STORAGE
# ------------------------------------------------------------

yard_center_y = (FRONT_YARD_FRONT_Y + FRONT_YARD_BACK_Y) / 2
yard_depth = FRONT_YARD_BACK_Y - FRONT_YARD_FRONT_Y

make_cube(
    "FrontYard_Grass",
    (-0.35, yard_center_y, 0.02),
    (17.1, yard_depth, 0.12),
    MATS["grass"],
    COL_YARD,
    0.03
)

OLD_X = -6.3
OLD_Y = -6.0

make_cube(
    "OldStorage_RaisedFloor",
    (OLD_X, OLD_Y, 0.22),
    (3.0, 2.4, 0.44),
    MATS["service"],
    COL_YARD,
    0.025
)

wall_x(
    "OldStorage_BackWall",
    OLD_X,
    OLD_Y + 1.08,
    3.0,
    col=COL_YARD,
    height=2.2,
    thickness=0.20,
    mat=MATS["brick"]
)

wall_y(
    "OldStorage_LeftWall",
    OLD_X - 1.40,
    OLD_Y,
    2.2,
    col=COL_YARD,
    height=2.2,
    thickness=0.20,
    mat=MATS["brick"]
)

wall_y(
    "OldStorage_RightWall",
    OLD_X + 1.40,
    OLD_Y,
    2.2,
    col=COL_YARD,
    height=2.2,
    thickness=0.20,
    mat=MATS["brick"]
)

for px in (-1.18, 1.18):
    make_cube(
        f"OldStorage_FrontPillar_{'L' if px < 0 else 'R'}",
        (OLD_X + px, OLD_Y - 1.02, 1.20),
        (0.28, 0.28, 2.4),
        MATS["service"],
        COL_YARD,
        0.015
    )

make_cube(
    "OldStorage_Roof",
    (OLD_X, OLD_Y, 2.52),
    (3.25, 2.62, 0.18),
    MATS["brick"],
    COL_YARD,
    0.03
)

# ------------------------------------------------------------
# 9. COMPOUND WALL + PROPERTY WALLS
# ------------------------------------------------------------

compound_length = PASSING_INNER_X - PROPERTY_LEFT_X
compound_center_x = (PROPERTY_LEFT_X + PASSING_INNER_X) / 2

wall_x(
    "CompoundWall_Front",
    compound_center_x,
    COMPOUND_WALL_Y,
    compound_length,
    col=COL_WALL_GATE,
    height=2.35,
    thickness=0.24,
    mat=MATS["wall"]
)

left_boundary_center_y = (FRONT_YARD_FRONT_Y + PROPERTY_BACK_Y) / 2
left_boundary_len = PROPERTY_BACK_Y - FRONT_YARD_FRONT_Y

wall_y(
    "Property_LeftBoundary",
    PROPERTY_LEFT_X,
    left_boundary_center_y,
    left_boundary_len,
    col=COL_WALL_GATE,
    height=2.25,
    thickness=0.24,
    mat=MATS["wall"]
)

wall_x(
    "Property_BackBoundary",
    (PROPERTY_LEFT_X + PROPERTY_RIGHT_X) / 2,
    PROPERTY_BACK_Y,
    PROPERTY_RIGHT_X - PROPERTY_LEFT_X,
    col=COL_WALL_GATE,
    height=2.25,
    thickness=0.24,
    mat=MATS["wall"]
)

# ------------------------------------------------------------
# 10. RIGHT-SIDE NARROW PASSING + MAIN GATE
# ------------------------------------------------------------

passing_center_x = (PASSING_INNER_X + PASSING_OUTER_X) / 2
passing_center_y = (PASSING_START_Y + PASSING_END_Y) / 2
passing_len = PASSING_END_Y - PASSING_START_Y

make_cube(
    "NarrowPassing_Floor",
    (passing_center_x, passing_center_y, 0.05),
    (PASSING_W, passing_len, 0.10),
    MATS["earth"],
    COL_PASSING,
    0.015
)

wall_y(
    "Passing_RightBoundaryWall",
    PASSING_OUTER_X,
    passing_center_y,
    passing_len + 0.6,
    col=COL_PASSING,
    height=2.7,
    thickness=0.24,
    mat=MATS["wall"]
)

gate_half = GATE_W / 2

lower_start = PASSING_START_Y
lower_end = GATE_CENTER_Y - gate_half
lower_len = lower_end - lower_start
lower_center = (lower_start + lower_end) / 2

wall_y(
    "Passing_InnerWall_BeforeGate",
    PASSING_INNER_X,
    lower_center,
    lower_len,
    col=COL_PASSING,
    height=2.55,
    thickness=0.24,
    mat=MATS["wall"]
)

upper_start = GATE_CENTER_Y + gate_half
upper_end = PASSING_END_Y
upper_len = upper_end - upper_start
upper_center = (upper_start + upper_end) / 2

wall_y(
    "Passing_InnerWall_AfterGate",
    PASSING_INNER_X,
    upper_center,
    upper_len,
    col=COL_PASSING,
    height=2.55,
    thickness=0.24,
    mat=MATS["wall"]
)

make_cube(
    "MainGate",
    (PASSING_INNER_X - 0.02, GATE_CENTER_Y, GATE_H / 2),
    (0.15, GATE_W, GATE_H),
    MATS["metal"],
    COL_WALL_GATE,
    0.02
)

wall_x(
    "Passing_EndWall",
    passing_center_x,
    PASSING_END_Y,
    PASSING_W,
    col=COL_PASSING,
    height=2.55,
    thickness=0.24,
    mat=MATS["wall"]
)

# ------------------------------------------------------------
# 11. COURTYARD
# ------------------------------------------------------------

court_center_x = (COURTYARD_LEFT_X + COURTYARD_RIGHT_X) / 2
court_center_y = (COURTYARD_FRONT_Y + COURTYARD_BACK_Y) / 2
court_w = COURTYARD_RIGHT_X - COURTYARD_LEFT_X
court_d = COURTYARD_BACK_Y - COURTYARD_FRONT_Y

make_cube(
    "Courtyard_Floor",
    (court_center_x, court_center_y, 0.035),
    (court_w, court_d, 0.07),
    MATS["earth"],
    COL_COURT,
    0.02
)

# ------------------------------------------------------------
# 12. MAIN LIVING WING
# ------------------------------------------------------------

make_cube(
    "LivingWing_MainBlock",
    (LIVING_CENTER_X, LIVING_CENTER_Y, LIVING_H / 2),
    (LIVING_W, LIVING_D, LIVING_H),
    MATS["house"],
    COL_LIVING,
    0.035
)

# Main living roof slab
make_cube(
    "LivingWing_MainRoof",
    (
        LIVING_CENTER_X,
        LIVING_CENTER_Y,
        LIVING_H + 0.12
    ),
    (LIVING_W + 0.18, LIVING_D + 0.18, 0.18),
    MATS["roof"],
    COL_ROOF,
    0.025
)

# ------------------------------------------------------------
# 13. VERANDA + DOORS + CHARPAIS
# ------------------------------------------------------------

living_front_y = LIVING_CENTER_Y - (LIVING_D / 2)
living_right_x = LIVING_CENTER_X + (LIVING_W / 2)

veranda_center_y = living_front_y - (VERANDA_DEPTH / 2)

# Shorten veranda slightly at right so the attached storeroom has its own face.
VERANDA_W = 7.35
VERANDA_CENTER_X = -4.15

make_cube(
    "Veranda_Floor",
    (
        VERANDA_CENTER_X,
        veranda_center_y,
        0.13
    ),
    (VERANDA_W, VERANDA_DEPTH, 0.26),
    MATS["veranda"],
    COL_VERANDA,
    0.02
)

PILLAR_Y = veranda_center_y - 0.48
add_pillar("Veranda_Pillar_01", -5.55, PILLAR_Y)
add_pillar("Veranda_Pillar_02", -2.00, PILLAR_Y)

door_y = living_front_y - 0.04

# Secondary / player room door
make_cube(
    "Door_PlayerRoom",
    (-5.45, door_y, 1.08),
    (0.98, 0.10, 2.16),
    MATS["wood"],
    COL_LIVING,
    0.02
)

# Main house door shifted to the right, beside the new attached storeroom.
MAIN_DOOR_X = -1.15

make_cube(
    "Door_MainHouse",
    (MAIN_DOOR_X, door_y, 1.08),
    (1.02, 0.10, 2.16),
    MATS["wood"],
    COL_LIVING,
    0.02
)

add_charpai("Charpai_01", -6.25, veranda_center_y - 0.12)
add_charpai("Charpai_02", -4.05, veranda_center_y - 0.12)
add_charpai("Charpai_03", -2.10, veranda_center_y - 0.12)

# ------------------------------------------------------------
# 14. ATTACHED RIGHT-SIDE STOREROOM
#
# Moved out of the middle.
# It now attaches to the RIGHT end of the living wing beside
# the main door, as requested.
# ------------------------------------------------------------

store_center_x = living_right_x + (STORE_W / 2)
store_center_y = living_front_y + (STORE_D / 2) - 0.05

make_cube(
    "StoreRoom_RightAttached_Block",
    (
        store_center_x,
        store_center_y,
        STORE_H / 2
    ),
    (STORE_W, STORE_D, STORE_H),
    MATS["service"],
    COL_SERVICE,
    0.03
)

# Storeroom front-facing door toward courtyard.
make_cube(
    "StoreRoom_RightAttached_Door",
    (
        store_center_x,
        store_center_y - (STORE_D / 2) - 0.04,
        1.02
    ),
    (0.82, 0.08, 1.95),
    MATS["wood"],
    COL_SERVICE,
    0.015
)

# Small roof slab over storeroom, also part of the accessible right roof composition.
make_cube(
    "StoreRoom_Roof",
    (
        store_center_x,
        store_center_y,
        STORE_H + 0.10
    ),
    (STORE_W + 0.15, STORE_D + 0.15, 0.18),
    MATS["roof"],
    COL_ROOF,
    0.02
)

# ------------------------------------------------------------
# 15. HANDPUMP + WASHROOM SERVICE CORNER
# ------------------------------------------------------------

make_cube(
    "ServiceArea_Platform",
    (4.20, 4.25, 0.10),
    (3.30, 3.35, 0.20),
    MATS["service"],
    COL_SERVICE,
    0.02
)

make_cube(
    "Handpump_Base",
    (3.65, 3.55, 0.18),
    (1.35, 1.25, 0.18),
    MATS["service"],
    COL_PROPS,
    0.02
)

make_cube(
    "Handpump_Body",
    (3.65, 3.55, 0.82),
    (0.26, 0.26, 1.45),
    MATS["metal"],
    COL_PROPS,
    0.02
)

make_cube(
    "Handpump_Spout",
    (3.35, 3.55, 1.12),
    (0.70, 0.12, 0.12),
    MATS["metal"],
    COL_PROPS,
    0.015
)

pump_handle = make_cube(
    "Handpump_Handle",
    (3.68, 3.55, 1.62),
    (0.12, 0.88, 0.12),
    MATS["metal"],
    COL_PROPS,
    0.015
)
pump_handle.rotation_euler.x = math.radians(18)

WASH_X = 4.85
WASH_Y = 6.65

for i in range(4):
    step_h = 0.12 + i * 0.10

    make_cube(
        f"Washroom_Step_{i+1}",
        (
            WASH_X,
            5.47 + i * 0.27,
            step_h / 2
        ),
        (
            1.60 - i * 0.10,
            0.34,
            step_h
        ),
        MATS["service"],
        COL_SERVICE,
        0.012
    )

make_cube(
    "Washroom_Block",
    (WASH_X, WASH_Y, 1.55),
    (2.0, 2.35, 3.10),
    MATS["service"],
    COL_SERVICE,
    0.03
)

make_cube(
    "Washroom_Door",
    (
        WASH_X,
        WASH_Y - 1.20,
        1.12
    ),
    (0.82, 0.08, 2.10),
    MATS["wood"],
    COL_SERVICE,
    0.015
)

# ------------------------------------------------------------
# 16. PROPER RIGHT-SIDE ROOF TERRACE
#
# This is the roof that the BACK stairs lead to.
# ------------------------------------------------------------

ROOF_CENTER_X = 3.70
ROOF_CENTER_Y = 7.65
ROOF_W = 5.0
ROOF_D = 4.0

make_cube(
    "RightRoof_TerraceSlab",
    (
        ROOF_CENTER_X,
        ROOF_CENTER_Y,
        ROOF_TERRACE_Z
    ),
    (ROOF_W, ROOF_D, 0.20),
    MATS["roof"],
    COL_ROOF,
    0.025
)

# Parapet at front, right, and partial rear.
roof_front_y = ROOF_CENTER_Y - (ROOF_D / 2)
roof_back_y = ROOF_CENTER_Y + (ROOF_D / 2)
roof_left_x = ROOF_CENTER_X - (ROOF_W / 2)
roof_right_x = ROOF_CENTER_X + (ROOF_W / 2)

wall_x(
    "RightRoof_ParapetFront",
    ROOF_CENTER_X,
    roof_front_y,
    ROOF_W,
    col=COL_ROOF,
    height=ROOF_PARAPET_H,
    thickness=0.16,
    mat=MATS["wall"]
)
# Raise parapet onto roof slab.
bpy.context.object.location.z += ROOF_TERRACE_Z

wall_y(
    "RightRoof_ParapetRight",
    roof_right_x,
    ROOF_CENTER_Y,
    ROOF_D,
    col=COL_ROOF,
    height=ROOF_PARAPET_H,
    thickness=0.16,
    mat=MATS["wall"]
)
bpy.context.object.location.z += ROOF_TERRACE_Z

# Rear parapet deliberately leaves a gap on left side for stair landing.
wall_x(
    "RightRoof_ParapetRear_Partial",
    ROOF_CENTER_X + 0.85,
    roof_back_y,
    ROOF_W - 1.70,
    col=COL_ROOF,
    height=ROOF_PARAPET_H,
    thickness=0.16,
    mat=MATS["wall"]
)
bpy.context.object.location.z += ROOF_TERRACE_Z

# ------------------------------------------------------------
# 17. BACKSIDE STAIRS TO ROOF
#
# Completely moved out of courtyard.
# Player reaches them from the rear utility garden.
# They climb along the BACK-RIGHT side to the roof terrace.
# ------------------------------------------------------------

STAIR_X = 2.20
STAIR_START_Y = 11.10
STAIR_COUNT = 12

# Descend Y as height rises, so the top lands toward the roof terrace.
for i in range(STAIR_COUNT):
    t = i / (STAIR_COUNT - 1)

    y = STAIR_START_Y - (t * 2.45)
    z = 0.12 + (t * (ROOF_TERRACE_Z - 0.28))

    step_depth = 0.31
    step_height = 0.22

    make_cube(
        f"BackRoofStair_{i+1:02d}",
        (STAIR_X, y, z),
        (1.20, step_depth, step_height),
        MATS["brick"],
        COL_ROOF,
        0.010
    )

# Stair side wall on right for a more believable stair flight.
wall_y(
    "BackRoofStair_RightSideWall",
    STAIR_X + 0.70,
    9.90,
    3.15,
    col=COL_ROOF,
    height=1.15,
    thickness=0.16,
    mat=MATS["wall"]
)
bpy.context.object.location.z = 0.58

# Landing at top of stairs.
make_cube(
    "BackRoofStair_TopLanding",
    (
        STAIR_X,
        8.45,
        ROOF_TERRACE_Z
    ),
    (1.30, 0.90, 0.18),
    MATS["roof"],
    COL_ROOF,
    0.015
)

# ------------------------------------------------------------
# 18. REAR UTILITY / GARDEN
# ------------------------------------------------------------

rear_center_y = (REAR_FRONT_Y + REAR_BACK_Y) / 2
rear_depth = REAR_BACK_Y - REAR_FRONT_Y

make_cube(
    "RearUtility_Ground",
    (-1.2, rear_center_y, 0.03),
    (13.8, rear_depth, 0.08),
    MATS["rear"],
    COL_REAR,
    0.02
)

# Clothesline posts
for x in (-4.2, -1.2):
    make_cube(
        f"Rear_ClotheslinePost_{x}",
        (x, 10.65, 1.15),
        (0.10, 0.10, 2.30),
        MATS["wood"],
        COL_REAR,
        0.01
    )

# ------------------------------------------------------------
# 19. WELL / KUAN IN BACKSIDE
# ------------------------------------------------------------

WELL_X = -0.10
WELL_Y = 10.75

# Stone cylinder body.
bpy.ops.mesh.primitive_cylinder_add(
    vertices=48,
    radius=0.92,
    depth=0.72,
    location=(WELL_X, WELL_Y, 0.36)
)
well_body = bpy.context.object
well_body.name = "RearWell_Kuan_Body"
well_body.data.materials.append(MATS["brick"])
move_to_collection(well_body, COL_REAR)

# Dark inner opening as a shallow inset cylinder.
bpy.ops.mesh.primitive_cylinder_add(
    vertices=48,
    radius=0.63,
    depth=0.035,
    location=(WELL_X, WELL_Y, 0.735)
)
well_hole = bpy.context.object
well_hole.name = "RearWell_Kuan_Opening"
well_hole.data.materials.append(MATS["well_inner"])
move_to_collection(well_hole, COL_REAR)

# Raised rim, approximated with a larger thin cylinder.
bpy.ops.mesh.primitive_cylinder_add(
    vertices=48,
    radius=1.00,
    depth=0.18,
    location=(WELL_X, WELL_Y, 0.76)
)
well_rim = bpy.context.object
well_rim.name = "RearWell_Kuan_Rim"
well_rim.data.materials.append(MATS["brick"])
move_to_collection(well_rim, COL_REAR)

# Put the dark opening slightly above rim so it visually reads as a hole.
well_hole.location.z = 0.86

# ------------------------------------------------------------
# 20. PLAYER SCALE REFERENCE
# ------------------------------------------------------------

# Capsule operator exists in current Blender; fall back to cylinder if unavailable.
try:
    bpy.ops.mesh.primitive_capsule_add(
        radius=0.28,
        depth=1.20,
        location=(1.25, -5.2, 0.88)
    )
    player = bpy.context.object
except Exception:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=0.28,
        depth=1.75,
        location=(1.25, -5.2, 0.875)
    )
    player = bpy.context.object

player.name = "REF_Player_Approx_1p75m"
player.data.materials.append(MATS["player"])
move_to_collection(player, COL_GUIDES)

# ------------------------------------------------------------
# 21. GUIDE LABELS
# ------------------------------------------------------------

add_label("ROAD", (0, -12.0, 0.16), 0.48)
add_label("NAALA", (-2.4, -9.4, 0.18), 0.40)
add_label("FRONT YARD", (0.0, -5.1, 0.18), 0.50)
add_label("OLD STORAGE", (-6.3, -4.65, 2.72), 0.32)
add_label("COMPOUND WALL", (-1.0, -1.72, 2.52), 0.34)
add_label("NARROW PASSING", (7.25, 1.65, 0.16), 0.30)
add_label("MAIN GATE", (6.05, 4.55, 2.70), 0.32)
add_label("COURTYARD", (-1.5, 2.1, 0.15), 0.50)
add_label("LIVING WING", (-3.5, 8.0, 3.35), 0.44)
add_label("VERANDA", (-4.0, 5.2, 0.32), 0.38)
add_label("STORE ROOM", (2.25, 6.20, 2.95), 0.32)
add_label("HANDPUMP", (3.65, 3.0, 0.30), 0.30)
add_label("WASHROOM", (4.85, 7.05, 3.45), 0.30)
add_label("ROOF TERRACE", (3.7, 7.65, 4.05), 0.36)
add_label("BACK STAIRS", (2.2, 9.80, 2.30), 0.30)
add_label("REAR WELL / KUAN", (-0.1, 10.75, 1.25), 0.32)

# ------------------------------------------------------------
# 22. REVIEW CAMERA + LIGHTING
# ------------------------------------------------------------

cam_data = bpy.data.cameras.new("ReviewCamera")
cam = bpy.data.objects.new("ReviewCamera", cam_data)
COL_CAMERA.objects.link(cam)

cam_data.type = 'PERSP'
cam_data.lens = 48
cam.location = (22.5, -27.0, 25.0)

point_at(cam, (-0.5, 0.6, 1.1))
bpy.context.scene.camera = cam

sun_data = bpy.data.lights.new("ReviewSun", type='SUN')
sun = bpy.data.objects.new("ReviewSun", sun_data)
COL_CAMERA.objects.link(sun)

sun.rotation_euler = (
    math.radians(35),
    math.radians(-10),
    math.radians(-35)
)
sun_data.energy = 2.0

area_data = bpy.data.lights.new("ReviewFill", type='AREA')
area = bpy.data.objects.new("ReviewFill", area_data)
COL_CAMERA.objects.link(area)

area.location = (-7.0, -5.0, 14.0)
area_data.energy = 700
area_data.size = 10.0
point_at(area, (-0.5, 1.0, 0.8))

# ------------------------------------------------------------
# 23. RENDER SETTINGS
# ------------------------------------------------------------

scene = bpy.context.scene

try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    pass

scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100

scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

scene.world.color = (0.045, 0.045, 0.045)

scene["GNOL_BlockoutVersion"] = "GrandparentsHouse_Inspired_v003"
scene["GNOL_DesignLaw"] = (
    "Inspired by Nani house; gameplay-first, not 1:1 reconstruction."
)
scene["GNOL_v003Changes"] = (
    "Back stairs; right-attached storeroom; proper roof terrace; rear well."
)

print("")
print("============================================================")
print(" GAME OF NO LORE - GRANDPARENTS' HOUSE BLOCKOUT v003")
print("============================================================")
print("Built successfully.")
print("")
print("v003 changes:")
print("- Roof stairs moved to BACK side.")
print("- Middle storage block removed.")
print("- Storeroom attached to RIGHT end of living wing.")
print("- Storeroom sits beside main house door.")
print("- Proper right-side roof terrace added.")
print("- Back stairs lead to roof terrace.")
print("- Well / kuan added in rear garden.")
print("")
print("Core route:")
print("Road -> Naala Crossing -> Front Yard -> Right Passing")
print("-> turn LEFT through Main Gate -> Courtyard")
print("")
print("Toggle 90_GUIDES off for a clean view.")
print("============================================================")
