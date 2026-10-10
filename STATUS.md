# Status: iva-redux

**Last updated:** 2026-10-11
**Version / milestone:** 0.6.0 + pose-fitted Mk1 and Mk1-3 interiors (unreleased) · KSP2 Redux 26w41a
**Health:** 🟢 Three pods built (1v, Mk1-3, 3v); the 3v has had a stock-style detail pass and playtest fixes. Camera-rig crash mitigated, to be confirmed over a longer session.

## Next steps
The prioritised to-do list is in **`BACKLOG.md`**. Top of it:
1. Matt checks the latest 3v build in game (upstairs fixes, brightness, frame rate, N/B, view orientation).
2. Tidy the last 3v items (short rib pieces, triangle budget, thin spots).
3. Moving around inside (unbuckle), then the stock-style pass on the Mk1-3 and Mk1, then cabins and Starlab.

Rebuild after any change: `.\scripts\sync-to-unity.ps1 -Project iva-redux`, then `.\scripts\build-mod.ps1 -Project iva-redux`
(about 20 s; run **IVA > Set Up Interiors** in batch first if the interior files changed).

## In progress
- Nothing yet. The project was imported from `_strip/` with the claude.ai handoff in `notes/`.

## Blockers / questions for Matt
- In-game testing needs Matt at the PC (Claude builds and reads logs; Matt flies).
- This repo is GPL-3.0, but the licence of Mudkip909's original is unknown. Check compatibility before going public.

## Done (recent)
- 2026-10-11 – Starlab, Hitchhiker and Wayfarer interiors (zero-g, ISS-style): rack rooms with every surface used, crew
  quarters and hygiene compartments recessed into the standoffs behind the walls, foot loops instead of chairs, railed
  tables, greenhouse (Starlab), window lounge and ergometer (Wayfarer). The 3v got a proper hygiene compartment and a
  railed table. Upright crew placement for cabins; N cycles on to the next crewed part. Laptop arms no longer cross screens.
- 2026-10-11 – 3v interior declared **v1**. Stock-style pass backported to the Mk1-3 and Mk1: ribs, ring frames, inspection
  plates, cable bundles into junction boxes, chamfered couch frames and console struts, stepped housings, deck plates,
  hatch segment ring and equipment boxes (Mk1-3). All three pods re-exported and built.
- 2026-10-10 – 3v stock-style detail pass (from rendering the stock Mk1-3 interior): new `art/stock.py` (chamfered ribs,
  ring frames and beams, colour-coded cable bundles with ties and sockets, inspection plates, light fixtures, floor
  hatches, foot restraints, wall racks, and a clearance check so structure fits round equipment). Solid panelled ceiling
  under the upper deck with box beams, lights, ducts and cables; tunnel hatch and equipment cassettes in the dome;
  chamfered couch frames, console struts and stepped console housings; lighter worn wall panels. ~750k triangles.
- 2026-10-10 – KSP2 stock-matched art pass: `IVA/Interior` surface shader (AO from vertex colour red; dimmed indirect),
  Cycles AO bake in `export_interior.py` (0.12 m contact distance, floor 0.4, exported as sRGB; printed faces and emissives
  skipped), dark wall-panel / gunmetal locker textures, dark cushions, olive canvas. 3v split into decks with `extra_lights`; then
  reworked to two decks plus an aft equipment bulkhead (three decks left the upper two about 0.9 m high). 3v `eye_marker` now builds a full basis (fixes the upside-down seat view). All three pods re-exported, set up, built.
- 2026-10-10 – Camera-rig crash root-caused: moving the flight camera outside the rig's view (old portrait fallback) makes
  the rig's terrain raycast crash natively. Custom IVA now uses a camera shot override (no transform moves); pods without
  an interior use Redux's own first-person camera. 3v pod plan approved; capture shows its crew live in the portrait booth.
- 2026-10-10 – Live instruments: navball turns with the real attitude (horizon frame via PhysicsSpace), altimeter
  (km + tens-of-km hands), outside pressure and temperature needles. Gauge faces without printed needles
  (`texgen.py` now builds named textures only, with Windows font fallback). Untested in game.
- 2026-10-10 – Window views (B): glide to the nearest window, cycle, back to the seat. Untested in game.
- 2026-10-10 – Stock cabin model (drawn in flight) hidden while the custom interior shows.
- 2026-10-10 – Reworked the Mk1 and Mk1-3 interiors round the game's real seated poses. The mod now dumps the posed
  kerbals once per pod type (`IVA-pose/<part>.obj`); `pose_extract.py` turns that into couch profiles, eyes, hands.
  Shared `art/capsule.py` (hull, windows, hatch, pose-fitted couches, console surfaces, overlap-checked layouts).
  Mk1: ceiling console above the face inside a crown of instruments. Mk1-3: new spec from the real hull and windows;
  Apollo-style three-section console over the crew, side consoles, couch frame, lockers, tanks, docking hatch.
  Previews `previews/mk1_*.png`, `previews/mk13_*.png`; exported, set up (35 / 37 materials) and built.
- 2026-10-10 – Camera now uses the game's `IVA EyeTransform`; only your own kerbal's head is hidden (body stays).
- 2026-10-10 – Bespoke Mk1 (1v) interior: reclined form-fit couch, horseshoe panel with the porthole in its centre, periscope
  display, foil-blanket walls, bolted side hatch. Built to the real hull (extracted from the game), overlap-checked panel layout,
  EEVEE previews in `previews/mk1_*.png`. Exported to `Interiors/Conical1v`, set up (34 materials) and built; catalogue entry added.
- 2026-10-10 – SDK project `C:\Games\KSP2Mods\IVA` (26w41a, Unity 6000.6.0f1) created and set up. Mod `IVA` created, source synced,
  real Unity compile clean after adding Addressables refs to `IVA.asmdef`. Set Up Interiors: 35 materials, address `IVA/Interior_Mk1-3`.
  Build for Player → `<KSP2>\mods\__Testing\IVA` (DLL, swinfo 0.6.0, catalogue includes the interior, 2.6 MB bundle).
- 2026-10-10 – Verified against the installed game (26w41a): runtime and editor code compile; `Assets.Load`, `crew`,
  render pipeline and flight camera confirmed; FBX, materials and textures validated. Fixed the `ILogger` ambiguity.
- 2026-10-10 – Repo transferred from MattAtAstralas (work) to https://github.com/bloke79/ksp2iva (personal).
- 2026-10-10 – Pushed to https://github.com/MattAtAstralas/ksp2iva (private), on top of the existing LICENSE commit.
- 2026-10-10 – Imported into the Claude Code workspace, with ADRs written for the 0.4 and 0.5 decisions.
- 2026-10-09/10 – (claude.ai) 0.3 port → 0.4 generated cabin (rejected) → 0.5 game interiors (none exist) →
  0.6 modelled Mk1-3 interior, renders approved, FBX exported, Unity setup menu and runtime placement written.
