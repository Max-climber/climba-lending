from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "animation" / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights, bpy.data.armatures):
        pass


def material(name, color, roughness=0.48, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True


def uv(name, location, scale, mat, segments=48, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth(obj)
    obj.data.materials.append(mat)
    return obj


def cube(name, location, scale, mat, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 4
    return obj


def text_obj(body, location, size, mat, align="CENTER"):
    bpy.ops.object.text_add(location=location, rotation=(math.radians(90), 0, 0))
    obj = bpy.context.object
    obj.data.body = body
    obj.data.align_x = align
    obj.data.size = size
    obj.data.extrude = 0.012
    obj.data.bevel_depth = 0.004
    obj.data.materials.append(mat)
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def parent_to_bone(obj, rig, bone_name):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_world = world


clean_scene()

# Palette sampled from the supplied mascot and Climba UI.
WHITE = material("Panda white", (0.91, 0.92, 0.95), 0.42)
INK = material("Panda ink", (0.045, 0.04, 0.055), 0.38)
IRIS = material("Warm eyes", (0.20, 0.16, 0.20), 0.25)
HIGHLIGHT = material("Eye sparkle", (1.0, 1.0, 1.0), 0.12)
ORANGE = material("Climba orange", (1.0, 0.16, 0.08), 0.34)
WALL = material("Warm concrete", (0.31, 0.30, 0.29), 0.82)
MAT = material("Landing mat", (0.12, 0.13, 0.14), 0.9)
HOLD = material("Black route holds", (0.018, 0.018, 0.021), 0.58)
SOFT_GRAY = material("Label", (0.78, 0.80, 0.84), 0.5)

# Vertical climbing wall and mat.
wall = cube("Vertical wall", (0, 1.20, 3.2), (3.25, 0.18, 3.2), WALL, 0.04)
mat = cube("Soft landing mat", (0, 0.0, 0.12), (3.7, 2.25, 0.12), MAT, 0.12)

# One-color technical route: small black footholds and slopers.
hold_specs = [
    (-0.72, 0.92, 0.65, (0.24, 0.10, 0.10), 12),
    (0.18, 0.92, 0.90, (0.20, 0.09, 0.09), -15),
    (-0.28, 0.92, 1.35, (0.19, 0.11, 0.08), 24),
    (0.70, 0.92, 1.72, (0.25, 0.10, 0.12), -28),
    (-0.62, 0.92, 2.10, (0.29, 0.12, 0.11), 15),
    (0.12, 0.92, 2.55, (0.24, 0.11, 0.10), -18),
    (0.82, 0.92, 3.03, (0.30, 0.12, 0.12), 8),
    (0.20, 0.92, 3.52, (0.23, 0.10, 0.09), 26),
    (-0.70, 0.92, 3.90, (0.28, 0.12, 0.12), -12),
    (0.05, 0.92, 4.38, (0.38, 0.14, 0.12), 0),
]
for idx, (x, y, z, sc, rot) in enumerate(hold_specs, 1):
    h = uv(f"7B black hold {idx:02d}", (x, y, z), sc, HOLD, 32, 20)
    h.rotation_euler[1] = math.radians(rot)

# Route badge.
badge = uv("7B badge", (-1.42, 0.85, 0.80), (0.34, 0.07, 0.34), ORANGE, 40, 24)
badge.rotation_euler[0] = math.radians(90)
text_obj("7B", (-1.42, 0.77, 0.74), 0.22, WHITE)
text_obj("BALANCE", (-1.40, 0.79, 0.33), 0.12, SOFT_GRAY)

# Armature for a compact production-friendly mascot rig.
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0.15, 1.60))
rig = bpy.context.object
rig.name = "CLIMBA_PANDA_RIG"
arm = rig.data
arm.name = "Climba Panda Skeleton"
root = arm.edit_bones[0]
root.name = "root"
root.head = (0, 0, 0)
root.tail = (0, 0, 0.45)

def bone(name, head, tail, parent=root):
    b = arm.edit_bones.new(name)
    b.head, b.tail, b.parent = head, tail, parent
    return b

spine = bone("spine", (0, 0, 0.38), (0, 0, 1.14))
head_b = bone("head", (0, 0, 1.08), (0, 0, 1.72), spine)
arm_l = bone("arm.L", (-0.18, 0, 0.98), (-0.88, 0, 0.66), spine)
arm_r = bone("arm.R", (0.18, 0, 0.98), (0.88, 0, 0.66), spine)
leg_l = bone("leg.L", (-0.18, 0, 0.38), (-0.43, 0, -0.42), root)
leg_r = bone("leg.R", (0.18, 0, 0.38), (0.43, 0, -0.42), root)
bpy.ops.object.mode_set(mode="POSE")
for pb in rig.pose.bones:
    pb.rotation_mode = "XYZ"
bpy.ops.object.mode_set(mode="OBJECT")

# Body pieces; the silhouette stays faithful to the supplied rounded mascot.
belly = uv("Body white", (0, 0.03, 2.03), (0.76, 0.46, 0.90), WHITE)
chest = uv("Body dark", (0, 0.10, 2.24), (0.82, 0.48, 0.78), INK)
belly.location.y = -0.35
head = uv("Head", (0, -0.02, 3.25), (1.02, 0.62, 0.84), WHITE)
ear_l = uv("Ear L", (-0.68, 0.02, 3.90), (0.35, 0.22, 0.36), INK)
ear_r = uv("Ear R", (0.68, 0.02, 3.90), (0.35, 0.22, 0.36), INK)

for obj in (belly, chest):
    parent_to_bone(obj, rig, "spine")
for obj in (head, ear_l, ear_r):
    parent_to_bone(obj, rig, "head")

# Face is placed toward camera (-Y).
for side, x in (("L", -0.36), ("R", 0.36)):
    patch = uv(f"Eye patch {side}", (x, -0.58, 3.40), (0.34, 0.09, 0.43), INK, 40, 28)
    eye = uv(f"Eye {side}", (x, -0.67, 3.43), (0.18, 0.055, 0.24), WHITE, 40, 28)
    pupil = uv(f"Pupil {side}", (x + (-0.02 if side == "L" else 0.02), -0.725, 3.42), (0.10, 0.035, 0.15), IRIS, 36, 24)
    sparkle = uv(f"Sparkle {side}", (x - 0.045, -0.76, 3.52), (0.035, 0.014, 0.05), HIGHLIGHT, 24, 16)
    for obj in (patch, eye, pupil, sparkle):
        parent_to_bone(obj, rig, "head")

nose = uv("Nose", (0, -0.72, 3.13), (0.13, 0.07, 0.09), INK, 32, 20)
parent_to_bone(nose, rig, "head")

limbs = [
    ("Arm L", (-0.64, -0.03, 2.18), (0.27, 0.25, 0.68), "arm.L", -18),
    ("Arm R", (0.64, -0.03, 2.18), (0.27, 0.25, 0.68), "arm.R", 18),
    ("Leg L", (-0.35, 0.0, 1.18), (0.31, 0.30, 0.56), "leg.L", -6),
    ("Leg R", (0.35, 0.0, 1.18), (0.31, 0.30, 0.56), "leg.R", 6),
]
for name, loc, sc, bname, rot in limbs:
    obj = uv(name, loc, sc, INK)
    obj.rotation_euler[1] = math.radians(rot)
    parent_to_bone(obj, rig, bname)

# Controlled balance animation: weight shifts happen before each reaching limb.
rig.location = (0.0, -0.05, 0.0)
for frame, x, z, roll in [
    (1, -0.25, 0.00, -5),
    (32, 0.18, 0.38, 6),
    (64, -0.12, 0.82, -4),
    (96, 0.24, 1.22, 5),
    (128, 0.02, 1.66, 0),
]:
    rig.location.x = x
    rig.location.z = z
    rig.rotation_euler[1] = math.radians(roll)
    rig.keyframe_insert("location", frame=frame)
    rig.keyframe_insert("rotation_euler", frame=frame)

pose_keys = {
    "arm.L": [(1, -20), (32, 26), (64, -14), (96, 30), (128, 6)],
    "arm.R": [(1, 18), (32, -15), (64, 28), (96, -10), (128, -4)],
    "leg.L": [(1, 8), (32, -24), (64, 20), (96, -20), (128, 5)],
    "leg.R": [(1, -8), (32, 22), (64, -18), (96, 24), (128, -5)],
}
for name, keys in pose_keys.items():
    pb = rig.pose.bones[name]
    for frame, degrees in keys:
        pb.rotation_euler[1] = math.radians(degrees)
        pb.keyframe_insert("rotation_euler", frame=frame)

# Lighting.
bpy.ops.object.light_add(type="AREA", location=(-3.2, -4.0, 6.8))
key = bpy.context.object
key.name = "Key softbox"
key.data.energy = 1050
key.data.shape = "DISK"
key.data.size = 5.0
look_at(key, (0, 0.2, 2.5))

bpy.ops.object.light_add(type="AREA", location=(3.5, -1.5, 4.2))
rim = bpy.context.object
rim.name = "Warm rim"
rim.data.energy = 720
rim.data.color = (1.0, 0.35, 0.18)
rim.data.size = 3.0
look_at(rim, (0, 0.4, 2.6))

bpy.ops.object.light_add(type="AREA", location=(0, 2.0, 5.8))
top = bpy.context.object
top.name = "Wall wash"
top.data.energy = 900
top.data.size = 4.0
look_at(top, (0, 1.0, 2.5))

# Portrait camera.
bpy.ops.object.camera_add(location=(0, -11.5, 3.0))
camera = bpy.context.object
camera.name = "CAM_PORTRAIT"
camera.data.lens = 52
look_at(camera, (0, 0.2, 2.6))
bpy.context.scene.camera = camera

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 128
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 540
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.018, 0.018, 0.025)
scene.render.filepath = str(OUTPUT / "panda_balance_keyframe.png")
scene.frame_set(64)

# Color management tuned for a clean app-commercial look.
scene.view_settings.look = "AgX - Medium High Contrast"

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "climba_panda_balance_prototype.blend"))
bpy.ops.render.render(write_still=True)
print(f"Saved prototype to {OUTPUT}")
