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
_2026-10-11: first version built. Collision is position-only markers (`stock.collision_markers`: hull profile, decks and
openings, oriented equipment boxes, hatches) read by `FreeMove.cs`; no Unity physics, so nothing touches the vessel.
Floating is zero-g everywhere for now; walking under gravity and climbing ladders are still to do._
- [x] 1. **Collision shell from the generator:** each interior exports simple colliders (hull cylinder rings, deck, consoles,
      couches, large props) as `IVA_Collider_*` boxes/capsules; Set Up Interiors turns them into colliders on one private
      layer. Nothing physical touches the game's colliders.
- [x] 2. **Free camera:** U unbuckles (key configurable). The view becomes a small capsule in pod space: WASD to move,
      Shift/Ctrl up/down, Q/E roll, mouse to look; it slides along the colliders (capsule sweeps, no rigidbody).
      Weightless drift with damping in orbit; on the ground or under thrust, "down" follows the pod's acceleration and you
      walk on the deck and floor, with ladders climbable (up/down while touching one).
- [x] 3. **Back to a seat:** U again returns you to the nearest couch (glide, as with window views); N still switches seats.
      Window views (B) work from wherever you are.
- [x] 4. **Hatch:** walking to the 3v's upper docking tunnel or side hatch just shows a "hatch" prompt for now (moving
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

---

# Plan: F as the action key — hatches, modules, getting in and out, interactive kit

_Written 2026-10-11 from Matt's notes. F already opens hygiene doors while floating; this grows it into one action
system. Nothing here is built yet beyond the doors._

## How interaction works (all of it)
- **Look to target:** while floating, a small dot sits at the centre of the view. The nearest interactive thing the dot
  is on, within about 1 m, is the target: it gets a soft outline/glow and a prompt ("F: open curtain").
- **Markers, not physics:** each interactive thing exports a position marker `IVA_Act_<kind>_<name>` (plus helper markers
  where it moves, like the doors' hinge markers). The mod keeps a registry of handlers by kind. No colliders.
- **Seated:** from a couch only things in reach work (switches, MFDs, the laptop on its arm); everything else needs you
  to unbuckle (U).

## Hatches: moving between modules, and getting in and out
- **Internal hatches (module to module):** every interior already marks its hatches (`IVA_Hatch_*`). At build time each
  hatch gets the attach node it sits on. In flight, F at a hatch looks up the part joined at that node:
  - if that part has an interior of ours: the hatch swings open (animated like the doors), you glide through the
    opening, the view fades for a moment while the next interior loads, and you arrive floating just inside that part's
    matching hatch, facing in. The kerbal's seat assignment moves with them (a real crew transfer in the game's crew
    data, so the portraits and capacity stay right). If the part is full, the prompt says so.
  - if it has no interior (a probe core, fuel tank, or a part we haven't built): "Nothing to go through to" / "Hatch
    blocked", like KSP's own transfer rules (a crewable part on the other side is needed).
- **External hatch (getting out):** F at a pod's side hatch (or a cabin's exterior hatch where it has one) opens it
  and hands over to the game's own EVA: the kerbal appears outside on EVA and the game camera takes over. Getting back in
  is the game's own "board" action; a toggle can drop you straight back into IVA at the hatch.
- **Research needed first:** the game calls for a crew transfer between parts and for EVA from a given part (the
  api-scout agent against the 26w41a DLLs), and how attach nodes map to our hatch markers on the 3v (tunnel, side
  hatch), Starlab, Hitchhiker and Wayfarer (both ends).

