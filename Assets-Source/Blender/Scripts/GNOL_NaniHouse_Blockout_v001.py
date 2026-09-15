import bpy
import math
from mathutils import Vector

# ============================================================
# GAME OF NO LORE
# NANI'S HOUSE - MEMORY BLOCKOUT GENERATOR v0.1
#
# PURPOSE:
# Generate an editable first-pass blockout from current memory.
# NOT final architecture.
#
# Blender 5.x compatible baseline.
# ============================================================


# ============================================================
# 0. USER-TWEAKABLE MASTER SETTINGS
# ============================================================

WALL_H = 2.8
WALL_T = 0.22

LOW_WALL_H = 1.05

HOUSE_FLOOR_Z = 0.10
VERANDA_H = 0.22

# Overall rough property dimensions
PROPERTY_W = 18.0
PROPERTY_D = 20.0

# Front world layout
ROAD_D = 3.2
NAALA_D = 0.80
FRONT_YARD_D = 7.2

# Right-side passing
PASSING_W = 1.55

# Colors are intentionally pastel/blockout-friendly.
COLORS = {
    "ground":     (0.43, 0.36, 0.22, 1),
    "grass":      (0.38, 0.47, 0.24, 1),
    "road":       (0.35, 0.24, 0.14, 1),
    "water":      (0.16, 0.34, 0.38, 1),

    "wall":       (0.66, 0.58, 0.45, 1),
    "house":      (0.72, 0.66, 0.54, 1),
    "brick":      (0.45, 0.25, 0.16, 1),
    "wood":       (0.31, 0.20, 0.12, 1),
    "metal":      (0.18, 0.20, 0.19, 1),

    "veranda":    (0.56, 0.48, 0.35, 1),
    "pillar":     (0.54, 0.68, 0.48, 1),
    "pillar_red": (0.55, 0.20, 0.15, 1),

    "storage":    (0.50, 0.42, 0.31, 1),
    "washroom":   (0.60, 0.56, 0.48, 1),
}


# ============================================================
# 1. CLEAN SCENE
# ============================================================

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for datablocks in (
    bpy.data.meshes,
    bpy.data.curves,
    bpy.data.materials,
    bpy.data.cameras,
    bpy.data.lights,
):
    pass


# ============================================================
# 2. COLLECTION HELPERS
# ============================================================

def collection(name):
    col = bpy.data.collections.get(name)

    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)

    return col


COL_SITE       = collection("00_SITE")
COL_FRONT      = collection("01_FRONT_APPROACH")
COL_HOUSE      = collection("02_MAIN_HOUSE")
COL_VERANDA    = collection("03_VERANDA")
COL_SERVICE    = collection("04_SERVICE_AREA")
COL_PASSING    = collection("05_RIGHT_PASSING")
COL_PROPS      = collection("06_BLOCKOUT_PROPS")
COL_REFERENCE  = collection("90_REFERENCE")
COL_CAMERA     = collection("99_CAMERA")


# ============================================================
# 3. MATERIAL HELPERS
# ============================================================

def make_mat(name, rgba):
    mat = bpy.data.materials.get(name)

    if mat is None:
        mat = bpy.data.materials.new(name)

    mat.diffuse_color = rgba
    mat.use_nodes = True

    bsdf = mat.node_tree.nodes.get("Principled BSDF")

    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.85
        bsdf.inputs["Metallic"].default_value = 0.0

    return mat


MATS = {
    k: make_mat(f"MAT_{k.upper()}", v)
    for k, v in COLORS.items()
}


# ============================================================
# 4. OBJECT HELPERS
# ============================================================

def move_to_collection(obj, col):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)

    col.objects.link(obj)


