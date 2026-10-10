# Status: iva-redux

**Last updated:** 2026-10-10
**Version / milestone:** 0.6.0 (modelled Mk1-3 interior) · KSP2 Redux 26w41a
**Health:** 🟡 needs attention: never compiled against the real DLLs or run in game

## Next steps
1. Set up the Redux SDK project (README › One-off setup), create the mod with ID `IVA`, copy
   `Unity/Assets/IVA` in, and **fix compile errors against the real assemblies** (PLAN step 1).
2. Run **IVA > Set Up Interiors**, then inspect the prefab from a seat transform.
3. Build for Player, fly a Mk1-3 and press C. Save the `IVA` log lines to `notes/`.

## In progress
- Nothing yet. The project was imported from `_strip/` with the claude.ai handoff in `notes/`.

## Blockers / questions for Matt
- Steps 1–3 need Matt's PC with KSP2 Redux 26w41a, Unity Hub and the Redux SDK Manager.
  Claude Code can edit code and read logs, but Matt has to drive the Unity editor and the game.
- Where is the KSP2 install, and where should the SDK Unity project live? (Record both here once known.)
- This repo is GPL-3.0, but the licence of Mudkip909's original is unknown. Check compatibility before going public.

## Done (recent)
- 2026-10-10 – Pushed to https://github.com/MattAtAstralas/ksp2iva (private), on top of the existing LICENSE commit.
- 2026-10-10 – Imported into the Claude Code workspace, with ADRs written for the 0.4 and 0.5 decisions.
- 2026-10-09/10 – (claude.ai) 0.3 port → 0.4 generated cabin (rejected) → 0.5 game interiors (none exist) →
  0.6 modelled Mk1-3 interior, renders approved, FBX exported, Unity setup menu and runtime placement written.
