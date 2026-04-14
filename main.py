"""
main.py — PyGravitas entry point.

Run with:  python main.py

Controls
--------
Click canvas          → spawn a new body at cursor position
Click + drag          → spawn with initial velocity (drag sets direction/speed)
Right-click a body    → select it for camera follow
F key                 → toggle camera follow on selected body
R key                 → reset scene
T key                 → toggle trails
Escape                → deselect / unfollow
"""

import numpy as np
import vpython as vp

from simulation import Simulation
from ui import UI
from body import Body
from presets import load_preset, solar_system


# ---------------------------------------------------------------------------
# Scene setup
# ---------------------------------------------------------------------------

scene = vp.canvas(
    title="<b>PyGravitas</b> — 3D Gravity Sandbox",
    width=1100,
    height=750,
    background=vp.color.black,              # pure black → emissive bodies pop
    forward=vp.vector(0, -0.3, -1),
    up=vp.vector(0, 1, 0),
    range=3e11,
)

# Low ambient so non-emissive objects are dark; emissive stars/planets glow.
scene.ambient = vp.color.gray(0.15)


# ---------------------------------------------------------------------------
# Simulation & UI
# ---------------------------------------------------------------------------

sim = Simulation(G_scale=1.0, dt=3600.0)   # dt = 1 hour per step


def on_reset() -> None:
    sim.clear()
    _state["follow_body"] = None
    if _state["drag_arrow"] is not None:
        _state["drag_arrow"].visible = False
    _state["drag_arrow"] = None


def on_preset(name: str) -> None:
    desc = load_preset(name, sim)
    scene.title = f"<b>PyGravitas</b> — {desc}"
    # Adjust camera range for each preset
    ranges = {"solar": 6.5e12, "binary": 6e11, "chaos": 4e11}
    scene.range = ranges.get(name, 3e11)
    _state["follow_body"] = None


ui = UI(sim, on_reset=on_reset, on_preset=on_preset)

# Load default scene
_desc = solar_system(sim)
scene.title = f"<b>PyGravitas</b> — {_desc}"
scene.range  = 6.5e12

# ---------------------------------------------------------------------------
# Interaction state
# ---------------------------------------------------------------------------

_state: dict = {
    "drag_start":   None,   # np.ndarray world pos where drag began
    "drag_arrow":   None,   # vp.arrow showing velocity direction
    "follow_body":  None,   # Body being followed by camera
    "paused":       False,
}

# Velocity scale: pixels → m/s.  Tuned so a 1AU drag gives ~30 km/s.
VEL_SCALE = 150.0


# ---------------------------------------------------------------------------
# Mouse helpers
# ---------------------------------------------------------------------------

def _screen_to_world(event) -> np.ndarray:
    """
    Map a mouse event to a 3D world coordinate on the XY plane (z=0).
    VPython's event.pos is a canvas-plane vector; project onto z=0.
    """
    # event.pos is already projected onto the scene plane by VPython
    return np.array([event.pos.x, event.pos.y, event.pos.z])


def _find_body_at(world_pos: np.ndarray) -> "Body | None":
    """Return first body whose sphere contains world_pos, or None."""
    for body in sim.bodies:
        if np.linalg.norm(body.pos - world_pos) < body.radius * 3:
            return body
    return None


# ---------------------------------------------------------------------------
# Mouse event handlers
# ---------------------------------------------------------------------------

def on_mousedown(evt) -> None:
    pos = _screen_to_world(evt)
    _state["drag_start"] = pos

    # Right-click → select body for follow
    if evt.event == "mousedown" and hasattr(evt, "which") and evt.which == 3:
        body = _find_body_at(pos)
        _state["follow_body"] = body
        return

    # Create drag arrow
    _state["drag_arrow"] = vp.arrow(
        pos=vp.vector(*pos),
        axis=vp.vector(0, 1e9, 0),
        shaftwidth=1e9,
        color=vp.color.yellow,
        opacity=0.7,
    )


def on_mousemove(evt) -> None:
    if _state["drag_start"] is None or _state["drag_arrow"] is None:
        return
    cur = _screen_to_world(evt)
    delta = cur - _state["drag_start"]
    if np.linalg.norm(delta) < 1e6:
        return
    arrow = _state["drag_arrow"]
    arrow.axis = vp.vector(*(delta * 0.5))   # visual scale


def on_mouseup(evt) -> None:
    start = _state["drag_start"]
    if start is None:
        return

    # Remove drag arrow
    if _state["drag_arrow"] is not None:
        _state["drag_arrow"].visible = False
        _state["drag_arrow"] = None

    end = _screen_to_world(evt)
    drag_vec = end - start

    # Velocity proportional to drag length
    vel = drag_vec * VEL_SCALE

    body = Body(
        pos=start.copy(),
        vel=vel,
        mass=ui.spawn_mass,
        radius=ui.spawn_radius,
        make_trail=sim.trails_enabled,
    )
    sim.add_body(body)

    _state["drag_start"] = None


# ---------------------------------------------------------------------------
# Keyboard handler
# ---------------------------------------------------------------------------

def on_keydown(evt) -> None:
    key = evt.key.lower()
    if key == "r":
        on_reset()
    elif key == "t":
        sim.set_trails(not sim.trails_enabled)
    elif key == "f":
        # Follow the body closest to scene centre
        if _state["follow_body"] is None and sim.bodies:
            com = sim.center_of_mass()
            closest = min(sim.bodies, key=lambda b: np.linalg.norm(b.pos - com))
            _state["follow_body"] = closest
        else:
            _state["follow_body"] = None
    elif key == "escape":
        _state["follow_body"] = None
    elif key == " ":
        _state["paused"] = not _state["paused"]


# ---------------------------------------------------------------------------
# Bind events
# ---------------------------------------------------------------------------

scene.bind("mousedown", on_mousedown)
scene.bind("mousemove", on_mousemove)
scene.bind("mouseup",   on_mouseup)
scene.bind("keydown",   on_keydown)


# ---------------------------------------------------------------------------
# Camera follow
# ---------------------------------------------------------------------------

def _update_camera() -> None:
    body = _state["follow_body"]
    if body is None or body not in sim.bodies:
        _state["follow_body"] = None
        # Free mode: gently drift toward centre of mass so the action
        # stays on screen even as bodies drift across the scene.
        if sim.bodies:
            com = vp.vector(*sim.center_of_mass())
            scene.center += (com - scene.center) * 0.008
        return
    # Follow mode: track the selected body with a snappier lerp.
    target = vp.vector(*body.pos)
    scene.center += (target - scene.center) * 0.08


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

TARGET_FPS = 120

def main() -> None:
    while True:
        vp.rate(TARGET_FPS)

        if _state["paused"]:
            continue

        sim.step()
        _update_camera()
        ui.update_labels()


if __name__ == "__main__":
    main()
