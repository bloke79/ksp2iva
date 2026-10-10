# Plan: Bespoke interior for the large 3v command pod

_Created 2026-10-10 · Status: approved 2026-10-10_

## Goal
A full, stock-quality interior for `pod_3v_conical_crew`, built round the game's real seated poses, with working window
views and live instruments, to the standard of the reworked Mk1-3 (deep consoles, pedestals, umbilicals, equipment).

## What we already know
- **Hull:** 4.17 m tall, 1.91 m base radius narrowing to about 0.8 m at the top (`reference/pod_3v_conical_crew`); hull base at part y -1.641.
- **Windows are painted, not glass:** six amber panes are part of the hull texture (found by colour with
  `art/window_paint.py`). From inside, the game's hull isn't drawn (one-sided), so we cut real openings there and see out.
  - Upper pair, front, ±22.9°, z 3.13 (half 0.28 x 0.16 m): the docking windows near the top.
  - Two two-pane side windows at ±65°: z 0.88 and 1.39 (each about 0.3 x 0.43 m).
- **Hatch:** front, below the upper windows, with a ladder outside (to be measured).
- **Unknown until captured:** how many seats, where the kerbals lie, and which stock interior prefab the game uses
  (there's no `interior_3v_*` prefab, so it borrows one).

## Capture findings (2026-10-10)
- **5 seats, but no in-pod crew.** The game keeps the 3v's kerbals in the crew-portrait booth (layer 24, with a backdrop,
  in a row beside the pod), not in the pod. So there's no stock cabin to hide, no game eye points, and nothing drawn
  inside the pod: the seat layout is ours to design (the mod now only uses game eyes for kerbals on layer 17).
- The body pose is the same rig as the Mk1-3's, so its captured couch profile, hands and eye offset carry over.
- **Kerbals in the couches:** while in IVA, move the booth kerbals onto our couches (pose relative to each seat as in the
  Mk1-3 prefab) and switch them to Local.Characters; put them back on exit. Without this you'd look down at an empty
  couch. Crew portraits in the UI go blank while in IVA.
- **Crash during capture:** the old portrait-camera fallback moved the flight camera into the portrait booth and the
  camera rig's terrain raycast crashed natively (TerrainHeightSampler via BasicCameraRigSolution.DoesCameraCollide).
  Pods without an interior now use Redux's own first-person camera instead; the portrait fallback is retired.

## Steps
- [x] 1. _(2026-10-10: done. Findings below; the session also hit the open camera-rig crash, now fixed.)_ **Pose capture (Matt, about 2 minutes).** Put a crewed 3v pod on the pad (fill every seat if possible) and press C.
      The mod now captures poses in pods without an interior: it logs the seats, the stock interior it uses, and writes
      `IVA-pose/pod_3v_conical_crew.obj`. Then press C again to leave.
- [x] 2. _(2026-10-10: done; eyes at z 1.0, five seats 0.62 m apart.)_ **Spec** `art/pods/pod_3v_conical_crew.json`: hull profile, the six windows (from `window_paint.py`), hatch (measured
      from the hull), pose block (`pose_extract.py` on the capture), cabin light, preview cameras.
- [x] 3. _(2026-10-10: approved; Matt asked for both decks filled out as a working mission cabin.)_ **Layout concept for approval:** a top-down plan and a side section render with the captured kerbals in place,
      showing where everything goes. Proposed layout, to adjust round the real poses:
      - **Lower deck:** the couches on one frame (Apollo style), a wide main display console hung above the faces in
        sections (one per seat), pedestal consoles between couches, side consoles by the two-pane windows, umbilicals.
      - **Upper deck** (the pod has ~2 m of headroom the smaller pods don't): an equipment ring round the walls (lockers,
        avionics racks, tanks), a central ladder up to the docking tunnel, and a **docking station**: a secondary console
        under the upper windows, for rendezvous views (window view B goes there).
      - Floor: ECS and power units behind the feet; stowage and safety kit on the walls.
- [x] 3b. _(2026-10-10: done, untested in game.)_ **Crew into the couches** (code): move the booth kerbals onto the IVA seats while in IVA (see findings).
- [x] 4. _(2026-10-10: `model_mk35.py` + `props.py` mission kit: sleeping bags, galley, science rack, laptop, whiteboard, tool board, cargo bags, jetpacks, cameras, binders, zero-g plush...)_ **Generator** `art/model_mk35.py` on `capsule.py` + `modules.py` (same tools as the Mk1-3), renders after each
      pass (eye views per seat, overview, upper deck, windows). Overlap checks must be clean.
