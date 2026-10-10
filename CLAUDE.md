# IVA Redux

First-person IVA (inside-the-cockpit view) mod for **KSP2 Redux**, with a modelled interior for the
Mk1-3 "Gumball" 3-seat pod. You sit in a high-quality cabin and see the real world through its windows.
Started as a port of Mudkip909's "KSP2 Free IVA" 0.2.6.

Read first: `STATUS.md` (where things stand) → `PLAN.md` (current plan) →
`notes/2026-10-10-claude-ai-handoff.md` (full design and history from the claude.ai session) →
`README.md` (user guide) / `CHANGES.md` (version history).

**Repo:** https://github.com/MattAtAstralas/ksp2iva (private, `main`, GPL-3.0). This folder is its own git
repo, separate from the rest of the workspace.

_Imported 2026-10-10 from `_strip/`. Everything before that was written in a cloud sandbox with
**stub DLLs**: none of it has been compiled against the real game or run in game._

## Stack
- **Game:** KSP2 Redux, Beta channel, snapshot **26w41a**
- **Mod code:** C# `KerbalMod` (Redux / SpaceWarp 2, ReduxLib for config, input and logging), built with the
  Redux SDK in **Unity 6000.6.0f1**, built-in render pipeline with post-processing
- **Art:** Blender **5.2.2** via its Python module (`pip install bpy`). The model and textures are built entirely from scripts.
- Mod version: **0.6.0**

## Layout
| Path | Purpose |
|---|---|
| `Unity/Assets/IVA/Code/IVAPlugin.cs` | Modes, keys, config, camera, look/zoom, numpad alignment |
| `Unity/Assets/IVA/Code/CustomInterior.cs` | `PodLocator`, `InteriorCatalogue`, `CustomInteriorSession` (measure, fit, place) |
| `Unity/Assets/IVA/Editor/IVAInteriorSetup.cs` | Menu **IVA > Set Up Interiors**: materials, prefab, addressable entry |
| `Unity/Assets/IVA/Interiors/Mk13/` | Exported `Mk13Interior.fbx`, `materials.json`, 15 textures |
| `art/` | Blender pipeline: `texgen.py` → `model_mk13.py` → `render_mk13.py` / `export_mk13.py` |
| `previews/` | Approved renders of the interior |
| `notes/` | Handoff, test logs (`YYYY-MM-DD-*.md`), findings |
| `docs/decisions/` | ADRs |

This folder is the **source of truth**. The Unity project made by the Redux SDK Manager lives outside
OneDrive (e.g. `C:\KSP2Mods\MyMods`), and `Unity/Assets/IVA` gets copied into it. Never copy SDK-generated
files (`Code/IVA.asmdef`, `IVA.asset`, `Pipelines/`) back here. Fixes made inside Unity must be copied back here.

## Commands
| Task | Command / action |
|---|---|
| Textures | `python -I art/texgen.py <textures-dir>` |
| Model | `python -I art/model_mk13.py <textures-dir> <scratch>/mk13.blend` |
| Previews | `python -I art/render_mk13.py <scratch>/mk13.blend <renders-dir>` (Cycles, about 3 min per view) |
| Export | `python -I art/export_mk13.py <scratch>/mk13.blend <export-dir>` |
| Unity setup | Menu **IVA > Set Up Interiors**. Should report 35 materials and address `IVA/Interior_Mk1-3` |
| Build | `Assets/IVA/Pipelines/` → **Build for Player** → **Execute** → `<KSP2>\mods\__Testing\IVA\` |

| Sync code to Unity | `.\scripts\sync-to-unity.ps1 -Project iva-redux` (from the workspace root; or `/sync-unity to iva-redux`) |
| Read the game log | `.\scripts\get-game-log.ps1 -Project iva-redux -Save <name>` (or `/log-triage iva-redux`) |

Paths live in `mod.config.json`. The game log is confirmed at
`%USERPROFILE%\AppData\LocalLow\Intercept Games\Kerbal Space Program 2\Player.log` and is overwritten every launch.
The stock game also logs "IVA Portrait…" lines, which aren't ours (the config filters them out).
Intermediate `.blend`, textures and renders go in the workspace `scratch/`. Full loop: `workflows/mod-build-test.md`.

## Design facts that code depends on
- Blender: metres, Z up, pod base at Z=0, cabin front -Y. Designed for an outer cone with a 1.25 m base radius,
  0.625 m top radius and 1.95 m height (**the height is assumed**). The FBX is exported with forward -Z, up Y and
  `bake_space_transform`, so Unity gets Y up and cabin front +Z.
- Seats `IVA_Seat0..2` are at Blender (0, 0.315, 1.075) and (±0.465, 0.315, 1.075), with identity rotation. Couches are at 0.75 scale.
- Fit: `sxz = podBaseRadius / 1.25`, `sy = podHeight / 1.95`, each clamped to 0.6–1.6, and made uniform if they're within 8%.
- The flight camera (`FlightCameraPhysics_Main`) is **never parented** in custom mode. Its pose is set in `LateUpdate` and
  `Camera.onPreCull`. Restore the original pose, FOV and near clip on exit.
- Blender scripts: `import bpy` must come **before** `bmesh`/`mathutils`.

## Conventions
- All diagnostics are logged with an `IVA` prefix. There's no debugger in game, so add log lines for anything that needs tuning.
- Use `FindObjectsByType` (not `FindObjectsOfType`) and the mod's own child search (not `FindChildRecursive`).
- Every setting is a `ConfigValue<T>` and gets a row in README's Settings table.
- Each release: bump the version (README step for `IVA.asset`) and add a `CHANGES.md` section.
- When an API guess turns out wrong against the real DLLs, record the correction in `notes/api-corrections.md`.

## Quality bar (from Matt)
- Visual quality matters. A code-generated cabin was rejected as "ghetto" (ADR-001). Show renders or
  screenshots for any visual change before calling it done.
- Style: KSP-flavoured, Apollo-inspired.

## Unity SDK project (set up 2026-10-10)
- `C:\Games\KSP2Mods\IVA`: template 26w41a, **Unity 6000.6.0f1** (must match the game). Created with `redux-sdk-cli`
  (`C:\Games\KSP2Mods\tools\`). Batch logs are in `C:\Games\KSP2Mods\tools\*.log`.
- **Patched by hand:** `Assets/IVA/Code/IVA.asmdef` has `"references": ["Unity.Addressables", "Unity.ResourceManager"]` added
  (the SDK generates it without them, and `Assets.Load` won't compile). Redo this if the asmdef is ever regenerated.
- `Assets/Editor/ReduxModBatch.cs` (copied from the workspace `scripts/unity/`) is an editor-only batch helper and doesn't ship.

## Gotchas
- Stock KSP2 pods have **no** modelled interiors (ADR-002).
- The original mod's `kerbalCam` cameras are portrait-booth cameras, not cameras inside the pod.
- The addressables group `addressables_IVA_all` only exists if the mod was created with Mod ID exactly `IVA`.
- This repo is GPL-3.0, but the licence of Mudkip909's original is still unknown. Check that it's compatible
  before making the repo public or releasing.
