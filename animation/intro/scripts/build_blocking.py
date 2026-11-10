"""Blocking: panda forward-rolls right→left in profile, hauls over the i, falls, laughs.

Usage (always right after build_scene.py, which resets the file):
  Blender --background --python animation/intro/scripts/build_blocking.py
Outputs (animation/intro/output/):
  climba_intro_scene.blend (animated), animatic/animatic_{9x16,16x9}.mp4,
  plates/{9x16,16x9}/plate_####.png (no proxy) and guide_####.png (with proxy)
"""

import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import bpy
from mathutils import Euler, Vector

sys.path.append(str(Path(__file__).resolve().parent))
from build_scene import (  # noqa: E402
    CAMERA_LENS,
    CAMERA_SENSOR,
    CAMERA_TARGET_Z,
    CAMERA_TILT_DEG,
    CAMERAS,
    FRAME_COUNT,
    OUTPUT_DIR,
    SCENE_BLEND,
    hex_to_linear,
    setup_viewport,
    world_bounds,
)

PLATES_DIR = OUTPUT_DIR / "plates"
ANIMATIC_DIR = OUTPUT_DIR / "animatic"

# Belly is the roll pivot. Standing loc.z = BELLY_Z puts the feet on the floor.
BELLY_Z = 0.40
LIE_Z = 0.18  # on her back after the fall; sit-up lifts back to BELLY_Z
ROLL_Y = -0.78  # clearly in front of the letters (letters sit around y=0)
CLIMB_Y = -0.34  # still on the camera side of the i, so the word stays behind her

SEGMENT_FRAMES = [1, 72, 144, 216, 288]
CLOSE_WIDTH = {"CAM_9x16": 2.40, "CAM_16x9": 3.50}
FOLLOW_STIFFNESS = 0.42  # panda stays near frame center while rolling
PULLBACK_START, PULLBACK_END = 223, 245  # wide before she sits
FADE_START, FADE_END = 11.2, 12.0  # hold the readable word first
# Root.x = a_hi + this. 0.55 left her overlapping a in camera; 1.15 leaves a readable gap.
START_X_CLEARANCE = 1.15
PANDA_X_PAD = 0.85  # half-body + margin so the overlap camera does not crop her

ANIMATIC_SIZE = {"CAM_9x16": (360, 640)}  # preview only; 16x9/plates later


# --- Scene queries ----------------------------------------------------------


def obj(name: str) -> bpy.types.Object:
    return bpy.data.objects[name]


def bounds(name: str) -> tuple[Vector, Vector]:
    return world_bounds([obj(name)])


def smoothstep(t: float) -> float:
    return t * t * (3 - 2 * t)


def lerp(a, b, t: float):
    return a + (b - a) * t


# --- Acting -----------------------------------------------------------------


@dataclass(frozen=True)
class Pose:
    loc: Vector
    # degrees. X = forward somersault (local, on PANDA_SPIN), Y = flop, Z = facing on root
    # Z: 0 = camera, -90 = looking left (profile, rolling toward -X)
    rot: Vector
    scale: Vector


NEUTRAL = Vector((1.0, 1.0, 1.0))
SQUASH = Vector((1.16, 1.10, 0.78))
BELLY = Vector((1.08, 1.04, 0.90))
STRETCH = Vector((0.94, 0.94, 1.12))


