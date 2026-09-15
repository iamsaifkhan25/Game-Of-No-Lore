import bpy
import math
from mathutils import Vector

# ============================================================
# GAME OF NO LORE
# TRADITIONAL OPEN CHULHA - ADD-ON ASSET SCRIPT v001
# Blender 5.2+ baseline
#
# PURPOSE
# Adds a small stylized rural mud/clay chulha to the CURRENT
# scene without deleting or changing the house.
#
# PLACEMENT
# 1. Put Blender's 3D Cursor where the chulha should sit.
# 2. Run this script.
# 3. Select "GNOL_Chulha_ROOT" to move/rotate the whole asset.
#
# ORIENTATION
# The firewood/feed opening faces LOCAL -Y.
# The back of the chulha faces LOCAL +Y (toward the wall).
# Rotate GNOL_Chulha_ROOT around Z if needed.
#
# DESIGN
# Inspired by traditional rural Indian / Bihari mud chulhas:
# - low clay/mud body
# - top pot opening/support
# - front firewood feed mouth
# - soot darkening
# - protruding firewood
# - ash patch in front
#
# This is a stylized game asset, not an engineering model.
# ============================================================


# ------------------------------------------------------------
# 0. USER-FRIENDLY SIZE SETTINGS
# ------------------------------------------------------------

WIDTH = 1.25
DEPTH = 0.78
HEIGHT = 0.52

BODY_BEVEL = 0.10

# ------------------------------------------------------------
# 1. COLLECTION + ROOT
# ------------------------------------------------------------

def get_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

COL = get_collection("GNOL_CHULHA")

cursor = bpy.context.scene.cursor
spawn_loc = cursor.location.copy()

root = bpy.data.objects.new("GNOL_Chulha_ROOT", None)
root.empty_display_type = 'PLAIN_AXES'
root.empty_display_size = 0.45
root.location = spawn_loc
COL.objects.link(root)


# ------------------------------------------------------------
# 2. MATERIAL HELPERS
# ------------------------------------------------------------

def make_mat(name, rgba, roughness=0.9, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)

    mat.use_nodes = True
    mat.diffuse_color = rgba

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic

    return mat


MAT_MUD = make_mat(
    "MAT_Chulha_Mud",
    (0.48, 0.32, 0.20, 1.0),
    roughness=0.98
)

MAT_MUD_LIGHT = make_mat(
    "MAT_Chulha_MudLight",
    (0.58, 0.42, 0.27, 1.0),
    roughness=0.98
)

MAT_SOOT = make_mat(
    "MAT_Chulha_Soot",
    (0.055, 0.047, 0.040, 1.0),
    roughness=1.0
)

MAT_WOOD = make_mat(
    "MAT_Chulha_Firewood",
    (0.29, 0.15, 0.075, 1.0),
    roughness=0.95
)

MAT_CHAR = make_mat(
    "MAT_Chulha_CharredWood",
    (0.065, 0.045, 0.030, 1.0),
    roughness=1.0
)

MAT_ASH = make_mat(
    "MAT_Chulha_Ash",
    (0.30, 0.285, 0.255, 1.0),
    roughness=1.0
)

MAT_EMBER = make_mat(
    "MAT_Chulha_Ember",
    (0.72, 0.15, 0.035, 1.0),
    roughness=0.75
)

# Give ember a little emission.
ember_bsdf = MAT_EMBER.node_tree.nodes.get("Principled BSDF")
if ember_bsdf:
    ember_bsdf.inputs["Emission Color"].default_value = (0.72, 0.08, 0.015, 1.0)
    ember_bsdf.inputs["Emission Strength"].default_value = 0.8


# ------------------------------------------------------------
# 3. OBJECT HELPERS
# ------------------------------------------------------------

def link_only(obj):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    COL.objects.link(obj)


def parent_local(obj, loc=(0, 0, 0), rot=(0, 0, 0)):
    obj.parent = root
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def cube(name, loc, dims, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims

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
        mod.segments = 3

    link_only(obj)
    parent_local(obj, loc)
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=20, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=(0, 0, 0)
    )
    obj = bpy.context.object
    obj.name = name

    if mat:
        obj.data.materials.append(mat)

    link_only(obj)
    parent_local(obj, loc, rot)
    return obj


# ------------------------------------------------------------
# 4. MAIN EARTHEN BODY
# ------------------------------------------------------------

body = cube(
    "Chulha_MudBody",
    (0, 0, HEIGHT / 2),
    (WIDTH, DEPTH, HEIGHT),
    MAT_MUD,
    BODY_BEVEL
)

# Slightly wider mud/plaster skirt at floor level.
cube(
    "Chulha_MudSkirt",
    (0, 0.015, 0.075),
    (WIDTH + 0.18, DEPTH + 0.12, 0.15),
    MAT_MUD_LIGHT,
    0.07
)

# A softly raised rear shoulder gives the handmade form
# a less box-like silhouette.
cube(
    "Chulha_RearShoulder",
    (0, 0.20, HEIGHT + 0.055),
    (WIDTH * 0.82, DEPTH * 0.30, 0.18),
    MAT_MUD,
    0.08
)


# ------------------------------------------------------------
# 5. TOP POT OPENING / SOOT RING
#
# The chulha remains intentionally simple and stylized.
# A dark inset plus torus reads as the burner opening.
# ------------------------------------------------------------

