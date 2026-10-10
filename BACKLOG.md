# Backlog: IVA Redux

_Last updated 2026-10-11. Ordered by priority within each section. Detailed designs live in `PLAN.md`; current state in `STATUS.md`._

## 1. Finish the 3v (Mk3-5, 5 seats): close to done
- [ ] **In-game check of the latest build** (`735b770`): upstairs fixes (glovebox, freezer, bike, table, cables into
      junction boxes, floor clutter removed), overall brightness, frame rate.
- [ ] **Basics still unconfirmed in game:** N switches seats, seat view the right way up, B reaches the docking windows,
      crew sit in the couches.
- [ ] **Short rib pieces** left between wall units (e.g. under the freezer): raise the minimum length or skip ribs where
      a unit sits.
- [ ] **Triangle budget** (~750k): the hull shell is ~128k (2 cm rings, over-tessellated) and the console ~137k.
      Coarsen the shell away from windows; check console module density.
- [ ] **Remaining thin spots:** upper wall bands of the living deck, and its middle band between the furniture rows.
- [ ] **Floors:** consider solid deck plates with grille inserts (stock look) instead of open grating everywhere.
- [ ] **Brightness tuning** if needed after Matt's check: AO floor (`IVA_AO_FLOOR` = 0.4), `_AODirect` (0.45), deck lights.

## 2. Features
- [ ] **Moving around inside (unbuckle):** U to unbuckle, WASD/mouse free camera with collision, U to return to the
      nearest couch, hatch prompt at the tunnel/side hatch. Exported collision shell from the generator.
      Test on the 3v first, then the Mk1-3. (`PLAN.md`, "Moving around inside")
- [ ] **Live instruments check:** navball orientation (nose on the horizon facing north shows N at centre, E to the
      right; pitching up brings blue up from the bottom), altimeter, pressure and temperature needles.
- [ ] **Window views (B):** confirm on all three pods.

## 3. Bring the other built pods up to the stock style
- [ ] **Mk1-3 (3 seats):** apply `art/stock.py` (ribs, frames, cable bundles, ceiling detail, stepped console housings,
      chamfered couch frames), re-export. It currently only has the lighter shared wall texture.
- [ ] **Mk1 (1 seat):** the same, scaled to the small cabin.

## 4. New interiors (renders first for each)
- [ ] **Remaining pods and cockpits:** 1.5v, cupola, landers (1v, 2v, 3v), Mk1/Mk2/Mk3 cockpits (and inline variants).
      Enter IVA in each once so the pose dump captures the seated kerbals, then `pose_extract.py`.
- [ ] **Crew cabins and Starlab** (`PLAN.md`, "Crew cabins and Starlab"):
  - [ ] Generalise the pipeline: specs without a pose block, upright seated kerbals moved in by the mod,
        catalogue entries for parts with no stock interior; painted windows via `window_paint.py`.
  - [ ] Capture: enter IVA once in each cabin.
  - [ ] Build in order: OSL-25 Starlab (3), PPD-10 Hitchhiker (4), PPD-20 Wayfarer (8), Mk1 Stowaway (2),
        Mk2 Tag Along (4), Mk3 Skybus (16).

## 5. Bugs and technical debt
- [ ] **Camera-rig crash:** mitigated (camera guard, N for next seat, Redux first-person fallback). Confirm it no
      longer happens across a longer session.
- [ ] **Pose dump** (`CustomInterior.DumpPoses`): keep, or put behind a setting, before release.
- [ ] **Painted windows:** if the game draws the hull double-sided anywhere, the panes would block the view from
      inside. Fallback: hide those hull faces while in IVA.
- [ ] **Diagnostics:** trim key-press and camera-report logging to a debug setting before release.

## 6. Release
- [ ] Check the licence of Mudkip909's original (repo is GPL-3.0) before making the repo public or releasing.
- [ ] Version bump (`IVA.asset`), `CHANGES.md` section, README settings and keys table up to date.
- [ ] Package with `/mod-release`.