class Performance:
    """One pose per frame so motion is real arcs, not spline easing."""

    def __init__(self, start: Vector, facing: float) -> None:
        self.poses = [Pose(start.copy(), Vector((0.0, 0.0, facing)), NEUTRAL.copy())]

    @property
    def last(self) -> Pose:
        return self.poses[-1]

    @property
    def frame(self) -> int:
        return len(self.poses)

    def _add(self, **changes) -> None:
        self.poses.append(replace(self.last, **changes))

    def hold(self, frames: int, scale: Vector = NEUTRAL) -> "Performance":
        start = self.last.scale
        for i in range(1, frames + 1):
            self._add(scale=start.lerp(scale, smoothstep(min(1.0, i / 3))))
        return self

    def anticipation(self, frames: int) -> "Performance":
        """Tuck the head forward, rock, then commit. Pandas do not spring into a roll."""
        base, rot = self.last.loc, self.last.rot
        for i in range(1, frames + 1):
            t = i / frames
            rock = math.sin(math.pi * t)
            self._add(
                loc=base + Vector((-0.05 * t, 0.0, 0.03 * rock)),
                rot=Vector((rot.x + 42 * t, rot.y, rot.z)),
                scale=lerp(NEUTRAL, SQUASH, t),
            )
        return self

    def roll(self, frames: int, to: Vector, turns: float) -> "Performance":
        """Forward somersaults toward -X, profile, looking left. Belly is the pivot."""
        start, rot0 = self.last.loc, self.last.rot
        for i in range(1, frames + 1):
            t = i / frames
            e = t if t < 0.9 else 0.9 + 0.1 * smoothstep((t - 0.9) / 0.1)
            loc = start.lerp(to, e)
            angle = turns * 2 * math.pi * e
            loc.z = BELLY_Z + 0.04 * abs(math.sin(angle))
            contact = 0.5 + 0.5 * math.cos(angle)
            scale = Vector((1.0 + 0.10 * contact, 1.04, 1.0 - 0.12 * contact))
            # +X on PANDA_SPIN is a forward tuck (nose down), so she rolls in the direction she faces.
            self._add(
                loc=loc,
                rot=Vector((rot0.x + turns * 360.0 * e, 10 * math.sin(angle), rot0.z)),
                scale=scale,
            )
        snapped_x = round(self.last.rot.x / 360.0) * 360.0
        self.poses[-1] = replace(
            self.last,
            loc=Vector((to.x, to.y, BELLY_Z)),
            rot=Vector((snapped_x, 0.0, rot0.z)),
            scale=NEUTRAL.copy(),
        )
        return self

    def wobble(self, frames: int) -> "Performance":
        """Land a roll: squash, dizzy side-to-side, settle onto the rump."""
        base, rot = self.last.loc.copy(), self.last.rot.copy()
        for i in range(1, frames + 1):
            t = i / frames
            wave = math.sin(2 * math.pi * t) * (1 - t)
            self._add(
                loc=base + Vector((0.03 * wave, 0.0, 0.04 * abs(wave))),
                rot=Vector((rot.x + 8 * wave, 10 * wave, rot.z)),
                scale=SQUASH.lerp(NEUTRAL, smoothstep(t)),
            )
        self.poses[-1] = replace(self.last, loc=base, rot=Vector((rot.x, 0.0, rot.z)), scale=NEUTRAL.copy())
        return self

    def look_up(self, frames: int) -> "Performance":
        """Sit in front of the i and look up at it, weight shifting like a cub."""
        base, rot = self.last.loc, self.last.rot
        for i in range(1, frames + 1):
            t = smoothstep(i / frames)
            self._add(
                loc=base + Vector((0.0, 0.0, 0.02 * math.sin(math.pi * i / frames))),
                rot=Vector((rot.x - 18 * t, rot.y, rot.z)),
                scale=lerp(NEUTRAL, Vector((1.06, 1.06, 0.94)), 0.5 * math.sin(math.pi * t)),
            )
        return self

    def rotate(self, frames: int, tilt: float | None = None, facing: float | None = None) -> "Performance":
        start = self.last.rot
        end = Vector((start.x if tilt is None else tilt, start.y, start.z if facing is None else facing))
        for i in range(1, frames + 1):
            self._add(rot=start.lerp(end, smoothstep(i / frames)))
        return self

    def crawl_to(self, frames: int, to: Vector, steps: int = 3) -> "Performance":
        """Belly close to the path, slow plantigrade pulls up the i."""
        start, rot = self.last.loc, self.last.rot
        for i in range(1, frames + 1):
            t = i / frames
            phase = t * steps
            loc = start.lerp(to, smoothstep(t))
            loc = loc + Vector((0.0, 0.0, 0.012 * abs(math.sin(2 * math.pi * phase))))
            self._add(
                loc=loc,
                rot=Vector((rot.x + 10 * math.sin(2 * math.pi * phase), 8 * math.sin(2 * math.pi * phase), rot.z)),
                scale=BELLY.copy(),
            )
        self.poses[-1] = replace(self.last, loc=to.copy(), rot=Vector((rot.x, 0.0, rot.z)), scale=BELLY.copy())
        return self

    def kick(self, frames: int) -> "Performance":
        """Hanging from the i-dot: hind legs thrash, pull-ups slip. The dot does not move."""
        base, rot = self.last.loc.copy(), self.last.rot.copy()
        for i in range(1, frames + 1):
            t = i / 24
            slip = (i % 16) / 16
            pull = 0.12 * math.sin(math.pi * slip) if slip < 0.55 else 0.0
            self._add(
                loc=base + Vector((0.03 * abs(math.sin(2 * math.pi * 1.6 * t)), 0.0, pull)),
                rot=Vector((
                    rot.x + 14 * math.sin(2 * math.pi * 4.2 * t),
                    18 * math.sin(2 * math.pi * 5.0 * t),
                    rot.z,
                )),
                scale=lerp(NEUTRAL, STRETCH, 0.3 + 2.0 * pull),
            )
        self.poses[-1] = replace(self.last, loc=base, rot=Vector((rot.x, 0.0, rot.z)))
        return self

    def haul_over(self, frames: int, to: Vector) -> "Performance":
        """She finally drags her belly over the still i-dot. Hind legs still dangle."""
        start, rot = self.last.loc, self.last.rot
        for i in range(1, frames + 1):
            t = smoothstep(i / frames)
            loc = start.lerp(to, t)
            loc.z = lerp(start.z, to.z, t) + 0.10 * math.sin(math.pi * t)
            self._add(
                loc=loc,
                rot=Vector((lerp(rot.x, rot.x + 100, t), 14 * math.sin(math.pi * t), rot.z)),
                scale=STRETCH.lerp(BELLY, t),
            )
        return self

    def tumble(self, frames: int, to: Vector) -> "Performance":
        """Clumsiest forward somersault off the letter. Ends FLAT on her back, not sitting."""
        start, rot = self.last.loc, self.last.rot
        # 270° from upright = lying on the back (local +X is a forward tuck).
        base = math.floor(rot.x / 360.0) * 360.0 + 270.0
        target_x = base if base > rot.x + 40 else base + 360.0
        for i in range(1, frames + 1):
            t = i / frames
            drop = t * t
            loc = Vector((
                lerp(start.x, to.x, 1 - (1 - t) ** 2),
                lerp(start.y, to.y, t),
                lerp(start.z, LIE_Z, drop) + 0.32 * 4 * t * (1 - t),
            ))
            scale = Vector((0.94, 0.94, 1.14)) if t < 0.78 else Vector((1.22, 1.18, 0.62))
            self._add(
                loc=loc,
                rot=Vector((lerp(rot.x, target_x, t), 28 * math.sin(2 * math.pi * t), rot.z)),
                scale=scale,
            )
        self.poses[-1] = replace(
            self.last,
            loc=Vector((to.x, to.y, LIE_Z)),
            rot=Vector((target_x, 0.0, rot.z)),
            scale=Vector((1.22, 1.18, 0.62)),
        )
        return self

    def sit_up(self, frames: int) -> "Performance":
        """Only now she sits: from her back on the floor up onto the rump."""
        start, rot = self.last.loc, self.last.rot
        upright_x = math.ceil(rot.x / 360.0) * 360.0
        to = Vector((start.x, start.y, BELLY_Z))
        for i in range(1, frames + 1):
            t = smoothstep(i / frames)
            self._add(
                loc=start.lerp(to, t),
                rot=Vector((lerp(rot.x, upright_x, t), 0.0, rot.z)),
                scale=Vector((1.22, 1.18, 0.62)).lerp(NEUTRAL, t),
            )
        return self

    def laugh(self, frames: int, calm_after: int) -> "Performance":
        """Belly laugh that eases into a smile, with a tiny idle breath so the last seconds are not frozen."""
        base_loc, base_rot = self.last.loc.copy(), self.last.rot.copy()
        for i in range(1, frames + 1):
            energy = 1.0 if i < calm_after else max(0.0, 1 - (i - calm_after) / 48)
            wave = math.sin(2 * math.pi * 5 * i / 24)
            breath = 0.01 * math.sin(2 * math.pi * 0.6 * i / 24)
            self._add(
                loc=base_loc + Vector((0.0, 0.0, 0.04 * energy * abs(wave) + breath)),
                rot=base_rot + Vector((0.0, 5 * energy * wave, 0.0)),
                scale=Vector((1.0, 1.0, 1.0 + 0.06 * energy * wave)),
            )
        return self


