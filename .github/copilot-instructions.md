# Copilot Instructions for Mimic Dice

These rules apply to **every** editor of this codebase, human or AI. They are not suggestions. Read this file before each session.

---

## Required reading order (before any change)

1. [README.md](../README.md) — what the project is and how to run it.
2. [docs/TODO.md](../docs/TODO.md) — current phase and roadmap.
3. [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — how the code actually works.
4. [docs/CHANGELOG.md](../docs/CHANGELOG.md) — most recent changes, so you know the current state.
5. The source files relevant to your task.

If a question is asked about *why* code was written a certain way, that is a request for an **explanation**, not a request for a code change. Do not modify code unless the user explicitly asks for a change.

---

## Required actions (after any change)

- Append an entry to [docs/CHANGELOG.md](../docs/CHANGELOG.md) following the format defined at the top of that file (ISO 8601 timestamp with timezone, file path, line numbers at time of edit, before/after code, why, and editor name including the AI model used).
- If your change altered how a system works, update the matching section of [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md). Out-of-date architecture docs are worse than none.
- If your change completes or adds a roadmap item, update [docs/TODO.md](../docs/TODO.md) (mark `[x]`, do not delete).

---

## Code style

- All Python code must be PEP-8 compliant.
- Less code is better; clean and readable is best.
- Prefer clear names over short ones. New class and function names must clearly describe their purpose.
- Do not change function or variable names unless the role has *completely* changed.
- Keep code free of dead imports, unused variables, unused functions, and legacy code.

## Architecture rules

- `GameManager` must stay thin. Offload responsibilities to dedicated classes.
- Classes should communicate through `GameManager` where possible. Avoid systems reaching directly into each other.
- Keep middlemen minimal: if A calls B and B only calls C, have A call C directly.
- All constants live in `settings.py`. **No magic numbers anywhere else.** When adding a constant, include a comment explaining its units and effect.

## The `legacy/` folder is read-only

- Treat everything under `legacy/` as reference material, not source.
- Do not edit, rename, move, or delete any file in `legacy/`.
- Do not import directly from `legacy/` in shipped code. To reuse legacy logic, copy the relevant code into the appropriate `systems/`, `ui/`, or `utils/` module under a new name and adapt it there.
- `legacy/zombie-dice-bots/` was originally paired with a separate tournament-runner module that is intentionally not part of this game. Difficulty tiers were measured from that simulation once and recorded in `docs/AI_OPPONENTS.md`; no further simulations are required.

## File and function layout

- Inside a class, group functions by role (setup, actions, physics, render, etc.).
- `update` and `run` go **last** and should only call other functions on the class.
- Separate logical sections inside a file with an all-caps banner comment, exactly this style:

  ```python
      # -------------------------
      # SECTION NAME
      # -------------------------
  ```

  Match the leading indentation of the surrounding class body. Keep the dashes the same length and the name in ALL CAPS.

## Comments and docstrings

- Every class and function must have a docstring with a one-line summary, plus `Args:` / `Returns:` blocks when applicable.
- Do not remove docstrings. Update them in place if behavior changes.
- Do not remove comments unless they are inaccurate; prefer updating them.
- Comments must explain **why**, not just what.
- Do not leave comments noting that a change was made, unless they explain a non-obvious bug fix or unconventional code.

## UI text

- ALL text displayed to the user must be ALL CAPS.

---

## Verifying edits in a Cowork session (OneDrive sync caveat)

Mimic Dice lives under OneDrive. In a Cowork session, the file tools (Read / Write / Edit) talk to the Windows-side file system and reflect every edit immediately, but the Linux shell sees the workspace through a mount that lags Windows by anywhere from a few seconds to a few minutes after each write. Anything run through `bash` — including any `python3` invocation — may execute against the stale file and produce errors that have nothing to do with what's actually on disk.

To avoid wasting time on stale views:

- Do not verify just-edited Python by `import`-ing it through `bash`. The interpreter will execute the old file.
- For behavior checks, paste the relevant logic into a `python3 -c` one-liner and test it inline, rather than importing from the source file you just wrote.
- For file-content checks, use the Read tool, not `cat` / `sed` / `wc`. Read is immediate.
- Real runtime tests (`python main.py`, controller input, fullscreen toggle, the Mental testing checklist below) belong on the Windows side outside Cowork; the Linux shell can't run pygame anyway.

---

## Mental testing checklist (run after major changes)

- The game still launches (`python main.py`).
- Window can be resized; the tray and dice respond correctly.
- Pressing `Space` triggers a fresh roll and dice settle on a face.
- The CRT overlay still renders in windowed mode and still skips in fullscreen.
- The quit combo (`Start + Back + L1 + R1`) still exits cleanly.
- No new magic numbers leaked outside `settings.py`.