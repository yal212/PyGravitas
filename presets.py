"""
presets.py — Pre-configured scenarios for PyGravitas.

Each function clears the simulation, adds bodies with physically
motivated initial conditions, and returns a human-readable description.

Coordinate system: SI units (metres, kg, m/s).
All circular orbit velocities are derived from v = sqrt(G*M/r).
"""

import math
import numpy as np
import vpython as vp
from simulation import Simulation
from body import Body


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _circular_speed(G: float, M_central: float, r: float) -> float:
    """Orbital speed for a circular orbit around mass M at radius r."""
    return math.sqrt(G * M_central / r)


# ---------------------------------------------------------------------------
# Preset 1 — Inner Solar System
# ---------------------------------------------------------------------------

def solar_system(sim: Simulation) -> str:
    """
    Full solar system: Sun + all 8 planets + Pluto + Moon + asteroid belt.

    Physics:
    - Elliptical orbits via vis-viva equation at given true anomaly
    - Each planet's eccentricity and inclination (to ecliptic) included
    - Moon in correct circular orbit around Earth

    Visuals:
    - Radii scaled ~50–200× physical (visible at AU scale)
    - Saturn with two concentric ring bands
    - 8 asteroid belt bodies between Mars and Jupiter
    - Trail length tuned per planet (inner = shorter; outer = longer)
    """
    sim.clear()
    sim.dt = 3600.0   # ensure 1 hr/step; chaos preset sets dt=86400

    AU    = 1.496e11
    G     = sim.G
    M_sun = 1.989e30

    # ── Orbit helper (Keplerian, vis-viva) ────────────────────────────────────
    def _orbit(a_m: float, e: float, theta_deg: float, inc_deg: float):
        """
        Returns (pos, vel) for a body on an elliptical orbit around the Sun.
        a_m        : semi-major axis in metres
        e          : eccentricity
        theta_deg  : true anomaly at start (degrees)
        inc_deg    : inclination to ecliptic (degrees), ascending node on +x axis
        """
        theta = math.radians(theta_deg)
        inc   = math.radians(inc_deg)

        p   = a_m * (1.0 - e * e)               # semi-latus rectum
        r   = p / (1.0 + e * math.cos(theta))   # radius at true anomaly
        sqt = math.sqrt(G * M_sun / p)           # √(GM/p) — constant for orbit

        # Radial and tangential velocity components in the orbital plane
        v_r = sqt * e * math.sin(theta)
        v_t = sqt * (1.0 + e * math.cos(theta))

        # Cartesian form (x = perihelion direction)
        ct, st = math.cos(theta), math.sin(theta)
        pos_orb = np.array([r * ct, r * st, 0.0])
        vel_orb = np.array([v_r * ct - v_t * st,
                             v_r * st + v_t * ct,
                             0.0])

        # Incline orbit: rotate around x-axis by inc
        ci, si = math.cos(inc), math.sin(inc)
        R = np.array([[1, 0, 0], [0, ci, -si], [0, si, ci]])
        return R @ pos_orb, R @ vel_orb

    # ── Sun ───────────────────────────────────────────────────────────────────
    sim.add_body(Body(
        pos=np.zeros(3), vel=np.zeros(3),
        mass=M_sun,
        radius=4.0e9,
        color=vp.vector(1.00, 0.92, 0.23),
        label="Sun",
        trail_retain=1,   # Sun barely moves; minimal trail
    ))

    # ── Planets ───────────────────────────────────────────────────────────────
    # Dict fields: a_au, e, mass, vis_r, color, theta, inc, retain, rings
    # theta = true anomaly at t=0 (spreads planets around their orbits)
    # inc   = inclination to ecliptic (degrees)
    planets = [
        dict(name="Mercury", a=0.387,  e=0.206, mass=3.301e23, vis_r=7.0e8,
             color=vp.vector(0.72, 0.62, 0.50), theta=  0, inc= 7.0, retain=800),

        dict(name="Venus",   a=0.723,  e=0.007, mass=4.867e24, vis_r=1.1e9,
             color=vp.vector(0.95, 0.75, 0.35), theta= 80, inc= 3.4, retain=500),

        dict(name="Earth",   a=1.000,  e=0.017, mass=5.972e24, vis_r=1.2e9,
             color=vp.vector(0.25, 0.55, 1.00), theta=155, inc= 0.0, retain=400),

        dict(name="Mars",    a=1.524,  e=0.093, mass=6.417e23, vis_r=9.0e8,
             color=vp.vector(0.85, 0.30, 0.10), theta=220, inc= 1.9, retain=350),

        dict(name="Jupiter", a=5.204,  e=0.049, mass=1.898e27, vis_r=4.5e9,
             color=vp.vector(0.85, 0.72, 0.55), theta=290, inc= 1.3, retain=400),

        dict(name="Saturn",  a=9.537,  e=0.057, mass=5.685e26, vis_r=3.5e9,
             color=vp.vector(0.92, 0.85, 0.65), theta=340, inc= 2.5, retain=300,
             rings=[
                 # B+C ring band — brightest, innermost
                 dict(radius=5.2e9, thickness=1.8e9,
                      color=vp.vector(0.90, 0.85, 0.65)),
                 # A ring band — slightly dimmer, outer edge
                 dict(radius=7.2e9, thickness=9.0e8,
                      color=vp.vector(0.82, 0.78, 0.58)),
             ]),

        dict(name="Uranus",  a=19.19,  e=0.046, mass=8.682e25, vis_r=2.2e9,
             color=vp.vector(0.60, 0.90, 0.95), theta=170, inc= 0.8, retain=250),

        dict(name="Neptune", a=30.07,  e=0.010, mass=1.024e26, vis_r=2.1e9,
             color=vp.vector(0.25, 0.40, 0.95), theta= 50, inc= 1.8, retain=250),

        dict(name="Pluto",   a=39.48,  e=0.248, mass=1.303e22, vis_r=8.0e8,
             color=vp.vector(0.75, 0.65, 0.60), theta=100, inc=17.1, retain=200),
    ]

    earth_body = None

    for p in planets:
        pos, vel = _orbit(p["a"] * AU, p["e"], p["theta"], p["inc"])
        body = Body(
            pos=pos, vel=vel,
            mass=p["mass"], radius=p["vis_r"],
            color=p["color"], label=p["name"],
            trail_retain=p["retain"],
            rings=p.get("rings"),
        )
        sim.add_body(body)
        if p["name"] == "Earth":
            earth_body = body

    # ── Moon (orbits Earth) ────────────────────────────────────────────────────
    if earth_body is not None:
        M_earth = earth_body.mass
        r_moon  = 3.844e8
        v_moon  = _circular_speed(G, M_earth, r_moon)
        # Earth's position angle in its orbit — rotate Moon 90° ahead (perpendicular)
        ep = earth_body.pos
        θe = math.atan2(ep[1], ep[0])
        moon_offset = r_moon * np.array([-math.sin(θe), math.cos(θe), 0.0])
        moon_vdelta = v_moon * np.array([-math.cos(θe), -math.sin(θe), 0.0])
        sim.add_body(Body(
            pos=ep + moon_offset,
            vel=earth_body.vel + moon_vdelta,
            mass=7.342e22, radius=5.0e8,
            color=vp.vector(0.78, 0.78, 0.78),
            label="Moon", trail_retain=200,
        ))

    # ── Asteroid belt ─────────────────────────────────────────────────────────
    # 8 representative bodies between Mars (1.52 AU) and Jupiter (5.2 AU).
    # Spread at different radii and angles to texture the inner–outer gap.
    belt = [
        (2.20,  10), (2.45,  55), (2.65, 118), (2.80, 195),
        (2.95, 248), (3.05, 310), (3.12, 165), (2.55, 295),
    ]
    belt_color = vp.vector(0.55, 0.48, 0.38)
    for a_au, theta_deg in belt:
        pos, vel = _orbit(a_au * AU, 0.08, theta_deg, 0.0)
        sim.add_body(Body(
            pos=pos, vel=vel,
            mass=5.0e20, radius=3.0e8,
            color=belt_color, label="",
            trail_retain=150,
        ))

    return (
        "Solar System: Sun · Mercury · Venus · Earth+Moon · Mars · "
        "Asteroid Belt · Jupiter · Saturn · Uranus · Neptune · Pluto"
    )