def build_performance() -> Performance:
    """12 s at 24 fps. Profile forward-rolls, hauls over the i, falls, laughs. Comments = end frame."""
    a_hi = bounds("letter_a")[1]
    i_lo, i_hi = bounds("letter_i")
    l_hi = bounds("letter_l")[1]
    dot_lo, dot_hi = bounds("letter_i_dot")
    dot = (dot_lo + dot_hi) / 2

    start = Vector((a_hi.x + START_X_CLEARANCE, ROLL_Y, BELLY_Z))
    at_i = Vector((i_hi.x + 0.32, ROLL_Y, BELLY_Z))
    hang = Vector((i_hi.x + 0.16, CLIMB_Y, max(dot.z - 0.06, BELLY_Z + 0.35)))
    over = Vector((i_lo.x - 0.10, CLIMB_Y, dot_hi.z + 0.10))
    landing = Vector(((l_hi.x + i_lo.x) / 2, ROLL_Y, BELLY_Z))

    p = Performance(start, facing=-90)
    p.hold(4)                  # 5    in profile, already looking left
    p.anticipation(6)          # 11   tucks — no idle
    p.roll(132, at_i, turns=4.5)  # 143 one continuous roll a→i; cut 72 is mid-roll
    p.crawl_to(32, hang, 5)    # 175  hits the i and climbs, no sit
    p.kick(40)                 # 215  hind legs dangle; cut 216
    p.haul_over(8, over)       # 223  over the letter
    p.tumble(22, landing)      # 245  falls on her back; pullback done
    p.hold(6)                  # 251  still down, word fully readable
    p.sit_up(8)                # 259  sits only after the wide shot
    p.rotate(8, facing=0)      # 267  turns to camera
    p.laugh(FRAME_COUNT - p.frame, calm_after=12)
    if p.frame != FRAME_COUNT:
        raise RuntimeError(f"Performance is {p.frame} frames, expected {FRAME_COUNT}")
    return p


