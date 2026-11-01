# Building an interior for IVA

For modders who want to give their own part (or a stock one) a walk-in interior. Read the README first for what players see; this is how
the pieces fit. Everything here is checked against the code in `Unity/Assets/IVA/Code/`; the marker lists are the ones the code reads, so
if the two ever disagree, the code wins.

## How IVA uses an interior
1. Player presses C in flight. IVA finds the crewed part (`PodLocator`) and asks `InteriorCatalogue.ForPod` for a design for it.
2. The design's `Address` is loaded with `Assets.Load<GameObject>` (addresses are global across mods), instantiated under the part, and
   fitted (`CustomInteriorSession`). Colliders on the model are stripped: IVA does its own movement and never uses Unity physics.
3. Everything IVA needs to know about the model comes from **object names**: markers (empty objects, position only) and named meshes.
   Positions are used rather than rotations, so Blender's axis conversion on import doesn't matter.

## The two things you ship
**A. The interior prefab**, an Addressables entry. Build and import it like any Unity model; the exact export naming is the contract
(`Mesh_<Material>` for static meshes, `IVA_<Material>` for materials, `Mesh_<Material>__Live_<name>` for moving parts, pivot at the origin).
IVA's own Blender pipeline (`art/`, `build_interior.ps1 -Pod <part>` then `-Export`) produces exactly this; a hand-made model works if it
follows the same names.

**B. A design file**: one JSON TextAsset with the Addressables label `iva_interior`. Keys are in the README section "Making an interior
for your part". `OnHull: true` means the model was built to the real hull, so IVA places it at `HullBaseY` and never scales it; otherwise
IVA fits it using `BaseRadius` and `Height`. Use `OnHull` for anything you modelled to the part's real size.

## Markers IVA reads (all optional unless noted; position-only empties)
| Marker | What it does |
|---|---|
| `IVA_Seat*` | **Needed for seated play.** One per seat, sorted by name. No seats: IVA falls back to the portrait view. |
| `IVA_View_<w>` + `IVA_ViewAt_<w>` | A window view: where the camera goes (`ViewAt`) and what it looks at (`View`). Both are needed. |
| `IVA_ColAxis_0/1` | The part's axis, floor to top. |
| `IVA_ColHull_<k>` | A point on the hull at each height: the radius profile that keeps you inside. |
| `IVA_ColDeck_<k>` | Deck heights. `IVA_ColHole_<k>_c/x/y/z` are openings you can pass through. |
| `IVA_ColBox_<k>_c/x/y/z` | Oriented box round equipment: centre plus three half-axis tips. Pushes you sideways. |
| `IVA_Floor_<k>_p/_n` | Walkable floor plane under gravity: a point on it, and a point 0.1 m along its up normal. No upward-facing floor means floating only. |
| `IVA_Hatch_<name>` | A hatch. Beyond it is the crewed part of ours nearest in that direction (within 45 degrees and 8 m). A `Side` hatch also leads outside (EVA). |
| `IVA_Act_<Kind>_<name>` | Where to look to use something with F: Door, Slide, Curtain, Lamp, Screen, Flush, Wash, Lights. |
| `IVA_Live...` | Moving instruments and doors, with `__Live_<name>` meshes (navball, needles, hinged doors, lockers). See `LiveInstruments.cs` and `Doors.cs`. |
| `IVA_MFD_*`, `IVA_LightPanel*`, `IVA_LightStrip*` | Screen pages and light fittings the F action drives. |

Start small: seats, one window view, hull and floor markers is a working interior. Add `Act`/`Live` things later.

## Order of work (what the existing interiors did)
1. Get the part's real exterior mesh and crew pose capture (turn **Pose dump** on in Settings, press C once in the part; it writes
   `IVA-pose/<part>.obj` under LocalLow). The game seats its kerbals lying back; couches and windows are laid out round those poses.
2. Model to real hull size so `OnHull` works; keep the hull base at Z=0 in Blender metres, cabin front -Y (see `CLAUDE.md`, "Design facts").
3. Add markers, export, set up the Addressables entry (IVA's menu **IVA > Set Up Interiors**, or your own copy).
4. Ship the JSON with the `iva_interior` label. No IVA release is needed.
5. Test with **Debug logging** on. Expect `IVA: registered interior ...`, then on C `IVA: placed the <name> interior ...`,
   `IVA: free movement ready ...` after U. Missing markers show up as `IVA: ... no seat points` / `no floor faces up` style lines.

## Rules
- A later registration for the same part replaces the earlier one (logged). Unknown JSON keys are ignored; a bad file is skipped.
- Don't rely on rotating an interior against its hull. Fixed interiors only for now; a spinning ring interior is separate work.
- IVA never edits your mod; it only reads names and positions from the prefab.
