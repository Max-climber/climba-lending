from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path('/Users/maksimizrailev/Desktop/climba-lending-2')
WORKING = ROOT / 'animation/output/climba_real_hall_working.blend'
UI = ROOT / 'animation/ui/reference'
PREVIEW = ROOT / 'animation/output/phone_ui'
PREVIEW.mkdir(parents=True, exist_ok=True)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def solid_material(name, color, roughness=0.4):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


def image_material(name, path):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(str(path), check_existing=True)
    texture.interpolation = 'Linear'
    mat.node_tree.links.new(texture.outputs['Color'], emission.inputs['Color'])
    emission.inputs['Strength'].default_value = 1.0
    mat.node_tree.links.new(emission.outputs['Emission'], out.inputs['Surface'])
    return mat


def rounded_cube(name, loc, scale, material, bevel=0.08, collection=None):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    mod = obj.modifiers.new('Rounded corners', 'BEVEL')
    mod.width = bevel
    mod.segments = 8
    if collection:
        for current in list(obj.users_collection):
            current.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def screen_plane(name, material, y, collection):
    bpy.ops.mesh.primitive_plane_add(
        size=2, location=(20, y, 2.0), rotation=(math.radians(90), 0, 0)
    )
    plane = bpy.context.object
    plane.name = name
    plane.scale = (0.57, 1.24, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plane.data.materials.append(material)
    for current in list(plane.users_collection):
        current.objects.unlink(plane)
    collection.objects.link(plane)
    return plane


def text(name, body, loc, size, color_mat, collection, align='CENTER'):
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(90), 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = align
    obj.data.align_y = 'CENTER'
    obj.data.size = size
    obj.data.extrude = 0.006
    obj.data.bevel_depth = 0.002
    obj.data.materials.append(color_mat)
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def visibility(obj, visible_ranges):
    frames = {1, 1110}
    for start, end in visible_ranges:
        frames.update({max(1, start - 1), start, end, min(1110, end + 1)})
    for frame in sorted(frames):
        visible = any(start <= frame <= end for start, end in visible_ranges)
        obj.hide_render = not visible
        obj.keyframe_insert('hide_render', frame=frame)


scene = bpy.context.scene

existing = bpy.data.collections.get('PHONE_UI_STAGE')
if existing:
    for obj in list(existing.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    existing = bpy.data.collections.new('PHONE_UI_STAGE')
    scene.collection.children.link(existing)

black = solid_material('Phone graphite', (0.008, 0.009, 0.012), 0.22)
white = solid_material('UI white', (0.98, 0.98, 0.99), 0.32)
ink = solid_material('UI ink', (0.055, 0.049, 0.060), 0.35)
orange = solid_material('Climba coral', (1.0, 0.16, 0.09), 0.30)
muted = solid_material('UI muted', (0.78, 0.78, 0.82), 0.42)

phone = rounded_cube('PHONE_BODY', (20, 0, 2.0), (0.63, 0.065, 1.34), black, 0.14, existing)
route = screen_plane('SCREEN_ROUTE_7B', image_material('Screen route 7B', UI / 'frame_63.png'), -0.071, existing)
ranking = screen_plane('SCREEN_RANKING', image_material('Screen ranking', UI / 'frame_67.png'), -0.073, existing)
profile = screen_plane('SCREEN_PROFILE', image_material('Screen profile', UI / 'frame_77.png'), -0.075, existing)

visibility(route, [(676, 795)])
visibility(ranking, [(796, 900)])
visibility(profile, [(901, 930)])

# Animated leaderboard row: the mascot profile rises from fourth to first.
rank_row = rounded_cube('RANK_CLIMBA_ROW', (20, -0.120, 0.92), (0.49, 0.012, 0.135), white, 0.055, existing)
rank_medal = rounded_cube('RANK_CLIMBA_MEDAL', (19.60, -0.148, 0.92), (0.105, 0.012, 0.105), orange, 0.045, existing)
rank_name = text('RANK_CLIMBA_NAME', 'climba', (19.91, -0.155, 0.92), 0.095, ink, existing, align='LEFT')
rank_xp = text('RANK_CLIMBA_XP', '+2430 XP', (20.30, -0.155, 0.92), 0.065, orange, existing)
rank_four = text('RANK_NUMBER_4', '4', (19.60, -0.173, 0.92), 0.10, white, existing)
rank_one = text('RANK_NUMBER_1', '1', (19.60, -0.175, 2.30), 0.10, white, existing)

for obj in (rank_row, rank_medal, rank_name, rank_xp):
    visibility(obj, [(826, 900)])
    obj.location.z = 0.92
    obj.keyframe_insert('location', frame=826)
    obj.keyframe_insert('location', frame=844)
    obj.location.z = 2.30
    obj.keyframe_insert('location', frame=884)
    obj.keyframe_insert('location', frame=900)
visibility(rank_four, [(826, 860)])
rank_four.location.z = 0.92
rank_four.keyframe_insert('location', frame=826)
rank_four.keyframe_insert('location', frame=844)
rank_four.location.z = 2.30
rank_four.keyframe_insert('location', frame=884)
visibility(rank_one, [(861, 900)])

# Exact requested tag replaces the empty state shown in the source recording.
tag_patch = rounded_cube('TAG_BALANCE_PATCH', (20, -0.092, 1.77), (0.35, 0.012, 0.09), white, 0.05, existing)
tag_text = text('TAG_BALANCE_TEXT', 'Баланс', (20, -0.108, 1.77), 0.105, ink, existing)
visibility(tag_patch, [(676, 795)])
visibility(tag_text, [(676, 795)])

# Confirmation sheet requested in the storyboard.
sheet_parts = []
sheet_parts.append(rounded_cube('LOGBOOK_SHEET', (20, -0.125, 1.15), (0.57, 0.018, 0.63), white, 0.10, existing))
sheet_parts.append(text('LOGBOOK_TITLE', 'Трасса №3.-1.29', (20, -0.150, 1.56), 0.13, ink, existing))
sheet_parts.append(text('LOGBOOK_QUESTION', 'Ты пролез трассу?', (20, -0.150, 1.34), 0.115, ink, existing))
sheet_parts.append(rounded_cube('BUTTON_NO', (19.72, -0.150, 0.87), (0.27, 0.015, 0.13), white, 0.05, existing))
sheet_parts.append(rounded_cube('BUTTON_YES', (20.28, -0.150, 0.87), (0.27, 0.015, 0.13), orange, 0.05, existing))
sheet_parts.append(text('BUTTON_NO_TEXT', 'Нет, в проект', (19.72, -0.170, 0.87), 0.068, ink, existing))
sheet_parts.append(text('BUTTON_YES_TEXT', 'Да, в логбук', (20.28, -0.170, 0.87), 0.068, white, existing))
for obj in sheet_parts:
    visibility(obj, [(736, 795)])

# Finger/tap cue on the positive button.
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=(20.33, -0.22, 0.82))
tap = bpy.context.object
tap.name = 'PAW_TAP_GUIDE'
tap.scale = (0.10, 0.04, 0.10)
tap.data.materials.append(orange)
for current in list(tap.users_collection):
    current.objects.unlink(tap)
existing.objects.link(tap)
visibility(tap, [(782, 795)])

# Dedicated softbox for the physical phone and 3D UI overlays. Screenshot
# planes are emissive, so their original app colors stay unchanged.
bpy.ops.object.light_add(type='AREA', location=(20, -3.2, 4.8))
phone_light = bpy.context.object
phone_light.name = 'PHONE_UI_SOFTBOX'
phone_light.data.energy = 1300
phone_light.data.size = 4.0
look_at(phone_light, (20, 0, 1.7))
for current in list(phone_light.users_collection):
    current.objects.unlink(phone_light)
existing.objects.link(phone_light)

# Dedicated close-up camera for the isolated UI stage.
camera = bpy.data.objects.get('CAM_07_PHONE_CLOSE')
camera.location = (20, -6.7, 2.0)
camera.data.lens = 70
look_at(camera, (20, 0, 2.0))

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 540
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.camera = camera

for frame, filename in [(700, 'phone_route.png'), (760, 'phone_confirm.png'), (840, 'phone_ranking.png')]:
    scene.frame_set(frame)
    scene.render.filepath = str(PREVIEW / filename)
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=str(WORKING))
print(f'Saved phone UI stage and previews to {PREVIEW}')
