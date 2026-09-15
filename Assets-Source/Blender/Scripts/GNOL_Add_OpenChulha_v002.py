import bpy
import math

# ============================================================
# GAME OF NO LORE
# TRADITIONAL OPEN CHULHA - ADD-ON ASSET SCRIPT v002
# Blender 5.2+ baseline
#
# FIX IN v002:
# - Removed bpy.ops.object.transform_apply(), which caused the
#   "context is incorrect" error when run from Blender's Text Editor.
# - Cube meshes are now created at their final dimensions directly.
# - This script is NON-DESTRUCTIVE: it does not clear the house.
#
# HOW TO USE:
# 1. In your existing grandparents-house .blend, place the 3D Cursor
#    on the floor by the LEFT wall where the chulha should sit.
# 2. Run this script.
# 3. Blender selects GNOL_Chulha_ROOT.
# 4. Move with G and rotate with R, Z.
#
# ORIENTATION:
# - Firewood/feed opening faces local -Y.
# - Back of chulha faces local +Y, toward the wall.
# ============================================================


# ------------------------------------------------------------
# 0. SIZE
# ------------------------------------------------------------

WIDTH = 1.25
DEPTH = 0.78
HEIGHT = 0.52


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

spawn_loc = bpy.context.scene.cursor.location.copy()

root = bpy.data.objects.new("GNOL_Chulha_ROOT", None)
root.empty_display_type = 'PLAIN_AXES'
root.empty_display_size = 0.45
root.location = spawn_loc
COL.objects.link(root)


# ------------------------------------------------------------
# 2. MATERIALS
# ------------------------------------------------------------

def make_mat(name, rgba, roughness=0.95, metallic=0.0):
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
    0.98
)

MAT_MUD_LIGHT = make_mat(
    "MAT_Chulha_MudLight",
    (0.58, 0.42, 0.27, 1.0),
    0.98
)

MAT_SOOT = make_mat(
    "MAT_Chulha_Soot",
    (0.055, 0.047, 0.040, 1.0),
    1.0
)

MAT_WOOD = make_mat(
    "MAT_Chulha_Firewood",
    (0.29, 0.15, 0.075, 1.0),
    0.95
)

MAT_CHAR = make_mat(
    "MAT_Chulha_CharredWood",
    (0.065, 0.045, 0.030, 1.0),
    1.0
)

MAT_ASH = make_mat(
    "MAT_Chulha_Ash",
    (0.30, 0.285, 0.255, 1.0),
    1.0
)

MAT_EMBER = make_mat(
    "MAT_Chulha_Ember",
    (0.72, 0.15, 0.035, 1.0),
    0.75
)

ember_bsdf = MAT_EMBER.node_tree.nodes.get("Principled BSDF")
if ember_bsdf:
    ember_bsdf.inputs["Emission Color"].default_value = (
        0.72, 0.08, 0.015, 1.0
    )
    ember_bsdf.inputs["Emission Strength"].default_value = 0.8


# ------------------------------------------------------------
# 3. ROBUST MESH HELPERS
# ------------------------------------------------------------

def link_only(obj):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    COL.objects.link(obj)


def parent_local(obj, local_loc=(0, 0, 0), local_rot=(0, 0, 0)):
    obj.parent = root
    obj.location = local_loc
    obj.rotation_euler = local_rot
    return obj


def cube_mesh(name, loc, dims, mat, bevel=0.0):
    """Create a cube at final dimensions without transform_apply()."""

    dx = dims[0] / 2
    dy = dims[1] / 2
    dz = dims[2] / 2

    verts = [
        (-dx, -dy, -dz),
        ( dx, -dy, -dz),
        ( dx,  dy, -dz),
        (-dx,  dy, -dz),
        (-dx, -dy,  dz),
        ( dx, -dy,  dz),
        ( dx,  dy,  dz),
        (-dx,  dy,  dz),
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7),
    ]

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    COL.objects.link(obj)

    if mat:
        obj.data.materials.append(mat)

    if bevel > 0:
        bev = obj.modifiers.new("Soft_Bevel", "BEVEL")
        bev.width = bevel
        bev.segments = 3

    parent_local(obj, loc)
    return obj


def cylinder(name, loc, radius, depth, mat,
             vertices=24, rot=(0, 0, 0)):

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth
    )

    obj = bpy.context.object
    obj.name = name

    if mat:
        obj.data.materials.append(mat)

    link_only(obj)
    parent_local(obj, loc, rot)

    return obj


# ------------------------------------------------------------
# 4. MAIN MUD BODY
# ------------------------------------------------------------

cube_mesh(
    "Chulha_MudBody",
    (0, 0, HEIGHT / 2),
    (WIDTH, DEPTH, HEIGHT),
    MAT_MUD,
    0.10
)

cube_mesh(
    "Chulha_MudSkirt",
    (0, 0.015, 0.075),
    (WIDTH + 0.18, DEPTH + 0.12, 0.15),
    MAT_MUD_LIGHT,
    0.06
)

