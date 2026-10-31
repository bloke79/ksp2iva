# API corrections

Where code written against stubs turned out wrong for the real KSP2 Redux assemblies.

| Date | Game version | What was wrong | Fix | File |
|---|---|---|---|---|
| 2026-10-10 | 26w41a | `ILogger` ambiguous: `ReduxLib.Logging.ILogger` vs `UnityEngine.ILogger` | `using ILogger = ReduxLib.Logging.ILogger;` | `Code/CustomInterior.cs` |
| 2026-10-31 | 26w43b | `ReduxLib.Configuration/Input/Logging` moved | `SpaceWarp2.API.*` (`using` lines in 9 files); `ReduxLib.dll`/`SpaceWarp2*.dll` dropped from the asmdef, `Ksp2Redux.dll` added | `Code/*.cs`, SDK `IVA.asmdef` |