# ---------------------------------------------------------------------------
# Preset 2 — Binary Stars
# ---------------------------------------------------------------------------

def binary_stars(sim: Simulation) -> str:
    """
    Unequal-mass binary: 2 M_sun blue-white + 1 M_sun yellow-orange.
    Both orbit their common centre of mass (CoM) at the origin.
    A circumbinary planet orbits the pair at 8 AU — inside the stable
    region for a 3 AU binary (stability limit ≈ 2.5 × separation).

    CoM derivation (CoM at origin):
        r_A = d × M_B / (M_A + M_B)
        r_B = d × M_A / (M_A + M_B)
        ω   = sqrt(G × (M_A + M_B) / d³)
        v_A = ω × r_A,   v_B = ω × r_B
    """
    sim.clear()
    sim.dt = 3600.0   # reset; chaos preset sets dt=86400

    G     = sim.G
    M_sun = 1.989e30
    M_A   = 2.0 * M_sun    # massive blue-white primary
    M_B   = 1.0 * M_sun    # lighter yellow-orange secondary
    M_tot = M_A + M_B
    d     = 4.5e11         # 3 AU separation

    omega = math.sqrt(G * M_tot / d ** 3)
    r_A   = d * M_B / M_tot    # CoM offset for A
    r_B   = d * M_A / M_tot    # CoM offset for B
    v_A   = omega * r_A
    v_B   = omega * r_B

    star_a = Body(
        pos=np.array([-r_A, 0.0, 0.0]),
        vel=np.array([ 0.0, -v_A, 0.0]),
        mass=M_A,
        radius=1.4e10,
        color=vp.vector(0.55, 0.75, 1.00),  # hot blue-white
        label="Star A (2M)",
        trail_retain=700,                    # long trails show the looping dance
    )
    star_b = Body(
        pos=np.array([ r_B, 0.0, 0.0]),
        vel=np.array([ 0.0,  v_B, 0.0]),
        mass=M_B,
        radius=8.0e9,
        color=vp.vector(1.00, 0.65, 0.20),  # warm yellow-orange
        label="Star B (1M)",
        trail_retain=700,
    )
    sim.add_body(star_a)
    sim.add_body(star_b)

    # Circumbinary planet — stable beyond ~2.5× binary separation
    r_planet = 12e11
    v_planet = _circular_speed(G, M_tot, r_planet)
    planet = Body(
        pos=np.array([0.0, r_planet, 0.0]),
        vel=np.array([-v_planet, 0.0, 0.0]),
        mass=3.0e26,
        radius=3.5e9,
        color=vp.vector(0.45, 0.85, 0.55),   # teal-green alien world
        label="Planet",
        trail_retain=400,
    )
    sim.add_body(planet)

    return "Binary Stars: 2M + 1M stars with circumbinary planet"