## Thruster sound (moving about)
- While you thrust (WASD/Shift/Ctrl), play the game's own EVA jetpack sound: short puffs on taps, a soft continuous
  hiss when held, quieter than outside (it's a hand-held cold-gas puffer, not the full EVA pack). Using the game's own
  sound events means nothing new to licence or ship. Research: the event names in the game's audio banks and how mods
  trigger them.

## Interactive kit (by kind)
| Kind | F does | Moves | Sound |
|---|---|---|---|
| Hygiene door (built) | open / close | door swings | latch, hinge |
| Toilet | flush | (lid) | suction whoosh, fan spin-up |
| Wash station | water on | — | water burst, air dryer |
| Crew quarters curtain | open / close | curtain slides | fabric |
| Crew quarters lamp | on / off | lamp lights | click |
| Sleep (in your own quarters) | sleep: the view dims, and with time warp allowed, warps until morning | — | — |
| Food warmer / oven | open, put a meal in, it hums, then dings | door, window glows | hum, ding |
| Water dispenser | fill a drink bag | — | pump, water |
| Food lockers, drawers, stowage | open / close | doors swing, drawers slide | latch |
| Freezer | open | door | seal pop, cold hiss |
| Glovebox | lights on, work at it | gloves sway | fan |
| Experiment racks (goo, materials) | run the part's real experiment (Starlab's science) | lamps, canister glow | servo |
| Laptops and MFDs | cycle pages (systems, map, engine, comms) | screen changes | key click |
| Switch banks, toggles | flip (cosmetic, or tied to real actions: lights, SAS) | toggle throws | click |
| Cabin lights | normal / night red / off for each deck | lights change | click |
| Window shutters | close / open over a window | shutter slides | motor |
| Binoculars, cameras | look through (zoomed view at the window) / take a screenshot | — | shutter |
| Comms headset | listen to mission chatter | — | radio |
| Ergometer | ride: pedal animation, your heart rate on its display | pedals spin | whirr |
| Fans, pumps (ambient) | — | fan blades turn | quiet loops per module |

## Order
1. Look-to-target, prompt, registry, and the cheap wins: curtains, lockers/drawers, oven, lights, toilet flush,
   laptops/MFD pages (all local: markers, a little animation, game sounds where they exist). **Built 2026-10-11.**
2. Thruster sound and ambient module sounds. **Built 2026-10-11** (ambience is a setting, off until a sound is chosen).
3. Hatches between modules (needs the crew-transfer research), then EVA out of the side hatch. **First version built
   2026-10-11:** F at a hatch moves you into a free seat of the crewed module beyond (`KerbalRosterManager.SetKerbalLocation`)
   and you arrive floating at its matching hatch; F at the side hatch (or a cabin end hatch with nothing beyond) calls
   `EVAUtils.TryStartEVA`. No hatch animation or fade yet.
4. Things tied to real game systems: experiments, lights/SAS switches, sleep with time warp. Plan below.

## Plan for 4: kit tied to real game systems

_Written 2026-10-11. The game calls below were checked in the 26w41a DLLs; none is wired yet._

| Item | What F does | Game call | Notes |
|---|---|---|---|
| Starlab experiment racks | Run the part's experiment; the rack's lamps light and its screen shows progress until done | `PartComponentModule_ScienceExperiment.RunExperiment(id)` / `StopExperiment`, `IndexOfRunningExperiment`, `GetInvalidSituationString` for "can't run here" | Find the module on the Starlab part (`_session.Pod.Model`). One rack per experiment the part defines; others say which experiment is running. Also the 3v lab tier and Mk1-3 science panel for the pod's own experiments |
| Light switch | Toggle the vessel's lights action group (the exterior lights) | `VesselComponent.SetActionGroup(KSPActionGroup.Lights, on)`, `GetActionGroupState` | Separate from the cabin light modes (which stay local). A guarded toggle on each console |
| SAS / RCS / gear / brakes switches | Toggle those action groups | the same with `KSPActionGroup.SAS`, `RCS`, `Gear`, `Brakes`; SAS mode buttons via `VesselAutopilot.SetMode(AutopilotMode.…)` | Only on the cockpit consoles (Mk1, Mk1-3, 3v), within reach while seated, so these need the seated version of look-to-target (see below) |
| Abort / stage handle | Stage, abort | `KSPActionGroup.Abort`; staging through the game's staging call (to be found) | Behind a lift-the-cover-then-pull two-step, never by accident |
| Sleep (own quarters) | Lie in, the view fades, time warps to a set wake time (morning at KSC, or 8 h), then fades up | `TimeWarp.WarpTo(ut, min, max)`, `CancelAutoWarp`; `GetMaxRateIndex` to respect the game's warp limits | Refuses in atmosphere, under thrust or near a manoeuvre node, the same as the game's warp rules |
| Instrument panels' real readouts | Already live (navball, needles); add fuel, power and comms readouts to the MFD pages | telemetry the live instruments already read | Pages stay textures; numbers drawn on top later |

**The seated version of look-to-target** (needed for console switches): while buckled in, with the mouse look, the
same dot and prompt, but only for targets within 0.8 m of the eye and only kinds marked "reach" (switches, MFDs). F is a
flight key while seated (the vessel's controls aren't locked), so the seated key needs to be different: hold the
middle mouse button and click, or a configurable key that doesn't clash (to choose with Matt).

**Order:** seated targeting, then the switch banks (lights, SAS, RCS, gear, brakes), then the Starlab experiments, then
sleep with time warp, then abort and staging.

