from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path('/Users/maksimizrailev/Desktop/climba-lending-2')
OUT = ROOT / 'animation/output/mascot_v2'
OUT.mkdir(parents=True, exist_ok=True)


def clean():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def mat(name, rgb, roughness=0.42):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*rgb, 1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return material


def sphere(name, loc, scale, material, rotation=(0, 0, 0), segments=64, rings=40):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.data.materials.append(material)
    return obj


def curve(name, points, material, bevel=0.025):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 16
    data.bevel_depth = bevel
    data.bevel_resolution = 5
    spline = data.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(material)
    return obj


def parent_bone(obj, rig, bone):
    matrix = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = 'BONE'
    obj.parent_bone = bone
    obj.matrix_world = matrix


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


clean()

INK = mat('Mascot charcoal', (0.055, 0.049, 0.062), 0.34)
INNER = mat('Ear inner', (0.105, 0.095, 0.115), 0.42)
WHITE = mat('Mascot warm white', (0.94, 0.945, 0.965), 0.39)
RIM = mat('Mascot cool rim', (0.76, 0.79, 0.84), 0.44)
MUZZLE = mat('Muzzle', (0.84, 0.86, 0.90), 0.41)
EYE = mat('Eye white', (0.995, 0.995, 1.0), 0.20)
PUPIL = mat('Pupil', (0.045, 0.041, 0.050), 0.20)
SPARK = mat('Eye sparkle', (1.0, 1.0, 1.0), 0.08)
BG = mat('Studio backdrop', (0.055, 0.060, 0.075), 0.65)

# Animation-ready skeleton.
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
rig = bpy.context.object
rig.name = 'CLIMBA_MASCOT_V2_RIG'
root = rig.data.edit_bones[0]
root.name = 'root'
root.head = (0, 0, 0.15)
root.tail = (0, 0, 0.75)

def add_bone(name, head, tail, parent):
    bone = rig.data.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.parent = parent
    return bone

spine = add_bone('spine', (0, 0, 0.65), (0, 0, 1.65), root)
head_b = add_bone('head', (0, 0, 1.55), (0, 0, 2.55), spine)
arm_l = add_bone('arm.L', (-0.35, 0, 1.45), (-0.85, 0, 0.82), spine)
arm_r = add_bone('arm.R', (0.35, 0, 1.45), (0.85, 0, 0.82), spine)
leg_l = add_bone('leg.L', (-0.22, 0, 0.68), (-0.33, 0, 0.10), root)
leg_r = add_bone('leg.R', (0.22, 0, 0.68), (0.33, 0, 0.10), root)
bpy.ops.object.mode_set(mode='OBJECT')

# Body: black pear silhouette with a large white belly, matching the flat mascot.
body = sphere('Body black silhouette', (0, 0, 1.12), (0.68, 0.48, 0.86), INK)
belly_rim = sphere('Belly cool rim', (0, -0.435, 1.13), (0.53, 0.075, 0.61), RIM)
belly = sphere('Belly white', (0, -0.493, 1.17), (0.49, 0.045, 0.56), WHITE)

# Oversized rounded-square head. Two nested ellipsoids recreate the cool outline.
head_rim = sphere('Head cool rim', (0, 0, 2.18), (1.02, 0.66, 0.80), RIM)
head = sphere('Head white', (0, -0.055, 2.21), (0.95, 0.62, 0.73), WHITE)

# Rounded ears with visible inner pads.
ear_l = sphere('Ear L', (-0.70, 0.00, 2.80), (0.38, 0.25, 0.39), INK, rotation=(0, math.radians(-8), math.radians(-8)))
ear_r = sphere('Ear R', (0.70, 0.00, 2.80), (0.38, 0.25, 0.39), INK, rotation=(0, math.radians(8), math.radians(8)))
ear_in_l = sphere('Ear inner L', (-0.70, -0.225, 2.81), (0.25, 0.035, 0.27), INNER)
ear_in_r = sphere('Ear inner R', (0.70, -0.225, 2.81), (0.25, 0.035, 0.27), INNER)

# Short tapered limbs; intentionally paw-like, not human cylinders.
arm_left = sphere('Arm L', (-0.64, -0.01, 1.20), (0.25, 0.25, 0.63), INK, rotation=(0, math.radians(-16), math.radians(-8)))
arm_right = sphere('Arm R', (0.64, -0.01, 1.20), (0.25, 0.25, 0.63), INK, rotation=(0, math.radians(16), math.radians(8)))
foot_l = sphere('Foot L', (-0.31, -0.08, 0.37), (0.32, 0.31, 0.33), INK, rotation=(math.radians(4), 0, math.radians(-3)))
foot_r = sphere('Foot R', (0.31, -0.08, 0.37), (0.32, 0.31, 0.33), INK, rotation=(math.radians(4), 0, math.radians(3)))

