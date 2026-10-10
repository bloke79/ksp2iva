# ADR-001: No code-generated cabin

_Date: 2026-10-09 · Status: accepted_

## Context
In 0.4 the mod built a cabin at run time from code, sized by raycasting the pod's colliders.

## Decision
Removed. Matt rejected it as "ghetto": visual quality matters more than avoiding hand-made assets.

## Consequences
Interiors are modelled assets, built in Blender (by script) and shipped as addressables. Every new pod
needs its own modelled interior.

## Alternatives considered
- **Improving the generated cabin**: it would still look generic and couldn't match the approved art direction.
