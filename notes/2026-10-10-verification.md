# Verification against the real KSP2 Redux install (2026-10-10)

Checked the 0.6.0 code and assets against the installed game, without opening Unity or running the game.

**Game:** `C:\Program Files (x86)\Steam\steamapps\common\Kerbal Space Program 2`, Redux DLLs dated 2026-10-09 (26w41a)
**Unity installed:** 6000.6.5f1 (the README says 6000.6.0f1. Use whatever the SDK Manager installs for template 26w41a.)
**Method:** compiled with Unity's bundled Roslyn (C# 9) against all 230 DLLs in `KSP2_x64_Data\Managed`,
read signatures with ilspycmd 9.1 (decompiled output kept in a temp folder, not in this repo), and inspected the FBX, JSON and PNGs directly.

## Code

| Check | Result |
|---|---|
| Runtime code (`IVAPlugin.cs`, `CustomInterior.cs`) compiles against the real DLLs | ✔ after 1 fix: `ILogger` was ambiguous (ReduxLib vs UnityEngine). Added `using ILogger = ReduxLib.Logging.ILogger;` |
| Every API listed in handoff §4.1 exists with compatible signatures | ✔ (compile) |
| `KerbalMod` (in `Assembly-CSharp`, `Redux.ExtraModTypes`) exposes `SWLogger`, `SWConfiguration`; `Assets`/`Game` come from `KerbalMonoBehaviour` | ✔ |
| `Assets.Load<T>(string key, Action<T> cb, bool logMissingKey)`: calls `cb(null)` on failure; third arg only silences the game's own error | ✔ The code handles `null` correctly |
| `Module_CrewedInterior.crew` is `Kerbal3DModel[]` with one slot **per seat** (empty seats use `EmptySeat()`) | ✔ `crew.Length` = seat count, so a Mk1-3 counts as 3 seats however many kerbals are aboard |
| Render pipeline | ✔ Built-in (no URP/HDRP runtime DLLs) plus Post Processing v2, so the `Standard` shader and `Camera.onPreCull` work |
| Flight camera `FlightCameraPhysics_Main` | ✔ Defined in `StreamingAssets\aa\StandaloneWindows64\coremanagers_assets_all.bundle` |
| `bone_kerbal_master_parent` (portrait mode) | ✔ Referenced in `Assembly-CSharp` |
| Editor script `IVAInteriorSetup.cs` compiles against the Unity 6000.6.5f1 editor DLLs | ✔ The 5 Addressables editor calls were checked against a stand-in. They need the real package from the SDK project |

## Assets

| Check | Result |
|---|---|
| `Mk13Interior.fbx` | ✔ Binary FBX 7400 (Unity 6 imports it), 35 `Mesh_*` nodes, `IVA_Seat0..2` present |
| Mesh ↔ material mapping (`Mesh_X` → `IVA_X`) | ✔ 35/35 match both ways |
| `materials.json` fields vs `Sheet`/`MatInfo` | ✔ Match. Extra `design`/`seats_blender` keys are ignored by JsonUtility |
| Textures referenced vs present | ✔ All 15 present and referenced |
| Texture formats | ✔ 24-bit PNG, mostly power-of-two. ⚠ `crt_*.png` are 768×512 (NPOT), so Unity rescales them to 1024×512. Harmless, slightly softer |
| Normal maps | ✔ Tangent-space (average RGB ≈ 127,127,255) |
| Windows | ✔ Open frames with no glass material, so the real world shows through |
| Previews | ✔ Render cleanly and match the materials |

## Still only provable in Unity or the game
1. The Addressables editor package API and group `addressables_IVA_all` (needs the SDK project, mod ID `IVA`).
2. Addressable loads from the mod's catalogue at run time.
3. Pod measurement, window yaw, fit scale, eye height (numpad tuning).
4. Lighting: the light strips use emission ×6 and may bloom heavily under post-processing. Tune if so.

## Environment notes
- An old BepInEx install (SpaceWarp 1 era) is still in the game folder, but **inactive**: no doorstop proxy DLL,
  last log July 2025. It's harmless. Remove it only if it causes confusion.
