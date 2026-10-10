# Plan: First build and in-game test of 0.6.0

_Created 2026-10-10 · Status: draft (from handoff §4–5)_

## Goal
Get 0.6.0 compiling against the real KSP2 Redux 26w41a assemblies and confirm in game that the Mk1-3
interior loads, sits inside the pod, lines up with its windows and shows the real world through them.

## Context
All code was written against stub DLLs in a cloud sandbox. The 10 riskiest assumptions are listed below,
in rough order of risk (details in `notes/2026-10-10-claude-ai-handoff.md` §4).

## Steps
- [ ] 1. **Compile.** Set up the SDK project, create mod `IVA`, copy `Unity/Assets/IVA` in, and fix API mismatches
      (`Assets.Load`, `PartBehavior.Name`, `Module_CrewedInterior.crew`/`IsProbe`,
      `ViewController.GetActiveSimVessel`/`GetBehaviorIfLoaded`, `GameState.FlightView`, `KeyboardShortcut`,
      `ConfigValue<T>`, `RangeConstraint<T>`). Log each fix in `notes/api-corrections.md` and copy fixed files back here.
- [ ] 2. **Editor setup.** Check the asmdef references (`Unity.Addressables`, `.Editor`, `Unity.ResourceManager`).
      Run **IVA > Set Up Interiors**, expect 35 materials and address `IVA/Interior_Mk1-3`. Check the prefab
      is upright with its front facing +Z, then look from `IVA_Seat0`.
- [ ] 3. **First flight.** Build for Player, launch, put a Mk1-3 on the pad and press C. Collect all `IVA` log lines into
      `notes/YYYY-MM-DD-first-test.md`. Record the log file location.
- [ ] 4. **Check the logged assumptions:** the addressable loads; Standard shader isn't pink or black; pod base radius
      and height are about 1.25 / 1.95 (not inflated by ladders or RCS); flight camera name; the interior layer is drawn;
      the exterior doesn't poke through.
- [ ] 5. **Tune** yaw (window angles from the log), fit scale and eye height, then save with numpad 5.
- [ ] 6. **Bake defaults:** hard-code the good per-pod yaw, scale and eye values in `InteriorCatalogue`.
- [ ] 7. Exercise V (all 3 seats), look, zoom, and exits (map, EVA, vessel switch, pod destroyed, C during load).

## Done when
- The log shows `placed the Mk1-3 interior` with no exceptions.
- The interior is lit correctly (not pink or black), its windows line up with the pod's, all three seats work, and every exit path restores the camera.
- Defaults are baked in, so a fresh install needs no numpad tuning.

## Risks / open questions
- Standard shader may not render in the game build. Fallback: copy a shader from a stock part's material at run time.
- The pod's height of 1.95 m is assumed. A wrong value distorts the fit.
- Which way the real Mk1-3's windows face is unknown until the first log.

## Follow-ups (from workspace setup)
- Make every log line use one distinctive prefix (`[IVA]`). The code currently mixes `IVA:`, `IVA align` and `[IVA]`,
  and the stock game logs "IVA Portrait…".
- Check the interior load never blocks on `.Result`/`WaitForCompletion` inside a callback (see
  `knowledge/ksp2-redux-modding.md` › Logs).

## Follow-ups (handoff §6)
- Kerbal crew models in the other seats; live navball and screens; animated switches; interior sounds.
- Interiors for other pods: repeat the `art/` pipeline, add an `InteriorCatalogue` entry, export into `Interiors/<Name>/`.

## History
