from pathlib import Path
import bpy
from mathutils import Vector

SRC = Path('/Users/maksimizrailev/Downloads/aiprintgen_Model-73d1083e_e4717411.glb')
OUT = Path('/Users/maksimizrailev/Desktop/climba-lending-2/animation/output/mascot_glb_rig_ready')
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
source = next((o for o in bpy.context.scene.objects if o.type == 'MESH'), None)
if source is None:
    raise RuntimeError('GLB does not contain a mesh')

source.name = 'MASCOT_GLB_SOURCE'
source.rotation_euler[2] = -1.57079632679
bpy.context.view_layer.update()
height = source.dimensions.z
source.scale = (1.35 / height,) * 3
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Separate only disconnected shells; this does not cut through the sculpt.
bpy.context.view_layer.objects.active = source
source.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')

parts = [o for o in bpy.context.selected_objects if o.type == 'MESH']
parts.sort(key=lambda o: o.name)
collection = bpy.data.collections.new('MASCOT_GLB_PARTS_FOR_RIG')
bpy.context.scene.collection.children.link(collection)
for index, obj in enumerate(parts, 1):
    obj.name = f'MASCOT_PART_{index:03d}'
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    obj['rig_status'] = 'separate shell; inspect before binding'

print(f'GLB separated into {len(parts)} disconnected mesh shells')
for obj in parts:
    print('PART', obj.name, tuple(round(v, 4) for v in obj.dimensions), len(obj.data.vertices))

bpy.ops.object.armature_add(location=(0, 0, 0))
rig = bpy.context.object
rig.name = 'CLIMBA_MASCOT_GLB_RIG'
rig.data.name = 'CLIMBA_MASCOT_GLB_RIG_DATA'
rig.show_in_front = True
rig['character_height_m'] = 1.35
rig['source_model'] = str(SRC)
rig['next_step'] = 'place deform bones after parts are approved'
for bone in rig.data.bones:
    bone.name = 'root'

mat = bpy.data.materials.new('Studio floor')
mat.diffuse_color = (0.045, 0.05, 0.065, 1)
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
floor = bpy.context.object
floor.name = 'Studio floor'
floor.data.materials.append(mat)

for loc, energy, size in [((-3, -4, 4), 900, 4), ((3, -2, 3), 600, 3), ((0, 3, 4), 800, 3)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    light.rotation_euler = (Vector((0, 0, 0.68)) - light.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.object.camera_add(location=(0, -3.8, 0.72))
cam = bpy.context.object
cam.name = 'CAM_GLB_FRONT'
cam.data.lens = 62
cam.rotation_euler = (Vector((0, 0, 0.68)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene = bpy.context.scene
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 720
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds.new('Mascot studio world')
scene.world.color = (0.02, 0.02, 0.025)
scene.render.filepath = str(OUT / 'glb_front_parts.png')
bpy.ops.render.render(write_still=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'climba_mascot_glb_rig_ready.blend'))
print(f'Saved rig-ready source to {OUT}')
