# Testing & Refactoring Rules

This document is the canonical source for **how to test changes** and **the
refactoring rules every editor follows** in Digital Logic Simulator. The rules
section is referenced from
[.github/copilot-instructions.md](../.github/copilot-instructions.md); keep them
in sync there if anything is added or removed here.

---

## How to test changes

There is no automated test suite yet (see the Tech Debt section of
[docs/TODO.md](TODO.md)). Until there is, every change is validated by hand.
Workflow:

1. **Launch the simulator.** `python main.py` should reach the workspace
   without errors and without warnings about missing assets.
2. **Run the manual checklist below**, mentally or live, against the changed
   subsystem first and then against everything that touches it.
3. **Exercise the abstraction loop end-to-end at least once per pass:** build
   a small circuit (e.g. NOT from one NAND), save it as a component, drop it
   back into the workspace, wire it up, save the project, restart, load the
   project, confirm everything is intact.
4. **Append a CHANGELOG entry** per the format at the top of
   [docs/CHANGELOG.md](CHANGELOG.md). No exceptions, including for one-line
   edits and including for documentation changes.

If a manual check fails, fix it before the change lands. Don't ship a known
regression "for now."

---

## Manual testing checklist

Run after any change of meaningful size, and definitely before declaring a
pass complete.

### Launch & lifecycle
- [ ] The game launches without errors (`python main.py`).
- [ ] Window is the expected size; the workspace, top menu bar, and toolbox
  are all visible.
- [ ] `Esc` from the workspace opens the quit-confirm dialog (does not exit
  silently).
- [ ] `F11` toggles fullscreen.

### Workspace interaction
- [ ] Drag and drop still works; components can be dragged from the toolbox
  into the workspace.
- [ ] Clicking a Switch toggles its output without dragging it.
- [ ] Components can be moved on the workspace by left-click drag.
- [ ] Marquee selection works; group drag moves the whole selection.
- [ ] Right-click deletes a component, a wire, or a text box, depending on
  what is under the cursor.

### Wiring
- [ ] Wiring still works: drag from one port, release on another compatible
  port (different parent, opposite direction).
- [ ] Right-click during an in-flight wire cancels it.
- [ ] Releasing in empty space cancels an in-flight wire.
- [ ] Multi-segment wires render and right-click delete still hits any segment.

### Simulation
- [ ] A NAND with both inputs LOW outputs HIGH; with both inputs HIGH outputs
  LOW; with one of each outputs HIGH.
- [ ] An LED lights when its input is HIGH and goes dark when its input is LOW.
- [ ] An SR latch built from two NANDs holds state across frames (set, then
  release: the output stays).
- [ ] Disconnecting a wire from a driven input causes that input to fall back
  to LOW (no latched stale value).

### Undo / redo
- [ ] `Ctrl+Z` reverses the action you just took (place, delete, wire,
  text box).
- [ ] `Ctrl+Y` re-applies it.
- [ ] Undo / redo work after a save-as-component (or, if history was
  intentionally cleared by save-as-component, the bank still functions).

### Save-as-component
- [ ] Build a small circuit, save it as a named component, confirm it appears
  in the toolbox.
- [ ] Drop the saved component back into the workspace and wire it up; it
  produces the expected truth table.
- [ ] INPUT ports of the saved component come from Switches, OUTPUT ports
  come from LEDs, and they are ordered top-to-bottom by Y-coordinate.

### Project save / load
- [ ] Save a project to disk, restart the simulator, load the project, and
  confirm components, wires, text boxes, and saved-component definitions are
  all intact.
- [ ] Old saves with lowercase text-box content load with the content
  upper-cased (UI-CAPS rule).

### Text boxes
- [ ] A text box can be created, edited, escape-committed, and deleted.
- [ ] Clicking outside an editing text box stops editing.

### Top menu bar
- [ ] FILE / EDIT / VIEW open with both clicks and mnemonics (`F`, `E`, `V`).
- [ ] Menu items run their actions when clicked.
- [ ] Clicking outside an open menu closes it without spurious workspace
  side effects.

### Hygiene
- [ ] No new magic numbers leaked outside `settings.py`.
- [ ] No new dead imports, unused variables, or unused functions.
- [ ] Every new class and function has a docstring with a summary, plus
  `Args:` / `Returns:` blocks where applicable.
- [ ] All new user-facing text is in ALL CAPS.

---

## Refactoring rules

Every editor of this codebase, human or AI, follows these. They are mirrored
in [.github/copilot-instructions.md](../.github/copilot-instructions.md).

### Process
- Update [docs/CHANGELOG.md](CHANGELOG.md) for every code change (timestamp
  with timezone, file path, line numbers at time of edit, before/after, why,
  and editor name including the AI model used). Read recent entries before
  making changes so you know the current state of the codebase.
- If a change altered how a system works, update the matching section of
  [docs/ARCHITECTURE.md](ARCHITECTURE.md).
- If a change completes or adds a roadmap item, update
  [docs/TODO.md](TODO.md) (mark `[x]`, do not delete).

### Code style
- All Python code must be PEP-8 compliant.
- Less code is better than more code, but clean and readable code is the best.
- Keep "middlemen" minimal: if A calls B and all B does is call C, A should
  just call C.
- Keep code clean of dead imports, unused variables and functions, and
  legacy code.

### Architecture & responsibilities
- `GameManager` must be light \u2014 offload responsibilities to other classes.
- `GameManager` is an **orchestrator, not a feature container**.
- `GameManager` should own app lifecycle, high-level state, and subsystem
  coordination.
- Feature logic should live in the class that owns that feature.
- State should live next to the behavior that uses it.
- Avoid passing the full `GameManager` into other classes unless absolutely
  necessary. Prefer explicit dependencies, narrow interfaces, and callbacks
  over giving a class access to all manager internals.
- "Communicate through `GameManager`" means coordination, not global access
  to shared mutable state.
- New features should not add large new blocks of logic directly into
  `GameManager` if a dedicated subsystem/controller is more appropriate.
- Event handling, rendering, persistence, and UI state should be separated
  by responsibility as much as reasonably possible.
- If a subsystem needs to trigger a cross-system action, prefer returning a
  result/action, calling a callback, or asking `GameManager` to coordinate it
  rather than directly reaching into another subsystem.
- When possible, classes should communicate to each other through `GameManager`.

### Names
- Any new names for classes and functions must clearly describe their function.
- Function and variable names must be descriptive.
- Do not change function names unless their role is now completely different.
- Do not change variable names if not necessary.

### Constants
- Keep all constants declared in `settings.py`. Avoid magic numbers anywhere
  else. When adding a constant, include a comment explaining its **units** and
  what changing it does.

### Docstrings & comments
- All classes and functions must have a docstring.
- All docstrings must have a summary, `Args:` (if applicable), and `Returns:`
  (if applicable).
- Do not remove comments. Comments must explain **why**, not just what.
- When making a change, do not leave a comment that a change was made,
  unless it was to fix a bug that wasn't obvious and the comment explains why
  something was done in an unconventional way.

### File and function layout
- Keep functions organized and grouped by role inside each class. The
  `update` and `run` functions go **last** and should do as little as possible
  \u2014 only call other functions if possible.
- Separate logical sections inside a file with an all-caps banner comment
  matching the indentation of the surrounding class body:

  ```python
      # -------------------------
      # SECTION NAME
      # -------------------------
  ```

### UI text
- **All text displayed to the user in the UI must be ALL CAPS.** This applies
  to menu items, buttons, dialog labels, banners, and every display string
  baked into `settings.py`.
