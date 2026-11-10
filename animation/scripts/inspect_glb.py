from pathlib import Path
import bpy
from mathutils import Vector

SRC = Path('/Users/maksimizrailev/Downloads/aiprintgen_Model-73d1083e_e4717411.glb')
OUT = Path('/Users/maksimizrailev/Desktop/climba-lending-2/animation/output/glb_inspect')
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))

meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in meshes:
    dims = tuple(round(v, 4) for v in o.dimensions)
    mats = [m.name for m in o.data.materials if m]
    print(f'MESH name={o.name!r} verts={len(o.data.vertices)} dims={dims} materials={mats}')

min_v = Vector((1e9, 1e9, 1e9))
max_v = Vector((-1e9, -1e9, -1e9))
for o in meshes:
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c)
        min_v = Vector((min(min_v.x, p.x), min(min_v.y, p.y), min(min_v.z, p.z)))
        max_v = Vector((max(max_v.x, p.x), max(max_v.y, p.y), max(max_v.z, p.z)))
print('TOTAL_BOUNDS', tuple(round(v, 4) for v in (max_v - min_v)))

# Set a neutral studio camera around the imported asset for visual inspection.
if meshes:
    # The GLB currently contains one mesh; keep it intact for inspection.
    asset = meshes[0]
    asset.name = 'GLB_MASCOT_SOURCE_COMBINED'
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    asset.location = (0, 0, 0)
    # Normalize to 1.35 m tall while preserving the imported silhouette.
    height = asset.dimensions.z
    if height > 0:
        asset.scale = (1.35 / height,) * 3
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    asset['source_file'] = str(SRC)
    asset['target_height_m'] = 1.35

    mat = bpy.data.materials.new('Inspection floor')
    mat.diffuse_color = (0.05, 0.055, 0.07, 1)
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    floor = bpy.context.object
    floor.data.materials.append(mat)

    for loc, energy, size in [((-3, -4, 4), 900, 4), ((3, -2, 3), 600, 3), ((0, 3, 4), 800, 3)]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = 'DISK'
        light.data.size = size
        light.rotation_euler = (0, 0, 0)

    bpy.ops.object.camera_add(location=(0, -3.9, 0.72))
    cam = bpy.context.object
    cam.data.lens = 62
    cam.rotation_euler = ((Vector((0, 0, 0.68)) - cam.location).to_track_quat('-Z', 'Y').to_euler())
    bpy.context.scene.camera = cam
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 720
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    if scene.world is None:
        scene.world = bpy.data.worlds.new('Inspection World')
    scene.world.color = (0.02, 0.02, 0.025)
    scene.render.filepath = str(OUT / 'glb_front.png')
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'glb_source_normalized.blend'))
