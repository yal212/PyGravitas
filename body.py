"""
body.py — Celestial body representation.

Each Body wraps a VPython sphere with an optional trail and stores
physics state (position, velocity, mass) as numpy arrays.

Trail type "curve" draws smooth connected lines instead of dot-points,
which looks far more cinematic at orbital timescales.
"""

import numpy as np
import vpython as vp


class Body:
    """A gravitational body with VPython visual representation."""

    def __init__(
        self,
        pos: np.ndarray,
        vel: np.ndarray,
        mass: float,
        radius: float,
        color: vp.vector = None,
        make_trail: bool = True,
        label: str = "",
        trail_retain: int = 400,
        rings: list | None = None,
    ):
        """
        Parameters
        ----------
        pos          : shape (3,) array, initial position in metres
        vel          : shape (3,) array, initial velocity in m/s
        mass         : body mass in kg
        radius       : visual radius in metres (also used for collision)
        color        : vpython.vector color; random if None
        make_trail   : whether to attach a motion trail
        label        : optional name shown in scene
        trail_retain : number of trail points to keep
        rings        : list of ring dicts for Saturn-style ring systems.
                       Each dict: {'radius': float, 'thickness': float,
                                   'color': vp.vector (optional)}
                       Ring axis is always (0,0,1) — lies in the orbital XY plane.
        """
        self.pos    = np.array(pos, dtype=float)
        self.vel    = np.array(vel, dtype=float)
        self.mass   = float(mass)
        self.radius = float(radius)
        self.acc    = np.zeros(3, dtype=float)
        self.label  = label

        if color is None:
            color = vp.vector(
                np.random.uniform(0.5, 1.0),
                np.random.uniform(0.5, 1.0),
                np.random.uniform(0.5, 1.0),
            )
        self.color = color

        # ── VPython sphere ────────────────────────────────────────────────────
        self.sphere = vp.sphere(
            pos=vp.vector(*self.pos),
            radius=self.radius,
            color=self.color,
            make_trail=make_trail,
            trail_type="curve",
            interval=2,
            retain=trail_retain,
        )
        self.sphere.emissive = True

        # ── Floating label ────────────────────────────────────────────────────
        self._vp_label: vp.label | None = None
        if label:
            self._vp_label = vp.label(
                pos=vp.vector(*self.pos),
                text=label,
                xoffset=20,
                yoffset=12,
                space=0,
                height=11,
                color=self.color,
                opacity=0,
                border=0,
                line=False,
            )

        # ── Ring system (e.g. Saturn) ─────────────────────────────────────────
        # Each ring lies in the XY (orbital) plane; axis=(0,0,1).
        # Seen from a slightly elevated camera, this appears as an ellipse.
        self._vp_rings: list = []
        if rings:
            vp_pos = vp.vector(*self.pos)
            for rd in rings:
                ring_obj = vp.ring(
                    pos=vp_pos,
                    axis=vp.vector(0, 0, 1),
                    radius=rd["radius"],
                    thickness=rd["thickness"],
                    color=rd.get("color", self.color),
                )
                self._vp_rings.append(ring_obj)

    # ── Visual sync ───────────────────────────────────────────────────────────

    def update_visual(self) -> None:
        """Sync VPython sphere, label, and rings to current numpy pos."""
        vp_pos = vp.vector(*self.pos)
        self.sphere.pos = vp_pos
        if self._vp_label is not None:
            self._vp_label.pos = vp_pos
        for ring in self._vp_rings:
            ring.pos = vp_pos

    # ── Trail control ─────────────────────────────────────────────────────────

    def set_trail(self, enabled: bool) -> None:
        self.sphere.make_trail = enabled
        if not enabled:
            self.sphere.clear_trail()

    def clear_trail(self) -> None:
        self.sphere.clear_trail()

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def remove(self) -> None:
        """Delete all VPython objects from the scene."""
        self.sphere.visible = False
        self.sphere.clear_trail()
        if self._vp_label is not None:
            self._vp_label.visible = False
            del self._vp_label
        for ring in self._vp_rings:
            ring.visible = False
        self._vp_rings.clear()
        del self.sphere

    # ── Helpers ───────────────────────────────────────────────────────────────

    def kinetic_energy(self) -> float:
        return 0.5 * self.mass * float(np.dot(self.vel, self.vel))

    def __repr__(self) -> str:
        return (
            f"Body({self.label or 'unnamed'}, "
            f"mass={self.mass:.2e}, pos={self.pos})"
        )
