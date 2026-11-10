from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path('/Users/maksimizrailev/Desktop/climba-lending-2')
WORKING = ROOT / 'animation/output/climba_real_hall_working.blend'
PREVIEW = ROOT / 'animation/output/route_7b_balance_guides.png'


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def material(name, color):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Emission Color'].default_value = (*color, 1)
    bsdf.inputs['Emission Strength'].default_value = 2.0
    return mat


scene = bpy.context.scene

old = bpy.data.collections.get('ROUTE_7B_BALANCE_GUIDES')
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    old = bpy.data.collections.new('ROUTE_7B_BALANCE_GUIDES')
    scene.collection.children.link(old)

orange = material('Route guide orange', (1.0, 0.12, 0.025))
blue = material('Center of mass guide', (0.05, 0.55, 1.0))

# Western vertical face of scan sector 3. Coordinates follow the visible black
# line from the supplied app recording: compact feet and alternating balance
# moves rather than long dynamic reaches.
contacts = [
    ('START_L_FOOT', (-12.03, 6.00, 0.56)),
    ('START_R_FOOT', (-12.03, 6.58, 0.70)),
    ('START_L_HAND', (-12.03, 5.90, 1.34)),
    ('START_R_HAND', (-12.03, 6.72, 1.52)),
    ('MOVE_01_L_FOOT', (-12.03, 5.67, 1.16)),
    ('MOVE_02_R_HAND', (-12.03, 6.82, 2.10)),
    ('MOVE_03_R_FOOT', (-12.03, 6.50, 1.62)),
    ('MOVE_04_L_HAND', (-12.03, 5.78, 2.52)),
    ('MOVE_05_L_FOOT', (-12.03, 5.58, 2.02)),
    ('MOVE_06_R_HAND', (-12.03, 6.47, 3.02)),
    ('MOVE_07_R_FOOT', (-12.03, 6.25, 2.47)),
    ('MOVE_08_L_HAND', (-12.03, 5.72, 3.54)),
    ('MOVE_09_L_FOOT', (-12.03, 5.62, 3.00)),
    ('FINISH_R_HAND', (-12.03, 6.30, 4.02)),
    ('FINISH_MATCH', (-12.03, 5.98, 4.12)),
]

for index, (name, position) in enumerate(contacts, 1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.095, location=position)
    marker = bpy.context.object
    marker.name = f'7B_{index:02d}_{name}'
    for collection in list(marker.users_collection):
        collection.objects.unlink(marker)
    old.objects.link(marker)
    marker.data.materials.append(orange)

# Center-of-mass path deliberately shifts laterally over each supporting foot.
com_points = [
    (-11.48, 6.25, 1.00),
    (-11.48, 5.80, 1.34),
    (-11.48, 6.48, 1.76),
    (-11.48, 5.72, 2.14),
    (-11.48, 6.30, 2.58),
    (-11.48, 5.73, 3.02),
    (-11.48, 6.08, 3.48),
]
curve_data = bpy.data.curves.new('7B_BALANCE_COM_PATH_DATA', 'CURVE')
curve_data.dimensions = '3D'
curve_data.bevel_depth = 0.035
curve_data.bevel_resolution = 4
spline = curve_data.splines.new('POLY')
spline.points.add(len(com_points) - 1)
for point, co in zip(spline.points, com_points):
    point.co = (*co, 1)
curve = bpy.data.objects.new('7B_BALANCE_CENTER_OF_MASS_PATH', curve_data)
old.objects.link(curve)
curve_data.materials.append(blue)

# Block the mascot socket through the seven weight-transfer beats.
socket = bpy.data.objects.get('MASCOT_SOCKET_REPLACE_HERE')
if socket:
    socket.rotation_mode = 'XYZ'
    for frame, co, lean in [
        (361, com_points[0], -3),
        (391, com_points[0], -3),
        (426, com_points[1], 5),
        (461, com_points[2], -5),
        (496, com_points[3], 4),
        (531, com_points[4], -4),
        (566, com_points[5], 3),
        (601, com_points[6], 0),
    ]:
        # Mascot front axis is -Y; -90° makes it face the western wall.
        socket.location = co
        socket.rotation_euler = (math.radians(lean), 0, math.radians(-90))
        socket.keyframe_insert('location', frame=frame)
        socket.keyframe_insert('rotation_euler', frame=frame)

# Technical route camera.
camera_data = bpy.data.cameras.new('CAM_ROUTE_GUIDE_DATA')
camera_data.lens = 58
camera = bpy.data.objects.new('CAM_ROUTE_GUIDE', camera_data)
scene.collection.objects.link(camera)
camera.location = (-6.9, 6.05, 2.35)
look_at(camera, (-12.03, 6.05, 2.30))
scene.camera = camera

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(PREVIEW)
scene.frame_set(496)

bpy.ops.wm.save_as_mainfile(filepath=str(WORKING))
bpy.ops.render.render(write_still=True)
print(f'Saved route blocking and preview: {PREVIEW}')
