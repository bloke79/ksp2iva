# IVA for KSP2 Redux (snapshot 26w41a)

First-person IVA for KSP2 Redux with a modelled interior for the Mk1-3 "Gumball" 3-seat pod: three couches, a full instrument panel with a navball, framed windows that look out on the real world, a side hatch, a docking tunnel and lockers. It started as a port of Mudkip909's "KSP2 Free IVA" 0.2.6. See `CHANGES.md` for the history and `previews/` for renders of the interior.

## What's in this package

```
IVA-Redux/
  README.md                         this guide
  CHANGES.md                        version history
  previews/                         renders of the Mk1-3 interior
  Unity/Assets/IVA/                 copy this folder into your Unity project's Assets/IVA
    Code/
      IVAPlugin.cs                  keys, settings, camera, alignment tool
      CustomInterior.cs             finds and measures the pod, places the interior
    Editor/
      IVAInteriorSetup.cs           adds the "IVA > Set Up Interiors" menu
      IVA.Editor.asmdef
    Interiors/Mk13/
      Mk13Interior.fbx              the model (about 89,000 triangles)
      materials.json                material settings for the setup button
      Textures/                     15 textures
  art/                              Blender scripts that build the model (only needed to change it)
```

## What you need

- KSP2 with Redux on the Beta channel, snapshot 26w41a.
- Git for Windows, Unity Hub and the Redux SDK Manager (free). The SDK Manager installs the right Unity version (6000.6.0f1) for you.
- No game files to download: the SDK Manager copies what it needs from your installed game.

## One-off setup (first mod only)

1. **Install Git for Windows and Unity Hub.**
2. **Install the Redux SDK Manager** from the Releases page of `github.com/KSP2Redux/Redux-SDK-Manager`.
3. **Check the Redux Launcher is on the Beta channel** and your game is on 26w41a (Launcher: gear icon next to the Mods tab > Release Channel > Beta).
4. **Create a project.** In the SDK Manager click **New**, choose an empty folder (for example `C:\KSP2Mods\MyMods`) and pick template version **26w41a**. When asked for KSP2, point it at `KSP2_x64.exe` in your game folder.
5. **Let it install Unity** if offered, and let the automatic setup finish (it imports the game into the project; this takes a while). If a **Setup** button shows afterwards, click it.
6. Click **Open** to open the project in Unity.

## Add the IVA mod

1. In Unity's top menu choose **Modding > Create New Mod**, enter `IVA` as the Mod ID (exactly that), tick the option to add code, and click **Create**.
2. In Windows Explorer, copy the package's `Unity/Assets/IVA` folder over your project's `Assets/IVA` folder. Say yes to replacing `Code/IVAPlugin.cs`. Leave everything else the SDK created (especially `Code/IVA.asmdef`, `IVA.asset` and `Pipelines`). If you added earlier versions of this mod, delete `GameInterior.cs`, `InteriorBuilder.cs` and `InteriorGeometry.cs` from `Assets/IVA/Code` if they're there.
3. Switch back to Unity and wait for it to import. Check the **Console** window shows no red errors.
4. Choose **IVA > Set Up Interiors** from the top menu. It reports what it set up; you should see "Mk13Interior: 35 materials, prefab and address 'IVA/Interior_Mk1-3'".
5. Click `Assets/IVA/IVA.asset` and fill in the Inspector: Name `IVA`, Author (you, crediting Mudkip909 in the description), Version `0.6.0`, a short description. Leave the SpaceWarp2 dependency as it is.

## Build it into your game

