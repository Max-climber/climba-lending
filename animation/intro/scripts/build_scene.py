"""Build the empty intro scene: 3D "climba" logo on a seamless cyclorama in the sampled palette.

Usage:
  Blender --background --python animation/intro/scripts/build_scene.py
Outputs (animation/intro/output/):
  climba_intro_scene.blend, scene_16x9.png, scene_9x16.png
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

INTRO_DIR = Path(__file__).resolve().parents[1]
LOGO_SVG = INTRO_DIR / "refs" / "climba_logo.svg"
OUTPUT_DIR = INTRO_DIR / "output"
SCENE_BLEND = OUTPUT_DIR / "climba_intro_scene.blend"

LETTERS = "climba"
LOGO_HEIGHT = 1.5
LETTER_DEPTH = 0.4
LETTER_BEVEL = 0.02
# Measured on the reference: gap between letters ≈ 1.6 × average letter width,
# word spans 12%–88% of the 16:9 frame width.
GAP_TO_LETTER_WIDTH = 1.6
FPS = 24
FRAME_COUNT = 288  # 12 s = 4 clips × 3 s; fade while she is still laughing

# Palette sampled from reference frames (see CLIMBA_INTRO_SCRIPT.md), screen-space bottom → top.
SKY_GRADIENT = [(0.0, "#C4D2F5"), (0.45, "#C3D1F4"), (0.70, "#BBCAE9"), (1.0, "#A0A6C2")]
CONTACT_SHADOW = "#7D8497"
LETTER_SHADE = "#000714"
LETTER_LIT = "#14181C"

CAMERA_LENS = 50.0
CAMERA_SENSOR = 36.0
CAMERA_TILT_DEG = 5.0
CAMERA_TARGET_Z = 0.62
CAMERAS = {
    "CAM_16x9": {"word_span": 0.76, "resolution": (1920, 1080)},
    "CAM_9x16": {"word_span": 0.92, "resolution": (1080, 1920)},
}


def hex_to_linear(value: str) -> tuple[float, float, float, float]:
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    rgb = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    return (*map(channel, rgb), 1.0)


def reset_scene() -> bpy.types.Scene:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, FRAME_COUNT
    return scene


# --- Logo -------------------------------------------------------------------


def import_logo_curves() -> list[bpy.types.Object]:
    bpy.ops.import_curve.svg(filepath=str(LOGO_SVG))
    curves = sorted(
        (o for o in bpy.context.scene.objects if o.type == "CURVE"),
        key=lambda o: min((o.matrix_world @ Vector(c)).x for c in o.bound_box),
    )
    if len(curves) != len(LETTERS):
        raise RuntimeError(f"Expected {len(LETTERS)} curves, got {len(curves)}")
    return curves


def world_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return lo, hi


def normalize_logo(curves: list[bpy.types.Object]) -> None:
    """Scale the word to LOGO_HEIGHT and stand it upright on the floor (Z=0)."""
    lo, hi = world_bounds(curves)
    scale = LOGO_HEIGHT / (hi.y - lo.y)

    for obj in curves:
        obj.data.dimensions = "2D"
        obj.data.fill_mode = "BOTH"
        obj.data.extrude = LETTER_DEPTH / 2 / scale
        obj.data.bevel_depth = LETTER_BEVEL / scale
        obj.data.bevel_resolution = 4
        obj.location = (obj.location - Vector((0.0, lo.y, 0.0))) * scale
        obj.scale *= scale
        obj.rotation_euler.x = math.radians(90)


def letters_to_meshes(curves: list[bpy.types.Object], material: bpy.types.Material) -> list[bpy.types.Object]:
    for obj, letter in zip(curves, LETTERS):
        select_only(obj)
        bpy.ops.object.convert(target="MESH")
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        obj.name = obj.data.name = f"letter_{letter}"
        obj.data.materials.clear()
        obj.data.materials.append(material)
    return curves


def space_letters(letters: list[bpy.types.Object]) -> float:
    """Lay letters out left to right with wide, equal gaps; returns the total word width."""
    widths = [world_bounds([o])[1].x - world_bounds([o])[0].x for o in letters]
    gap = GAP_TO_LETTER_WIDTH * sum(widths) / len(widths)
    word_width = sum(widths) + gap * (len(letters) - 1)

    cursor = -word_width / 2
    for obj, width in zip(letters, widths):
        obj.location.x += cursor - world_bounds([obj])[0].x
        cursor += width + gap
    bpy.context.view_layer.update()
    return word_width


def split_i_dot(letter_i: bpy.types.Object) -> None:
    """The dot is a separate animated prop (the gag), so it becomes its own object."""
    _, top = world_bounds([letter_i])
    select_only(letter_i)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.mesh.separate(type="LOOSE")

    parts = list(bpy.context.selected_objects)
    is_dot = {o: (world_bounds([o])[0].z + world_bounds([o])[1].z) / 2 > top.z * 0.7 for o in parts}
    for name, group in (("letter_i", [o for o in parts if not is_dot[o]]), ("letter_i_dot", [o for o in parts if is_dot[o]])):
        bpy.ops.object.select_all(action="DESELECT")
        for o in group:
            o.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        if len(group) > 1:
            bpy.ops.object.join()
        joined = bpy.context.view_layer.objects.active
        joined.name = joined.data.name = name
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")


def select_only(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


# --- Environment ------------------------------------------------------------


def build_cyclorama(material: bpy.types.Material) -> None:
    """Floor that bends into a back wall, so there is no visible horizon line."""
    radius, wall_y, half_width = 6.0, 8.0, 120.0
    profile = [(y, 0.0) for y in (-100.0, wall_y)]
    profile += [
        (wall_y + radius * math.sin(a), radius - radius * math.cos(a))
        for a in (math.radians(d) for d in range(5, 91, 5))
    ]
    profile.append((wall_y + radius, 100.0))

    bm = bmesh.new()
    rows = [[bm.verts.new((x, y, z)) for y, z in profile] for x in (-half_width, half_width)]
    for i in range(len(profile) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    mesh = bpy.data.meshes.new("cyclorama")
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.materials.append(material)
    bpy.context.scene.collection.objects.link(bpy.data.objects.new("cyclorama", mesh))


def make_cyclorama_material() -> bpy.types.Material:
    """Emission keeps the sampled palette exact; AO adds soft contact shadows under the letters."""
    mat = bpy.data.materials.new("M_Cyclorama")
    mat.diffuse_color = hex_to_linear(SKY_GRADIENT[1][1])
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    coords = nodes.new("ShaderNodeTexCoord")
    split = nodes.new("ShaderNodeSeparateXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    set_ramp(ramp, SKY_GRADIENT)
    links.new(coords.outputs["Window"], split.inputs[0])
    links.new(split.outputs["Y"], ramp.inputs["Fac"])

    ao = nodes.new("ShaderNodeAmbientOcclusion")
    ao.samples = 24
    ao.inputs["Distance"].default_value = 1.2

    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    to_rgb = nodes.new("ShaderNodeShaderToRGB")
    to_bw = nodes.new("ShaderNodeRGBToBW")
    links.new(diffuse.outputs[0], to_rgb.inputs[0])
    links.new(to_rgb.outputs[0], to_bw.inputs[0])

    shadow = nodes.new("ShaderNodeMath")
    shadow.operation = "MULTIPLY"
    links.new(ao.outputs["AO"], shadow.inputs[0])
    links.new(to_bw.outputs[0], shadow.inputs[1])

    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    links.new(shadow.outputs[0], mix.inputs[0])
    mix.inputs[6].default_value = hex_to_linear(CONTACT_SHADOW)
    links.new(ramp.outputs["Color"], mix.inputs[7])

    emission = nodes.new("ShaderNodeEmission")
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(mix.outputs[2], emission.inputs["Color"])
    links.new(emission.outputs[0], output.inputs["Surface"])
    return mat


def make_letter_material() -> bpy.types.Material:
    """Matte dark plastic: sampled tones, real form shadows from the key light."""
    mat = bpy.data.materials.new("M_Letters")
    mat.diffuse_color = hex_to_linear(LETTER_LIT)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = hex_to_linear(LETTER_LIT)
    bsdf.inputs["Roughness"].default_value = 0.55
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.12
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs[0], output.inputs["Surface"])
    return mat


def add_lights(scene: bpy.types.Scene) -> None:
    """Soft key from above-front, like the Pixar intro; fill so the gradient does not go black."""
    key = bpy.data.objects.new("LIGHT_KEY", bpy.data.lights.new("LIGHT_KEY", "SUN"))
    key.data.energy = 2.2
    key.data.angle = math.radians(35)
    key.data.color = hex_to_linear("#E8EEF8")[:3]
    key.rotation_euler = (math.radians(48), math.radians(8), math.radians(-25))
    scene.collection.objects.link(key)

    fill = bpy.data.objects.new("LIGHT_FILL", bpy.data.lights.new("LIGHT_FILL", "AREA"))
    fill.data.energy = 120
    fill.data.size = 12
    fill.data.color = hex_to_linear("#C3D1F4")[:3]
    fill.location = (0.0, -8.0, 6.0)
    fill.rotation_euler = (math.radians(70), 0.0, 0.0)
    scene.collection.objects.link(fill)

    eevee = getattr(scene, "eevee", None)
    if eevee is not None:
        for attr, value in (("use_shadows", True), ("taa_render_samples", 32)):
            if hasattr(eevee, attr):
                setattr(eevee, attr, value)


def set_ramp(ramp: bpy.types.Node, stops: list[tuple[float, str]]) -> None:
    elements = ramp.color_ramp.elements
    while len(elements) < len(stops):
        elements.new(0.5)
    for element, (position, color) in zip(elements, stops):
        element.position = position
        element.color = hex_to_linear(color)


# --- Cameras & render -------------------------------------------------------


def build_cameras(word_width: float) -> None:
    """Place each camera so the word fills its `word_span` share of the frame width."""
    target = bpy.data.objects.new("CAM_TARGET", None)
    target.location = (0.0, 0.0, CAMERA_TARGET_Z)
    target.hide_viewport = True
    bpy.context.scene.collection.objects.link(target)
    for name, cfg in CAMERAS.items():
        distance = (word_width / cfg["word_span"]) * CAMERA_LENS / CAMERA_SENSOR
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        cam.data.lens = CAMERA_LENS
        cam.data.sensor_width = CAMERA_SENSOR
        cam.data.sensor_fit = "HORIZONTAL"
        cam.data.clip_end = 500.0
        cam.location = (0.0, -distance, CAMERA_TARGET_Z + distance * math.tan(math.radians(CAMERA_TILT_DEG)))
        constraint = cam.constraints.new("TRACK_TO")
        constraint.target = target
        constraint.track_axis = "TRACK_NEGATIVE_Z"
        constraint.up_axis = "UP_Y"
        bpy.context.scene.collection.objects.link(cam)


def setup_viewport(scene: bpy.types.Scene, camera_name: str) -> None:
    """Open the file looking through `camera_name` with real colors, without editor overlays.

    Blender does not keep Rendered shading in files saved from background mode,
    so Material Preview is used; Solid mode falls back to material display colors.
    """
    scene.camera = bpy.data.objects[camera_name]
    scene.render.resolution_x, scene.render.resolution_y = CAMERAS[camera_name]["resolution"]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            space.shading.type = "MATERIAL"
            space.shading.color_type = "MATERIAL"
            space.overlay.show_overlays = False
            space.region_3d.view_perspective = "CAMERA"


def configure_render(scene: bpy.types.Scene) -> None:
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.image_settings.file_format = "PNG"


def render_cameras(scene: bpy.types.Scene) -> None:
    for name, cfg in CAMERAS.items():
        scene.camera = bpy.data.objects[name]
        scene.render.resolution_x, scene.render.resolution_y = cfg["resolution"]
        scene.render.filepath = str(OUTPUT_DIR / f"scene_{name.removeprefix('CAM_')}.png")
        bpy.ops.render.render(write_still=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene = reset_scene()

    curves = import_logo_curves()
    normalize_logo(curves)
    letters = letters_to_meshes(curves, make_letter_material())
    word_width = space_letters(letters)
    split_i_dot(bpy.data.objects["letter_i"])
    build_cyclorama(make_cyclorama_material())
    add_lights(scene)
    build_cameras(word_width)
    configure_render(scene)

    render_cameras(scene)
    setup_viewport(scene, "CAM_16x9")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_BLEND))


if __name__ == "__main__":
    main()
