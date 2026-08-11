# Agent instructions

Read `docs/CLAUDE_CODE_CODEX_HANDOFF.md` before changing architecture.
Read `memory.md` for prior session progress, decisions and open blockers
before starting work, and append a new entry to it when your session ends.

Primary objectives:
1. Preserve Hetzner shared-hosting compatibility.
2. Keep heavy GIS processing offline.
3. Treat parcels as the primary object.
4. Preserve data provenance and geometry-status semantics.
5. Do not imply derived parcel geometry is official cadastral geometry.

Before adding infrastructure, demonstrate why the existing static + CGI + PostGIS design cannot satisfy the requirement.