# ---------------------------------------------------------------------------
# Preset 3 — Pythagorean 3-Body (guaranteed chaos)
# ---------------------------------------------------------------------------

def chaotic_three_body(sim: Simulation) -> str:
    """
    Pythagorean 3-body (Burrau 1913): masses 3:4:5 at the vertices of
    a right triangle, starting at rest. Proven chaotic — the lightest
    body is eventually ejected while the two heaviest form a tight binary.

    Masses are stellar (≈ 1.5–2.5 M_sun each) so the crossing-time is
    ~days-to-weeks; at dt = 1 day/step the drama unfolds in ~30–60 s.

    A small z-offset on the lightest body seeds 3D motion so the
    out-of-plane ejection trajectory is visually dramatic.
    """
    sim.clear()

    # Advance time faster so chaos is visible quickly (~30–60 s real-time)
    sim.dt = 86400.0   # 1 day per step

    m_unit = 1.5e30    # ≈ 0.75 M_sun per mass unit
    scale  = 2.0e11    # ~1.3 AU between vertices

    # Burrau positions: right angle at origin (standard normalisation)
    bodies_params = [
        # (mass,        pos,                                    vel)
        (3 * m_unit, np.array([ 1.0,  3.0,  0.00]) * scale, np.zeros(3)),   # lightest
        (4 * m_unit, np.array([-2.0, -1.0,  0.00]) * scale, np.zeros(3)),
        (5 * m_unit, np.array([ 1.0, -1.0,  0.15]) * scale, np.zeros(3)),   # z-seed
    ]
    # Neon palette — high contrast so trails never look like the same body.
    colors = [
        vp.vector(0.00, 1.00, 1.00),   # cyan    (3M — lightest, ejected)
        vp.vector(0.85, 0.00, 1.00),   # magenta (4M)
        vp.vector(0.55, 1.00, 0.00),   # lime    (5M — heaviest)
    ]
    labels = ["Cyan (3M)", "Magenta (4M)", "Lime (5M)"]

    for (mass, pos, vel), color, label in zip(bodies_params, colors, labels):
        sim.add_body(Body(
            pos=pos, vel=vel, mass=mass,
            radius=5.0e9,
            color=color, label=label,
            trail_retain=1000,   # long trails = chaos looks like art
        ))

    return "Pythagorean 3-body: 3:4:5 masses at rest — watch Cyan get ejected"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PRESETS: dict[str, tuple] = {
    "solar":  (solar_system,         "Inner Solar System"),
    "binary": (binary_stars,         "Binary Stars"),
    "chaos":  (chaotic_three_body,   "3-Body Chaos"),
}


def load_preset(name: str, sim: Simulation) -> str:
    """Load a preset by key. Returns description string."""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset '{name}'. Options: {list(PRESETS)}")
    fn, _ = PRESETS[name]
    return fn(sim)
