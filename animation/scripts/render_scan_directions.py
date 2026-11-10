from pathlib import Path
import math

import bpy
from mathutils import Vector


OUT = Path('/Users/maksimizrailev/Desktop/climba-lending-2/animation/output/scan_directions')
OUT.mkdir(parents=True, exist_ok=True)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 540
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'WORLD'
scene.display.shading.background_type = 'THEME'

meshes = [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.vertices) > 100]
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.lens = 38
scene.camera = camera

# Manually derived navigable interior points from scan bounds.
centers = [
    Vector((5.7, -0.8, 2.0)),
    Vector((-5.1, -4.2, 2.0)),
    Vector((-5.3, 6.8, 2.0)),
]
headings = [('N', 90), ('E', 0), ('S', -90), ('W', 180)]

for sector_index, center in enumerate(centers, 1):
    camera.location = center
    for label, angle in headings:
        radians = math.radians(angle)
        direction = Vector((math.cos(radians), math.sin(radians), 0))
        look_at(camera, center + direction * 5 + Vector((0, 0, 0.25)))
        scene.render.filepath = str(OUT / f'sector_{sector_index}_{label}.png')
        bpy.ops.render.render(write_still=True)

print(f'Rendered directional scan views to {OUT}')
