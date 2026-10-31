# Changes from the original (0.2.6)

## 1.0.0: for KSP2 Redux 26w43b (major update)

- **Requires KSP2 Redux 26w43b** (template 26w43a). Not compatible with 26w41a: `ReduxLib` moved to `SpaceWarp2.API` in the game, so config, input and logging now use that namespace. Rebuild against the 26w43 SDK template.
- Not yet flown in game on 26w43b.

- Bespoke Mk1 and Mk3-5 interiors, built to the real hulls and crew poses.
- Mk3-5, cabins and Starlab interiors, with zero-g ISS-style layouts.
- Lander cans for 1v, 2v and 3v, with drawers, ladders and an EVA hatch.
- Walking under gravity on landed vessels, with jump, crouch and auto-crouch.
- Unbuckle with U and float around the cabin in zero g.
- F action key: curtains, lockers, oven, cabin lights, toilet flush, laptop pages and hatches.
- Hatches move you between crewed modules, with a fade to black over the transfer.
- EVA out of the side hatch.
- Live instruments: navball, altimeter, pressure and temperature needles.
- Window views: glide to the nearest window, cycle, and return to your seat.
- Lighting pass with sharper shadows and ambient occlusion inside custom interiors.
- Camera uses a shot override instead of moving the flight camera, avoiding the rig crash.
- Back into IVA after boarding: after an EVA from a hatch, boarding returns you to that kerbal's seat (setting, on by default).
- Debug logging and Pose dump settings, both on by default.
## 0.6.0: modelled Mk1-3 interior

- A modelled and textured interior for the Mk1-3 "Gumball" pod, made in Blender for this mod: three quilted couches with harnesses, a curved console with a 3D navball, three screens, analogue gauges, guarded switches, ABORT and STAGE buttons and circuit-breaker panels, four framed windows that open onto the real world, a side hatch with a wheel, a docking tunnel with ladder rungs and top hatch, lockers, grab rails, light strips and a grated floor. About 89,000 triangles, 35 materials, 15 textures.
- Unity editor menu **IVA > Set Up Interiors**: builds the materials, prefab and addressable entry from the exported model in one click.
- The mod loads the interior by address, measures the pod and sizes the interior to fit, and places it inside the real pod, so the game camera draws the interior and the outside together with real sunlight and shadows through the windows.
- Seats come from eye points in the model; V cycles through them.
- Automatic fix if Unity imports the model tipped over.
- Numpad alignment now also turns and scales the interior; the log lists the pod's own window angles to help line it up.
- Removes the game-interior code from 0.5.0: the stock pods turned out to have no modelled interiors to use.
- Blender build scripts (`art/`) included so the interior can be regenerated or changed.

## 0.5.0: the game's own interiors (superseded)

- Replaces the generated cabin from 0.4.0 with KSP2's own pod interior art.
- Finds the interior the pod's crew are sitting in (in the game's internal space, layer 16). If there isn't one, it loads the pod's interior model by its `InteriorName` from the game's assets, with scripts, cameras, physics and sound stripped out.
- Overlay mode (default): a second camera draws the live interior and crew over the game camera's real outside view, matched to the same eye position, KSP1-style. InPod mode places a static copy inside the real pod instead.
- Seats come from the crew's own portrait cameras, so V moves between your actual crew's seats.
- Numpad alignment tool to line the interior up with the outside view, saved to config.
- Option to hide interior meshes by name (for example a portrait backdrop behind the windows).
- Interior loading is asynchronous; pressing C again cancels it.
- The game camera is never parented into the pod or the interior, so it survives if either is destroyed.
- Corrects a finding in 0.4.0: the `kerbalCam` cameras sit beside the crew inside the pod's interior model in the internal space. The original mod did show the real interior, but the windows couldn't show the real world, because the internal space sits apart from it.
- Detailed `IVA:` log lines (pods, interior names, meshes, layers, seats) to make tuning possible without a debugger.

## Ported to Redux

- Now a `KerbalMod` (Redux / SpaceWarp 2) instead of a BepInEx `BaseUnityPlugin`.
- Built with the Redux SDK in Unity instead of the old Visual Studio project. The hard-coded HintPaths, the Steam path, the XCOPY post-build step and the unused SpaceWarp 1 and Harmony references are gone.
- Uses `FindObjectsByType` instead of `FindObjectsOfType`, which recent Unity versions have deprecated.
- Uses its own child search instead of the game's `FindChildRecursive`, which has moved namespace in Redux.

## Bugs fixed

1. **Crash cycling seats with V.** The index check was `>` instead of `>=`, so pressing V on the last crew member threw an IndexOutOfRangeException.
2. **Near clip plane set to 0 on exit.** The original value was never saved on entry. It is now saved and restored.
3. **Exit pose overwritten.** The camera repositioning code ran on exit as well as on entry, undoing the restore. It now runs on entry only.
4. **Crashes with no crew or outside flight.** C on a probe, in the VAB or at the main menu threw an exception, and so did every frame after that. The mod now only responds in flight and logs a message when there's no crew.
5. **Stale seat number.** The seat index carried over between vessels and could point past the end of the crew list. It is now range-checked.
6. **Wrong body hidden after switching seats.** The previous kerbal stayed invisible and the new kerbal's body showed in your view. Each switch now restores the old body and hides the new one, restoring the saved scale instead of assuming 1.
7. **Look and zoom froze while paused and depended on frame rate.** Mouse input was multiplied by `Time.deltaTime`. Mouse look no longer uses it.
8. **Unbounded look and odd zoom start.** Pitch is clamped, yaw wraps, look resets on entry, zoom starts at a set field of view, and scroll-up now zooms in.
9. **Stuck in IVA after scene changes.** If the crew camera or flight camera is destroyed (vessel switch, EVA, scene load) or you open the map, the mod leaves IVA cleanly. It also leaves IVA if the mod is unloaded.

## Improvements

- All keys and limits are configurable (see README).
- Optional "hold right mouse button to look" mode, so the cursor stays free for the UI.
- The camera pose is applied in `LateUpdate`, after the game's camera code has run, so the game is less likely to override it.
- Seat order is stable, so V cycles in the same order each time.
- If the expected cameras aren't found, it logs the names of every camera in the scene, which makes it quick to fix if Redux renames them.
- Fallback lookup via the game's `KerbalCamera` component if no camera is named `kerbalCam`.
- Version and metadata cleaned up (the original said 0.2.5.0, 0.2.6 and 1.0.0.0 in different places, and its product name was copied from another mod, "Autostrut").
