import bpy
from mathutils import Vector

RIG_COLLECTION = "GNOL_RenderRig"
TARGET_NAME = "GNOL_CameraTarget"
CAMERA_NAME = "GNOL_ArtCamera"
KEY_NAME = "GNOL_KeyLight"
FILL_NAME = "GNOL_FillLight"

def get_or_create_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def remove_object_if_exists(name):
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)

def aim_at(obj, target):
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene = bpy.context.scene
rig = get_or_create_collection(RIG_COLLECTION)

# Clean only our generated rig, never the user's artwork.
for name in [TARGET_NAME, CAMERA_NAME, KEY_NAME, FILL_NAME]:
    remove_object_if_exists(name)

# Camera target roughly at the visual center of a small wall/door test.
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, 0.0, 1.15))
target = bpy.context.object
target.name = TARGET_NAME

# Move target into rig collection.
for col in list(target.users_collection):
    col.objects.unlink(target)
rig.objects.link(target)

# Candidate fixed 3/4 orthographic camera.
camera_data = bpy.data.cameras.new(CAMERA_NAME)
camera = bpy.data.objects.new(CAMERA_NAME, camera_data)
rig.objects.link(camera)
camera.location = (5.8, -5.8, 8.0)
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 5.4
camera_data.lens = 50
aim_at(camera, target.location)
scene.camera = camera

# Soft key area light.
key_data = bpy.data.lights.new(KEY_NAME, type='AREA')
key = bpy.data.objects.new(KEY_NAME, key_data)
rig.objects.link(key)
key.location = (-3.5, -4.0, 6.5)
key_data.energy = 650
key_data.shape = 'DISK'
key_data.size = 5.0
aim_at(key, Vector((0.0, 0.0, 0.8)))

# Gentle fill to avoid harsh CG contrast.
fill_data = bpy.data.lights.new(FILL_NAME, type='AREA')
fill = bpy.data.objects.new(FILL_NAME, fill_data)
rig.objects.link(fill)
fill.location = (4.0, 2.0, 4.0)
fill_data.energy = 220
fill_data.size = 4.0
aim_at(fill, Vector((0.0, 0.0, 0.8)))

# Rendering baseline.
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except Exception:
        pass

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True

# Neutral world. Film is transparent, but viewport/render previews remain pleasant.
scene.world.color = (0.055, 0.055, 0.055)

# Mild ambient occlusion where supported.
if hasattr(scene, "eevee"):
    try:
        scene.eevee.use_gtao = True
        scene.eevee.gtao_distance = 3
        scene.eevee.gtao_factor = 0.8
    except Exception:
        pass

print("Game of No Lore art test rig created.")
print("Camera:", CAMERA_NAME)
print("Resolution: 1024 x 1024 RGBA")
print("Keep this camera unchanged while comparing Micro Test A variants.")