**Art:** the console toggle banks become live parts (each toggle throws), with `IVA_Act_Switch_<group>` markers and
labels under them; the Starlab racks get an `IVA_Act_Experiment_<n>` marker and a progress screen.

# Plan: Interiors for the remaining crewed parts

_Written 2026-10-11 for Matt's list: the Mk3 shuttle cockpit, the three lander cans, the cupola, the rover truck cab,
the Mk1/Mk2/Mk3 fuselage crew cabins (2, 4 and 16 seats) and the marine survey lab. Sizes and crew counts are from the
extracted parts (`C:\Games\KSP2Mods\reference`); none are built yet._

## The one big split: gravity or zero g
Everything so far is zero-g (pods and stations: foot loops, every surface used). Most of this list lives under gravity,
so it gets a **gravity layout**: a real floor, seats that face forward, things stowed so they don't fall, ladders and
steps. Free movement (U) then needs walking for these parts (backlog: "walking under gravity, ladders"); until then
they work seated, with N between seats and B to the windows, like the pods.

| Part | Crew | Size (w × h × d) | Lives | Layout |
|---|---|---|---|---|
| Mk3 cockpit (shuttle) | 4 | 3.35 × 4.48 long × 3.75 | atmosphere and orbit | gravity (a flight deck) |
| Lander can 1v | 1 | 1.68 dia × 1.4 | landed / descent | gravity |
| Lander can 2v | 2 | 2.73 dia × 1.4 | landed / descent | gravity |
| Lander can 3v | 4 | 3.8 dia × 2.24 | landed / descent | gravity |
| Cupola | 1 | 2.73 dia × 1.24 | orbit (station) | zero g |
| Rover truck cab | 3 | 2.6 × 4.0 tall × 1.9 | surface | gravity, upright |
| Mk1 crew cabin | 2 | 1.25 dia × 1.94 long | atmosphere | gravity (cabin) |
| Mk2 crew cabin | 4 | 2.5 × 1.5 lifting body × 1.88 long | atmosphere | gravity (cabin) |
| Mk3 crew cabin | 16 | 3.25 × 3.79 × 3.75 long | atmosphere and orbit | gravity (two decks) |
| Marine survey lab | 1 | 2v (to extract) | in water | gravity, submersible |

## Designs

**Mk3 cockpit — shuttle flight deck.** The Space Shuttle's layout scaled to KSP: commander and pilot side by side at the
front under the eight forward/overhead windows, two mission specialists behind. Forward glareshield with MFDs and the
navball, centre console between the front seats, overhead switch panels (the shuttle's famous ceiling of breakers),
aft flight-deck station facing back through the two aft windows (the docking/robotic-arm controls, like the orbiter's
aft deck), a ladder hole in the floor down to a small mid-deck (lockers, galley strip, side hatch for EVA, and the
connecting hatch aft to the Mk3 fuselage). Windows from the extracted glass (8 panes).

_Matt's reference floorplan (2026-10-11, orbiter crew-compartment cutaways):_ two levels joined by a ladder (with a
floor-level hole/interdeck hatch on the port side). **Flight deck:** commander (port) and pilot (starboard) seats with
their controls forward; aft controls station behind them. **Mid deck:** storage lockers in walls of drawers at the
forward bulkhead (both sides), sleeping area (bunk stack) on the starboard side, side crew hatch (round) on the port
side, galley on the port side next to the ladder, toilet (waste-collection) compartment on the port side aft, room for
exercise (treadmill) in the middle. Lower deck below: stowage and equipment. Use this split for the Mk3 cockpit: flight
deck above, mid-deck below the floor hatch, scaled to the part.

**Lander cans — Apollo LM style, three sizes.** Standing/strapped-in crew facing two triangular forward windows that
look down at the landing site (the 3v already shows that window band), with a descent panel between them: navball,
altitude and vertical-speed tapes, a radar altimeter dial, an abort/stage pair. Overhead docking window and hatch
(rendezvous), floor hatch out to the ladder (EVA). Behind the crew: a wall of stowage, sample containers and a
suit-and-helmet rack. Sized up:
- 1v: one standing station, harness from the floor, everything within arm's reach (a phone box).
- 2v: two stations side by side (the LM itself), shared centre console.
- 3v: four seats in two rows, a small galley and sleep hammocks strung across the back for surface stays.

