# KSP2 runner brief (2026-10-31)

RUNNER IDLE: waiting on Matt. Nothing offline is left that doesn't need a playtest, a design call or new art.

## What Matt needs to do
1. Fly the walking playtest (walking plan step 6): a lander on the pad and on the Mun. Unbuckle (U), walk to the EVA hatch and drawers, jump, crouch.
2. Fly the new build (test lists below).
3. Pick the seated key for console switches: F is a flight key while buckled (PLAN "Plan for 4"). Suggested: hold middle mouse and click.
4. Say whether Blender work may go in the runner. Switch banks, Starlab racks and sleep all need new `IVA_Act_*` markers and art.

## Next chunk once unblocked
Ladders (walking step 3), after Matt has tried walking. Seed: `ladder()`/`pole()` export `IVA_Ladder_<k>_0/_1`; grab, W/S climb, top hatch prompt. Needs new marker names, a contract change, so it is the Lead's call.

## Open ⏸ items
- Walking playtest; ladders wait on it.
- Seated targeting, switch banks, Starlab experiments, sleep with time warp, abort/stage: key choice and art.
- `notes/local-style.md` is still untracked (another session's file, the gate lists it as OTHER WIP). The runner left it alone, so it isn't in git.

## Decisions made this run
- Debug logging and Pose dump default ON until release; BACKLOG section 6 now has the step to flip them. Debug logging gates only the camera report: there were no key-press-only logs to gate.
- Pose dump also gates CapturePoses, since it writes the same .obj files.
- Fade covers through-transfers only, not EVA. A hatch used during the 0.4 s fade-in is ignored.
- Boarding watch only follows EVAs started from our hatch. C during the EVA cancels it. A part with no interior cancels it.

## In-game test list: settings
- Defaults on: log unchanged, including `IVA: cameras:`.
- Both off, IVA-pose folder deleted, press C: no `IVA: cameras:` line, no .obj written, zoom and leaving IVA still fine (companion cameras still work).

## In-game test list: fade and boarding
1. U, then F at a hatch to a crewed part: fades black, no exterior flash, fades in beyond. Log `IVA: moved ...`.
2. F at a hatch whose part beyond is full: no fade, `IVA: <part> is full.`
3. F at the side hatch: EVA, no fade. Board: about 2 s later, IVA in that kerbal's seat. Log `IVA: boarded, back into IVA (<part>).`
4. EVA by F, switch vessel: nothing. 5. EVA by F, press C, board: no IVA. 6. EVA from the portrait, board: no IVA.
7. C during the fade: screen clears, 6 s at worst.
8. Setting off: board stays outside. Never see `IVA: hatch fade failed` or `IVA: boarding watch failed`.
Risk to watch: entering IVA 2 s after boarding is a new camera moment; check it against the old camera-rig crash.
