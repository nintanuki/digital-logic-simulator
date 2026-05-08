# Copilot Instructions for Digital Logic Simulator

These rules apply to **every** editor of this codebase, human or AI. They are not suggestions. Read this file at the start of every session.

If a question is asked about *why* code was written a certain way, that is a request for an **explanation**, not a request for a code change. Do not modify code unless the user explicitly asks for a change.

---

## Required reading order (before any change)

1. [README.md](../README.md) — what the project is and how to run it.
2. [docs/CHANGELOG.md](../docs/CHANGELOG.md) — most recent entries, so you know the current state of the codebase.
3. [docs/TESTING.md](../docs/TESTING.md) — how to test changes, manual checklist, and the full refactoring rules.
4. [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — how the code is put together and why.
5. [docs/TODO.md](../docs/TODO.md) — current pass and roadmap.
6. The source files relevant to your task.

---

## Required actions (after any change)

- **Append an entry to [docs/CHANGELOG.md](../docs/CHANGELOG.md)** following the format defined at the top of that file: ISO 8601 timestamp with timezone, file path, line numbers at time of edit, before/after code, why, and editor name including the AI model used. New entries go at the **bottom** of the file.
- **If your change altered how a system works, update the matching section of [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).** Out-of-date architecture docs are worse than none.
- **If your change completes or adds a roadmap item, update [docs/TODO.md](../docs/TODO.md)** (mark `[x]`, do not delete).
- **Run the manual checklist in [docs/TESTING.md](../docs/TESTING.md)** mentally, and re-test any subsystem you touched.

---

## Code style

- All Python code must be PEP-8 compliant.
- Less code is better; clean and readable is best.
- Prefer clear names over short ones. New class and function names must clearly describe their purpose.
- Do not change function or variable names unless the role has *completely* changed.
- Keep code free of dead imports, unused variables, unused functions, and legacy code.
- Keep middlemen minimal: if A calls B and B only calls C, have A call C directly.

## Architecture rules

- `GameManager` is an **orchestrator, not a feature container**. It owns app lifecycle, high-level state, and subsystem coordination — nothing more.
- Feature logic lives in the class that owns that feature. State lives next to the behavior that uses it.
- Classes should communicate **through `GameManager`** where possible. "Communicate through `GameManager`" means coordination, not global access to shared mutable state.
- Avoid passing the full `GameManager` into other classes unless absolutely necessary. Prefer explicit dependencies, narrow interfaces, and callbacks over giving a class access to all manager internals.
- If a subsystem needs to trigger a cross-system action, prefer returning a result/action, calling a callback, or asking `GameManager` to coordinate it rather than reaching directly into another subsystem.
- Event handling, rendering, persistence, and UI state should be separated by responsibility as much as reasonably possible.
- New features should not add large new blocks of logic directly into `GameManager` if a dedicated subsystem/controller is more appropriate.
- All constants live in `settings.py`. **No magic numbers anywhere else.** When adding a constant, include a comment explaining its units and effect.

## File and function layout

- Inside a class, group functions by role (setup, actions, rendering, etc.).
- `update` and `run` go **last** and should only call other functions on the class — they are coordinators, not implementations.
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

- **ALL text displayed to the user must be ALL CAPS.** This includes menu items, buttons, dialog labels, banners, and any string baked into `settings.py` for display.

---

## Mental testing checklist (run after major changes)

- The game still launches (`python main.py`).
- Drag and drop still works; components can be dragged from the toolbox into the workspace.
- Wiring still works (drag from a port to a port; right-click cancels in-flight wires).
- Right-click still deletes components, wires, and text boxes.
- Switch / LED logic still propagates correctly through NAND and saved components.
- Undo (`Ctrl+Z`) and redo (`Ctrl+Y`) cover the action you just changed.
- Save-as-component round-trips: build a circuit, save it, drop it back into the workspace, wire it up.
- Project save / load round-trips: save a workspace, restart, load it, verify wires and components are intact.
- An SR latch built from saved NAND-derived gates still holds state across frames.
- Text boxes can be created, edited, escape-committed, and deleted.
- The top menu bar (FILE / EDIT / VIEW) responds to both clicks and mnemonics.
- No new magic numbers leaked outside `settings.py`.
