import bpy
import bmesh
import math
from mathutils import Matrix

# ============================================================
# GAME OF NO LORE
# OPEN CHULHA ADD-ON ASSET v003
# Blender 5.2+ baseline
#
# IMPORTANT FIX:
# This version uses Blender's DATA/BMESH API instead of
# bpy.ops.mesh primitive operators, so geometry cannot get
# accidentally merged into the object you were editing.
#
# SAFETY:
# - Does NOT clear or rebuild the house.
# - Refuses to run unless Blender is in OBJECT MODE.
# - Refuses to run if a GNOL_CHULHA collection already exists.
#
# HOW TO USE:
# 1. Revert/undo the broken v002 run first.
# 2. Press TAB until top-left says "Object Mode".
# 3. Put the 3D Cursor where the chulha should be.
# 4. Run this script.
# 5. Move/rotate GNOL_Chulha_ROOT.
#
# ORIENTATION:
# Fire opening = local -Y
# Back/wall side = local +Y
# ============================================================


# ------------------------------------------------------------
# 0. SAFETY GUARDS
# ------------------------------------------------------------

if bpy.context.mode != 'OBJECT':
    raise RuntimeError(
        "GNOL Chulha v003: Switch to OBJECT MODE first (press TAB), "
        "then run the script again."
    )

if bpy.data.collections.get("GNOL_CHULHA") is not None:
    raise RuntimeError(
        "GNOL Chulha v003: A GNOL_CHULHA collection already exists. "
        "Undo/reopen the clean house file or delete the old failed "
        "GNOL_CHULHA collection before running v003."
    )


# ------------------------------------------------------------
# 1. SETTINGS
# ------------------------------------------------------------

WIDTH = 1.25
DEPTH = 0.78
HEIGHT = 0.52

spawn_loc = bpy.context.scene.cursor.location.copy()


# ------------------------------------------------------------
# 2. COLLECTION + ROOT
# ------------------------------------------------------------

COL = bpy.data.collections.new("GNOL_CHULHA")
bpy.context.scene.collection.children.link(COL)

root = bpy.data.objects.new("GNOL_Chulha_ROOT", None)
root.empty_display_type = 'PLAIN_AXES'
root.empty_display_size = 0.45
root.location = spawn_loc
COL.objects.link(root)


# ------------------------------------------------------------
# 3. MATERIALS
# ------------------------------------------------------------

def make_mat(name, rgba, roughness=0.95, metallic=0.0, emission=None):
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

        if emission is not None:
            color, strength = emission
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = strength

    return mat


MAT_MUD = make_mat(
    "MAT_Chulha_Mud",
    (0.48, 0.32, 0.20, 1.0),
    0.98
)

MAT_MUD_LIGHT = make_mat(
    "MAT_Chulha_MudLight",
    (0.59, 0.43, 0.28, 1.0),
    0.98
)

MAT_SOOT = make_mat(
    "MAT_Chulha_Soot",
    (0.05, 0.045, 0.04, 1.0),
    1.0
)

MAT_WOOD = make_mat(
    "MAT_Chulha_Firewood",
    (0.29, 0.15, 0.075, 1.0),
    0.96
)

MAT_CHAR = make_mat(
    "MAT_Chulha_CharredWood",
    (0.06, 0.04, 0.025, 1.0),
    1.0
)

MAT_ASH = make_mat(
    "MAT_Chulha_Ash",
    (0.31, 0.295, 0.27, 1.0),
    1.0
)

MAT_EMBER = make_mat(
    "MAT_Chulha_Ember",
    (0.70, 0.12, 0.025, 1.0),
    0.80,
    emission=((0.75, 0.06, 0.01, 1.0), 0.7)
)


# ------------------------------------------------------------
# 4. BMESH OBJECT HELPERS
# ------------------------------------------------------------

def finish_object(name, bm, mat, loc=(0, 0, 0), rot=(0, 0, 0),
                  scale=(1, 1, 1), bevel=0.0):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    COL.objects.link(obj)

    if mat:
        obj.data.materials.append(mat)

    obj.parent = root
    obj.location = loc
    obj.rotation_euler = rot
    obj.scale = scale

    if bevel > 0:
        bev = obj.modifiers.new("Soft_Bevel", "BEVEL")
        bev.width = bevel
        bev.segments = 3

    return obj


def add_cube(name, loc, dims, mat, bevel=0.0, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)

    transform = Matrix.Diagonal((
        dims[0],
        dims[1],
        dims[2],
        1.0
    ))
    bmesh.ops.transform(bm, matrix=transform, verts=bm.verts)

    return finish_object(
        name,
        bm,
        mat,
        loc=loc,
        rot=rot,
        bevel=bevel
    )


def add_cylinder(name, loc, radius, depth, mat,
                 segments=24, rot=(0, 0, 0), scale=(1, 1, 1)):
    bm = bmesh.new()

    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=depth
    )

    return finish_object(
        name,
        bm,
        mat,
        loc=loc,
        rot=rot,
        scale=scale
    )


# ------------------------------------------------------------
# 5. MAIN MUD BODY
# ------------------------------------------------------------

add_cube(
    "Chulha_MudBody",
    (0, 0, HEIGHT / 2),
    (WIDTH, DEPTH, HEIGHT),
    MAT_MUD,
    bevel=0.10
)

