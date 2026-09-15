import bpy
import math
from mathutils import Vector

# ============================================================
# GAME OF NO LORE
# GRANDPARENTS' HOUSE - INSPIRED BLOCKOUT GENERATOR v002
# Blender 5.2+ baseline
#
# IMPORTANT:
# - GAME-ADAPTED layout inspired by Nani's house.
# - NOT a literal reconstruction.
# - CLEARS the current Blender scene.
# - Built as named/editable parts for manual correction.
# ============================================================

# ------------------------- MASTER TWEAKS ---------------------
WALL_H = 2.8
WALL_T = 0.22
PROPERTY_LEFT_X = -9.0
PROPERTY_RIGHT_X = 8.5
PROPERTY_BACK_Y = 11.5
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
REAR_FRONT_Y = 9.35
REAR_BACK_Y = 11.2

COLORS = {
    'road': (0.38, 0.27, 0.17, 1),
    'water': (0.20, 0.40, 0.44, 1),
    'grass': (0.43, 0.53, 0.31, 1),
    'earth': (0.52, 0.43, 0.29, 1),
    'wall': (0.69, 0.64, 0.54, 1),
    'house': (0.76, 0.71, 0.62, 1),
    'wood': (0.36, 0.24, 0.15, 1),
    'metal': (0.20, 0.22, 0.22, 1),
    'brick': (0.52, 0.31, 0.22, 1),
    'veranda': (0.59, 0.50, 0.38, 1),
    'pillar': (0.52, 0.66, 0.47, 1),
    'pillar_red': (0.58, 0.22, 0.18, 1),
    'service': (0.60, 0.55, 0.46, 1),
    'rear': (0.47, 0.56, 0.36, 1),
    'guide': (0.95, 0.75, 0.20, 1),
    'player': (0.22, 0.43, 0.80, 1),
}

# ---------------------------- CLEAN --------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# -------------------------- COLLECTIONS ----------------------
def get_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

COL_WORLD = get_collection('00_WORLD_REFERENCE')
COL_APPROACH = get_collection('01_FRONT_APPROACH')
COL_YARD = get_collection('02_FRONT_YARD')
COL_WALL_GATE = get_collection('03_COMPOUND_WALL_GATE')
COL_PASSING = get_collection('04_NARROW_PASSING')
COL_COURT = get_collection('05_COURTYARD')
COL_LIVING = get_collection('06_LIVING_WING')
COL_VERANDA = get_collection('07_VERANDA')
COL_SERVICE = get_collection('08_SERVICE_AREA')
COL_REAR = get_collection('09_REAR_AREA')
COL_PROPS = get_collection('10_BLOCKOUT_PROPS')
COL_GUIDES = get_collection('90_GUIDES')
COL_CAMERA = get_collection('99_CAMERA_REVIEW')

# --------------------------- MATERIALS -----------------------
def make_material(name, rgba, roughness=0.88):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = rgba
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = rgba
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = 0.0
    return mat

MATS = {k: make_material(f'MAT_{k.upper()}', v) for k, v in COLORS.items()}

# ----------------------------- HELPERS -----------------------
def move_to_collection(obj, col):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    col.objects.link(obj)

