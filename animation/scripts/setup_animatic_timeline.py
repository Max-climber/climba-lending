from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path('/Users/maksimizrailev/Desktop/climba-lending-2')
WORKING = ROOT / 'animation/output/climba_real_hall_working.blend'


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def make_camera(collection, name, location, target, lens):
    data = bpy.data.cameras.new(name + '_DATA')
    data.lens = lens
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj


scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 1110

scene.timeline_markers.clear()
shots = [
    (1, 'S01_DOOR_ENTER'),
    (61, 'S02_FACE_DISCOVERY'),
    (121, 'S03_ENTER_EYE'),
    (196, 'S04_MAP_FLIGHT'),
    (301, 'S05_CHALK_BIRD_VIEW'),
    (361, 'S06_START_HOLDS'),
    (391, 'S07_BALANCE_CLIMB'),
    (601, 'S08_FINISH_MATCH'),
    (646, 'S09_DROP_TO_MAT'),
    (676, 'S10_PHONE_REVEAL'),
    (736, 'S11_ROUTE_CARD_7B_BALANCE'),
    (796, 'S12_ADD_LOGBOOK'),
    (826, 'S13_RANK_4_TO_1'),
    (901, 'S14_TROPHY_EYES'),
    (946, 'S15_CHALK_AVALANCHE'),
    (1006, 'S16_PAWS_IN_CHALK'),
    (1036, 'S17_THUMBS_UP_ENDCARD'),
]
for frame, name in shots:
    scene.timeline_markers.new(name, frame=frame)

old = bpy.data.collections.get('SHOT_CAMERAS')
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    old = bpy.data.collections.new('SHOT_CAMERAS')
    scene.collection.children.link(old)

cameras = {
    'CAM_01_ENTRY_WIDE': ((-5.15, -8.5, 2.55), (-5.1, 1.6, 1.45), 48),
    'CAM_02_MASCOT_CLOSE': ((-5.15, -1.3, 1.62), (-5.15, 1.35, 1.62), 76),
    'CAM_03_EYE_MACRO': ((-5.15, 0.2, 1.72), (-5.15, 1.35, 1.75), 110),
    'CAM_04_MAP_FLY': ((-10.8, -0.5, 5.4), (-5.2, 7.1, 2.7), 28),
    'CAM_05_BIRD_VIEW': ((-5.2, 2.0, 7.8), (-5.2, 2.0, 0.2), 42),
    'CAM_06_ROUTE_SIDE': ((0.0, 3.0, 2.8), (-5.2, 7.0, 2.6), 58),
    'CAM_07_PHONE_CLOSE': ((-4.35, 0.0, 1.45), (-5.15, 1.35, 1.25), 88),
    'CAM_08_CHALK_WIDE': ((-5.15, -5.5, 2.4), (-5.15, 1.35, 1.0), 52),
}
created = {}
for name, (location, target, lens) in cameras.items():
    created[name] = make_camera(old, name, location, target, lens)

# Bind the broad camera changes to timeline markers. Fine cuts will be adjusted
# after route contact points and the final mascot are approved.
bindings = [
    (1, 'CAM_01_ENTRY_WIDE'),
    (61, 'CAM_02_MASCOT_CLOSE'),
    (121, 'CAM_03_EYE_MACRO'),
    (196, 'CAM_04_MAP_FLY'),
    (301, 'CAM_05_BIRD_VIEW'),
    (361, 'CAM_06_ROUTE_SIDE'),
    (676, 'CAM_07_PHONE_CLOSE'),
    (946, 'CAM_08_CHALK_WIDE'),
]
for frame, camera_name in bindings:
    marker = scene.timeline_markers.new('CUT_' + camera_name, frame=frame)
    marker.camera = created[camera_name]

scene.camera = created['CAM_01_ENTRY_WIDE']

notes = bpy.data.texts.get('CLIMBA_ANIMATIC_NOTES') or bpy.data.texts.new('CLIMBA_ANIMATIC_NOTES')
notes.clear()
notes.write(
    'Mascot replacement: parent the final rig to MASCOT_SOCKET_REPLACE_HERE, '\
    'zero location/rotation, and match a ~1.55 m world height.\n'\
    'Route: scan sector 3, black holds, 7B, tag BALANCE.\n'\
    'Climbing rule: hips close to wall; weight moves over supporting foot before each reach.\n'
)

bpy.ops.wm.save_as_mainfile(filepath=str(WORKING))
print(f'Configured {len(shots)} story markers and {len(created)} cameras in {WORKING}')