# Signature oversized eyes and tilted panda patches.
face_parts = []
for side, x, angle in [('L', -0.37, -12), ('R', 0.37, 12)]:
    patch = sphere(f'Eye patch {side}', (x, -0.625, 2.30), (0.36, 0.065, 0.46), INK, rotation=(math.radians(2), math.radians(angle), 0))
    eye = sphere(f'Eye white {side}', (x, -0.687, 2.32), (0.205, 0.035, 0.285), EYE)
    pupil_x = x + (0.035 if side == 'L' else -0.035)
    pupil = sphere(f'Pupil {side}', (pupil_x, -0.722, 2.28), (0.125, 0.022, 0.185), PUPIL)
    shine_big = sphere(f'Spark big {side}', (pupil_x - 0.047, -0.747, 2.39), (0.055, 0.010, 0.074), SPARK, segments=32, rings=20)
    shine_small = sphere(f'Spark small {side}', (pupil_x + 0.055, -0.748, 2.20), (0.026, 0.009, 0.033), SPARK, segments=24, rings=16)
    face_parts += [patch, eye, pupil, shine_big, shine_small]

# Small muzzle, triangular nose, and the exact friendly double-curve smile.
muzzle = sphere('Muzzle pad', (0, -0.681, 1.98), (0.25, 0.043, 0.19), MUZZLE)
nose = sphere('Nose', (0, -0.731, 2.07), (0.115, 0.028, 0.075), INK, rotation=(math.radians(8), 0, 0), segments=40, rings=24)
mouth_center = curve('Mouth center', [(0, -0.755, 2.02), (0, -0.762, 1.94)], INK, 0.021)
smile_l = curve('Smile L', [(0, -0.759, 1.95), (-0.10, -0.760, 1.88), (-0.22, -0.754, 1.96)], INK, 0.024)
smile_r = curve('Smile R', [(0, -0.759, 1.95), (0.10, -0.760, 1.88), (0.22, -0.754, 1.96)], INK, 0.024)

for obj in (body, belly_rim, belly):
    parent_bone(obj, rig, 'spine')
for obj in (head_rim, head, ear_l, ear_r, ear_in_l, ear_in_r, muzzle, nose, mouth_center, smile_l, smile_r, *face_parts):
    parent_bone(obj, rig, 'head')
parent_bone(arm_left, rig, 'arm.L')
parent_bone(arm_right, rig, 'arm.R')
parent_bone(foot_l, rig, 'leg.L')
parent_bone(foot_r, rig, 'leg.R')

# Neutral pose and subtle mascot stance.
rig.pose.bones['arm.L'].rotation_mode = 'XYZ'
rig.pose.bones['arm.R'].rotation_mode = 'XYZ'
rig.pose.bones['arm.L'].rotation_euler[1] = math.radians(-4)
rig.pose.bones['arm.R'].rotation_euler[1] = math.radians(4)

# Studio floor and curved-looking dark background.
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 1.2, 0.02))
floor = bpy.context.object
floor.name = 'Studio floor'
floor.data.materials.append(BG)

for name, loc, energy, size, color in [
    ('Key', (-3.2, -4.5, 5.2), 1250, 4.5, (1.0, 0.88, 0.80)),
    ('Fill', (3.5, -3.0, 3.4), 850, 3.5, (0.62, 0.76, 1.0)),
    ('Rim', (0.5, 2.6, 4.3), 1100, 3.0, (1.0, 0.32, 0.18)),
]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    look_at(light, (0, 0, 1.6))

bpy.ops.object.camera_add(location=(0, -8.5, 1.72))
cam = bpy.context.object
cam.name = 'CAM_MASCOT_FRONT'
cam.data.lens = 62
look_at(cam, (0, 0, 1.55))

scene = bpy.context.scene
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 720
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world.color = (0.025, 0.028, 0.038)
scene.view_settings.look = 'AgX - Medium High Contrast'

bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'climba_mascot_v2.blend'))
scene.render.filepath = str(OUT / 'mascot_v2_front.png')
bpy.ops.render.render(write_still=True)

# Three-quarter verification view.
cam.location = (4.5, -7.0, 2.15)
look_at(cam, (0, 0, 1.55))
scene.render.filepath = str(OUT / 'mascot_v2_three_quarter.png')
bpy.ops.render.render(write_still=True)

print(f'Saved mascot V2 to {OUT}')