- [ ] 5. _(2026-10-10: exported, set up (60 materials), catalogue entry added, built; ~630k triangles.)_ **Approval of renders**, then export, Unity set-up and a catalogue entry in `CustomInterior.cs`
      (`Parts = pod_3v_conical_crew`, `OnHull`, `HullBaseY = -1.641`, `Yaw = 180`).
- [ ] 6. **In-game test (Matt):** seat switching (V), window views (B) including the docking windows, live instruments,
      lighting, nothing clipping through, leaving IVA cleanly.

## Done when
- Matt approves the renders and the in-game look; every seat's eye view shows its console section.
- All six windows line up with the hull's panes and window views reach them.
- The log shows the interior placed with no errors, and no part or stock-cabin geometry shows through.

## Risks / open questions
- Painted windows: if the game draws the hull double-sided anywhere, the panes would block the view from inside;
  fallback is to hide those hull faces while in IVA.
- The borrowed stock interior may put the kerbals somewhere awkward for a 4 m pod (e.g. a 3-seat layout in a bigger
  shell); the capture decides the layout.
- An upper deck is only seen through window views until moving around inside (FreeIva-style) exists; it's still worth
  building, as it's what you look up into from the couches.

_Previous plan (first build and in-game test of 0.6.0) is complete; see git history and STATUS.md._

---

# Plan: Moving around inside, and a polish pass on the 3v

_Created 2026-10-10 · Status: draft, awaiting Matt's approval_

## Goal
Get out of the couch and float/walk round the cabin (FreeIva-style, our own code), and make the 3v's kit look like real
equipment rather than toy blocks.

## A. Moving around (unbuckle)
- [ ] 1. **Collision shell from the generator:** each interior exports simple colliders (hull cylinder rings, deck, consoles,
      couches, large props) as `IVA_Collider_*` boxes/capsules; Set Up Interiors turns them into colliders on one private
      layer. Nothing physical touches the game's colliders.
- [ ] 2. **Free camera:** U unbuckles (key configurable). The view becomes a small capsule in pod space: WASD to move,
      Shift/Ctrl up/down, Q/E roll, mouse to look; it slides along the colliders (capsule sweeps, no rigidbody).
      Weightless drift with damping in orbit; on the ground or under thrust, "down" follows the pod's acceleration and you
      walk on the deck and floor, with ladders climbable (up/down while touching one).
- [ ] 3. **Back to a seat:** U again returns you to the nearest couch (glide, as with window views); N still switches seats.
      Window views (B) work from wherever you are.
- [ ] 4. **Hatch:** walking to the 3v's upper docking tunnel or side hatch just shows a "hatch" prompt for now (moving
      between parts is a later step).
- [ ] 5. Test on the 3v first (it has the most room), then the Mk1-3; the Mk1 is too small to be worth it.

## B. 3v polish (from the in-game screenshot)
- [x] 1. **Materials:** woven canvas texture for bags, textured locker finish (seams, grime) instead of flat white plastic,
      darker neutral colours, less glossy.
- [x] 2. **Proportions:** thinner straps and handles, smaller bevels (crisper edges), flatter cargo bags, thinner hazard-striped
      rails, slimmer ladder.
- [x] 3. **Upper deck dressing:** fewer identical white boxes; vary sizes and types (lockers, drawers, racks with gear).
- [x] 4. Renders from the same spots as Matt's screenshot before export.

## Done when
- You can unbuckle, move anywhere in the 3v (both decks, up the ladder) without passing through walls or equipment, and
  buckle back in; no crashes, camera restored on exit.
- The upper deck screenshot angle looks like real kit.

---

# Plan: Stock-level detail pass (all pods)

_Written 2026-10-10 after rendering the stock Mk1-3 interior (`interior_2v_m1_pod_crew`) from inside, for reference only._

## What the stock cabin does that ours doesn't
- **Detail is modelled, not painted.** Stock textures are mostly flat greys with grime; the Mk1-3 console alone is
  about 91k vertices. Every unit is a chamfered, stepped housing (45° bevels, plates on plates, inset doors with latches).
