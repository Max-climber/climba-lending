from pathlib import Path

import bpy


OUT = Path('/Users/maksimizrailev/Desktop/climba-lending-2/animation/output/ik_debug')
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.camera = bpy.data.objects['CAM_ROUTE_GUIDE']
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

scan = [o for o in bpy.data.objects if o.name.startswith('LUCH_SCAN_SECTOR_')]
for obj in scan:
    obj.hide_render = True

for frame in (391, 496, 601):
    scene.frame_set(frame)
    scene.render.filepath = str(OUT / f'ik_frame_{frame}.png')
    bpy.ops.render.render(write_still=True)

print(f'Rendered IK debug frames to {OUT}')
