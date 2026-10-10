# Handoff: IVA mod for KSP2 Redux (from a claude.ai session, 9 to 10 October 2026)

This picks up a long chat session where the mod was ported, redesigned and given a modelled interior. That session ran in a cloud sandbox with no access to the user's PC, so nothing has been built in Unity or run in game. Claude Code on the user's machine can close that gap.

## 1. Goal

First-person IVA in KSP2 Redux 26w41a, starting with the Mk1-3 "Gumball" 3-seat pod: sit inside a high-quality modelled cabin and see the real world through its windows.

## 2. History (why things are the way they are)

1. **Start:** user uploaded Mudkip909's "KSP2 Free IVA" 0.2.6 (one BepInEx plugin, `IVAclass.cs`). Reviewed it and found 8 bugs, including a V-key off-by-one crash, near clip reset to 0, the exit pose overwritten, and a crash with no crew.
2. **Port (0.3):** Redux has no BepInEx. Rewrote it as a `KerbalMod` with config and the bug fixes.
3. **Generated interior (0.4):** code-built cabin sized by raycasting the pod's colliders. **User rejected it as "ghetto".** Removed.
4. **Game's own interiors (0.5):** found KSP2's internal space (`UniverseView.InternalSpaceTransform`, layer 16 `LayerInternalScenery`), `Data_CrewedInterior.InteriorName`, and `IInternalSeat` (seats in part-local coordinates). Built an overlay-camera approach. **User then confirmed stock pods have no modelled interiors**, so this was removed too.
5. **Custom modelled interior (0.6, current):** designed in Blender from code (KSP-flavoured, Apollo-inspired, user's style choice). User approved the renders in `previews/`. Exported to FBX and added the Unity setup button and runtime placement.

Finding worth keeping: the original mod's `kerbalCam` cameras are portrait cameras in a separate portrait set, so the original mod showed a portrait booth, not the pod.

## 3. Current design

### Runtime (`Unity/Assets/IVA/Code`)

- `IVAPlugin` (`[DefaultExecutionOrder(30000)]`), modes:
  1. **CustomInterior:** `PodLocator.FindPod` (name filter, else 3-seat pods, else the biggest) > `InteriorCatalogue.ForPod(seats)` > `Assets.Load<GameObject>("IVA/Interior_Mk1-3")` (async, cached; C cancels) > `CustomInteriorSession.Create`.
  2. **Portrait:** the original behaviour (parent the flight camera to the `kerbalCam` parent at local (-0.001, 0.625, 0.1), hide `bone_kerbal_master_parent`'s parent by scaling it to 0).
- `CustomInteriorSession.Create`: measures the pod first (collider bounds in pod-local space, renderer fallback), instantiates the prefab under an inactive holder parented to the pod, sets every layer to the pod renderer's layer, strips colliders, finds the `IVA_Seat*` transforms, fixes a tipped-over import (`CorrectOrientation`, using the seat height axis), then fits and places it.
- Fit: `sxz = podBaseRadius / 1.25`, `sy = podHeight / 1.95`, both clamped to 0.6 to 1.6; uniform if they're within 8% of each other. Position = pod axis centre at `yMin` + config offset. Yaw and extra scale come from config.
- Camera: the flight camera (`FlightCameraPhysics_Main`) is **not parented** in custom mode. Its world pose is set from the seat each frame in `LateUpdate` and again in `Camera.onPreCull` (so it survives the pod being destroyed). The original local pose, FOV and near clip are restored on exit.
- Exits automatically on: leaving `GameState.FlightView`, active vessel change, session invalid.
- Numpad alignment (custom mode only): 8/2 4/6 9/3 move, 7/1 yaw, * and / scale, Shift = eye offset, +/- step size, 5 = `SWConfiguration.Save()`, 0 = reset.

### Editor (`Unity/Assets/IVA/Editor/IVAInteriorSetup.cs`)

For each `Interiors/*/materials.json`, the setup button:

- sets normal maps to the NormalMap texture type
- creates Standard-shader materials, converting Blender's linear colours to sRGB with `.gamma`, smoothness = 1 - roughness, `_MainTex` tiling from the Blender mapping node, `_BumpMap`/`_NORMALMAP`, and `_EMISSION` (from the texture or a colour, multiplied by strength)
- sets the model importer: material import mode None, no cameras, lights, animation or colliders
- builds the prefab, mapping `Mesh_X` renderers to `IVA_X` materials, and adds a point light at (0, 1.55, 0)
- calls `CreateOrMoveEntry` into group `addressables_IVA_all` with address `IVA/Interior_Mk1-3`.

### Model (`art/`, Blender 5.2.2 via `pip install bpy`)

- Run with `python -I script.py args`. `import bpy` must come before `bmesh`/`mathutils`.
- Blender coordinates: metres, Z up, pod base at Z=0, cabin front = -Y. Designed for an outer cone with a 1.25 m base radius, 0.625 m top radius and 1.95 m height (the height is assumed, not confirmed; 2.5 m to 1.25 m is the MD-to-SM size class). Inner wall sits 0.07 m inside.
- The FBX is exported with axis_forward -Z, axis_up Y and bake_space_transform. Expected in Unity: Y up, cabin front +Z. Seats `IVA_Seat0..2` are at Blender (0, 0.315, 1.075) and (+-0.465, 0.315, 1.075), with identity rotation (forward = cabin front).
- Couches are fitted by a search (`couch_layout`). They ended up at 0.75 scale (kerbal-sized) in a parallel row, because the cone is too narrow at head height for full-size couches.
- About 89k triangles, 35 meshes/materials (one per material), 15 textures (textures are procedural, from `texgen.py`).
- Previews: Cycles CPU with OIDN denoising, AgX "Punchy", 1280 px at 32 samples. Roughly 2.5 to 3 min per view on 2 cores.

## 4. Assumptions to check in game (in rough order of risk)

1. **The mod compiles against the real DLLs.** Only stubs were used before. Watch for API differences (`Assets.Load` signature, `PartBehavior.Name`, `Module_CrewedInterior.crew`/`IsProbe`, `ViewController.GetActiveSimVessel`/`GetBehaviorIfLoaded`, `GameState.FlightView`, `KeyboardShortcut`, `ConfigValue<T>`, `RangeConstraint<T>`).
2. **The editor script compiles and runs.** The asmdef references `Unity.Addressables`, `Unity.Addressables.Editor` and `Unity.ResourceManager`. Group `addressables_IVA_all` exists only if the mod was created with ID `IVA`.
3. **The addressable loads at run time** from the mod's catalogue via `Assets.Load`.
4. **The Standard shader renders in KSP2 Redux.** The project uses the built-in pipeline plus post-processing, so it should, but pink or black means it doesn't. Fallback: copy a shader from a stock part's material at run time.
5. **FBX orientation in Unity:** the cabin should be upright with its front facing +Z. `CorrectOrientation` handles tipping, not yaw.
6. **Pod local frame is Y up.** Which horizontal direction the real Mk1-3's windows face is unknown; the log prints the pod's window mesh angles. Set Alignment > Yaw accordingly, then consider hard-coding a default yaw per pod in `InteriorCatalogue`.
7. **Pod measurement:** the collider bounds may include extras (ladders, RCS). Check the logged base radius and height against roughly 1.25 and 1.95.
8. **Flight camera name** `FlightCameraPhysics_Main` still exists; if not, the log lists all cameras.
9. **Layer:** the interior uses the pod renderer's layer. If the flight camera doesn't draw it, check culling masks.
10. **The pod's exterior mesh** may show inside. Use the config option or hide specific renderers.

## 5. First test plan

1. Set up the Redux SDK project (README steps), add the mod, copy `Unity/Assets/IVA` over it, fix compile errors against the real assemblies.
2. Run **IVA > Set Up Interiors** and confirm the dialog reports 35 materials and the address. Check the prefab visually in the editor (open it, look from a seat transform).
3. Build for Player, launch, fly a Mk1-3 on the pad, press C. Collect all `IVA` log lines.
4. Tune: yaw (windows line up), fit scale, eye height. Save with numpad 5. Bake good defaults into the code or catalogue.
5. Record the log file location and any API corrections in this file.

## 6. Likely next work

- Bake per-pod alignment defaults once known.
- Optional polish the user may want: kerbal crew models in the other seats, working navball or screens (live data), animated switches, interior sounds.
- More interiors for other pods (user said "design them"): repeat the `art/` pipeline per pod, add an `InteriorCatalogue` entry, and drop the export into `Interiors/<Name>/`.

## 7. References

- Redux API docs (DocFX, beta): https://github.com/KSP2Redux/API-Documentation (pages: `Redux.ExtraModTypes.KerbalMod`, `KSP.Sim.impl.PartBehavior`, `KSP.Modules.Module_CrewedInterior`, `KSP.Sim.impl.ViewController`, `KSP.Game.GameState`, `KSP.Assets.AssetProvider`)
- ReduxLib (config, input, logging, layers): https://github.com/KSP2Redux/ReduxLib
- Redux SDK (tag 26w41a): https://github.com/KSP2Redux/SDK (`Editor/Modding/Mod.cs`, `CreateNewModWindow.cs`, `Thunderkit/StageAddressablesGroups.cs`)
- Templates (tag 26w41a): https://github.com/KSP2Redux/Redux.Templates
- SDK Manager: https://github.com/KSP2Redux/Redux-SDK-Manager
- Reference Redux mod using addressables and KerbalMod: https://github.com/IanMealworm/K2D2Redux (`AssetsLoader.cs`, `K2D2_Plugin.cs`, `NOTICE.md`)
- Migration notes: https://modding.kerbal.wiki/Migrating_from_SpaceWarp_1.x
- Pod info: https://kerbal.wiki/Mk1-3_%22Gumball%22