def make_cube(name, loc, dims, mat, col, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel > 0:
        mod = obj.modifiers.new('Soft_Bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    move_to_collection(obj, col)
    return obj

def wall_x(name, center_x, y, length, col=COL_WALL_GATE, height=WALL_H, thickness=WALL_T, mat=None):
    return make_cube(name, (center_x, y, height/2), (length, thickness, height), mat or MATS['wall'], col)

def wall_y(name, x, center_y, length, col=COL_WALL_GATE, height=WALL_H, thickness=WALL_T, mat=None):
    return make_cube(name, (x, center_y, height/2), (thickness, length, height), mat or MATS['wall'], col)

def add_label(text, loc, size=0.42):
    bpy.ops.object.text_add(location=loc)
    obj = bpy.context.object
    obj.name = 'GUIDE_' + text.replace(' ', '_').replace('/', '_')
    obj.data.body = text
    obj.data.align_x = 'CENTER'
    obj.data.align_y = 'CENTER'
    obj.data.size = size
    obj.data.extrude = 0.01
    obj.data.materials.append(MATS['guide'])
    move_to_collection(obj, COL_GUIDES)
    return obj

def add_pillar(name, x, y, h=2.55):
    make_cube(name, (x, y, h/2), (0.44, 0.44, h), MATS['pillar'], COL_VERANDA, 0.02)
    make_cube(name+'_RedBase', (x, y, 0.22), (0.46, 0.46, 0.44), MATS['pillar_red'], COL_VERANDA, 0.01)

def add_charpai(name, x, y):
    make_cube(name+'_Bed', (x, y, 0.48), (1.75, 0.72, 0.11), MATS['wood'], COL_PROPS, 0.015)
    for sx in (-0.76, 0.76):
        for sy in (-0.26, 0.26):
            make_cube(f'{name}_Leg_{sx}_{sy}', (x+sx, y+sy, 0.24), (0.10, 0.10, 0.48), MATS['wood'], COL_PROPS, 0.01)

def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# ---------------------- ROAD / PROPERTY BASE ----------------
make_cube('Road', (0, ROAD_Y, -0.08), (23.0, 3.2, 0.16), MATS['road'], COL_WORLD, 0.03)
make_cube('Property_Base', (-0.25, 1.0, -0.16), (18.2, 20.2, 0.16), MATS['earth'], COL_WORLD, 0.02)

# ---------------------- NAALA + CROSSING ---------------------
make_cube('Naala_Water', (0, NAALA_Y, -0.18), (19.0, 0.80, 0.28), MATS['water'], COL_APPROACH, 0.02)
wall_x('Naala_Bank_RoadSide', 0, NAALA_Y-0.51, 19.0, col=COL_APPROACH, height=0.38, thickness=0.25, mat=MATS['brick'])
wall_x('Naala_Bank_YardSide', 0, NAALA_Y+0.51, 19.0, col=COL_APPROACH, height=0.38, thickness=0.25, mat=MATS['brick'])

# Deliberately separate from the right-side passing.
CROSSING_X = 1.25
for i in range(6):
    plank_y = NAALA_Y - 0.48 + i*0.19
    make_cube(f'WoodCrossing_Plank_{i+1:02d}', (CROSSING_X, plank_y, 0.10), (1.35, 0.17, 0.12), MATS['wood'], COL_APPROACH, 0.015)

# -------------------------- FRONT YARD -----------------------
yard_center_y = (FRONT_YARD_FRONT_Y + FRONT_YARD_BACK_Y) / 2
yard_depth = FRONT_YARD_BACK_Y - FRONT_YARD_FRONT_Y
make_cube('FrontYard_Grass', (-0.35, yard_center_y, 0.02), (17.1, yard_depth, 0.12), MATS['grass'], COL_YARD, 0.03)

# Old open storage on the LEFT front.
OLD_X, OLD_Y = -6.3, -6.0
make_cube('OldStorage_RaisedFloor', (OLD_X, OLD_Y, 0.22), (3.0, 2.4, 0.44), MATS['service'], COL_YARD, 0.025)
wall_x('OldStorage_BackWall', OLD_X, OLD_Y+1.08, 3.0, col=COL_YARD, height=2.2, thickness=0.20, mat=MATS['brick'])
wall_y('OldStorage_LeftWall', OLD_X-1.40, OLD_Y, 2.2, col=COL_YARD, height=2.2, thickness=0.20, mat=MATS['brick'])
wall_y('OldStorage_RightWall', OLD_X+1.40, OLD_Y, 2.2, col=COL_YARD, height=2.2, thickness=0.20, mat=MATS['brick'])
for px, suffix in ((-1.18,'L'), (1.18,'R')):
    make_cube(f'OldStorage_FrontPillar_{suffix}', (OLD_X+px, OLD_Y-1.02, 1.20), (0.28,0.28,2.4), MATS['service'], COL_YARD, 0.015)
make_cube('OldStorage_Roof', (OLD_X, OLD_Y, 2.52), (3.25,2.62,0.18), MATS['brick'], COL_YARD, 0.03)

# -------------------- COMPOUND WALL / BOUNDARY -------------
compound_length = PASSING_INNER_X - PROPERTY_LEFT_X
compound_center_x = (PROPERTY_LEFT_X + PASSING_INNER_X) / 2
wall_x('CompoundWall_Front', compound_center_x, COMPOUND_WALL_Y, compound_length, col=COL_WALL_GATE, height=2.35, thickness=0.24, mat=MATS['wall'])

left_boundary_center_y = (FRONT_YARD_FRONT_Y + PROPERTY_BACK_Y) / 2
left_boundary_len = PROPERTY_BACK_Y - FRONT_YARD_FRONT_Y
wall_y('Property_LeftBoundary', PROPERTY_LEFT_X, left_boundary_center_y, left_boundary_len, col=COL_WALL_GATE, height=2.25, thickness=0.24, mat=MATS['wall'])
wall_x('Property_BackBoundary', (PROPERTY_LEFT_X+PROPERTY_RIGHT_X)/2, PROPERTY_BACK_Y, PROPERTY_RIGHT_X-PROPERTY_LEFT_X, col=COL_WALL_GATE, height=2.25, thickness=0.24, mat=MATS['wall'])

# ----------------------- RIGHT-SIDE PASSING ------------------
passing_center_x = (PASSING_INNER_X + PASSING_OUTER_X) / 2
passing_center_y = (PASSING_START_Y + PASSING_END_Y) / 2
passing_len = PASSING_END_Y - PASSING_START_Y
make_cube('NarrowPassing_Floor', (passing_center_x, passing_center_y, 0.05), (PASSING_W, passing_len, 0.10), MATS['earth'], COL_PASSING, 0.015)
wall_y('Passing_RightBoundaryWall', PASSING_OUTER_X, passing_center_y, passing_len+0.6, col=COL_PASSING, height=2.7, thickness=0.24, mat=MATS['wall'])

# Inner wall split around the gate opening.
gate_half = GATE_W/2
lower_start, lower_end = PASSING_START_Y, GATE_CENTER_Y-gate_half
upper_start, upper_end = GATE_CENTER_Y+gate_half, PASSING_END_Y
wall_y('Passing_InnerWall_BeforeGate', PASSING_INNER_X, (lower_start+lower_end)/2, lower_end-lower_start, col=COL_PASSING, height=2.55, thickness=0.24, mat=MATS['wall'])
wall_y('Passing_InnerWall_AfterGate', PASSING_INNER_X, (upper_start+upper_end)/2, upper_end-upper_start, col=COL_PASSING, height=2.55, thickness=0.24, mat=MATS['wall'])

# Gate is in LEFT wall of passage: walk up passage, then turn left into courtyard.
make_cube('MainGate', (PASSING_INNER_X-0.02, GATE_CENTER_Y, GATE_H/2), (0.15, GATE_W, GATE_H), MATS['metal'], COL_WALL_GATE, 0.02)
wall_x('Passing_EndWall', passing_center_x, PASSING_END_Y, PASSING_W, col=COL_PASSING, height=2.55, thickness=0.24, mat=MATS['wall'])

# --------------------------- COURTYARD -----------------------
court_center_x = (COURTYARD_LEFT_X + COURTYARD_RIGHT_X) / 2
court_center_y = (COURTYARD_FRONT_Y + COURTYARD_BACK_Y) / 2
court_w = COURTYARD_RIGHT_X - COURTYARD_LEFT_X
court_d = COURTYARD_BACK_Y - COURTYARD_FRONT_Y
make_cube('Courtyard_Floor', (court_center_x, court_center_y, 0.035), (court_w,court_d,0.07), MATS['earth'], COL_COURT, 0.02)

# -------------------------- LIVING WING ----------------------
make_cube('LivingWing_MainBlock', (LIVING_CENTER_X,LIVING_CENTER_Y,LIVING_H/2), (LIVING_W,LIVING_D,LIVING_H), MATS['house'], COL_LIVING, 0.035)
make_cube('LivingWing_RoofSlab', (LIVING_CENTER_X,LIVING_CENTER_Y,LIVING_H+0.12), (LIVING_W+0.18,LIVING_D+0.18,0.18), MATS['wall'], COL_LIVING, 0.025)

# ---------------------------- VERANDA ------------------------
living_front_y = LIVING_CENTER_Y - LIVING_D/2
veranda_center_y = living_front_y - VERANDA_DEPTH/2
make_cube('Veranda_Floor', (LIVING_CENTER_X,veranda_center_y,0.13), (LIVING_W-0.4,VERANDA_DEPTH,0.26), MATS['veranda'], COL_VERANDA, 0.02)
PILLAR_Y = veranda_center_y - 0.48
add_pillar('Veranda_Pillar_01', LIVING_CENTER_X-2.35, PILLAR_Y)
add_pillar('Veranda_Pillar_02', LIVING_CENTER_X+1.75, PILLAR_Y)

door_y = living_front_y - 0.04
make_cube('Door_GrandparentsRoom', (LIVING_CENTER_X-2.05,door_y,1.08), (0.98,0.10,2.16), MATS['wood'], COL_LIVING, 0.02)
make_cube('Door_PlayerRoom', (LIVING_CENTER_X+1.70,door_y,1.08), (0.98,0.10,2.16), MATS['wood'], COL_LIVING, 0.02)
add_charpai('Charpai_01', LIVING_CENTER_X-2.85, veranda_center_y-0.12)
add_charpai('Charpai_02', LIVING_CENTER_X-0.55, veranda_center_y-0.12)
add_charpai('Charpai_03', LIVING_CENTER_X+2.05, veranda_center_y-0.12)

# --------------------------- SERVICE AREA --------------------
make_cube('ServiceArea_Platform', (4.15,4.55,0.10), (3.25,4.25,0.20), MATS['service'], COL_SERVICE, 0.02)
make_cube('Handpump_Base', (3.65,3.55,0.18), (1.35,1.25,0.18), MATS['service'], COL_PROPS, 0.02)
make_cube('Handpump_Body', (3.65,3.55,0.82), (0.26,0.26,1.45), MATS['metal'], COL_PROPS, 0.02)
make_cube('Handpump_Spout', (3.35,3.55,1.12), (0.70,0.12,0.12), MATS['metal'], COL_PROPS, 0.015)
pump_handle = make_cube('Handpump_Handle', (3.68,3.55,1.62), (0.12,0.88,0.12), MATS['metal'], COL_PROPS, 0.015)
pump_handle.rotation_euler.x = math.radians(18)

WASH_X, WASH_Y = 4.65, 6.35
for i in range(4):
    step_h = 0.12 + i*0.10
    make_cube(f'Washroom_Step_{i+1}', (WASH_X,5.20+i*0.27,step_h/2), (1.60-i*0.10,0.34,step_h), MATS['service'], COL_SERVICE, 0.012)
make_cube('Washroom_Block', (WASH_X,WASH_Y,1.55), (2.0,2.35,3.10), MATS['service'], COL_SERVICE, 0.03)
make_cube('Washroom_Door', (WASH_X,WASH_Y-1.20,1.12), (0.82,0.08,2.10), MATS['wood'], COL_SERVICE, 0.015)

make_cube('UtilityStorage_Block', (2.30,6.70,1.35), (2.25,2.25,2.70), MATS['service'], COL_SERVICE, 0.03)
make_cube('UtilityStorage_Door', (2.30,5.54,1.05), (0.82,0.08,1.95), MATS['wood'], COL_SERVICE, 0.015)

# -------------------------- ROOF STAIRS ----------------------
STAIR_X, STAIR_START_Y = 0.75, 7.60
for i in range(9):
    make_cube(f'RoofStair_{i+1:02d}', (STAIR_X,STAIR_START_Y+i*0.28,0.12+i*0.16), (1.15,0.34,0.24+i*0.01), MATS['brick'], COL_SERVICE, 0.012)

# ----------------------- REAR UTILITY AREA -------------------
rear_center_y = (REAR_FRONT_Y + REAR_BACK_Y)/2
rear_depth = REAR_BACK_Y - REAR_FRONT_Y
make_cube('RearUtility_Ground', (-1.3,rear_center_y,0.03), (13.6,rear_depth,0.08), MATS['rear'], COL_REAR, 0.02)
for x in (-2.8,0.8):
    make_cube(f'Rear_ClotheslinePost_{x}', (x,10.15,1.15), (0.10,0.10,2.30), MATS['wood'], COL_REAR, 0.01)

# ---------------------- PLAYER SCALE REFERENCE ---------------
bpy.ops.mesh.primitive_capsule_add(radius=0.28, depth=1.20, location=(1.25,-5.2,0.88))
player = bpy.context.object
player.name = 'REF_Player_Approx_1p75m'
player.data.materials.append(MATS['player'])
move_to_collection(player, COL_GUIDES)

# ----------------------------- LABELS ------------------------
add_label('ROAD', (0,-12.0,0.16), 0.48)
add_label('NAALA', (-2.4,-9.4,0.18), 0.40)
add_label('FRONT YARD', (0.0,-5.1,0.18), 0.50)
add_label('OLD STORAGE', (-6.3,-4.65,2.72), 0.32)
add_label('COMPOUND WALL', (-1.0,-1.72,2.52), 0.34)
add_label('NARROW PASSING', (7.25,1.65,0.16), 0.30)
add_label('MAIN GATE', (6.10,4.55,2.70), 0.32)
add_label('COURTYARD', (-1.5,2.1,0.15), 0.50)
add_label('LIVING WING', (-3.5,8.0,3.35), 0.44)
add_label('VERANDA', (-3.5,5.2,0.32), 0.38)
add_label('SERVICE', (4.15,3.0,0.28), 0.34)
add_label('REAR UTILITY', (-1.3,10.15,0.18), 0.42)

# --------------------------- REVIEW CAMERA -------------------
cam_data = bpy.data.cameras.new('ReviewCamera')
cam = bpy.data.objects.new('ReviewCamera', cam_data)
COL_CAMERA.objects.link(cam)
cam_data.type = 'PERSP'
cam_data.lens = 48
cam.location = (21.5,-26.0,24.0)
point_at(cam, (-0.5,0.0,1.0))
bpy.context.scene.camera = cam

sun_data = bpy.data.lights.new('ReviewSun', type='SUN')
sun = bpy.data.objects.new('ReviewSun', sun_data)
COL_CAMERA.objects.link(sun)
sun.rotation_euler = (math.radians(35), math.radians(-10), math.radians(-35))
sun_data.energy = 2.0

area_data = bpy.data.lights.new('ReviewFill', type='AREA')
area = bpy.data.objects.new('ReviewFill', area_data)
COL_CAMERA.objects.link(area)
area.location = (-7.0,-5.0,14.0)
area_data.energy = 700
area_data.size = 10.0
point_at(area, (-0.5,1.0,0.8))

# -------------------------- SCENE SETTINGS -------------------
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
scene.world.color = (0.045,0.045,0.045)
scene['GNOL_BlockoutVersion'] = 'GrandparentsHouse_Inspired_v002'
scene['GNOL_DesignLaw'] = 'Inspired by Nani house; gameplay-first, not 1:1 reconstruction.'

print('')
print('============================================================')
print(" GAME OF NO LORE - GRANDPARENTS' HOUSE BLOCKOUT v002")
print('============================================================')
print('Built successfully.')
print('Core route:')
print('Road -> Naala Crossing -> Front Yard -> Right Passing')
print('-> turn LEFT through Main Gate -> Courtyard')
print('-> Veranda / Living Wing / Service Area / Rear Utility')
print('')
print('Toggle 90_GUIDES off for a clean view.')
print('This is a game-adapted layout, NOT a 1:1 replica.')
print('============================================================')