# --- Panda proxy (master_c construction: big dark cartoon eyes, round cub) -


PANDA_GLOW = "#FFF6EA"
PANDA_LAMP_ENERGY = 0.0  # never a rolling lamp; studio lights only
IRIS = "#2A2428"


def flat_material(name: str, color: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = hex_to_linear(color)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = hex_to_linear(color)
    bsdf.inputs["Roughness"].default_value = 0.7
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs[0], output.inputs["Surface"])
    return mat


def lamp_material(name: str, color: str, strength: float) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = hex_to_linear(color)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = hex_to_linear(color)
    emission.inputs["Strength"].default_value = strength
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = hex_to_linear(color)
    bsdf.inputs["Roughness"].default_value = 0.45
    add = nodes.new("ShaderNodeAddShader")
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs[0], add.inputs[0])
    links.new(emission.outputs[0], add.inputs[1])
    links.new(add.outputs[0], output.inputs["Surface"])
    return mat


def add_panda_lamp(parent: bpy.types.Object) -> bpy.types.Object:
    data = bpy.data.lights.new("LIGHT_PANDA", "POINT")
    data.energy = PANDA_LAMP_ENERGY
    data.color = hex_to_linear(PANDA_GLOW)[:3]
    data.shadow_soft_size = 0.5
    lamp = bpy.data.objects.new("LIGHT_PANDA", data)
    lamp.location = (0.0, -0.18, 0.08)
    bpy.context.scene.collection.objects.link(lamp)
    lamp.parent = parent
    return lamp


def _sphere(name: str, loc, scale, mat, parent, rot=(0.0, 0.0, 0.0)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=loc, segments=32, ring_count=20)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = Vector((scale, scale, scale)) if isinstance(scale, (int, float)) else Vector(scale)
    ob.rotation_euler = Euler(rot)
    ob.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    ob.parent = parent
    return ob


