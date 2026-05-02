# Roadmap

A handoff-friendly task list for circuit-builder. Items are roughly ordered:
do **Now** first, then **Next**, then **Later**. Each task lists the smallest
concrete steps so the work can be resumed in a fresh session without
rebuilding context. Known bugs live in **Known Issues** at the bottom.

Before starting any item, read `docs/TESTING.md` (refactoring rules + manual
test checklist) and skim recent entries in `docs/CHANGELOG.md`.

## Read TESTING.md before making any changes

---

## Now — Port highlighting

Smallest visible win, and the test rig for the hover infrastructure that
hover labels and wiring will reuse. The `Port` class already exposes a hit
`rect` and a screen-space `center`, so this is just adding state and wiring
it to mouse motion.

- [ ] Add `self.hovered = False` in `Port.__init__`.
- [ ] Add `PORT_HIGHLIGHT_COLOR` to `ComponentSettings` in `settings.py`.
- [ ] In `Port.draw`, pick `PORT_HIGHLIGHT_COLOR` when `self.hovered`, else `PORT_COLOR`.
- [ ] In `GameManager._handle_mouse`, on `MOUSEMOTION` walk every component's `ports` and set `port.hovered = port.rect.collidepoint(event.pos)`. Toolbox templates count too.
- [ ] Manual test: hover a port — it lights up. Move away — it un-lights. Drag a component — its ports stay hot under the cursor as expected.

---

## Next — Port hover labels

After highlighting works, the label is one extra draw call when `hovered`.

- [ ] Add `PORT_LABEL_COLOR`, `PORT_LABEL_FONT_SIZE`, and `PORT_LABEL_OFFSET` to `ComponentSettings`.
- [ ] Cache one `pygame.font.Font` for port labels at the `GameManager` level — do not spin up a new font per port (related to the font-init polish item below).
- [ ] In `Port.draw` (or split out a `Port.draw_label`), if `hovered` render `self.name` near the port. Use `self.direction` to decide which side to offset to: `INPUT` → label drawn to the left of the port, `OUTPUT` → label drawn to the right.
- [ ] Manual test: hover each port on a NAND, see "A", "B", "OUT".

---

## Next — Wiring

The biggest feature in the queue. Probably worth a brief design pass before
starting, but the rough shape:

- [ ] New `Wire` class — likely its own file `wires.py` to mirror the existing one-role-per-file pattern. Holds `(source_port, target_port)` and draws a line between their `center`s each frame so it follows when either component is dragged.
- [ ] `GameManager` owns `self.wires: list[Wire]` (or, if it grows, a `WireManager`).
- [ ] Click-and-drag from a port to start a wire; release on another port to commit. Show a "ghost" wire from the source port to the cursor while dragging.
- [ ] Cancel on right-click or release in empty space.
- [ ] Validate: outputs may only connect to inputs, and an input may have at most one incoming wire (replace if a second is committed).
- [ ] Right-click an existing wire to delete it.
- [ ] Manual test: connect two NANDs, drag both, the wire follows both endpoints.

---

## Next — Live signal state

After wires exist.

- [ ] Add `self.live = False` to `Port`. Add `PORT_LIVE_COLOR` to settings.
- [ ] Each frame, propagate signals: for each gate, compute `output = NOT (A.live AND B.live)`; for each wire, copy `source.live` to `target.live`.
- [ ] Use a two-phase update (read all inputs into a temp buffer, then write all outputs) so SR latches and other feedback circuits behave.
- [ ] Click an unconnected input port to toggle it manually, so students can drive signals.
- [ ] Manual test: a single NAND with both inputs HIGH outputs LOW; with either input LOW outputs HIGH. An SR latch built from two NANDs holds state.

---

## Later

Bigger features, in roughly the order they unlock student workflows.

- [ ] **Text boxes:** draggable, editable labels students can drop on the workspace to annotate their circuits.
- [ ] **Save / load a project:** JSON file containing components (type, position), ports, wires, and text boxes. Pick a schema version field early so future formats can migrate.
- [ ] **Main menu:** "New Project" / "Load Project" before the workspace opens.
- [ ] **Save as Component:** package the current workspace as a reusable named component that drops into the toolbox as a new template ("black box" abstraction). This is the keystone feature of the project — the moment students can build NOT/AND/OR from NAND and reuse them.
- [ ] **Toolbox redesign:** shrink the templates so more fit; scroll if the toolbox overflows.
- [ ] **Toolbox menu button:** "Save current circuit as component" / "Start a new workspace".

---

## Polish / tech debt

Not bugs, just code-quality items worth fixing the next time the surrounding
code is touched.

- [ ] `pygame.font.init()` runs inside `Component.__init__`, so every spawned gate re-initializes the font subsystem. Move it to `GameManager.__init__` and cache fonts there (or on a dedicated class). This becomes important once port labels also need a font.
- [ ] `Component.handle_event` falls off the end implicitly returning `None` on most paths. Add an explicit `return None` so the docstring contract (`str | None`) is honest at a glance.
- [ ] `Component.__init__` defaults `width=100`, `height=60` — magic numbers. Move to `ComponentSettings.DEFAULT_WIDTH` / `DEFAULT_HEIGHT`.
- [ ] `crt.py::CRT` calls `super().__init__()` despite inheriting from `object`. Harmless, but unnecessary; remove when next editing the file.

---

## Known issues

Bugs that affect behavior. Repro → fix → log in `docs/CHANGELOG.md` → re-run
the manual checklist in `docs/TESTING.md`.

- [ ] **Components can be dragged behind the toolbox.** A component should not be allowed below `UISettings.BANK_RECT.top`. Probably also clamp to the other three screen edges so a gate can't be lost off-screen. Fix lives in the `MOUSEMOTION` branch of `Component.handle_event`: clamp `self.rect.x` / `self.rect.y` after the assignment, ideally via a small `_clamp_to_workspace` helper that reads bounds from `ScreenSettings` and `UISettings`. Reported by user 2026-05-01.