**Cupola — observation and robotics.** One seat in the middle facing up into the dome of windows (seven panes, like the
ISS cupola), two hand controllers on swing-out arms for a robotic arm, a laptop on its arm, camera and binocular
stowage, foot loops round the rim. Window shutters (an F action from the interactive kit plan) that close over each pane.

**Rover truck cab — the expedition cab.** Tall, upright and narrow: a driver's seat forward and high behind the big
front windows with a steering yoke, throttle, a navigation map screen and a camera monitor; two passenger seats behind
facing the side windows; a floor hatch out the back to the ladder (EVA), suit lockers, a sample drawer bank and a
tool rack. Grab handles everywhere (it's bumpy). Gravity, upright.

**Mk1 crew cabin (2).** A small business-jet cabin: two reclining seats facing each other across a fold-down table,
overhead lockers, side panels with reading lights, a tiny galley shelf. Doors at both ends to the next fuselage parts.

**Mk2 crew cabin (4).** The lifting-body cross-section is wide and low: four seats in two facing pairs either side of a
narrow aisle, low overhead bins, a crew panel at one end with the cabin display, and a hatch at each end.

**Mk3 crew cabin (16).** An airliner-style cabin on two levels, or one tall level with seats 2-2 and a middle aisle
(16 seats in four rows of four), overhead bins, galley and lavatory at one end (reusing the hatch-door bathroom), a
crew station at the other, floor hatches between levels if two decks. In orbit it reads as the shuttle mid-deck's
big sister.

**Marine survey lab (1).** A submarine science station: one operator seat at a sonar/sampling console facing a big
viewing port, a sample lock (wet lock) in the floor, specimen tanks with lit water, pipes and valves with handwheels
(like the new floor hatches). Extract the part first (not in the reference set yet).

## Shared work before building
- **Gravity kit:** seats (upright, with harness), a floor, steps/ladders, stowage that's latched, grab handles. New
  `art/gravity.py` alongside `cabin.py`.
- **Windows:** the landers, cupola, truck and cabins use tinted glass the window extractor doesn't recognise yet (it
  found 0 windows); extend `window_extract.py` to their glass materials.
- **Seats and eyes:** the cockpits have stock interiors (their seat poses are in `reference/poses`); the landers,
  cupola, truck and cabins put their crew in the portrait booth, so they use our seat points with upright crew, as the
  Starlab and cabins do. Enter IVA once in each part so the pose and stock-interior dump runs.
- **Hatches:** each part's real hatch positions (EVA side/floor hatches and the attach ends) as `IVA_Hatch_*` markers.

## Order (renders first for each)
1. Lander 2v (the classic LM; sets up the gravity kit), then 1v and 3v from the same kit.
2. Rover truck cab (gravity, upright; uses the same kit).
3. Cupola (zero g; small, reuses the station kit).
4. Mk3 cockpit (shuttle) — the biggest single interior.
5. Mk1, Mk2, Mk3 crew cabins (seating rows).
6. Marine survey lab (after extracting the part).
Later: the 1.5v pod, the Mk1 and Mk2 cockpits and the inline cockpits.

## Update 2026-10-11: the cockpits already have stock interiors
Extracted (`C:\Games\KSP2Mods\reference\interior_*_cockpit_crew*`) and rendered: the Mk1, Mk1 inline, Mk2, Mk2 inline and
Mk3 cockpits all have complete, detailed stock interiors (glareshields, consoles, sticks and pedals, overhead panels,
seats; the Mk3 is a four-seat shuttle flight deck, the Mk2 a side-by-side two-seater, the Mk2 inline a crew/stowage
bay). Proposal: don't rebuild them. Keep the stock interior visible and add an invisible **overlay** per cockpit with
only what the mod needs (collision markers for floating, hatches, window views, interactive targets), seated at the
game's own eye points. The Mk2's interior sits about (3.5, -1.5, -6.3) m from its part origin in the prefab, so the
overlay must be placed from the stock interior's transform, not the part's.

## Mk3-5 pod rework (2026-10-11): floorplan in the cockpit design language

Matt asked for the 5-seat pod to get the shuttle-era design language and a fresh floorplan built on the lessons so far.
Floorplan: `scratch/iva-redux/mk35_floorplan.png` (side section and both deck plans, drawn on the measured hull).

**Lessons it's built on**
- The hull is a cone: inner radius 1.83 m at the floor, 1.43 m at the upper deck, about 1.0 m at the docking windows.
  Tall boxes against the wall clip (the old hygiene booth was 43 cm through the hull), so tall items go inboard and
  wall kit is placed with the hull measurement and leans with the cone.
