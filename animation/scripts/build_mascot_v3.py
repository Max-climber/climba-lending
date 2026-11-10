from pathlib import Path
import math
import runpy

import bpy
from mathutils import Vector


ROOT = Path('/Users/maksimizrailev/Desktop/climba-lending-2')
OUT = ROOT / 'animation/output/mascot_v3'
OUT.mkdir(parents=True, exist_ok=True)

# Build the proven smooth base, then turn it into the correctly scaled V3 master.
runpy.run_path(str(ROOT / 'animation/scripts/build_mascot_v2.py'), run_name='__main__')

rig = bpy.data.objects.get('CLIMBA_MASCOT_V2_RIG')
rig.name = 'CLIMBA_MASCOT_V3_RIG'

# The base character is 3.20 m from sole to ear. Uniform rig scaling keeps all
# face and body proportions intact while setting the production height to 1.35 m.
production_scale = 1.35 / 3.20
rig.scale = (production_scale,) * 3
bpy.context.view_layer.update()

rig['character_height_m'] = 1.35
rig['surface_style'] = 'smooth_cartoon_no_fur'
rig['reference_set'] = 'Climba SVG orthographic set'
rig['usage'] = 'video_production'

scene = bpy.context.scene
scene.render.resolution_x = 720
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.render.engine = 'BLENDER_EEVEE'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.world.color = (0.025, 0.028, 0.038)

cam = bpy.data.objects.get('CAM_MASCOT_FRONT')
cam.data.lens = 70

def look_at(target):
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()

target = (0, 0, 0.69)
views = {
    'front': ((0, -3.65, 0.74), target),
    'three_quarter': ((2.15, -3.15, 0.90), target),
    'side': ((3.75, 0, 0.74), target),
    'back': ((0, 3.65, 0.74), target),
}

# Reframe the existing studio lights around the 1.35 m character.
for light in [obj for obj in bpy.data.objects if obj.type == 'LIGHT']:
    light.location *= 0.52
    light.data.energy *= 0.70

for label, (location, aim) in views.items():
    cam.location = location
    look_at(aim)
    scene.render.filepath = str(OUT / f'mascot_v3_{label}.png')
    bpy.ops.render.render(write_still=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'climba_mascot_v3_master.blend'))
print(f'Saved V3 master and four approval renders to {OUT}')