cube_mesh(
    "Chulha_RearShoulder",
    (0, 0.20, HEIGHT + 0.055),
    (WIDTH * 0.82, DEPTH * 0.30, 0.18),
    MAT_MUD,
    0.07
)


# ------------------------------------------------------------
# 5. TOP POT OPENING
# ------------------------------------------------------------

cylinder(
    "Chulha_TopOpening",
    (0, -0.055, HEIGHT + 0.105),
    0.235,
    0.035,
    MAT_SOOT,
    32
)

bpy.ops.mesh.primitive_torus_add(
    major_radius=0.255,
    minor_radius=0.050,
    major_segments=32,
    minor_segments=10
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
# 6. FIREWOOD FEED MOUTH
# ------------------------------------------------------------

cube_mesh(
    "Chulha_FireMouth_Dark",
    (0, -(DEPTH / 2) - 0.012, 0.225),
    (0.52, 0.055, 0.31),
    MAT_SOOT,
    0.08
)

# Simple dark upper arch/shadow.
cylinder(
    "Chulha_FireMouth_Arch",
    (0, -(DEPTH / 2) - 0.035, 0.330),
    0.235,
    0.055,
    MAT_SOOT,
    24,
    (math.radians(90), 0, 0)
)

cube_mesh(
    "Chulha_FireMouth_LeftLip",
    (-0.315, -(DEPTH / 2) - 0.010, 0.215),
    (0.13, 0.11, 0.38),
    MAT_MUD_LIGHT,
    0.04
)

cube_mesh(
    "Chulha_FireMouth_RightLip",
    (0.315, -(DEPTH / 2) - 0.010, 0.215),
    (0.13, 0.11, 0.38),
    MAT_MUD_LIGHT,
    0.04
)


# ------------------------------------------------------------
# 7. FIREWOOD
# ------------------------------------------------------------

log_specs = [
    (-0.14, -0.72, 0.125, -5),
    ( 0.02, -0.76, 0.105,  3),
    ( 0.16, -0.67, 0.145,  8),
]

for idx, (x, y, z, yaw_deg) in enumerate(log_specs, start=1):

    cylinder(
        f"Chulha_Firewood_{idx:02d}",
        (x, y, z),
        0.055,
        0.78,
        MAT_WOOD,
        12,
        (math.radians(90), 0, math.radians(yaw_deg))
    )

    cylinder(
        f"Chulha_FirewoodChar_{idx:02d}",
        (x, y + 0.25, z),
        0.057,
        0.12,
        MAT_CHAR,
        12,
        (math.radians(90), 0, math.radians(yaw_deg))
    )


# ------------------------------------------------------------
# 8. ASH PATCH
# ------------------------------------------------------------

# Use a flattened UV sphere without apply-transform.
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=24,
    ring_count=12
)

ash = bpy.context.object
ash.name = "Chulha_AshPatch"
ash.data.materials.append(MAT_ASH)
ash.scale = (0.48, 0.28, 0.025)

link_only(ash)

parent_local(
    ash,
    (0.0, -0.78, 0.018)
)


# ------------------------------------------------------------
# 9. EMBERS
# ------------------------------------------------------------

ember_positions = [
    (-0.07, -0.47, 0.075),
    ( 0.08, -0.49, 0.065),
    ( 0.00, -0.44, 0.090),
]

for idx, pos in enumerate(ember_positions, start=1):

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1,
        radius=0.035
    )

    ember = bpy.context.object
    ember.name = f"Chulha_Ember_{idx:02d}"
    ember.data.materials.append(MAT_EMBER)

    link_only(ember)
    parent_local(ember, pos)


# ------------------------------------------------------------
# 10. OPTIONAL WALL SOOT
# ------------------------------------------------------------

cube_mesh(
    "OPTIONAL_Chulha_WallSoot",
    (0, (DEPTH / 2) + 0.012, 0.54),
    (0.68, 0.022, 0.62),
    MAT_SOOT,
    0.11
)


# ------------------------------------------------------------
# 11. ROOT NOTES
# ------------------------------------------------------------

root["GNOL_Asset"] = "Traditional Open Chulha"
root["GNOL_Version"] = "v002"
root["GNOL_FrontDirection"] = "Local -Y"
root["GNOL_BackDirection"] = "Local +Y toward wall"
root["GNOL_Usage"] = (
    "Place by left wall. Move and rotate GNOL_Chulha_ROOT only."
)


# ------------------------------------------------------------
# 12. SELECT ROOT
# ------------------------------------------------------------

bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root

print("")
print("====================================================")
print(" GAME OF NO LORE - OPEN CHULHA v002 ADDED")
print("====================================================")
print("House scene was NOT cleared.")
print("")
print("Selected: GNOL_Chulha_ROOT")
print("G = move")
print("R, Z = rotate around floor")
print("")
print("Fire opening faces local -Y.")
print("Back faces local +Y toward the wall.")
print("")
print("OPTIONAL_Chulha_WallSoot may be hidden/deleted.")
print("====================================================")