def build_panda_proxy() -> tuple[bpy.types.Object, bpy.types.Object, list[bpy.types.Object], bpy.types.Object]:
    """master_c. Root = belly + facing. PANDA_SPIN = local-X forward somersaults."""
    root = bpy.data.objects.new("PANDA_ROOT", None)
    bpy.context.scene.collection.objects.link(root)
    spin = bpy.data.objects.new("PANDA_SPIN", None)
    bpy.context.scene.collection.objects.link(spin)
    spin.parent = root
    white = flat_material("M_PandaWhite", PANDA_GLOW)
    black = flat_material("M_PandaBlack", "#2B2430")
    iris = flat_material("M_PandaIris", IRIS)

    parts = [
        _sphere("panda_body", (0.0, 0.04, -0.12), (0.24, 0.20, 0.26), white, spin),
        _sphere("panda_head", (0.0, 0.04, 0.30), (0.32, 0.30, 0.32), white, spin),
        _sphere("panda_ear_l", (-0.22, 0.02, 0.54), 0.11, black, spin),
        _sphere("panda_ear_r", (0.22, 0.02, 0.54), 0.11, black, spin),
        _sphere("panda_patch_l", (-0.12, -0.22, 0.32), (0.13, 0.05, 0.14), black, spin),
        _sphere("panda_patch_r", (0.12, -0.22, 0.32), (0.13, 0.05, 0.14), black, spin),
        _sphere("panda_eye_l", (-0.10, -0.26, 0.32), 0.085, white, spin),
        _sphere("panda_eye_r", (0.10, -0.26, 0.32), 0.085, white, spin),
        _sphere("panda_iris_l", (-0.10, -0.32, 0.31), 0.055, iris, spin),
        _sphere("panda_iris_r", (0.10, -0.32, 0.31), 0.055, iris, spin),
        _sphere("panda_pupil_l", (-0.10, -0.36, 0.31), 0.028, black, spin),
        _sphere("panda_pupil_r", (0.10, -0.36, 0.31), 0.028, black, spin),
        _sphere("panda_hi_l", (-0.12, -0.38, 0.35), 0.016, white, spin),
        _sphere("panda_hi_r", (0.08, -0.38, 0.35), 0.016, white, spin),
        _sphere("panda_nose", (0.0, -0.32, 0.22), 0.038, black, spin),
        _sphere("panda_leg_l", (-0.09, 0.02, -0.28), (0.08, 0.09, 0.13), black, spin),
        _sphere("panda_leg_r", (0.09, 0.02, -0.28), (0.08, 0.09, 0.13), black, spin),
        _sphere("panda_arm_l", (-0.26, -0.02, -0.04), (0.08, 0.08, 0.18), black, spin,
                rot=(math.radians(40), 0.0, math.radians(20))),
        _sphere("panda_arm_r", (0.22, -0.10, 0.06), (0.08, 0.08, 0.20), black, spin,
                rot=(math.radians(85), 0.0, math.radians(-12))),
    ]
    return root, spin, parts, add_panda_lamp(spin)


def bake_performance(root: bpy.types.Object, spin: bpy.types.Object, performance: Performance) -> None:
    # Root yaws (facing). Spin does the forward somersault in local X, so profile rolls stay in XZ.
    for frame, pose in enumerate(performance.poses, start=1):
        root.location = pose.loc
        root.rotation_euler = Euler((0.0, 0.0, math.radians(pose.rot.z)))
        root.scale = pose.scale
        spin.rotation_euler = Euler((math.radians(pose.rot.x), math.radians(pose.rot.y), 0.0))
        for path in ("location", "rotation_euler", "scale"):
            root.keyframe_insert(path, frame=frame)
        spin.keyframe_insert("rotation_euler", frame=frame)


# --- Camera: same tilt the whole time, follow X, then dolly back ------------


def camera_pose(x: float, target_z: float, frame_width: float) -> tuple[Vector, Euler]:
    distance = frame_width * CAMERA_LENS / CAMERA_SENSOR
    tilt = math.radians(CAMERA_TILT_DEG)
    location = Vector((x, -distance, target_z + distance * math.tan(tilt)))
    return location, Euler((math.radians(90) - tilt, 0.0, 0.0))


