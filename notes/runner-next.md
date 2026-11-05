# KSP2 runner brief (2026-11-01)

RUNNER IDLE: waiting on Matt. Modular interiors (M1-M4) landed in e8bd26c and the Unity build is OK; M5 needs Matt to fly it.
Everything else that is runnable offline is done; what is left needs the game or a design call.

## New 2026-11-05: ring orientation fix (BACKLOG section 0) is NOT runnable on main
`IVA_RingAxis_0` markers and ring code exist only on branch `iva-ring`; main has just `CorrectOrientation` (CustomInterior.cs:370). The fix belongs on `iva-ring` (Matt's call, see cross-project-issues row 2026-11-03), and a main build would drop the ring code from the installed DLL. Patch sketch: `projects/ksp2-spaceparts/docs/iva-patch/ring-orientation-fix.md`.

## What Matt needs to do
0. Either approve `iva-ring` for main, or tell the runner to work on that branch/worktree (`C:\Work\worktrees\iva-redux-ring`) for the orientation fix.
1. Turn Debug logging ON in the IVA config before any playtest that needs the log (defaults are now OFF; an existing config keeps its saved values).
2. Fly the walking playtest (walking plan step 6): a lander on the pad and on the Mun. Unbuckle (U), walk to the EVA hatch and drawers, jump, crouch.
3. Fly the test lists below (fade/boarding from 2026-10-31, modular interiors from today).
4. Pick the seated key for console switches: F is a flight key while buckled (PLAN "Plan for 4"). Suggested: hold middle mouse and click.

## Next chunk once unblocked
Ladders (walking step 3), after Matt has tried walking. Seed: `ladder()`/`pole()` export `IVA_Ladder_<k>_0/_1`; grab, W/S climb, top hatch prompt. Needs new marker names, a contract change, so it is the Lead's call.
Release step left in BACKLOG section 6: the rest of the 1.0 release items (version, public repo) are Matt's.

## Open items (waiting on Matt)
- Walking playtest; ladders wait on it.
- Seated targeting, switch banks, Starlab experiments, sleep with time warp, abort/stage: key choice and art.
- `notes/local-style.md` is still untracked (another session's file; the gate lists it as OTHER WIP).
- Ring habitat interior (KSP2SpaceParts) is 1.1: needs spin gravity, after the walking playtest.

## Decisions made this run
- Plan route used (rewrite-large): s1-s4 code via local_code, all passed unity-check in round 1; README/CHANGES drafted locally, then three small gate fixes by hand (null JSON array, merged CHANGES bullet, comment placement).
- `Assets.LoadByLabel<TextAsset>(label, perAsset, done)` confirmed by reflection (KSP.Assets.AssetProvider). OnPostInitialized is a KerbalMod member. Newtonsoft.Json.dll is already in the SDK asmdef.
- The `Interiors:` log line is repeated after the scan, only when something registered (OnInitialized logs it before the scan).
- protected-lines flagged the repeated `Interiors:` line as 2x: expected, not a defect.
- Not re-gated after the fixes (they were the gate's own exact edits).

## In-game test list: modular interiors
Turn Debug logging on first. Fresh config: Settings show Debug logging and Pose dump OFF.
1. No labelled asset: no exception at start-up, `Interiors:` line same as before, C into a stock pod works. Watch for an Addressables InvalidKey error for label iva_interior in the log (it may appear outside our try/catch; harmless if so, tell me).
2. Add a test TextAsset labelled iva_interior (JSON keys in README "Making an interior for your part") for a stock part: expect `IVA: registered interior '<name>' for <parts> from label iva_interior`, `IVA: interior '<name>' replaces '<old>' for part '<part>'`, a second `Interiors:` line listing it, and C loads it.
3. Second file for the same part: replaces line, the later one wins. Extra key: `IVA: ignored unknown key ...` once. Bad JSON or Seats 0: `IVA: skipped interior file ...`, game carries on. Remove the test asset after.

## In-game test list: fade and boarding (2026-10-31, still unflown)
1. U, then F at a hatch to a crewed part: fades black, no exterior flash, fades in beyond. Log `IVA: moved ...`.
2. Hatch to a full part: no fade, `IVA: <part> is full.`
3. F at the side hatch: EVA, no fade. Board: about 2 s later, IVA in that seat. Log `IVA: boarded, back into IVA (<part>).`
4. EVA then switch vessel, or C during the EVA, or EVA from the portrait: no IVA on boarding. 5. C during the fade: clears within 6 s.
Risk: entering IVA 2 s after boarding is a new camera moment; check against the old camera-rig crash.