- **Fat colour-coded cables** (black, red, green, yellow) loop across the ceiling and between units, entering
  sockets through grommets and collars. They give the cabin its "lived-in machine" look.
- **No bare surface.** The ceiling has a segmented ring frame round the hatch, the floor has vent grilles and a hatch
  with chamfered frame and latches, the walls have bolted inspection plates. Seat frames are chunky chamfered struts.
- **Lighter walls than ours:** light-to-mid grey walls with rust/wear at edges, dark charcoal console faces, red cushions.

## Steps
1. New building blocks in `modules.py`: chamfered stepped housing (profile extrude), cable bundle (3 to 5 coloured
   cables with collars, clamps and socket ends), inspection plate, ring frame, latch, vent grille. Wear/grime texture.
2. Wall palette: mid-grey panels with edge wear (closer to stock), keep the dark consoles.
3. 3v first: dome and ceiling of the living deck (ring frame round the tunnel, equipment cassettes, light housings,
   ducts, cable runs), deck undersides on the flight deck, floor detail (foot restraints, under-floor stowage hatches),
   cable bundles linking the bulkhead, consoles and ceiling.
4. Then bring the Mk1-3 and 1v up to the same density. Keep an eye on the triangle budget (3v ~600k now).

---

# Plan: Crew cabins and Starlab

_Thinking only; nothing built yet. Data from the game's part definitions and extracted hulls (reference/, not in repo)._

| Part | Name | Crew | Size | Length x radius | Windows (painted) |
|---|---|---|---|---|---|
| `cabin_1v_m1_crew` | Mk1 "Stowaway" | 2 | S | 1.94 x 0.63 m | two ovals, one side |
| `cabin_2v_m2_crew` | Mk2 "Tag Along" | 4 | M (Mk2 profile) | 1.88 x 1.26 m | pairs on each side |
| `cabin_3v_m3_crew` | Mk3 "Skybus" | 16 | L (Mk3 profile) | 3.75 x 1.89 m | strip along the side |
| `cabin_2v_crew_hitchhiker` | PPD-10 "Hitchhiker" | 4 | M | 2.71 x 1.38 m | one porthole |
| `cabin_3v_crew` | PPD-20 "Wayfarer" | 8 | L | 5.0 x 1.96 m | triangle row |
| `lab_2v_science_orbital` | OSL-25 "Starlab" | 3 | M | 4.7 m long | one large window |

## Differences from pods
- **No stock interiors or seat poses.** Only pods and cockpits have `interior_*` prefabs; cabins seat their crew in the
  portrait booth. So we choose the seats and eye points ourselves (no `pose_extract` step), and move the crew's
  kerbals in as we do for the 3v (`MoveCrewIntoSeats`), seated upright or at stations rather than lying on their backs.
- **Orientation:** the Mk1/Mk2/Mk3 cabins are fuselage parts (plane-style: floor along the axis, seats facing the nose).
  The PPD cabins and Starlab are station modules (zero-g layouts: crew stations round the wall, "up" towards one end).
- **Windows are painted** on the hull texture: find them with `window_paint.py` as for the 3v.

## Proposed designs
- **Stowaway (2):** tandem airline seats, overhead lockers, a small bulkhead console at the front, the windows at seat height.
- **Tag Along (4):** two rows of two with a narrow aisle, overhead bins, galley cart and a crew panel at the front bulkhead.
- **Skybus (16):** an airliner cabin: four rows of four with a centre aisle, overhead bins, a galley and toilet at one end.
- **Hitchhiker (4):** a station crew module: four sleep stations round the wall, a fold-out table, galley, stowage.
- **Wayfarer (8):** a two-level hab along its 5 m: eight sleep stations, wardroom table, galley, hygiene, exercise.
- **Starlab (3):** three lab workstations along the walls, experiment racks, glovebox, the large window as an
  observation station, and a ceiling of cable trays and equipment (stock-level detail from the start).

## Steps
1. Generalise the pipeline: a spec format without a pose block (seats by position and facing), upright seated kerbal
   placement in the mod, catalogue entries for parts with no stock interior.
2. Capture: enter IVA (portrait) in each cabin once so the mod logs its hull and crew setup.
3. Build in order: Starlab, Hitchhiker, Wayfarer, then the fuselage cabins. Renders first for each.