- Review clean (`review.py`) before showing anything. The current model has 179 clips, 69 hull hits and 95 flicker pairs,
  mostly from free-hanging cable drops and junction boxes, so those go.
- Cockpit finish: grey legend panels, glareshield button beam, blue segmented cushions, cream padded walls with velcro,
  off-white lockers in living areas, yellow grab bars, round hatches with wheels.

**Layout (second pass: the toilet stays downstairs, as Matt asked)**
- Three ways in, all on clear paths. The floor hatch and the ladder share the aft aisle (x +/-0.40). The EVA hatch
  has a clear route forward over the couches' head end.
- Flight deck:
  - Five couches where the crew lie, restyled with blue cushions. Pedestals between them, side consoles beside them.
  - The five-section main display console overhead, with the button beam along its head edge.
  - Low lockers in the front corners, below the window line.
- Toilet compartment, port aft, entered from the aisle. Its two flat walls face the aisle and the couches; the hull is
  its outer wall, so nothing pokes through. Inside: light, vent, handholds, towels and a curtained wash point.
- Equipment bay, starboard aft, mirroring the toilet: ECS, power and CO2 cartridges. The suit umbilicals leave it in
  a manifold under the couch frame, so no hose crosses the aisle.
- Living deck:
  - Docking station (leaning with the cone) and a glovebox forward, under the docking windows.
  - Five sleeping berths on the quiet sides: three to starboard, two to port with crew lockers.
  - Galley, fold-out table and pantry either side of the ladder hole.
  - Ergometer front-port.
  - The middle stays clear for the climb from the ladder to the docking hatch.


## Lander cans: floorplans (2026-10-12), redone KSP1-style and built (2026-10-13)
Matt: "they were far more cramped than you're proposing". The first plans (open floor, panels on the walls) were redrawn
after the KSP1 Mk1/Mk2 lander can IVAs (`scratch/iva-redux/lander_plan_v2_{1v,2v,3v}.png`). Built in
`art/model_lander.py` (commit 1dd14f4).

**The pattern (all three):**
- the crew sit at the panels
- everything else is floor-to-ceiling drawer banks fitted to the hull (`bank()`: a flat front, with a body that runs back
  to the lining), with silly labels (`labelgen.py` atlas)
- a narrow aisle runs to the hazard-striped EVA hatch
- a ladder runs up to the docking hatch

**Per lander:**
- **1v:**
  - The seat is in the middle, with the descent panels on the lining's window pillars either side of the window, facing the
    pilot.
  - Drawer stacks either side of the seat carry the side panels.
  - Overhead switches.
  - A helmet shelf and extinguisher, a tall locker, and a climbing pole beside the hatch.
- **2v:**
  - Two seats at the main panel, with side consoles at the elbows.
  - The ladder sits right behind the seats.
  - Drawer banks line the aisle: a whiteboard set into one, a glovebox and a poster in the other.
- **3v:**
  - Four seats in two rows under the window band, with side consoles topped by sloping panels.
  - A galley nook to port (counter, oven splashback, cupboards).
  - A science bank to starboard (glovebox, whiteboard).
  - The ladder sits behind the rear seats.
  - Lockers and a helmet closet to port of the aisle; the toilet opens onto the aisle to starboard.

**Still to do:** catalogue entries (`CustomInterior.cs`) and export, then a playtest.


# Plan: Walking under gravity (and ladders)

_Written 2026-10-13. For Matt's review before any code._

## Goal
Unbuckle (U) in a landed lander, or any cabin built with a floor, and **walk**:
- feet on the deck, gravity pulling you down, the walls and furniture solid
- climb the ladder to the docking hatch
- buckle back in at a seat

Floating stays exactly as it is in orbit.

