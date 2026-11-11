# Other subjects: what to build, what data to use, what people get wrong

The engine (`lib/explainer.js`, `lib/materials.js`, the scripts) is subject-agnostic. Replace `cell.js`
with a module that builds parts, exports `anchors`, and poses everything in `update(t)`. These are starting
points; every claim still goes through the fact sheet and the critic.

| Subject | Parts, one per beat | Real data | The trap the critic must catch |
|---|---|---|---|
| **Why fingers never touch** (the @anxuanng film) | skin → cells → molecules → atoms → electron clouds as ψ² point clouds; the gap stays | atomic radii, hydrogen wavefunctions | it is **electrostatic repulsion between electron clouds plus the Pauli exclusion principle**, not Zeno's paradox; "touch" means the repulsion you feel. Electrons are probability clouds, not orbits |
| **An atom** | nucleus (protons/neutrons), 1s/2s/2p clouds, scale jump | CODATA radii, analytic orbitals | nucleus ~10⁻⁵ of the atom's width: say what you scaled; no planetary orbits |
| **A virus** (SARS-CoV-2, HIV, phage) | envelope, spikes, capsid, genome | PDB spike (6VXX), capsid structures; diameter from the literature | spike counts and density vary per virion; "alive" is a definition argument, keep it off screen |
| **A protein / enzyme** | backbone (Cα tube), domains, active site, substrate | PDB coordinates (one ID, on screen) | ribbon colours are a convention; show the real fold, not a guessed one |
| **DNA** | double helix, base pairs, major/minor groove, chromatin zoom-out | B-DNA geometry: ~10.5 bp per turn (~3.4–3.6 nm pitch), ~2 nm wide | don't draw a ladder twisted the wrong way (B-DNA is right-handed) |
| **A nuclear reactor** ("take it apart in three.js", @konstantinsaifo) | vessel, fuel assemblies, control rods, moderator, coolant loop, steam generator, turbine | a published PWR layout, rod and assembly dimensions | fission heats water; the reactor cannot explode like a bomb (low enrichment); control rods absorb neutrons, they do not "cool" |
| **An engine** | block, pistons, crank, valves, cams, four strokes | a real bore/stroke, firing order | valve timing and firing order per engine type; the spark plug fires near the top of compression |
| **A black hole** | event horizon, photon sphere, accretion disk, lensing | Schwarzschild radius 2GM/c², the 1.5 r_s photon sphere | "sucks things in" is wrong: far away it pulls like any mass of the same size |
| **A maths idea** (the Rubik's cube film, @cube_224) | the object, a move as a transformation, the group, a number on screen | compute it (43,252,003,274,489,856,000 positions; God's number 20 in the half-turn metric) | avoid clichés the prompt warned about; verify every number by code, not by memory |
| **The Earth / a planet** | core, mantle, crust, atmosphere layers | PREM radii, NASA fact sheets | layer thicknesses to scale make the crust invisible: say you thickened it |

Notes:

- 2D maths (graphs, proofs, equations moving) belongs in `manim-skill`; use this skill when the idea is
  spatial (a 4D cube's shadow, a knot, a cube group acting on a 3D object).
- Data from the PDB: parse `ATOM`/`HETATM` lines (columns 31–54 are x, y, z in Å); for big assemblies
  draw one sphere per residue at the Cα, or a tube through the Cα trace. A 10,000-atom protein is fine as
  one `InstancedMesh`.
- Machines are better "taken apart": an exploded view (each part slides out along its axis on its beat),
  then the assembly runs (a crank angle from t). Same label system, same camera keys.
