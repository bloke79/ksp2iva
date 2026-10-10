# Status: iva-redux

**Last updated:** 2026-10-10
**Version / milestone:** 0.6.0 (modelled Mk1-3 interior) · KSP2 Redux 26w41a
**Health:** 🟢 compiles against the real KSP2 Redux DLLs, and assets validated (`notes/2026-10-10-verification.md`). Not yet run in game.

## Next steps
1. **First in-game test (Matt):** launch KSP2 through the Redux Launcher, put a Mk1-3 on the pad, press **C**. Try V,
   mouse look, scroll zoom, and exits (map, EVA, vessel switch). Then `/log-triage iva-redux first-test`.
2. Tune yaw, scale and eye with the numpad (save with 5), then bake the defaults into `InteriorCatalogue`.

Rebuild after any change: `.\scripts\sync-to-unity.ps1 -Project iva-redux`, then `.\scripts\build-mod.ps1 -Project iva-redux`
(about 20 s; run **IVA > Set Up Interiors** in batch first if the interior files changed).

## In progress
- Nothing yet. The project was imported from `_strip/` with the claude.ai handoff in `notes/`.

## Blockers / questions for Matt
- Steps 1–3 need Matt's PC with KSP2 Redux 26w41a, Unity Hub and the Redux SDK Manager.
  Claude Code can edit code and read logs, but Matt has to drive the Unity editor and the game.
- Where is the KSP2 install, and where should the SDK Unity project live? (Record both here once known.)
- This repo is GPL-3.0, but the licence of Mudkip909's original is unknown. Check compatibility before going public.

## Done (recent)
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
