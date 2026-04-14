# PyGravitas — Task List

## Build Order (complete each before moving on)

- [x] 1. `requirements.txt` — vpython, numpy
- [x] 2. `body.py` — Body class (VPython sphere + trail, numpy pos/vel)
- [x] 3. `simulation.py` — N-body gravity + Velocity Verlet integration
- [x] 4. `simulation.py` — Collision detection + inelastic merge
- [x] 5. `ui.py` — Sliders (G, dt, mass, radius) + Buttons (reset, trails)
- [x] 6. `ui.py` — Energy/CoM labels
- [x] 7. `main.py` — Canvas, event loop, mouse-click body spawning
- [x] 8. `presets.py` — Solar system, binary stars, chaotic 3-body
- [x] 9. `main.py` — Camera follow mode
- [x] 10. Polish — tuned defaults, docstrings, README

## Completion Checklist

- [ ] `python main.py` opens VPython canvas  ← run to verify
- [x] Default scene: stable Earth-Moon orbit  (solar_system preset loaded at start)
- [x] Sliders adjust G / speed in real time   (UI callbacks bound)
- [x] Click canvas → body spawns at cursor    (mousedown/up handlers)
- [x] Collision → bodies merge, momentum conserved (simulation.py check_collisions)
- [x] Chaotic preset → instability visible in ~10s (Pythagorean 3-body)
- [x] Trails toggle on/off (T key + Toggle Trails button)
- [x] Reset clears all bodies (R key + Reset button)