# Dark hole inset.
cylinder(
    "Chulha_TopOpening",
    (0, -0.055, HEIGHT + 0.105),
    0.235,
    0.035,
    MAT_SOOT,
    vertices=32
)

# Mud/soot support ring.
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.255,
    minor_radius=0.050,
    major_segments=32,
    minor_segments=10,
    location=(0, 0, 0)
)
ring = bpy.context.object
ring.name = "Chulha_PotSupportRing"
ring.data.materials.append(MAT_SOOT)
link_only(ring)
parent_local(
    ring,
    (0, -0.055, HEIGHT + 0.135)
)


# ------------------------------------------------------------
# 6. FRONT FIREWOOD FEED MOUTH
#
# Front of asset = local -Y.
# We model the opening as a deep dark recess with a mud lip.
# ------------------------------------------------------------

# Main dark recess.
cube(
    "Chulha_FireMouth_Dark",
    (0, -(DEPTH / 2) - 0.012, 0.225),
    (0.52, 0.055, 0.31),
    MAT_SOOT,
    0.10
)

# Upper soot shadow / arch suggestion.
cylinder(
    "Chulha_FireMouth_Arch",
    (0, -(DEPTH / 2) - 0.042, 0.345),
    0.245,
    0.060,
    MAT_SOOT,
    vertices=24,
    rot=(math.radians(90), 0, 0)
)

# Mud lip on either side of opening.
cube(
    "Chulha_FireMouth_LeftLip",
    (-0.315, -(DEPTH / 2) - 0.010, 0.215),
    (0.13, 0.11, 0.38),
    MAT_MUD_LIGHT,
    0.045
)

cube(
    "Chulha_FireMouth_RightLip",
    (0.315, -(DEPTH / 2) - 0.010, 0.215),
    (0.13, 0.11, 0.38),
    MAT_MUD_LIGHT,
    0.045
)


# ------------------------------------------------------------
# 7. FIREWOOD
#
# Logs extend out of the feed mouth like a working open chulha.
# ------------------------------------------------------------

log_specs = [
    (-0.14, -0.72, 0.125, -5),
    ( 0.02, -0.76, 0.105,  3),
    ( 0.16, -0.67, 0.145,  8),
]

for idx, (x, y, z, yaw_deg) in enumerate(log_specs, start=1):
    log = cylinder(
        f"Chulha_Firewood_{idx:02d}",
        (x, y, z),
        0.055,
        0.78,
        MAT_WOOD,
        vertices=12,
        rot=(math.radians(90), 0, math.radians(yaw_deg))
    )

    # Charred tip nearer the fire.
    cylinder(
        f"Chulha_FirewoodChar_{idx:02d}",
        (x, y + 0.25, z),
        0.057,
        0.12,
        MAT_CHAR,
        vertices=12,
        rot=(math.radians(90), 0, math.radians(yaw_deg))
    )


# ------------------------------------------------------------
# 8. ASH + EMBERS IN FRONT
# ------------------------------------------------------------

# Flattened ash patch.
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=24,
    ring_count=12,
    location=(0, 0, 0)
)
ash = bpy.context.object
ash.name = "Chulha_AshPatch"
ash.scale = (0.48, 0.28, 0.025)
bpy.ops.object.transform_apply(
    location=False,
    rotation=False,
    scale=True
)
ash.data.materials.append(MAT_ASH)
link_only(ash)
parent_local(
    ash,
    (0.0, -0.78, 0.018)
)

# A few tiny embers near mouth.
ember_positions = [
    (-0.07, -0.47, 0.075),
    ( 0.08, -0.49, 0.065),
    ( 0.00, -0.44, 0.090),
]

for idx, pos in enumerate(ember_positions, start=1):
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1,
        radius=0.035,
        location=(0, 0, 0)
    )
    ember = bpy.context.object
    ember.name = f"Chulha_Ember_{idx:02d}"
    ember.data.materials.append(MAT_EMBER)
    link_only(ember)
    parent_local(ember, pos)


# ------------------------------------------------------------
# 9. OPTIONAL WALL-SOOT MARKER
#
# This is a movable flat dark patch behind the chulha.
# Keep it if the chulha sits directly against the wall.
# Delete/hide it if you do not want visible wall blackening.
# ------------------------------------------------------------

soot_marker = cube(
    "OPTIONAL_Chulha_WallSoot",
    (0, (DEPTH / 2) + 0.012, 0.54),
    (0.68, 0.022, 0.62),
    MAT_SOOT,
    0.14
)

# ------------------------------------------------------------
# 10. ROOT CUSTOM NOTES
# ------------------------------------------------------------

root["GNOL_Asset"] = "Traditional Open Chulha"
root["GNOL_Version"] = "v001"
root["GNOL_FrontDirection"] = "Local -Y"
root["GNOL_BackDirection"] = "Local +Y (toward wall)"
root["GNOL_Usage"] = (
    "Place by left wall/open cooking area. Move/rotate ROOT only."
)

# Select root for immediate adjustment.
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root

print("")
print("====================================================")
print(" GAME OF NO LORE - OPEN CHULHA v001 ADDED")
print("====================================================")
print("The current house scene was NOT cleared or rebuilt.")
print("")
print("Selected object: GNOL_Chulha_ROOT")
print("Move this Empty to reposition the whole chulha.")
print("Rotate it on Z to aim the fire opening.")
print("")
print("Front/fire opening = local -Y")
print("Back/wall side      = local +Y")
print("")
print("OPTIONAL_Chulha_WallSoot can be hidden/deleted.")
print("====================================================")
