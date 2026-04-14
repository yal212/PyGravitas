"""
ui.py — VPython UI: sliders, buttons, and live stat labels.

All controls mutate the Simulation object directly via callbacks.
Labels are refreshed each frame by calling update_labels().
"""

import vpython as vp
from simulation import Simulation

# ── Palette ──────────────────────────────────────────────────────────────────
_C = {
    "head":    "#7ecfff",   # section header blue
    "dim":     "#888888",   # muted hint text
    "val":     "#ffe066",   # live value yellow
    "good":    "#66dd88",   # positive / KE green
    "warn":    "#ff8844",   # negative / PE orange
    "reset":   vp.color.red,
    "trail":   vp.color.cyan,
    "clear":   vp.color.orange,
    "preset":  vp.color.green,
}

_HR  = '<hr style="border:none;border-top:1px solid #444;margin:6px 0">'
_SEP = "\n"


def _h(text: str, color: str = _C["head"]) -> str:
    """Styled section header HTML."""
    return f'<span style="color:{color};font-weight:bold;font-size:1.05em">{text}</span>'


def _dim(text: str) -> str:
    return f'<span style="color:{_C["dim"]};font-size:0.85em">{text}</span>'


class UI:
    """Builds and manages all interactive controls for the sandbox."""

    spawn_mass: float   = 5.972e24   # ~Earth mass
    spawn_radius: float = 6.371e6    # ~Earth radius

    def __init__(self, sim: Simulation, on_reset, on_preset):
        self.sim = sim
        self._on_reset  = on_reset
        self._on_preset = on_preset
        self._build_controls()

    # ── Control construction ──────────────────────────────────────────────────

    def _build_controls(self) -> None:
        scene = vp.canvas.get_selected()
        c = scene.append_to_caption   # shorthand

        # ── Header ────────────────────────────────────────────────────────────
        c('\n<div style="font-size:1.2em;font-weight:bold;color:#7ecfff;'
          'letter-spacing:1px;margin-bottom:2px">PyGravitas</div>\n')
        c(_dim("3D gravity sandbox") + "\n")
        c(_HR + _SEP)

        # ── Physics ───────────────────────────────────────────────────────────
        c(_h("Physics") + _SEP)

        c("  Gravity  G× ")
        self._g_label = vp.wtext(text=self._val(f"{self.sim.G_scale:.1f}×"))
        c(_SEP)
        vp.slider(min=0.01, max=200.0, value=self.sim.G_scale, step=0.01,
                  length=220, bind=self._on_G_change)
        c("\n")

        c("  Speed  dt  ")
        self._dt_label = vp.wtext(text=self._val(self._fmt_time(self.sim.dt)))
        c(_SEP)
        vp.slider(min=60, max=86400 * 7, value=self.sim.dt, step=60,
                  length=220, bind=self._on_dt_change)
        c("\n")
        c(_HR + _SEP)

        # ── Spawn params ──────────────────────────────────────────────────────
        c(_h("Spawn Body") + _SEP)

        c("  Mass      ")
        self._mass_label = vp.wtext(text=self._val(self._fmt_mass(self.spawn_mass)))
        c(_SEP)
        vp.slider(min=22, max=30.3, value=24.776, step=0.01,
                  length=220, bind=self._on_mass_change)
        c("\n")

        c("  Radius    ")
        self._radius_label = vp.wtext(text=self._val(self._fmt_dist(self.spawn_radius)))
        c(_SEP)
        vp.slider(min=5, max=9, value=6.804, step=0.01,
                  length=220, bind=self._on_radius_change)
        c("\n")
        c(_dim("  Click canvas to spawn · drag to set velocity") + "\n")
        c(_HR + _SEP)

        # ── Scene controls ────────────────────────────────────────────────────
        c(_h("Scene") + _SEP + "  ")
        vp.button(text=" Reset ",       bind=self._on_reset_click,
                  background=_C["reset"], color=vp.color.white)
        c("  ")
        vp.button(text=" Trails ",      bind=self._on_trails_click,
                  background=_C["trail"], color=vp.color.black)
        c("  ")
        vp.button(text=" Clear Trails", bind=self._on_clear_trails,
                  background=_C["clear"], color=vp.color.white)
        c("\n")
        c(_HR + _SEP)

        # ── Presets ───────────────────────────────────────────────────────────
        c(_h("Presets") + _SEP + "  ")
        vp.button(text=" Solar System", bind=lambda _: self._on_preset("solar"),
                  background=_C["preset"], color=vp.color.white)
        c("  ")
        vp.button(text=" Binary Stars", bind=lambda _: self._on_preset("binary"),
                  background=_C["preset"], color=vp.color.white)
        c("  ")
        vp.button(text=" 3-Body Chaos", bind=lambda _: self._on_preset("chaos"),
                  background=_C["preset"], color=vp.color.white)
        c("\n")
        c(_HR + _SEP)

        # ── Live stats ────────────────────────────────────────────────────────
        c(_h("Live Stats") + _SEP)
        self._stat_label = vp.wtext(text="initialising…")
        c("\n")
        c(_HR + _SEP)

        # ── Hotkeys ───────────────────────────────────────────────────────────
        c(_h("Keys", "#aaaaaa") + _SEP)
        c(_dim(
            "  Space  pause/resume\n"
            "  R      reset\n"
            "  T      toggle trails\n"
            "  F      follow nearest body\n"
            "  Esc    deselect\n"
            "  RMB    select body to follow\n"
        ) + "\n")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _val(text: str) -> str:
        """Highlight a live value."""
        return f'<span style="color:{_C["val"]};font-weight:bold">{text}</span>'

    # ── Slider callbacks ──────────────────────────────────────────────────────

    def _on_G_change(self, s: vp.slider) -> None:
        self.sim.G_scale = s.value
        self._g_label.text = self._val(f"{s.value:.2f}×")

    def _on_dt_change(self, s: vp.slider) -> None:
        self.sim.dt = s.value
        self._dt_label.text = self._val(self._fmt_time(s.value))

    def _on_mass_change(self, s: vp.slider) -> None:
        self.spawn_mass = 10 ** s.value
        self._mass_label.text = self._val(self._fmt_mass(self.spawn_mass))

    def _on_radius_change(self, s: vp.slider) -> None:
        self.spawn_radius = 10 ** s.value
        self._radius_label.text = self._val(self._fmt_dist(self.spawn_radius))

    # ── Button callbacks ──────────────────────────────────────────────────────

    def _on_reset_click(self, _) -> None:
        self._on_reset()

    def _on_trails_click(self, _) -> None:
        self.sim.set_trails(not self.sim.trails_enabled)

    def _on_clear_trails(self, _) -> None:
        self.sim.clear_all_trails()

    # ── Per-frame label update ────────────────────────────────────────────────

    def update_labels(self) -> None:
        sim  = self.sim
        n    = len(sim.bodies)
        ke   = sim.kinetic_energy()
        pe   = sim.potential_energy()
        te   = ke + pe
        com  = sim.center_of_mass()

        ke_str = f'<span style="color:{_C["good"]}">{self._fmt_energy(ke)}</span>'
        pe_str = f'<span style="color:{_C["warn"]}">{self._fmt_energy(pe)}</span>'
        te_str = self._val(self._fmt_energy(te))
        n_str  = self._val(str(n))

        self._stat_label.text = (
            f"  Bodies   {n_str}\n"
            f"  KE       {ke_str}\n"
            f"  PE       {pe_str}\n"
            f"  Total E  {te_str}\n"
            f"  CoM  ({com[0]:.2e}, {com[1]:.2e}, {com[2]:.2e}) m\n"
        )

    # ── Formatters ────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt_mass(kg: float) -> str:
        if kg >= 1e30:
            return f"{kg/1.989e30:.2f} M☉"
        if kg >= 1e27:
            return f"{kg/1.898e27:.2f} MJ"
        if kg >= 1e24:
            return f"{kg/5.972e24:.2f} M⊕"
        return f"{kg:.2e} kg"

    @staticmethod
    def _fmt_dist(m: float) -> str:
        if m >= 1e9:
            return f"{m/1.496e11:.3f} AU"
        if m >= 1e6:
            return f"{m/1e6:.0f} Mm"
        return f"{m:.2e} m"

    @staticmethod
    def _fmt_energy(j: float) -> str:
        a = abs(j)
        if a >= 1e40:
            return f"{j:.2e} J"
        if a >= 1e33:
            return f"{j/1e33:.2f}×10³³ J"
        return f"{j:.2e} J"

    @staticmethod
    def _fmt_time(s: float) -> str:
        if s >= 86400:
            return f"{s/86400:.1f} days/step"
        if s >= 3600:
            return f"{s/3600:.1f} hr/step"
        return f"{s:.0f} s/step"