def animate_cameras(performance: Performance) -> None:
    """Same 5° tilt forever. Close follow with the panda in the center, then zoom out to the word."""
    lo, hi = world_bounds([obj(f"letter_{c}") for c in "climba"])
    word_cx = (lo.x + hi.x) / 2
    word_w = hi.x - lo.x
    span = PULLBACK_END - PULLBACK_START

    for name, cfg in CAMERAS.items():
        cam = obj(name)
        cam.constraints.clear()
        close_w = CLOSE_WIDTH[name]
        wide_loc, rotation = camera_pose(word_cx, CAMERA_TARGET_Z, word_w / cfg["word_span"])
        follow_x = performance.poses[0].loc.x
        for frame, pose in enumerate(performance.poses, start=1):
            follow_x = lerp(follow_x, pose.loc.x, FOLLOW_STIFFNESS)
            close_loc, _ = camera_pose(follow_x, CAMERA_TARGET_Z, close_w)
            t = smoothstep(min(1.0, max(0.0, (frame - PULLBACK_START) / span)))
            cam.location = close_loc.lerp(wide_loc, t)
            cam.rotation_euler = rotation
            cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=1)


# --- Rendering --------------------------------------------------------------


def set_proxy_render(parts: list[bpy.types.Object], lamp: bpy.types.Object, visible: bool) -> None:
    for part in parts:
        part.hide_render = not visible
    lamp.hide_render = not visible
    lamp.data.energy = PANDA_LAMP_ENERGY if visible else 0.0


def render_still(camera: str, frame: int, size: tuple[int, int], path: Path, *, seek: bool = True) -> None:
    scene = bpy.context.scene
    scene.render.use_compositing = False
    scene.camera = obj(camera)
    scene.render.resolution_x, scene.render.resolution_y = size
    if seek:
        scene.frame_set(frame)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def _overlap_camera(left_x: float, right_x: float, keep_left_of_center: float | None) -> tuple[Vector, Euler]:
    """Fit [left_x, right_x]. If keep_left_of_center is set, that world-X stays on the left half."""
    width = max(right_x - left_x, CLOSE_WIDTH["CAM_9x16"]) * 1.10
    cx = (left_x + right_x) / 2.0
    if keep_left_of_center is not None:
        want_cx = keep_left_of_center + 0.16 * width
        if want_cx > cx:
            cx = want_cx
            width = max(width, 2.0 * (cx - left_x) * 1.04)
    return camera_pose(cx, CAMERA_TARGET_Z, width)


def _render_overlap_frame(
    frame: int,
    left_letter: str,
    right_letter: str,
    parts: list[bpy.types.Object],
    lamp: bpy.types.Object,
    *,
    keep_left_of_center: float | None = None,
) -> None:
    """Two solid letters in one 9:16 still. Pose camera AFTER frame_set; detach action or render snaps it."""
    scene = bpy.context.scene
    cam = obj("CAM_9x16")
    scene.frame_set(frame)
    bpy.context.view_layer.update()

    left_lo, _ = bounds(f"letter_{left_letter}")
    _, right_hi = bounds(f"letter_{right_letter}")
    panda_x = obj("PANDA_ROOT").location.x
    lo = left_lo.x - 0.40
    hi = max(right_hi.x, panda_x) + PANDA_X_PAD
    loc, rot = _overlap_camera(lo, hi, keep_left_of_center)
    print(
        f"overlap f{frame}: {left_letter}+{right_letter} "
        f"left={left_lo.x:.3f} right={right_hi.x:.3f} panda_x={panda_x:.3f} "
        f"span={hi - lo:.3f} cam_x={loc.x:.3f}"
    )

    action = cam.animation_data.action if cam.animation_data else None
    cam.animation_data_clear()
    cam.location, cam.rotation_euler = loc, rot
    bpy.context.view_layer.update()

    folder = PLATES_DIR / "9x16"
    folder.mkdir(parents=True, exist_ok=True)
    size = CAMERAS["CAM_9x16"]["resolution"]
    for prefix, visible in (("plate", False), ("guide", True)):
        set_proxy_render(parts, lamp, visible)
        render_still("CAM_9x16", frame, size, folder / f"{prefix}_{frame:04d}.png", seek=False)

    if action is not None:
        cam.animation_data_create()
        cam.animation_data.action = action