def cube(
    name,
    loc,
    scale,
    mat=None,
    col=None,
    bevel=0.03
):
    bpy.ops.mesh.primitive_cube_add(location=loc)

    obj = bpy.context.object
    obj.name = name

    obj.dimensions = scale

    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True
    )

    if mat:
        obj.data.materials.append(mat)

    if bevel > 0:
        mod = obj.modifiers.new("Soft_Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2

    if col:
        move_to_collection(obj, col)

    return obj


def wall_x(name, x, y, length, h=WALL_H, t=WALL_T, mat=None, col=None):
    return cube(
        name,
        (x, y, h / 2),
        (length, t, h),
        mat or MATS["wall"],
        col,
        0.025
    )


def wall_y(name, x, y, length, h=WALL_H, t=WALL_T, mat=None, col=None):
    return cube(
        name,
        (x, y, h / 2),
        (t, length, h),
        mat or MATS["wall"],
        col,
        0.025
    )


def pillar(name, x, y, h=2.6):
    main = cube(
        name,
        (x, y, h / 2),
        (0.45, 0.45, h),
        MATS["pillar"],
        COL_VERANDA,
        0.025
    )

    # red lower section
    cube(
        f"{name}_RedBase",
        (x, y, 0.20),
        (0.46, 0.46, 0.40),
        MATS["pillar_red"],
        COL_VERANDA,
        0.01
    )

    return main


# ============================================================
# 5. GLOBAL COORDINATE LOGIC
# ============================================================

# +Y = toward back of property
# -Y = toward road
# +X = right side / narrow passing
# -X = left side / old storage

road_y = -10.0
naala_y = -7.95
front_yard_center_y = -4.0

house_front_y = 0.0
house_back_y = 7.3

left_edge = -PROPERTY_W / 2
right_edge = PROPERTY_W / 2

passing_center_x = right_edge - PASSING_W / 2


# ============================================================
# 6. ROAD
# ============================================================

cube(
    "Road",
    (0, road_y, -0.08),
    (24, ROAD_D, 0.16),
    MATS["road"],
    COL_SITE,
    0.04
)


# ============================================================
# 7. NAALA
# ============================================================

cube(
    "Naala_Channel",
    (0, naala_y, -0.23),
    (PROPERTY_W + 2, NAALA_D, 0.35),
    MATS["water"],
    COL_FRONT,
    0.04
)

# side banks
wall_x(
    "Naala_Bank_RoadSide",
    0,
    naala_y - 0.52,
    PROPERTY_W + 2,
    0.38,
    0.28,
    MATS["brick"],
    COL_FRONT
)

wall_x(
    "Naala_Bank_YardSide",
    0,
    naala_y + 0.52,
    PROPERTY_W + 2,
    0.38,
    0.28,
    MATS["brick"],
    COL_FRONT
)


# ============================================================
# 8. WOODEN CROSSING
#
# IMPORTANT:
# This is deliberately NOT aligned with the right-side passing.
# ============================================================

crossing_x = 2.1

for i in range(5):
    plank_y = naala_y - 0.40 + i * 0.20

    cube(
        f"Naala_Crossing_Plank_{i+1}",
        (crossing_x, plank_y, 0.08),
        (1.25, 0.18, 0.14),
        MATS["wood"],
        COL_FRONT,
        0.02
    )


# ============================================================
# 9. FRONT GRASSY AREA
# ============================================================

cube(
    "Front_Grass_Yard",
    (
        -0.7,
        front_yard_center_y,
        0.00
    ),
    (
        PROPERTY_W - 1.4,
        FRONT_YARD_D,
        0.14
    ),
    MATS["grass"],
    COL_FRONT,
    0.04
)


# ============================================================
# 10. OLD FRONT STORAGE
#
# This is intentionally simple and highly editable.
# ============================================================

storage_x = -6.2
storage_y = -4.9

cube(
    "OldStorage_Floor",
    (storage_x, storage_y, 0.22),
    (3.1, 2.4, 0.44),
    MATS["storage"],
    COL_FRONT,
    0.03
)

# rear wall
wall_x(
    "OldStorage_RearWall",
    storage_x,
    storage_y + 1.1,
    3.1,
    2.25,
    0.22,
    MATS["brick"],
    COL_FRONT
)

# side walls
wall_y(
    "OldStorage_LeftWall",
    storage_x - 1.44,
    storage_y,
    2.2,
    2.25,
    0.22,
    MATS["brick"],
    COL_FRONT
)

wall_y(
    "OldStorage_RightWall",
    storage_x + 1.44,
    storage_y,
    2.2,
    2.25,
    0.22,
    MATS["brick"],
    COL_FRONT
)

# two front pillars
cube(
    "OldStorage_Pillar_L",
    (storage_x - 1.25, storage_y - 1.02, 1.25),
    (0.30, 0.30, 2.5),
    MATS["storage"],
    COL_FRONT,
    0.02
)

cube(
    "OldStorage_Pillar_R",
    (storage_x + 1.25, storage_y - 1.02, 1.25),
    (0.30, 0.30, 2.5),
    MATS["storage"],
    COL_FRONT,
    0.02
)

cube(
    "OldStorage_Roof",
    (storage_x, storage_y, 2.58),
    (3.35, 2.6, 0.20),
    MATS["brick"],
    COL_FRONT,
    0.04
)


# ============================================================
# 11. FRONT HOUSE / COMPOUND DIVIDE
#
# Current interpretation:
# the house starts immediately once the front grassy area ends.
# ============================================================

wall_x(
    "House_Front_Boundary_Left",
    -4.7,
    house_front_y,
    7.2,
    LOW_WALL_H,
    WALL_T,
    MATS["wall"],
    COL_HOUSE
)

wall_x(
    "House_Front_Boundary_Mid",
    1.5,
    house_front_y,
    4.6,
    LOW_WALL_H,
    WALL_T,
    MATS["wall"],
    COL_HOUSE
)


# ============================================================
# 12. RIGHT-SIDE NARROW PASSING
#
# IMPORTANT:
# Separate from naala crossing.
# Right edge is primarily boundary wall.
# ============================================================

passing_start_y = -5.6
passing_end_y = 3.6
passing_length = passing_end_y - passing_start_y

cube(
    "RightPassing_Floor",
    (
        passing_center_x,
        (passing_start_y + passing_end_y) / 2,
        0.07
    ),
    (
        PASSING_W,
        passing_length,
        0.14
    ),
    MATS["ground"],
    COL_PASSING,
    0.025
)

# outer/right wall
wall_y(
    "RightPassing_OuterWall",
    right_edge,
    (passing_start_y + passing_end_y) / 2,
    passing_length + 1.0,
    WALL_H,
    WALL_T,
    MATS["wall"],
    COL_PASSING
)

# left wall of passing
wall_y(
    "RightPassing_InnerWall",
    right_edge - PASSING_W,
    (passing_start_y + passing_end_y) / 2,
    passing_length - 0.7,
    WALL_H,
    WALL_T,
    MATS["wall"],
    COL_PASSING
)


# ============================================================
# 13. MAIN GATE
#
# Gate placed at FAR / INNER END of passing.
# Gate opens LEFTWARD into house/courtyard area.
# ============================================================

gate_y = passing_end_y

cube(
    "MainGate",
    (
        right_edge - PASSING_W / 2,
        gate_y,
        1.25
    ),
    (
        PASSING_W - 0.18,
        0.16,
        2.5
    ),
    MATS["metal"],
    COL_PASSING,
    0.025
)


# ============================================================
# 14. MAIN HOUSE LIVING MASS
#
# Deliberately on LEFT / CENTRE,
# away from narrow passing.
#
# Main door faces courtyard/front-house side,
# not toward right passing.
# ============================================================

living_x = -3.2
living_y = 3.8
living_w = 8.8
living_d = 5.6

cube(
    "MainHouse_LivingBlock",
    (
        living_x,
        living_y,
        1.5
    ),
    (
        living_w,
        living_d,
        3.0
    ),
    MATS["house"],
    COL_HOUSE,
    0.04
)


# ============================================================
# 15. VERANDA
#
# Current placeholder orientation:
# veranda faces toward interior/open house area.
#
# Easy to rotate/move once memory is clarified.
# ============================================================

veranda_y = living_y - living_d / 2 - 0.95

cube(
    "Veranda_Floor",
    (
        living_x,
        veranda_y,
        VERANDA_H / 2
    ),
    (
        living_w - 0.7,
        1.8,
        VERANDA_H
    ),
    MATS["veranda"],
    COL_VERANDA,
    0.025
)

# pillars
pillar("Veranda_Pillar_01", living_x - 2.3, veranda_y - 0.55)
pillar("Veranda_Pillar_02", living_x + 1.6, veranda_y - 0.55)


# ============================================================
# 16. MAIN DOORS
#
# Doors deliberately away from passing.
# ============================================================

door_y = living_y - living_d / 2 - 0.04

cube(
    "Living_Door_01",
    (
        living_x - 2.0,
        door_y,
        1.08
    ),
    (
        1.0,
        0.10,
        2.15
    ),
    MATS["wood"],
    COL_HOUSE,
    0.025
)

cube(
    "Living_Door_02",
    (
        living_x + 1.8,
        door_y,
        1.08
    ),
    (
        1.0,
        0.10,
        2.15
    ),
    MATS["wood"],
    COL_HOUSE,
    0.025
)


# ============================================================
# 17. CHARPAIS - SIMPLE BLOCKOUTS
# ============================================================

def charpai(name, x, y):
    # frame
    cube(
        f"{name}_Bed",
        (x, y, 0.48),
        (1.8, 0.75, 0.12),
        MATS["wood"],
        COL_PROPS,
        0.02
    )

    # legs
    for dx in (-0.78, 0.78):
        for dy in (-0.28, 0.28):
            cube(
                f"{name}_Leg_{dx}_{dy}",
                (x + dx, y + dy, 0.25),
                (0.10, 0.10, 0.50),
                MATS["wood"],
                COL_PROPS,
                0.01
            )


charpai("Charpai_01", living_x - 2.8, veranda_y)
charpai("Charpai_02", living_x - 0.4, veranda_y)
charpai("Charpai_03", living_x + 2.0, veranda_y)


# ============================================================
# 18. SERVICE / FUEL STORAGE
# ============================================================

fuel_x = 2.65
fuel_y = 3.2

cube(
    "FuelStorage_Floor",
    (fuel_x, fuel_y, 0.12),
    (2.4, 3.1, 0.24),
    MATS["storage"],
    COL_SERVICE,
    0.025
)

wall_x(
    "FuelStorage_BackWall",
    fuel_x,
    fuel_y + 1.45,
    2.4,
    2.4,
    0.20,
    MATS["brick"],
    COL_SERVICE
)

wall_y(
    "FuelStorage_LeftWall",
    fuel_x - 1.1,
    fuel_y,
    3.0,
    2.4,
    0.20,
    MATS["brick"],
    COL_SERVICE
)


# roof
cube(
    "FuelStorage_Roof",
    (fuel_x, fuel_y, 2.45),
    (2.55, 3.2, 0.18),
    MATS["wood"],
    COL_SERVICE,
    0.02
)


# ============================================================
# 19. WASHROOM BLOCK
# ============================================================

wash_x = 5.1
wash_y = 4.8

# steps
for i in range(4):
    cube(
        f"Washroom_Step_{i+1}",
        (
            wash_x,
            wash_y - 1.45 + i * 0.26,
            0.09 + i * 0.09
        ),
        (
            1.7 - i * 0.12,
            0.32,
            0.18 + i * 0.04
        ),
        MATS["washroom"],
        COL_SERVICE,
        0.015
    )

cube(
    "Washroom_Block",
    (wash_x, wash_y, 1.6),
    (2.0, 2.3, 3.2),
    MATS["washroom"],
    COL_SERVICE,
    0.035
)

cube(
    "Washroom_Door",
    (wash_x, wash_y - 1.17, 1.25),
    (0.82, 0.08, 2.25),
    MATS["wood"],
    COL_SERVICE,
    0.02
)


# ============================================================
# 20. HANDPUMP - BLOCKOUT
# ============================================================

pump_x = 4.8
pump_y = 1.8

cube(
    "Handpump_Base",
    (pump_x, pump_y, 0.18),
    (1.45, 1.45, 0.20),
    MATS["washroom"],
    COL_PROPS,
    0.025
)

cube(
    "Handpump_Body",
    (pump_x, pump_y, 0.82),
    (0.26, 0.26, 1.45),
    MATS["metal"],
    COL_PROPS,
    0.025
)

cube(
    "Handpump_Spout",
    (pump_x - 0.28, pump_y, 1.16),
    (0.62, 0.12, 0.12),
    MATS["metal"],
    COL_PROPS,
    0.02
)

handle = cube(
    "Handpump_Handle",
    (pump_x + 0.05, pump_y, 1.65),
    (0.12, 0.85, 0.12),
    MATS["metal"],
    COL_PROPS,
    0.02
)

handle.rotation_euler.x = math.radians(20)


# ============================================================
# 21. GRAIN / OLD ITEMS STORAGE
# ============================================================

grain_x = 2.6
grain_y = 6.2

cube(
    "GrainStorage_Block",
    (grain_x, grain_y, 1.5),
    (3.3, 2.5, 3.0),
    MATS["storage"],
    COL_SERVICE,
    0.035
)

cube(
    "GrainStorage_Door",
    (grain_x, grain_y - 1.28, 1.1),
    (0.9, 0.08, 2.05),
    MATS["wood"],
    COL_SERVICE,
    0.02
)


# ============================================================
# 22. STAIRS TO ROOF
# ============================================================

stairs_x = 4.45
stairs_start_y = 6.0

for i in range(8):
    cube(
        f"RoofStep_{i+1:02d}",
        (
            stairs_x,
            stairs_start_y + i * 0.30,
            0.12 + i * 0.18
        ),
        (
            1.15,
            0.34,
            0.24 + i * 0.02
        ),
        MATS["brick"],
        COL_SERVICE,
        0.015
    )


# ============================================================
# 23. BACK / UNCERTAIN ZONES
#
# These are ghost blockouts only.
# Move/delete them freely.
# ============================================================

ghost_mat = make_mat(
    "MAT_OPEN_UNCONFIRMED",
    (0.45, 0.58, 0.50, 0.40)
)

ghost_mat.diffuse_color = (0.45, 0.58, 0.50, 0.40)

bsdf = ghost_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.45, 0.58, 0.50, 1)
    bsdf.inputs["Alpha"].default_value = 0.40

