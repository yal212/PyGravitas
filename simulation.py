"""
simulation.py — N-body gravitational physics engine.

Uses Velocity Verlet integration for good energy conservation.
Softened gravity prevents force singularities at near-zero separation.
Inelastic collision merges conserve momentum exactly.
"""

import numpy as np
from body import Body


# Gravitational constant (SI)
G_SI = 6.674e-11

# Softening length (metres) — prevents infinite force at r→0
SOFTENING = 1e8


class Simulation:
    """Manages all bodies and advances the physics each timestep."""

    def __init__(self, G_scale: float = 1.0, dt: float = 3600.0):
        """
        Parameters
        ----------
        G_scale : multiplier on G_SI; tuned via UI slider
        dt      : timestep in seconds (default 1 hour)
        """
        self.bodies: list[Body] = []
        self.G_scale = G_scale      # user-controlled multiplier
        self.dt = dt                # user-controlled timestep
        self.trails_enabled = True
        self._pending_remove: list[Body] = []  # bodies queued for deletion

    # ------------------------------------------------------------------
    # Body management
    # ------------------------------------------------------------------

    @property
    def G(self) -> float:
        return G_SI * self.G_scale

    def add_body(self, body: Body) -> None:
        body.acc = self._compute_acc_single(body)
        self.bodies.append(body)

    def clear(self) -> None:
        """Remove all bodies from simulation and scene."""
        for b in self.bodies:
            b.remove()
        self.bodies.clear()

    # ------------------------------------------------------------------
    # Force / acceleration computation
    # ------------------------------------------------------------------

    def _compute_acc_single(self, target: Body) -> np.ndarray:
        """Acceleration on *target* from all other current bodies."""
        acc = np.zeros(3)
        for other in self.bodies:
            if other is target:
                continue
            delta = other.pos - target.pos
            dist_sq = np.dot(delta, delta) + SOFTENING ** 2
            dist = np.sqrt(dist_sq)
            acc += self.G * other.mass / dist_sq * (delta / dist)
        return acc

    def _compute_all_acc(self) -> list[np.ndarray]:
        """
        Compute accelerations for every body using Newton's 3rd law
        to halve the work: a_ij = -a_ji (scaled by mass ratio).
        Returns list aligned with self.bodies.
        """
        n = len(self.bodies)
        accs = [np.zeros(3) for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                bi = self.bodies[i]
                bj = self.bodies[j]
                delta = bj.pos - bi.pos
                dist_sq = np.dot(delta, delta) + SOFTENING ** 2
                dist = np.sqrt(dist_sq)
                unit = delta / dist
                f_mag = self.G / dist_sq  # per-unit-mass factor
                accs[i] += f_mag * bj.mass * unit
                accs[j] -= f_mag * bi.mass * unit

        return accs

    # ------------------------------------------------------------------
    # Velocity Verlet integration
    # ------------------------------------------------------------------

    def _integrate(self, old_accs: list[np.ndarray]) -> None:
        """
        Velocity Verlet:
            x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt²
            a(t+dt) = f(x(t+dt))
            v(t+dt) = v(t) + 0.5*(a(t) + a(t+dt))*dt
        """
        dt = self.dt
        n = len(old_accs)  # bodies present when step began

        # Half-step position update
        for i in range(n):
            b = self.bodies[i]
            b.pos += b.vel * dt + 0.5 * old_accs[i] * dt ** 2

        # Recompute accelerations at new positions
        new_accs = self._compute_all_acc()

        # Velocity update using average of old and new accelerations
        for i in range(n):
            b = self.bodies[i]
            b.vel += 0.5 * (old_accs[i] + new_accs[i]) * dt
            b.acc = new_accs[i]

    # ------------------------------------------------------------------
    # Collision detection & inelastic merge
    # ------------------------------------------------------------------

    def _check_collisions(self) -> None:
        """
        Detect pairwise overlaps and merge colliding bodies.
        Deferred removal prevents list mutation during iteration.
        Momentum is conserved exactly. Mass and radius combine.
        """
        n = len(self.bodies)
        to_remove: set[int] = set()

        for i in range(n):
            if i in to_remove:
                continue
            for j in range(i + 1, n):
                if j in to_remove:
                    continue
                bi = self.bodies[i]
                bj = self.bodies[j]
                delta = bj.pos - bi.pos
                dist = np.linalg.norm(delta)
                if dist < bi.radius + bj.radius:
                    # Merge j into i
                    total_mass = bi.mass + bj.mass
                    # Momentum conservation: v = (m1*v1 + m2*v2) / (m1+m2)
                    bi.vel = (bi.mass * bi.vel + bj.mass * bj.vel) / total_mass
                    # Centre of mass position
                    bi.pos = (bi.mass * bi.pos + bj.mass * bj.pos) / total_mass
                    bi.mass = total_mass
                    # Volume-conserving radius: r = cbrt(r1³ + r2³)
                    bi.radius = (bi.radius ** 3 + bj.radius ** 3) ** (1 / 3)
                    bi.sphere.radius = bi.radius
                    # Pick colour of heavier body (already bi)
                    to_remove.add(j)

        # Remove merged bodies (reverse order to keep indices valid)
        for idx in sorted(to_remove, reverse=True):
            self.bodies[idx].remove()
            self.bodies.pop(idx)

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Advance simulation by one timestep and update visuals."""
        if len(self.bodies) < 1:
            return

        old_accs = self._compute_all_acc()
        self._integrate(old_accs)
        self._check_collisions()

        for b in self.bodies:
            b.update_visual()

    # ------------------------------------------------------------------
    # Observables
    # ------------------------------------------------------------------

    def kinetic_energy(self) -> float:
        return sum(b.kinetic_energy() for b in self.bodies)

    def potential_energy(self) -> float:
        """Gravitational PE = -G*m1*m2/r for all pairs."""
        pe = 0.0
        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                bi, bj = self.bodies[i], self.bodies[j]
                dist = np.linalg.norm(bj.pos - bi.pos)
                if dist > 0:
                    pe -= self.G * bi.mass * bj.mass / float(dist)
        return float(pe)

    def total_energy(self) -> float:
        return self.kinetic_energy() + self.potential_energy()

    def center_of_mass(self) -> np.ndarray:
        if not self.bodies:
            return np.zeros(3)
        total_mass = float(sum(b.mass for b in self.bodies))
        if total_mass == 0.0:
            return np.zeros(3)
        result = np.zeros(3, dtype=float)
        for b in self.bodies:
            result += b.mass * b.pos
        out: np.ndarray = result / total_mass
        return out

    def total_momentum(self) -> np.ndarray:
        result = np.zeros(3, dtype=float)
        for b in self.bodies:
            result += b.mass * b.vel
        return result

    # ------------------------------------------------------------------
    # Trail control
    # ------------------------------------------------------------------

    def set_trails(self, enabled: bool) -> None:
        self.trails_enabled = enabled
        for b in self.bodies:
            b.set_trail(enabled)

    def clear_all_trails(self) -> None:
        for b in self.bodies:
            b.clear_trail()
