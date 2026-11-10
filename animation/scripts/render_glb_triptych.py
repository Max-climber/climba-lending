from pathlib import Path
import bpy
from mathutils import Vector

SRC = Path('/Users/maksimizrailev/Downloads/aiprintgen_Model-73d1083e_e4717411.glb')
OUT = Path('/Users/maksimizrailev/Desktop/climba-lending-2/animation/output/glb_triptych')
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
mesh = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
mesh.rotation_euler[2] = -1.57079632679
bpy.context.view_layer.update()
mesh.scale = (1.35 / mesh.dimensions.z,) * 3
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

mat = bpy.data.materials.new('Floor')
mat.diffuse_color = (0.06, 0.065, 0.08, 1)
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat)
for loc, energy, size in [((4, -3, 4), 1200, 4), ((2, 3, 3), 700, 3), ((-3, 0, 4), 900, 3)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object
    l.data.energy = energy
    l.data.size = size
    l.rotation_euler = (Vector((0, 0, 0.65)) - l.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add(location=(3.9, 0, 0.75))
cam = bpy.context.object
cam.data.lens = 52
cam.rotation_euler = (Vector((0, 0, 0.68)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene = bpy.context.scene
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds.new('World')
scene.world.color = (0.02, 0.02, 0.025)
scene.render.filepath = str(OUT / 'triptych_front.png')
bpy.ops.render.render(write_still=True)
