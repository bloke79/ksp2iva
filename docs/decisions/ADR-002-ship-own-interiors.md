# ADR-002: Ship our own interiors instead of using the game's

_Date: 2026-10-10 · Status: accepted (supersedes the 0.5 approach)_

## Context
0.5 used KSP2's internal space (`UniverseView.InternalSpaceTransform`, layer 16 `LayerInternalScenery`),
`Data_CrewedInterior.InteriorName` and `IInternalSeat`, with an overlay camera drawn on top of the real outside view.
Matt then confirmed that **stock pods have no modelled interiors**.

## Decision
Ship a modelled interior per pod, loaded by address (`IVA/Interior_<Pod>`), placed inside the real pod in
world space, and drawn by the normal flight camera. That way the real world and sunlight come through the windows.

## Consequences
- No overlay camera is needed, and lighting and shadows from outside are real.
- Every pod needs its own interior (Blender pipeline in `art/`).
- The interior must be fitted to the measured pod and aligned (yaw) with the pod's real windows.

## Alternatives considered
- **Game interiors with an overlay camera (0.5)**: there's nothing to render.
- **Portrait camera (original mod)**: kept as a fallback mode. It shows a portrait booth, not the pod.