## How it works now
`FreeMove.cs` is a small sphere (r 0.13) that floats in pod space. It has no Unity physics (colliders would join the
pod's rigidbody). Its world comes from position-only markers that `stock.collision_markers` exports:
- the hull radius profile up the axis
- deck heights
- openings in decks
- oriented boxes round the equipment
- hatch points

Walking reuses all of this. It adds a down direction, feet and a few new markers.

## 1. Which way is down
- Each frame, read the vessel's **felt acceleration**: gravity plus its own acceleration, the thing a g-meter shows, as
  a vector in pod space. (API to verify with api-scout. `LiveInstruments.cs` already reads `VesselComponent` telemetry.)
- **v1 rule: walk only when landed, splashed or pre-launch**, and the felt gravity is over ~0.03 g (Minmus is 0.05 g).
  Everywhere else you float as now. Thrust in flight keeps you floating.
- Down is used as it is, so a lander parked on a slope has a tilted floor. Over ~30° of tilt you slide and can't climb
  it.

## 2. Which interiors have a floor
A new spec field, `"floors"`: deck planes (height and normal), exported as `IVA_Floor_<k>` markers. Walking only switches
on when down is within ~35° of a floor's normal. Otherwise, under gravity, U says "no floor to stand on" and you stay
buckled.

| Interior | Floor |
|---|---|
| Landers 1v/2v/3v | the deck, normal = the part axis |
| Mk3 cockpit and Mk3 cabins (horizontal fuselage) | the flight deck and lower deck, normal = the cabin's down on a runway |
| Pods (Mk1-3, Mk1, Mk3-5), Starlab, crew cabins in orbit | none |

## 3. The walker (FreeMove gets a second mode)
- **Body:** a capsule 0.26 wide, with the eye 0.86 above the feet (a kerbal's eye height, from the seated poses).
- **Ground:** the highest walkable surface under the feet. That's a deck, or the top of a box no more than a 12 cm step
  up (kick strips, sills).
- **Falling:** off an edge or through a deck opening, you fall under the felt g and land.
- **Head:** where the ceiling is lower than eye + 10 cm (the 1v and 2v are 1.2 m tall inside), the view crouches
  automatically.
- **Walls:** the hull profile and equipment boxes, as now. With gravity they're sideways pushes only, so you slide along
  a drawer bank.
- **Controls:**
  - W/S/A/D to walk.
  - The mouse turns about down, with the pitch clamped to ±85° (no roll).
  - Space jumps. On the Mun that's a long, slow hop, capped by the ceiling.
  - Ctrl crouches.
  - Same keys as floating.
- **Speed:** a new setting, "Walk speed" (default 0.9 m/s, with a README row).

## 4. Ladders
- `ladder()` and `pole()` in the generator export `IVA_Ladder_<k>_0/_1` (bottom, top).
- Walk into a ladder facing it (or press F at it) to grab on. Then W/S climb, gravity is off, and you stay on the
  ladder's line. Step off at the bottom or sideways.
- At the top, the existing hatch prompt appears ("go through to the …"), so the docking hatch works from the ladder.
- Deck openings without a ladder (the Mk3 cockpit floor hatch) get one. Otherwise the way back up is a jump.

## 5. Getting in and out
- **Unbuckling:** you stand up in front of your seat.
- **Buckling (U):** you sit in the nearest free seat, as now.
- **Hatches:** going through a hatch while walking keeps walking in the next part if it has a floor and gravity.
  Otherwise you arrive as now.
- **EVA from a landed lander:** that's the existing EVA lever/hatch. Nothing changes.

## 6. Order (each step is a playtest for Matt)
1. **Down, logged only:**
   - Felt-g vector in pod space, the situation, and the matching floor, logged when you unbuckle.
   - Test on the launchpad (1 g) and in orbit (0 g).
   - No movement changes yet.
2. **Floors and walking on the deck, landers first:**
   - The walker mode, crouch and steps.
   - Catalogue entries and an export for the three landers.
3. **Ladders:** markers, climbing, and the top hatch.
4. **The other gravity interiors:** the Mk3 cockpit and cabins (landed), plus a ladder at the Mk3 floor hatch.
5. **Polish:**
   - footstep sounds
   - optional head bob
   - landing thuds
   - the "no floor" message

## Done when
- On the Mun, in each lander, you can:
  - unbuckle
  - walk to the EVA hatch and the drawers without passing through anything
  - climb to the docking hatch and go through
  - come back and buckle in
- On the launchpad the same works at 1 g. In orbit you float as before.
- The log shows the down vector and the mode switches, with no exceptions.

## Risks / open questions
- **Felt-g API:**
  - Which `VesselComponent` field gives a stable vector while landed (the contact forces make "acceleration" noisy)?
  - Fallback: gravity at the vessel's position, used only when landed.
- **Hull profiles:** the collision hull is a radius-around-the-axis profile, which is fine for the round landers. The
  boxy Mk3 cabins may need box walls (more ColBox markers).
- **Capsules under gravity (Matt to decide):** on the pad, should U in the Mk1-3 or Mk3-5 pod say "no floor", or should
  you be able to clamber over the couches? Proposed: "no floor" for now.
- **Thrust (Matt to decide):** walk only when landed (proposed). The alternative is that thrust in flight pins you to the
  aft bulkhead: fun, but a lot of edge cases.
