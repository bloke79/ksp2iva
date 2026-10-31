# Backlog: IVA Redux

_Last updated 2026-10-11. Ordered by priority within each section. Detailed designs live in `PLAN.md`; current state in `STATUS.md`._

## 1. 3v (Mk3-5, 5 seats): v1 done 2026-10-11; in-game checks left
- [ ] **In-game check of the latest build**: upstairs fixes (glovebox, freezer, bike, table, cables into
      junction boxes, floor clutter removed), overall brightness, frame rate.
- [ ] **Basics still unconfirmed in game:** N switches seats, seat view the right way up, B reaches the docking windows,
      crew sit in the couches.
- [x] **Short rib pieces** left between wall units (e.g. under the freezer): raise the minimum length or skip ribs where
      a unit sits.
- [x] **Triangle budget** (~750k → ~500k: adaptive shell rings, single-segment tiny bevels): the hull shell is ~128k (2 cm rings, over-tessellated) and the console ~137k.
      Coarsen the shell away from windows; check console module density.
- [x] **Remaining thin spots:** (upper rack row added; recheck in game) upper wall bands of the living deck, and its middle band between the furniture rows.
- [x] **Floors:** (solid deck plates with grille inserts) consider solid deck plates with grille inserts (stock look) instead of open grating everywhere.
- [x] **Meal tray with food art** (procedural food and label textures)
- [ ] **Brightness tuning** if needed after Matt's check: AO floor (`IVA_AO_FLOOR` = 0.4), `_AODirect` (0.45), deck lights.

## 2. Features
- [x] **Moving around inside (unbuckle), first version (zero-g floating, all pods; walking under gravity and ladders later):** U to unbuckle, WASD/mouse free camera with collision, U to return to the
      nearest couch, hatch prompt at the tunnel/side hatch. Exported collision shell from the generator.
      Test on the 3v first, then the Mk1-3. (`PLAN.md`, "Moving around inside")
- [ ] **Live instruments check:** navball orientation (nose on the horizon facing north shows N at centre, E to the
      right; pitching up brings blue up from the bottom), altimeter, pressure and temperature needles.
- [ ] **Window views (B):** confirm on all three pods.

## 3. Bring the other built pods up to the stock style (done 2026-10-11; in-game check left)
- [x] **Mk1-3 (3 seats):** apply `art/stock.py` (ribs, frames, cable bundles, ceiling detail, stepped console housings,
      chamfered couch frames), re-export. It currently only has the lighter shared wall texture.
- [x] **Mk1 (1 seat):** the same, scaled to the small cabin.

## 4. New interiors (renders first for each)
- [ ] **Remaining pods and cockpits:** 1.5v, cupola, landers (1v, 2v, 3v), Mk1/Mk2/Mk3 cockpits (and inline variants).
      Enter IVA in each once so the pose dump captures the seated kerbals, then `pose_extract.py`.
- [x] **Crew cabins and Starlab, first version** (zero-g ISS-style rack rooms, built 2026-10-11; in-game check left):
  - OSL-25 Starlab: workstations, glovebox, freezers, floor racks, greenhouse in the ceiling (stock crops hidden inside).
  - PPD-10 Hitchhiker: four recessed crew quarters round one bay; galley, recessed hygiene compartment, railed table, porthole.
  - PPD-20 Wayfarer: eight recessed crew quarters in two bays; galley, hygiene, table; window lounge and ergometer.
  - Every crew position floats with foot loops (no chairs); N moves on to the next crewed part after the last seat.
- [x] **Hygiene door opening** (F while floating).
- [ ] **F action system** (`PLAN.md`, "F as the action key"): look-to-target with a prompt, then (1-3 built 2026-10-11, untested in game):
  - [x] cheap interactive kit: curtains, lockers/drawers, oven, cabin lights, toilet flush, laptop/MFD pages
  - [x] thruster sound while floating (the game's EVA jetpack sound), ambient module sounds
  - [x] hatches between modules (real crew transfer, arrive floating at the matching hatch), EVA out of the side hatch, fade over hatch transfers, boarding straight back into IVA (built 2026-10-31, untested in game)
  - [ ] choose sounds with the audition keys (placeholders now) and a cabin ambience
  - [ ] kit tied to game systems (plan written, `PLAN.md` "Plan for 4"): Starlab experiments, light/SAS switches, sleep with time warp
- [ ] **Remaining fuselage cabins:** Mk1 Stowaway, Mk2 Tag Along, Mk3 Skybus (plane-style, gravity layouts are right there).
- [ ] _(original plan entry)_ **Crew cabins and Starlab** (`PLAN.md`, "Crew cabins and Starlab"):
  - [ ] Generalise the pipeline: specs without a pose block, upright seated kerbals moved in by the mod,
        catalogue entries for parts with no stock interior; painted windows via `window_paint.py`.
  - [ ] Capture: enter IVA once in each cabin.
  - [ ] Build in order: OSL-25 Starlab (3), PPD-10 Hitchhiker (4), PPD-20 Wayfarer (8), Mk1 Stowaway (2),
        Mk2 Tag Along (4), Mk3 Skybus (16).

## 5. Bugs and technical debt
- [ ] **Move to KSP2 Redux 26w43b** (`workflows/game-update.md`, `/game-update`): the game files changed on 2026-10-31 at 15:05, after
      the last build. Nothing has been migrated or compiled against them: the SDK project is on the 26w41a template (`unity-check`
      compiles against that, so a clean check says nothing about 26w43b), and `mod.config.json` and CLAUDE.md still say 26w41a.
      Unity is unchanged at 6000.6.0f1. API diff done (`notes/2026-10-31-26w43b-api-diff.md`): `ReduxLib` moved to `SpaceWarp2.API`,
      an 11-line `using` fix that compiles clean in a scratch copy. Not applied, because it breaks the 26w41a compile. The current
      build is expected not to load on the new game. Needs a new SDK template and the asmdef patch (Matt), the fix, a rebuild,
      and a flight test, including the bundles, boarding and the camera-rig crash.
- [ ] **Camera-rig crash:** mitigated (camera guard, N for next seat, Redux first-person fallback). Confirm it no
      longer happens across a longer session.
- [x] **Pose dump:** behind the Pose dump setting (on until release).
- [ ] **Painted windows:** if the game draws the hull double-sided anywhere, the panes would block the view from
      inside. Fallback: hide those hull faces while in IVA.
- [x] **Diagnostics:** camera report behind the Debug logging setting (on until release).

## 6. Release
- [ ] Check the licence of Mudkip909's original (repo is GPL-3.0) before making the repo public or releasing.
- [ ] Turn Debug logging and Pose dump off by default, and reword the README "Nothing happens on C" row.
- [ ] Version bump (`IVA.asset`), `CHANGES.md` section, README settings and keys table up to date.
- [ ] Package with `/mod-release`.
