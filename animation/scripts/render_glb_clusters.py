from pathlib import Path
import bpy
from mathutils import Vector

SRC = Path('/Users/maksimizrailev/Downloads/aiprintgen_Model-73d1083e_e4717411.glb')
OUT = Path('/Users/maksimizrailev/Desktop/climba-lending-2/animation/output/glb_clusters')
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
source = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
source.rotation_euler[2] = -1.57079632679
bpy.context.view_layer.update()
source.scale = (1.35 / source.dimensions.z,) * 3
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.context.view_layer.objects.active = source
source.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')
parts = [o for o in bpy.context.selected_objects if o.type == 'MESH']
ys = sorted((o.matrix_world @ Vector((0, 0, 0))).y for o in parts)
low, high = ys[len(ys)//3], ys[(2*len(ys))//3]
zs = sorted((o.matrix_world @ Vector((0, 0, 0))).z for o in parts)
floor = zs[len(zs)//2]
groups = {
    'column_low_top': [o for o in parts if (o.matrix_world @ Vector((0, 0, 0))).y <= low and (o.matrix_world @ Vector((0, 0, 0))).z >= floor],
    'column_mid_top': [o for o in parts if low < (o.matrix_world @ Vector((0, 0, 0))).y <= high and (o.matrix_world @ Vector((0, 0, 0))).z >= floor],
    'column_high_top': [o for o in parts if (o.matrix_world @ Vector((0, 0, 0))).y > high and (o.matrix_world @ Vector((0, 0, 0))).z >= floor],
    'column_low_bottom': [o for o in parts if (o.matrix_world @ Vector((0, 0, 0))).y <= low and (o.matrix_world @ Vector((0, 0, 0))).z < floor],
    'column_mid_bottom': [o for o in parts if low < (o.matrix_world @ Vector((0, 0, 0))).y <= high and (o.matrix_world @ Vector((0, 0, 0))).z < floor],
    'column_high_bottom': [o for o in parts if (o.matrix_world @ Vector((0, 0, 0))).y > high and (o.matrix_world @ Vector((0, 0, 0))).z < floor],
}
for name, group in groups.items():
    for o in parts: o.hide_render = o not in group
    bpy.ops.object.camera_add(location=(3.9, 0, 0.72))
    cam = bpy.context.object
    cam.data.lens = 52
    cam.rotation_euler = (Vector((0, 0, 0.68)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene = bpy.context.scene
    scene.camera = cam
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 480
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.world = bpy.data.worlds.new(name + '_world')
    scene.world.color = (0.03, 0.03, 0.04)
    scene.render.filepath = str(OUT / f'{name}.png')
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
