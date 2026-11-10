from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path('/Users/maksimizrailev/Desktop/climba-lending-2')
WORKING = ROOT / 'animation/output/climba_real_hall_working.blend'
PREVIEW = ROOT / 'animation/output/route_7b_ik_blocking.png'


scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
camera = bpy.data.objects['CAM_ROUTE_GUIDE']
rig = bpy.data.objects['CLIMBA_MASCOT_V2_RIG']
socket = bpy.data.objects['MASCOT_SOCKET_REPLACE_HERE']
guide_collection = bpy.data.collections['ROUTE_7B_BALANCE_GUIDES']


def cast_to_wall(approx, offset=0.075):
    direction = (Vector(approx) - camera.location).normalized()
    hit, location, normal, _, obj, _ = scene.ray_cast(
        depsgraph, camera.location, direction, distance=30
    )
    if not hit or not obj.name.startswith('LUCH_SCAN_SECTOR_3'):
        raise RuntimeError(f'No sector-3 wall hit for {approx}')
    return location + normal * offset, normal


# Move all route markers from rough plane coordinates onto the actual scanned
# surface. The normal offset prevents z-fighting and keeps guides visible.
markers = sorted(
    [o for o in guide_collection.objects if o.name.startswith('7B_')],
    key=lambda obj: obj.name,
)
contact = {}
normal_by_name = {}
for marker in markers:
    corrected, normal = cast_to_wall(marker.location)
    marker.location = corrected
    short_name = marker.name.split('_', 2)[2]
    contact[short_name] = corrected.copy()
    normal_by_name[short_name] = normal.copy()


def replace_empty(name):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    empty = bpy.data.objects.new(name, None)
    guide_collection.objects.link(empty)
    empty.empty_display_type = 'SPHERE'
    empty.empty_display_size = 0.12
    return empty


targets = {
    'hand.L': replace_empty('IK_TARGET_HAND_L'),
    'hand.R': replace_empty('IK_TARGET_HAND_R'),
    'foot.L': replace_empty('IK_TARGET_FOOT_L'),
    'foot.R': replace_empty('IK_TARGET_FOOT_R'),
}


def key_target(target, sequence):
    previous = None
    for frame, contact_name in sequence:
        destination = contact[contact_name]
        if previous is not None:
            target.location = previous
            target.keyframe_insert('location', frame=max(frame - 10, 1))
        target.location = destination
        target.keyframe_insert('location', frame=frame)
        previous = destination.copy()


key_target(targets['hand.L'], [
    (391, 'START_L_HAND'), (496, 'MOVE_04_L_HAND'),
    (566, 'MOVE_08_L_HAND'), (601, 'FINISH_MATCH'),
])
key_target(targets['hand.R'], [
    (391, 'START_R_HAND'), (461, 'MOVE_02_R_HAND'),
    (531, 'MOVE_06_R_HAND'), (601, 'FINISH_R_HAND'),
])
key_target(targets['foot.L'], [
    (391, 'START_L_FOOT'), (426, 'MOVE_01_L_FOOT'),
    (531, 'MOVE_05_L_FOOT'), (566, 'MOVE_09_L_FOOT'),
])
key_target(targets['foot.R'], [
    (391, 'START_R_FOOT'), (496, 'MOVE_03_R_FOOT'),
    (566, 'MOVE_07_R_FOOT'),
])

# Attach the placeholder rig. These constraints are intentionally isolated so
# a final externally supplied rig can be retargeted without changing timing.
for bone_name, target_key in [
    ('arm.L', 'hand.L'), ('arm.R', 'hand.R'),
    ('leg.L', 'foot.L'), ('leg.R', 'foot.R'),
]:
    pose_bone = rig.pose.bones.get(bone_name)
    if not pose_bone:
        continue
    for constraint in list(pose_bone.constraints):
        if constraint.name.startswith('CLIMBA_IK_'):
            pose_bone.constraints.remove(constraint)
    ik = pose_bone.constraints.new('IK')
    ik.name = 'CLIMBA_IK_' + bone_name
    ik.target = targets[target_key]
    ik.chain_count = 1
    ik.use_stretch = True

# Correct center-of-mass blocking against the real wall, keeping the body
# roughly 55 cm off the surface. The lateral shift precedes each hand move.
body_beats = [
    (391, (6.25, 1.05), -3),
    (426, (5.82, 1.38), 5),
    (461, (6.42, 1.76), -5),
    (496, (5.77, 2.12), 4),
    (531, (6.28, 2.56), -4),
    (566, (5.76, 3.00), 3),
    (601, (6.06, 3.46), 0),
]
for frame, (wall_y, wall_z), lean in body_beats:
    wall_point, normal = cast_to_wall((-12.0, wall_y, wall_z), offset=0.0)
    socket.location = wall_point + normal * 0.62
    socket.rotation_mode = 'XYZ'
    socket.rotation_euler = (math.radians(lean), 0, math.radians(-90))
    socket.keyframe_insert('location', frame=frame)
    socket.keyframe_insert('rotation_euler', frame=frame)

# Head/eye intention: look at the next hand target before reaching.
look_target = replace_empty('LOOK_TARGET_NEXT_HOLD')
for frame, contact_name in [
    (391, 'MOVE_02_R_HAND'),
    (451, 'MOVE_04_L_HAND'),
    (486, 'MOVE_06_R_HAND'),
    (531, 'MOVE_08_L_HAND'),
    (566, 'FINISH_R_HAND'),
]:
    look_target.location = contact[contact_name]
    look_target.keyframe_insert('location', frame=frame)

head = rig.pose.bones.get('head')
if head:
    for constraint in list(head.constraints):
        if constraint.name == 'CLIMBA_LOOK_NEXT_HOLD':
            head.constraints.remove(constraint)
    track = head.constraints.new('DAMPED_TRACK')
    track.name = 'CLIMBA_LOOK_NEXT_HOLD'
    track.target = look_target
    track.track_axis = 'TRACK_Y'
    track.influence = 0.38

scene.camera = camera
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(PREVIEW)
scene.frame_set(531)

bpy.ops.wm.save_as_mainfile(filepath=str(WORKING))
bpy.ops.render.render(write_still=True)
print(f'Saved real-surface route IK blocking: {PREVIEW}')
