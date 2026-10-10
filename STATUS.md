# Status: iva-redux

**Last updated:** 2026-10-10
**Version / milestone:** 0.6.0 + pose-fitted Mk1 and Mk1-3 interiors (unreleased) · KSP2 Redux 26w41a
**Health:** 🟡 Both interiors rebuilt round the game's seated poses; built, not yet seen in game. Open bug: one native crash in the game's camera rig right after entering IVA (see `notes/2026-10-10-first-test.md`).

## Next steps
0. **Test both reworked interiors in game** (C in a 1v and a full Mk1-3): couches should sit under the kerbals, the
   console fill the view straight up, windows line up with the hull's. Check whether the game's own stick/pedal
   meshes (`IVA_Cockpit_Controls`) also show; if so, drop our hand controllers.
1. Investigate the camera-rig crash (`/bugfix`): IVA moves the flight camera while the game's rig raycasts terrain.
2. Next interiors, each bespoke with renders first: 1.5v, 3v, cupola, landers, cockpits. Enter IVA in each once
   first so the pose dump captures its seated kerbals, then run `pose_extract.py` on the capture.
3. Before release: decide whether to keep the pose dump (`CustomInterior.DumpPoses`) or put it behind a setting.

Rebuild after any change: `.\scripts\sync-to-unity.ps1 -Project iva-redux`, then `.\scripts\build-mod.ps1 -Project iva-redux`
(about 20 s; run **IVA > Set Up Interiors** in batch first if the interior files changed).

## In progress
- Nothing yet. The project was imported from `_strip/` with the claude.ai handoff in `notes/`.

## Blockers / questions for Matt
- In-game testing needs Matt at the PC (Claude builds and reads logs; Matt flies).
- This repo is GPL-3.0, but the licence of Mudkip909's original is unknown. Check compatibility before going public.

## Done (recent)
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