def render_s1_overlap_plates(parts: list[bpy.types.Object], lamp: bpy.types.Object) -> None:
    """Overlapping 9:16 plates for Kling joins. Does not rmtree other plates. No animatic.

    f1  a+b, panda standing to the RIGHT of a (not between a and b).
    f72 b+m, panda mid-roll so Kling cannot skip m.
    f144 m+i, panda arriving at i.
    """
    a_lo, a_hi = bounds("letter_a")
    _render_overlap_frame(1, "b", "a", parts, lamp, keep_left_of_center=a_hi.x)
    _render_overlap_frame(72, "m", "b", parts, lamp)
    _render_overlap_frame(144, "i", "m", parts, lamp)
    # Close laugh: same sitting pose as the wide end, so S5 can dolly without smearing.
    _render_overlap_frame(267, "l", "i", parts, lamp)
    bpy.context.scene.frame_set(1)
    print(f"start check: a=[{a_lo.x:.3f},{a_hi.x:.3f}] panda_x should be > {a_hi.x + START_X_CLEARANCE - 0.01:.3f}")


def render_plates(parts: list[bpy.types.Object], lamp: bpy.types.Object) -> None:
    cameras = {"CAM_9x16": CAMERAS["CAM_9x16"]} if os.environ.get("CLIMBA_FAST") == "1" else CAMERAS
    if os.environ.get("CLIMBA_FAST") != "1":
        shutil.rmtree(PLATES_DIR, ignore_errors=True)
    for camera, cfg in cameras.items():
        folder = PLATES_DIR / camera.removeprefix("CAM_")
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True, exist_ok=True)
        for frame in SEGMENT_FRAMES:
            for prefix, visible in (("plate", False), ("guide", True)):
                set_proxy_render(parts, lamp, visible)
                render_still(camera, frame, cfg["resolution"], folder / f"{prefix}_{frame:04d}.png")


def setup_fade(scene: bpy.types.Scene) -> None:
    return


def render_animatic(parts: list[bpy.types.Object], lamp: bpy.types.Object) -> None:
    scene = bpy.context.scene
    set_proxy_render(parts, lamp, True)
    scene.render.use_compositing = False
    scene.render.use_stamp = True
    scene.render.use_stamp_frame = True
    scene.render.use_stamp_time = True
    for camera, size in ANIMATIC_SIZE.items():
        tag = camera.removeprefix("CAM_")
        frames_dir = ANIMATIC_DIR / f"frames_{tag}"
        shutil.rmtree(frames_dir, ignore_errors=True)
        scene.camera = obj(camera)
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = str(frames_dir / "f_")
        bpy.ops.render.render(animation=True)
        encode_mp4(frames_dir, ANIMATIC_DIR / f"animatic_{tag}.mp4", scene.render.fps)
        shutil.rmtree(frames_dir, ignore_errors=True)
    scene.render.use_stamp = False


def encode_mp4(frames_dir: Path, out: Path, fps: int) -> None:
    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    fade = f"fade=t=out:st={FADE_START}:d={FADE_END - FADE_START}:color=black"
    subprocess.run(
        [ffmpeg, "-y", "-v", "error", "-framerate", str(fps), "-start_number", "1",
         "-i", str(frames_dir / "f_%04d.png"), "-vf", fade,
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "20", "-movflags", "+faststart", str(out)],
        check=True,
    )


def clear_previous_proxy() -> None:
    leftover = [
        o for o in bpy.data.objects
        if o.name in {"PANDA_ROOT", "PANDA_SPIN", "LIGHT_PANDA", "CHALK_ROOT"}
        or o.name.startswith("panda_")
        or o.name.startswith("chalk_")
    ]
    for ob in leftover:
        bpy.data.objects.remove(ob, do_unlink=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SCENE_BLEND))
    clear_previous_proxy()
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, FRAME_COUNT
    scene.eevee.taa_render_samples = 1
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"

    performance = build_performance()
    root, spin, parts, lamp = build_panda_proxy()
    bake_performance(root, spin, performance)
    animate_cameras(performance)
    setup_fade(scene)

    if os.environ.get("CLIMBA_SKIP_RENDER") != "1":
        if os.environ.get("CLIMBA_S1_OVERLAP") == "1":
            render_s1_overlap_plates(parts, lamp)
        elif os.environ.get("CLIMBA_PLATES") == "1":
            render_plates(parts, lamp)
        if os.environ.get("CLIMBA_SKIP_ANIMATIC") != "1" and os.environ.get("CLIMBA_S1_OVERLAP") != "1":
            render_animatic(parts, lamp)

    set_proxy_render(parts, lamp, False)
    scene.frame_set(1)
    setup_viewport(scene, "CAM_9x16")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_BLEND))


if __name__ == "__main__":
    main()
