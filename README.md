# PyGravitas

A real-time interactive 3D gravity sandbox built with VPython. Spawn planets, watch orbits form, trigger collisions, and observe the chaos of the three-body problem — all driven by real Newtonian physics.

---

## What it does

- **N-body gravity** — every body attracts every other body via F = G m₁m₂ / r²
- **Spawn bodies interactively** — click to place, drag to set initial velocity
- **Inelastic collisions** — bodies merge on contact, conserving momentum exactly
- **3 built-in presets** — inner solar system, binary stars, and the Pythagorean 3-body problem
- **Live stats** — kinetic energy, potential energy, total energy, centre of mass
- **Camera follow** — lock onto any body and track it through the scene

---

## Physics

### Gravity

Each timestep, every pair of bodies exerts a gravitational force on each other:

```
F = G * m1 * m2 / r²
```

Acceleration is computed pair-wise (O(n²)) using Newton's third law to halve
the work — the force on body i from body j is equal and opposite to the force
on j from i.

A **softening factor** ε = 10⁸ m is applied:

```
r_eff = sqrt(r² + ε²)
```

This prevents force singularities when two bodies pass very close together,
keeping the simulation stable without requiring collision detection at every
sub-step.

### Integration — Velocity Verlet

Simple Euler integration accumulates energy error rapidly. PyGravitas uses
**Velocity Verlet**, a second-order symplectic integrator that conserves
energy far better over long time spans:

```
x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt²
a(t+dt) = f(x(t+dt))                       ← forces at new positions
v(t+dt) = v(t) + 0.5*(a(t) + a(t+dt))*dt
```

### Collisions

Two bodies merge when their surfaces touch (`|r₁ - r₂| < radius₁ + radius₂`).
The merge conserves:

- **Momentum exactly**: `v_merged = (m₁v₁ + m₂v₂) / (m₁ + m₂)`
- **Position** at centre of mass: `pos_merged = (m₁p₁ + m₂p₂) / (m₁ + m₂)`
- **Volume** (approximately): `r_merged = cbrt(r₁³ + r₂³)`

Merges are deferred until after the full force step to prevent cascade
instability within a single timestep.

---

## Installation

**Requires Python 3.12** (VPython is not yet compatible with 3.13+).

```bash
git clone https://github.com/yal212/PyGravitas
cd PyGravitas

python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** `setuptools<71` is pinned in `requirements.txt` because VPython
> depends on `pkg_resources`, which was removed from newer setuptools releases.

---

## Running

```bash
python main.py
```

A browser tab opens with the 3D canvas (VPython runs in the browser via WebGL).
The control panel appears to the right of the canvas.

---

## Controls

### Mouse

| Action | Result |
|--------|--------|
| Click canvas | Spawn a body at cursor position with zero velocity |
| Click and drag | Spawn a body — drag direction and length set initial velocity |
| Right-click a body | Select it for camera follow |

### Keyboard

| Key | Action |
|-----|--------|
| `Space` | Pause / resume simulation |
| `R` | Reset — remove all bodies |
| `T` | Toggle motion trails on/off |
| `F` | Follow body nearest to centre of mass |
| `Esc` | Stop following, free camera |

### Control Panel (right of canvas)

| Control | Range | Description |
|---------|-------|-------------|
| Gravity (G×) | 0.01 – 200× | Scale the gravitational constant |
| Speed (dt) | 1 min – 7 days per step | Simulation timestep |
| Spawn mass | ~Moon to 10× Jupiter | Mass of next body to spawn |
| Spawn radius | Mm to AU scale | Radius of next body to spawn |
| Reset | — | Clear scene |
| Toggle Trails | — | Show/hide motion trails |
| Clear Trails | — | Erase trail history without disabling |

---

## Presets

### Inner Solar System
Sun (1 M☉) with Mercury, Venus, Earth + Moon, and Mars on circular prograde
orbits in the XY plane. Orbital velocities are derived from `v = sqrt(G*M/r)`
so every orbit is initially stable.

### Binary Stars
Two equal-mass stars (1 M☉ each) separated by 2 AU, orbiting their common
centre of mass. Initial velocities satisfy the circular orbit condition:
`v = sqrt(G*M / 2d)`.

### 3-Body Chaos — Pythagorean Problem
The classic **Burrau (1913)** configuration: three bodies with masses 3, 4, 5
placed at the vertices of a 3-4-5 right triangle, starting from rest. This
system is proven to be non-integrable — after a period of complex interaction,
two bodies eject the third and escape as a bound pair. Chaos is visible within
seconds.

---

## Project structure

```
PyGravitas/
├── main.py          Entry point: canvas, event loop, mouse and keyboard input
├── body.py          Body class — VPython sphere + trail, numpy pos/vel/acc
├── simulation.py    Physics engine: N-body gravity, Verlet integration, collisions
├── ui.py            Control panel: sliders, buttons, live stat labels
├── presets.py       Preset scenarios: solar system, binary stars, 3-body chaos
└── requirements.txt vpython, numpy, setuptools<71
```

### Key design decisions

**`body.py`** wraps a VPython `sphere` alongside numpy arrays for physics state.
The two representations stay in sync: physics runs entirely in numpy (fast,
no VPython overhead), and `update_visual()` pushes the result to the sphere
each frame.

**`simulation.py`** is pure physics — no VPython imports. It accepts and
returns `Body` objects but never touches the renderer directly. This makes
the physics easy to test in isolation.

**`ui.py`** mutates `Simulation` attributes directly via slider callbacks.
Changing G or dt takes effect on the very next `sim.step()` call — no restart
needed.

**`presets.py`** calls `sim.clear()` before adding bodies, so presets are
hot-swappable at any time without restarting the program.

---

## Physics you can observe

### Why orbits exist
A body in orbit is continuously falling toward the central mass, but its
tangential velocity carries it sideways fast enough that the curvature of
its fall matches the curvature of the surface below. Reduce G with the slider
and watch the orbit expand and eventually escape — the balance breaks.

### Why the 3-body problem is chaotic
Two-body systems have an exact analytical solution (Kepler's laws). Add a
third body and the system becomes non-integrable: no closed-form solution
exists. Tiny differences in initial conditions lead to exponentially
diverging trajectories — deterministic chaos. The Pythagorean preset makes
this visible every time you run it.

### Conservation laws
- **Momentum** is conserved exactly by the Verlet integrator and by the
  collision merge formula.
- **Energy** is approximately conserved. The Verlet integrator has bounded
  energy error (it oscillates rather than drifts), so total energy stays
  close to its initial value over many orbits. Watch the Total E readout —
  it should remain nearly constant for stable systems.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `vpython` | 3D rendering, canvas, UI widgets |
| `numpy` | Vector math, physics state arrays |
| `setuptools<71` | Provides `pkg_resources` required by vpython |

---

## License

MIT