1. Open `Assets/IVA/Pipelines/`, click **Build for Player**, then **Execute** in the Inspector.
2. The mod is written to `<your KSP2 folder>\mods\__Testing\IVA\`. Start the game through the Redux Launcher.

Run **Build for Player** again after any change. Run **IVA > Set Up Interiors** again only if the interior files change.

## Using it

| Key / input | Action |
|---|---|
| C | Enter or leave IVA (in flight only; C again while it loads cancels) |
| N | Next seat (V is the game's camera-mode key) |
| B | Window view: lean up to the nearest window, again for the next, and after the last back to your seat |
| U | Unbuckle and float round the cabin; U again (or N / B) to sit in the nearest couch |
| W A S D, Shift / Ctrl, Q / E | While floating: move, up / down, roll (the vessel's flight controls are locked meanwhile) |
| F | While floating: open or close the door you're next to (hygiene compartments) |
| [ / ] | Only with *Audition keys* on: play the previous / next candidate game sound, with its name on screen |
| Mouse | Look around |
| Scroll wheel | Zoom (up zooms in) |

Fly a Mk1-3 pod (or any crewed 3-seat pod) and press C. The interior is placed inside the pod, sized to the pod's measured shape, and you start in the centre seat facing the console. IVA turns itself off if you open the map, leave flight, switch vessels or the pod is destroyed. Pods without an interior of their own get the original portrait-camera view (or the Mk1-3 interior, if you turn on *Use for pods without their own interior*).

### Lining it up (numpad, in IVA)

The interior should land in the right place on its own. If the windows don't line up with the pod's own windows, or the cabin is too big or small:

| Numpad | Does |
|---|---|
| 7 / 1 | turn the interior (this is the main one: line its windows up with the pod's) |
| 8 / 2, 4 / 6, 9 / 3 | move forward/back, left/right, up/down |
| * / / | bigger / smaller |
| hold Shift + 8/2, 4/6, 9/3 | move your eye instead |
| + / - | bigger / smaller steps |
| 5 | save to config |
| 0 | reset (with Shift: reset the eye) |

The log also lists the pod's own window meshes and their angles, which tells you roughly which way to turn it.

## Settings

All in the mod's config file (Redux may also show them in the in-game mod settings).

| Section | Setting | Default | What it does |
|---|---|---|---|
| Keys | Toggle IVA / Next seat / Window view / Unbuckle / Open door | C / N / B / U / F | Unity key names; modifiers with `+`, for example `LeftAlt+C` |
| Look | sensitivity, invert, hold right mouse, max angle | 2 / off / off / 85 | |
| Look | Window glide time | 0.5 | Seconds to move between seat and window (0 = instant) |
| Look | Float speed | 1.2 | Top speed when floating round the cabin (m/s) |
| Sound | Interior sounds | on | Cabin sounds (thrusters, doors, buckles) from the game's own sound events |
| Sound | Thruster sound | on | Moving while floating plays the EVA jetpack's thruster sound |
| Sound | Volume | 0.6 | Volume of the cabin sounds (0 to 1) |
| Sound | Cabin ambience | blank | A looping game sound event to play while in a cabin (stopped with the same name plus `_stop`) |
| Sound | Audition keys | off | Testing aid: [ and ] step through candidate game sounds |
| Zoom | starting, min, max field of view, speed, invert | 75 / 30 / 110 / 5 / off | |
| Zoom | Window view field of view | 60 | Field of view at a window |
| Interior | Use custom interiors | on | Off = original portrait-camera view |
| Interior | Pod name filter | blank | Pick a pod by part of its name (names are in the log) |
| Interior | Use for pods without their own interior | off | Put the Mk1-3 interior in other crewed pods too |
| Interior | Fit to pod | on | Size the interior to the pod's measured shape |
| Interior | Hide pod exterior in IVA | off | Turn on if bits of the pod's outer model poke through |
| Alignment | Offset X/Y/Z, Yaw, Scale, Eye X/Y/Z | 0 / 0 / 1 / 0 | Set by the numpad tool |
| General | Hide own kerbal | on | Hides your own kerbal's head (custom interiors) or whole body (portrait view) |

## First test: what to check

This hasn't been run in game yet. After pressing C, look in the game log for lines starting with `IVA`:

- `crewed parts on vessel` lists the pods it found.
- `loading interior 'IVA/Interior_Mk1-3'` then `placed the Mk1-3 interior` with the pod's measured size and the fit scale. If instead it says it couldn't load the interior, **Set Up Interiors** probably wasn't run before **Build for Player**.
- `the pod's own window meshes` lists window angles, for lining up.
- A warning that the model came in tipped over means Unity imported it on its side; the mod corrects it automatically.

| What you see | Try |
|---|---|
| Interior is pink or black | The Standard shader isn't working in the game build. Send me the log. |
| Windows face the wrong way | Numpad 7 / 1 until they line up, then 5 to save |
| Cabin too big (walls cut by the pod's hull) or too small | Numpad * and /, or turn off *Fit to pod* |
| Pod's outer model visible inside | Turn on *Hide pod exterior in IVA* |
| Eye in the wrong spot | Shift + numpad |
| Nothing happens on C | The log lists every camera in the scene; send me that line |

## Changing the interior

Each interior is built entirely from the Blender scripts in `art/`, one spec per pod in `art/pods/`. One command
builds the textures, model and preview renders, and `-Export` also writes the FBX, `materials.json` and textures into
`Unity/Assets/IVA/Interiors/<Interior>`:

```
.\art\build_interior.ps1 -Pod pod_2v_conical_crew            (model + previews)
.\art\build_interior.ps1 -Pod pod_2v_conical_crew -Export    (also export for Unity)
```

Then run **IVA > Set Up Interiors** and **Build for Player**. Or just tell me what to change.

## Credits and licence

Original mod by Mudkip909 (KSP2 Free IVA, 0.2.6). The Mk1-3 interior model and textures were made for this mod. The original source zip had no licence file, so check the original repository's licence before sharing this publicly. For your own use it doesn't matter.
