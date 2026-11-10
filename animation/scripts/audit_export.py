from pathlib import Path
import math

import bpy
from mathutils import Vector


OUT = Path('/Users/maksimizrailev/Desktop/climba-lending-2/animation/output/export_audit_textured')
OUT.mkdir(parents=True, exist_ok=True)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.display.shading.light = 'STUDIO'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'WORLD'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.background_type = 'THEME'

meshes = [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.vertices) > 100]

bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.lens = 52
scene.camera = camera

for index, target in enumerate(meshes, 1):
    for obj in meshes:
        obj.hide_render = obj != target

    center = target.matrix_world @ (sum((Vector(corner) for corner in target.bound_box), Vector()) / 8)
    radius = max(target.dimensions)
    camera.location = center + Vector((0, -radius * 1.7, radius * 0.12))
    look_at(camera, center)
    scene.render.filepath = str(OUT / f'sector_{index}_front.png')
    bpy.ops.render.render(write_still=True)

    camera.location = center + Vector((radius * 0.95, -radius * 1.35, radius * 0.38))
    look_at(camera, center)
    scene.render.filepath = str(OUT / f'sector_{index}_angle.png')
    bpy.ops.render.render(write_still=True)

print(f'Rendered {len(meshes)} sectors into {OUT}')