add_cube(
    "Chulha_MudSkirt",
    (0, 0.015, 0.075),
    (WIDTH + 0.18, DEPTH + 0.12, 0.15),
    MAT_MUD_LIGHT,
    bevel=0.06
)

add_cube(
    "Chulha_RearShoulder",
    (0, 0.20, HEIGHT + 0.055),
    (WIDTH * 0.82, DEPTH * 0.30, 0.18),
    MAT_MUD,
    bevel=0.07
)


# ------------------------------------------------------------
# 6. TOP POT OPENING + THREE SUPPORT LUGS
# ------------------------------------------------------------

add_cylinder(
    "Chulha_TopOpening",
    (0, -0.055, HEIGHT + 0.105),
    0.235,
    0.035,
    MAT_SOOT,
    segments=32
)

# Three small pot supports around the opening.
for idx, (x, y) in enumerate([
    (-0.24, -0.01),
    ( 0.24, -0.01),
    ( 0.00,  0.20),
], start=1):
    add_cube(
        f"Chulha_PotSupport_{idx:02d}",
        (x, y, HEIGHT + 0.155),
        (0.13, 0.13, 0.13),
        MAT_MUD_LIGHT,
        bevel=0.04
    )


# ------------------------------------------------------------
# 7. FRONT FIRE MOUTH
# ------------------------------------------------------------

add_cube(
    "Chulha_FireMouth_Dark",
    (0, -(DEPTH / 2) - 0.015, 0.225),
    (0.52, 0.055, 0.31),
    MAT_SOOT,
    bevel=0.08
)

add_cube(
    "Chulha_FireMouth_LeftLip",
    (-0.315, -(DEPTH / 2) - 0.010, 0.215),
    (0.13, 0.11, 0.38),
    MAT_MUD_LIGHT,
    bevel=0.04
)

add_cube(
    "Chulha_FireMouth_RightLip",
    (0.315, -(DEPTH / 2) - 0.010, 0.215),
    (0.13, 0.11, 0.38),
    MAT_MUD_LIGHT,
    bevel=0.04
)

add_cube(
    "Chulha_FireMouth_TopLip",
    (0, -(DEPTH / 2) - 0.010, 0.405),
    (0.52, 0.11, 0.11),
    MAT_MUD_LIGHT,
    bevel=0.04
)


# ------------------------------------------------------------
# 8. FIREWOOD LOGS
# ------------------------------------------------------------

log_specs = [
    (-0.14, -0.72, 0.125, -5),
    ( 0.02, -0.76, 0.105,  3),
    ( 0.16, -0.67, 0.145,  8),
]

for idx, (x, y, z, yaw_deg) in enumerate(log_specs, start=1):

    rot = (
        math.radians(90),
        0,
        math.radians(yaw_deg)
    )

    add_cylinder(
        f"Chulha_Firewood_{idx:02d}",
        (x, y, z),
        0.055,
        0.78,
        MAT_WOOD,
        segments=12,
        rot=rot
    )

    add_cylinder(
        f"Chulha_FirewoodChar_{idx:02d}",
        (x, y + 0.25, z),
        0.057,
        0.12,
        MAT_CHAR,
        segments=12,
        rot=rot
    )


# ------------------------------------------------------------
# 9. ASH PATCH + EMBERS
# ------------------------------------------------------------

add_cylinder(
    "Chulha_AshPatch",
    (0.0, -0.79, 0.018),
    0.34,
    0.025,
    MAT_ASH,
    segments=32,
    scale=(1.45, 0.75, 1.0)
)

for idx, (x, y, z) in enumerate([
    (-0.07, -0.47, 0.060),
    ( 0.08, -0.49, 0.055),
    ( 0.00, -0.44, 0.070),
], start=1):
    add_cube(
        f"Chulha_Ember_{idx:02d}",
        (x, y, z),
        (0.055, 0.045, 0.035),
        MAT_EMBER,
        bevel=0.015
    )


# ------------------------------------------------------------
# 10. OPTIONAL WALL SOOT PATCH
# ------------------------------------------------------------

add_cube(
    "OPTIONAL_Chulha_WallSoot",
    (0, (DEPTH / 2) + 0.015, 0.54),
    (0.70, 0.025, 0.64),
    MAT_SOOT,
    bevel=0.10
)


# ------------------------------------------------------------
# 11. ROOT NOTES
# ------------------------------------------------------------

root["GNOL_Asset"] = "Traditional Open Chulha"
root["GNOL_Version"] = "v003"
root["GNOL_FrontDirection"] = "Local -Y"
root["GNOL_BackDirection"] = "Local +Y toward wall"
root["GNOL_Usage"] = (
    "Place by left wall. Move/rotate GNOL_Chulha_ROOT."
)

# Object-mode only, so setting active root is safe.
for obj in bpy.context.selected_objects:
    obj.select_set(False)

root.select_set(True)
bpy.context.view_layer.objects.active = root


print("")
print("====================================================")
print(" GAME OF NO LORE - OPEN CHULHA v003 ADDED")
print("====================================================")
print("No mesh operators were used.")
print("Nothing can merge into the house mesh.")
print("")
print("Selected: GNOL_Chulha_ROOT")
print("G = move")
print("R, Z = rotate")
print("")
print("Fire opening faces local -Y.")
print("Back faces local +Y toward wall.")
print("====================================================")