ghost_mat.surface_render_method = 'DITHERED'

cube(
    "OPEN_BackSection_01",
    (-4.5, 8.5, 1.1),
    (4.5, 2.2, 2.2),
    ghost_mat,
    COL_REFERENCE,
    0.03
)

cube(
    "OPEN_BackSection_02",
    (0.4, 8.5, 1.1),
    (4.5, 2.2, 2.2),
    ghost_mat,
    COL_REFERENCE,
    0.03
)


# ============================================================
# 24. SIMPLE WELL PLACEHOLDER - OPEN / UNCONFIRMED
# ============================================================

bpy.ops.mesh.primitive_cylinder_add(
    vertices=32,
    radius=0.85,
    depth=0.8,
    location=(5.8, 8.5, 0.4)
)

well = bpy.context.object
well.name = "OPEN_Well_Kuan"
well.data.materials.append(ghost_mat)
move_to_collection(well, COL_REFERENCE)


# ============================================================
# 25. BOUNDARY WALLS
# ============================================================

# left side boundary
wall_y(
    "Property_LeftBoundary",
    left_edge,
    1.0,
    15.7,
    2.2,
    0.24,
    MATS["wall"],
    COL_SITE
)

# back boundary
wall_x(
    "Property_BackBoundary",
    0,
    9.6,
    PROPERTY_W,
    2.2,
    0.24,
    MATS["wall"],
    COL_SITE
)


