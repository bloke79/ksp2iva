Local-model notes for IVA Redux. Add one line for every new recurring slip.
- Paths in edits are relative to the project: `Unity/Assets/IVA/Code/<File>.cs`. Files are one namespace `IVA`.
- Logs: always the `IVA:` prefix. In `IVAPlugin` it is `SWLogger.LogInfo($"IVA: ...")`; other classes take a logger, `log?.LogInfo($"IVA: ...")`. The logger is `SpaceWarp2.API.Logging.ILogger`, with `using ILogger = SpaceWarp2.API.Logging.ILogger;` at the top (Unity has its own ILogger).
- Finding objects: `FindObjectsByType`, never `FindObjectsOfType`. Child search: the mod's own `PodLocator.FindChildRecursive(parent, name)`, not the game's extension.
- Every setting is a `ConfigValue<T>` with a row in README's Settings table.
- Keep maths and rules in plain classes with minimal Unity types.
- Space: horizon vectors go through `UniverseView.PhysicsSpace.VectorToPhysics`. Never parent the camera.
- Marker and mesh names (`IVA_*`, `Mesh_<Material>`, `__Live_<name>`), the pod spec keys, `materials.json` and `InteriorDesign` are contracts: never change them.
- Blender scripts in `art/`: `import bpy` comes before `bmesh` and `mathutils`.
