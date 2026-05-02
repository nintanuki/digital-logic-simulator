# Roadmap

A handoff-friendly task list for circuit-builder. Items are roughly ordered:
do **Now** first, then **Next**, then **Later**. Each task lists the smallest
concrete steps so the work can be resumed in a fresh session without
rebuilding context. Known bugs live in **Known Issues** at the bottom.

Before starting any item, read `docs/TESTING.md` (refactoring rules + manual
test checklist) and skim recent entries in `docs/CHANGELOG.md`.

---

## Done — Port highlighting (2026-05-01)

Smallest visible win, and the test rig for the hover infrastructure that
hover labels and wiring reuse.

- [x] Add `self.hovered = False` in `Port.__init__`.
- [x] Add `PORT_HIGHLIGHT_COLOR` to `ComponentSettings` in `settings.py`.
- [x] In `Port.draw`, pick `PORT_HIGHLIGHT_COLOR` when `self.hovered`, else `PORT_COLOR`.
- [x] In `GameManager._handle_mouse`, on `MOUSEMOTION` walk every component's `ports` and set `port.hovered = port.rect.collidepoint(event.pos)`. Toolbox templates count too. (Implemented as `_update_port_hover`.)
- [X] Manual test: hover a port — it lights up. Move away — it un-lights. Drag a component — its ports stay hot under the cursor as expected. *(needs a human at a keyboard)*

---

## Done — Port hover labels (2026-05-01)

- [x] Add `PORT_LABEL_COLOR`, `PORT_LABEL_FONT_SIZE`, and `PORT_LABEL_OFFSET` to `ComponentSettings`.
- [x] Cache one `pygame.font.Font` for port labels at the `GameManager` level. *(Implemented as a dedicated `Fonts` class — exposes `Fonts.component_label` and `Fonts.port_label`, init'd once at boot.)*
- [x] Split out `Port.draw_label`. INPUT anchors right (label sits to the left of the port), OUTPUT anchors left. Called from Component.draw after the body so labels stay on top.
- [X] Manual test: hover each port on a NAND, see "A", "B", "OUT". *(needs a human at a keyboard)*

---

## Done — Wiring (2026-05-01)

- [x] New `Wire` class in `wires.py`. Holds `(source, target)` Port references (no cached coordinates) so it follows when either component is dragged. Includes `hit(pos)` (point-to-segment distance) for right-click delete.
- [x] `WireManager` (separate class — wiring grew enough state to deserve one). GameManager owns it as `self.wires`.
- [x] Click-and-drag from a port starts a wire; release on a valid target port commits. Ghost line drawn in `WireSettings.GHOST_COLOR` while dragging.
- [x] Cancel on right-click during drag, or release in empty space.
- [x] Validation: output↔input only (auto-swap so the user can drag from either end), no self-connections (same parent rejected), one incoming wire per input (existing wire on the target is dropped before commit).
- [x] Right-click an existing wire to delete it.
- [x] Wires touching a deleted component are dropped via `WireManager.drop_wires_for_component`.
- [X] Manual test: connect two NANDs, drag both, the wire follows both endpoints. *(needs a human at a keyboard)*

---

## Done — Live signal state (2026-05-02)

- [x] Add `self.live = False` to `Port`. Add `PORT_LIVE_COLOR` to settings.
- [x] Each frame, propagate signals: for each gate, compute `output = NOT (A.live AND B.live)`; for each wire, copy `source.live` to `target.live`. *(Implemented in `signals.py::SignalManager.update`. NAND logic lives on `Component.update_logic` (default 2-input NAND); subclasses override.)*
- [x] Use a two-phase update (read all inputs into a temp buffer, then write all outputs) so SR latches and other feedback circuits behave. *(Phase 1 reads inputs into `output_buffer`. Phase 2 writes buttons to ports. Phase 3 resets every INPUT to LOW then propagates `wire.target.live = wire.source.live`, so a disconnected input falls back to LOW instead of latching.)*
- [x] ~~Click an unconnected input port to toggle it manually...~~ Replaced per the user's note in the same bullet: dedicated `Switch` and `LED` components, both circles for now. Switch has one OUTPUT port and toggles on a stationary click; LED has one INPUT port and lights up green when HIGH. Both spawn from the toolbox alongside NAND.
- [X] Manual test: a single NAND with both inputs HIGH outputs LOW; with either input LOW outputs HIGH. An SR latch built from two NANDs holds state. *(needs a human at a keyboard)*

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

- [x] ~~`pygame.font.init()` runs inside `Component.__init__`...~~ Done 2026-05-01. New `fonts.py` with a `Fonts` class loaded once by `GameManager.__init__`.
- [x] ~~`Component.handle_event` falls off the end implicitly...~~ Done 2026-05-01. Explicit `return None` added.
- [x] ~~`Component.__init__` defaults `width=100`, `height=60`...~~ Done 2026-05-01. Replaced with `ComponentSettings.DEFAULT_WIDTH` / `DEFAULT_HEIGHT` via a `None` sentinel default.
- [x] ~~`crt.py::CRT` calls `super().__init__()`...~~ Done 2026-05-01. Removed.

---

## Known issues

Bugs that affect behavior. Repro → fix → log in `docs/CHANGELOG.md` → re-run
the manual checklist in `docs/TESTING.md`.

- [x] ~~**Components can be dragged behind the toolbox.**~~ Fixed 2026-05-01. `Component._clamp_to_workspace` clamps `rect.x`/`rect.y` after every drag-driven assignment so a component cannot enter the toolbox bank or leave the screen. Reported by user 2026-05-01.
- [ ] ~~**Wires only go in a straight line, can't be bent or curved.**~~ Right now if a user wants to connect to components and there is another component between them, or they want to create a loop, this results in ugly straight lines everywhere. Perhaps allow them to create the wire in "segments"
-  [ ] ~~**Port highlighting is active inside the toolbox.** When hovering over the ports of a component in the toolbox port highlighting works as if it was in the workspace. This is a low priority issue.