# ============================================================
# 26. CAMERA FOR BLOCKOUT REVIEW
# ============================================================

cam_data = bpy.data.cameras.new("BlockoutCamera")
cam = bpy.data.objects.new("BlockoutCamera", cam_data)
COL_CAMERA.objects.link(cam)

cam_data.type = 'ORTHO'
cam_data.ortho_scale = 26

cam.location = (22, -25, 24)


def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


point_at(cam, (0, 0, 0))

bpy.context.scene.camera = cam


# ============================================================
# 27. SUN / AREA LIGHTS
# ============================================================

sun_data = bpy.data.lights.new("BlockoutSun", type='SUN')
sun = bpy.data.objects.new("BlockoutSun", sun_data)
COL_CAMERA.objects.link(sun)

sun.rotation_euler = (
    math.radians(35),
    0,
    math.radians(-35)
)

sun_data.energy = 2.0


area_data = bpy.data.lights.new("BlockoutFill", type='AREA')
area = bpy.data.objects.new("BlockoutFill", area_data)
COL_CAMERA.objects.link(area)

area.location = (-6, -5, 12)
area_data.energy = 650
area_data.size = 9

point_at(area, (0, 0, 0))


# ============================================================
# 28. RENDER SETTINGS
# ============================================================

scene = bpy.context.scene

try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except:
    pass

scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100

scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

scene.world.color = (0.04, 0.04, 0.04)


# ============================================================
# 29. FINAL ORGANIZATION / INFO
# ============================================================

print("============================================")
print("Game of No Lore - Nani House Blockout built")
print("============================================")
print("")
print("IMPORTANT:")
print("This is an editable MEMORY INTERPRETATION.")
print("It is NOT final geometry.")
print("")
print("Collections:")
print("00_SITE")
print("01_FRONT_APPROACH")
print("02_MAIN_HOUSE")
print("03_VERANDA")
print("04_SERVICE_AREA")
print("05_RIGHT_PASSING")
print("06_BLOCKOUT_PROPS")
print("90_REFERENCE")
print("99_CAMERA")
print("")
print("Unconfirmed objects begin with OPEN_.")
print("Move, resize, rotate or delete them freely.")
print("============================================")