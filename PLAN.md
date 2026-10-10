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
- [ ] 3. _(2026-10-10: concept built, renders `previews/mk35_concept_*.png`, awaiting approval.)_ **Layout concept for approval:** a top-down plan and a side section render with the captured kerbals in place,
      showing where everything goes. Proposed layout, to adjust round the real poses:
      - **Lower deck:** the couches on one frame (Apollo style), a wide main display console hung above the faces in
        sections (one per seat), pedestal consoles between couches, side consoles by the two-pane windows, umbilicals.
      - **Upper deck** (the pod has ~2 m of headroom the smaller pods don't): an equipment ring round the walls (lockers,
        avionics racks, tanks), a central ladder up to the docking tunnel, and a **docking station**: a secondary console
        under the upper windows, for rendezvous views (window view B goes there).
      - Floor: ECS and power units behind the feet; stowage and safety kit on the walls.
- [ ] 3b. **Crew into the couches** (code): move the booth kerbals onto the IVA seats while in IVA (see findings).
- [ ] 4. **Generator** `art/model_mk35.py` on `capsule.py` + `modules.py` (same tools as the Mk1-3), renders after each
      pass (eye views per seat, overview, upper deck, windows). Overlap checks must be clean.
- [ ] 5. **Approval of renders**, then export, Unity set-up and a catalogue entry in `CustomInterior.cs`
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
