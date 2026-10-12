# IVA Redux

First-person IVA (inside-the-cockpit view) mod for **KSP2 Redux**, with a modelled interior for the
Mk1-3 "Gumball" 3-seat pod. You sit in a high-quality cabin and see the real world through its windows.
Started as a port of Mudkip909's "KSP2 Free IVA" 0.2.6.

Read first: `STATUS.md` (where things stand) → `PLAN.md` (current plan) →
`notes/2026-10-10-claude-ai-handoff.md` (full design and history from the claude.ai session) →
`README.md` (user guide) / `CHANGES.md` (version history).

**Repo:** https://github.com/bloke79/ksp2iva (private, `main`, GPL-3.0). This folder is its own git
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
| Shared textures | `python -I art/texgen.py <textures-dir>` (into `Interiors/Shared/Textures`) |
| Model + previews | `.\art\build_interior.ps1 -Pod <part>` (EEVEE previews in `scratch/iva-redux/<part>/renders`, review report in `review.txt`) |
| Review only | `blender -b <part.blend> --python art/review.py -- art/pods/<part>.json <out.txt>` |
| Export | `.\art\build_interior.ps1 -Pod <part> -Export` (FBX, materials.json, pod textures into `Interiors/<Interior>`) |
| Pose data | `pose_extract.py <pose.obj> <stock_interior.json> <spec>` (see "Seated poses" below) |
| Unity setup | Menu **IVA > Set Up Interiors**, or batch `ReduxModBatch.RunMenu -menu "IVA/Set Up Interiors"`. Mk1-3: 37 materials, `IVA/Interior_Mk1-3`; Mk1: 35, `IVA/Interior_pod_1v_conical_crew` |
| Build | `Assets/IVA/Pipelines/` → **Build for Player** → **Execute** → `<KSP2>\mods\__Testing\IVA\` |

| Sync code to Unity | `.\scripts\sync-to-unity.ps1 -Project iva-redux` (from the workspace root; or `/sync-unity to iva-redux`) |
| Read the game log | `.\scripts\get-game-log.ps1 -Project iva-redux -Save <name>` (or `/log-triage iva-redux`) |

Paths live in `mod.config.json`. The game log is confirmed at
`%USERPROFILE%\AppData\LocalLow\Intercept Games\Kerbal Space Program 2\Player.log` and is overwritten every launch.
The stock game also logs "IVA Portrait…" lines, which aren't ours (the config filters them out).
Intermediate `.blend`, textures and renders go in the workspace `scratch/`. Full loop: `workflows/mod-build-test.md`.

## Design facts that code depends on
- Blender: metres, Z up, hull base (`hull_base_y` in the spec) at Z=0, cabin front -Y. With the catalogue's Yaw 180 and
  `OnHull` placement, Unity part space is (x, z + hull_base_y, y): models are built directly in pod coordinates.
- **Seated poses:** the game draws its own kerbals lying on their backs, heads to the front (-Y), looking up (+Z), and the
  camera uses their `IVA EyeTransform`. Couches, consoles and windows are laid out round the spec `pose` block (eyes,
  couch profile, hands, head) made by `pose_extract.py` from the mod's pose capture
  (`<LocalLow>/.../IVA-pose/<part>.obj`, written once per pod type on entering IVA; reference copies in
  `C:\Games\KSP2Mods\reference\poses`, never in the repo). Previews show the captured kerbals as `REF_*` objects, which the exporter drops.
- **Markers and live parts** (position-only, so no axis conventions): `IVA_View_<w>`/`IVA_ViewAt_<w>` window views;
  moving parts are `IVA_Live_<name>` meshes (exported unmerged as `Mesh_<Material>__Live_<name>`, pivot at origin) with
  `IVA_Live<Role>_<name>` markers (Axis/Zero/Mid for needles; Zenith/North/Axis/Up for the navball). `LiveInstruments.cs`
  drives them from `VesselComponent` telemetry; horizon vectors go through `UniverseView.PhysicsSpace.VectorToPhysics`.
- **Camera:** custom IVA hands the game a camera shot (`IvaCameraShot`, via `UniverseCameraManager.SetCameraShotOverride
  (CameraID.Flight, …)`, the mechanism Redux's own first-person camera uses), so the game places the physics, scaled-space,
  cloud and reflection cameras consistently. The mod only forces the near clip to 0.02 m and keeps the "Close Vessel" camera
  off in `Camera.onPreCull`. If the override can't be set, it falls back to moving the camera itself (never parented).
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
- **Review every build top to tail before showing it** (Matt, 2026-10-11), for:
  1. cropping of parts
  2. clipping of parts
  3. parts hidden by other things
  4. a sanity check that it looks useful and would work

  `review.py` runs automatically in `build_interior.ps1`. It checks:
  - clip, buried, and through-the-hull
  - occluded from the seat, and blocked window views
  - floating parts, z-fighting, and reach

  Get it to zero, or explain each remaining line. Then look at every preview zoomed in. The script can't judge
  sight lines (anything hanging in front of a panel) or whether a layout makes sense to use. For non-round hulls, place
  wall fittings with `hullshell.inner()`, never at fixed offsets.

## Unity SDK project (set up 2026-10-10)
- `C:\Games\KSP2Mods\IVA`: template 26w41a, **Unity 6000.6.0f1** (must match the game). Created with `redux-sdk-cli`
  (`C:\Games\KSP2Mods\tools\`). Batch logs are in `C:\Games\KSP2Mods\tools\*.log`.
- **Patched by hand:** `Assets/IVA/Code/IVA.asmdef` has `"references": ["Unity.Addressables", "Unity.ResourceManager",
  "Unity.Postprocessing.Runtime"]` added (the SDK generates it without them: `Assets.Load` and the cabin ambient
  occlusion, `CabinAo.cs`, won't compile). Redo this if the asmdef is ever regenerated.
- `Assets/Editor/ReduxModBatch.cs` (copied from the workspace `scripts/unity/`) is an editor-only batch helper and doesn't ship.

## Gotchas
- Stock interior prefabs (`interior_1v_m1_pod_crew` etc.) do have modelled cabins (seats, sticks, ceiling screens), and the game draws them **in flight** round the seated kerbals (visible through the windows from outside). Custom IVA hides them (except the kerbals) while ours is showing and restores them on exit.
- The original mod's `kerbalCam` cameras are portrait-booth cameras, not cameras inside the pod.
- The addressables group `addressables_IVA_all` only exists if the mod was created with Mod ID exactly `IVA`.
- This repo is GPL-3.0, but the licence of Mudkip909's original is still unknown. Check that it's compatible
  before making the repo public or releasing.
