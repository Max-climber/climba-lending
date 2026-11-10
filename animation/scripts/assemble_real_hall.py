from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path('/Users/maksimizrailev/Desktop/climba-lending-2')
PANDA_BLEND = ROOT / 'animation/output/mascot_v2/climba_mascot_v2.blend'
OUT_DIR = ROOT / 'animation/output'
OUT_BLEND = OUT_DIR / 'climba_real_hall_working.blend'
OUT_RENDER = OUT_DIR / 'real_hall_panda_blocking.png'


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def append_panda():
    wanted_prefixes = (
        'CLIMBA_MASCOT_V2_RIG', 'Body ', 'Head', 'Ear ', 'Eye patch ', 'Eye ',
        'Pupil ', 'Spark ', 'Nose', 'Muzzle', 'Mouth', 'Smile', 'Belly',
        'Arm ', 'Foot '
    )
    with bpy.data.libraries.load(str(PANDA_BLEND), link=False) as (data_from, data_to):
        data_to.objects = [
            name for name in data_from.objects
            if any(name.startswith(prefix) for prefix in wanted_prefixes)
        ]

    collection = bpy.data.collections.new('MASCOT_PANDA')
    bpy.context.scene.collection.children.link(collection)
    for obj in data_to.objects:
        if obj is not None and not obj.users_collection:
            collection.objects.link(obj)
    return bpy.data.objects['CLIMBA_MASCOT_V2_RIG'], collection


def area_light(name, location, energy, size, color, target):
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    light.data.color = color
    look_at(light, target)
    return light


OUT_DIR.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene

# Keep all three true scan sectors. Rename them for production readability.
scan_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.vertices) > 100]
for index, obj in enumerate(scan_meshes, 1):
    obj.name = f'LUCH_SCAN_SECTOR_{index}'

rig, panda_collection = append_panda()

# Stable replacement point. A future final mascot only needs to be parented to
# this empty with zeroed transforms; cameras and animation can stay untouched.
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-5.15, 1.35, 0.12))
mascot_socket = bpy.context.object
mascot_socket.name = 'MASCOT_SOCKET_REPLACE_HERE'
mascot_socket.rotation_euler[2] = math.radians(145)
mascot_socket.empty_display_size = 0.45
rig.parent = mascot_socket

# The scan is in metres. Mascot source was intentionally oversized for modelling.
# Final mascot height is approximately 1.55 m.
rig.scale = (0.48, 0.48, 0.48)
rig.location = (0, 0, 0)
rig.rotation_euler = (0, 0, 0)

# Freeze the first balanced stance for the integration proof.
scene.frame_set(1)

# Camera looks into the third hall sector from a diagonal that keeps both the
# real wall texture and the mascot silhouette readable.
bpy.ops.object.camera_add(location=(-5.15, -8.5, 2.55))
camera = bpy.context.object
camera.name = 'CAM_REAL_HALL_BLOCKING'
camera.data.lens = 58
look_at(camera, (-5.10, 1.60, 1.35))
scene.camera = camera

area_light(
    'Key softbox', (0.0, 0.0, 7.5), 1800, 5.5, (1.0, 0.88, 0.78),
    (-4.8, 5.8, 2.2)
)
area_light(
    'Cool fill', (-10.0, 2.0, 5.0), 1200, 4.0, (0.55, 0.70, 1.0),
    (-5.0, 6.0, 2.0)
)
area_light(
    'Wall wash', (-3.0, 11.0, 6.0), 1600, 5.0, (1.0, 0.58, 0.38),
    (-5.0, 7.0, 2.5)
)

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 540
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT_RENDER)
scene.render.film_transparent = False
scene.world.color = (0.015, 0.018, 0.025)
scene.view_settings.look = 'AgX - Medium High Contrast'

# Store external scan textures inside the working scene so it remains portable.
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
bpy.ops.render.render(write_still=True)
print(f'Saved working scene: {OUT_BLEND}')
print(f'Saved integration render: {OUT_RENDER}')
