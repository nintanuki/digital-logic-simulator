# Digital Logic Simulator — Architecture

This document explains **how the Digital Logic Simulator code is put together and why**. It is meant for anyone touching the code — human or AI. It deliberately skips things any Pygame project does (open a window, fill a background, flip the buffer) and focuses on the parts that are specific to this simulator: signal propagation, the abstraction loop (build → save → reuse), persistence, and the workspace UI.

> **Maintenance rule:** every pass that meaningfully changes a system must update the matching section here. Out-of-date architecture docs are worse than none. If you add a new subsystem, add a section.

A glossary of terms used throughout this document is at the bottom — see [section 10](#10-glossary).

---

## 1. The shape of the program

```
                              +---------------------+
                              |   main.py           |
                              |   GameManager       |   (orchestrator)
                              +----------+----------+
                                         |
       +-----------+-----------+---------+---------+-----------+----------------+
       |           |           |                   |           |                |
       v           v           v                   v           v                v
  ComponentBank  Workspace  SignalManager     WireManager  TextBoxManager   TopMenuBar
   (ui/bank)    Controller  (core/signals)   (core/wires)  (ui/text_boxes) (ui/top_menu_bar)
                (core/                                                           |
                 workspace_                                                      v
                 controller)                                                 Dialogs
                                                                       (ui/*_dialog.py,
                                                                        ui/quit_confirm_dialog,
                                                                        ui/save_as_component_handler)
                              +---------------------+
                              |   ProjectManager    |   (core/project_manager)
                              |   History           |   (core/commands)
                              |   CRT               |   (ui/crt)
                              +---------------------+
```

`GameManager` is intentionally an orchestrator. Its only jobs are:

- own the Pygame display, clock, fonts, and top-level lifecycle,
- drain the event queue and route each event to the right subsystem,
- call `update(...)` and `draw(...)` on the systems it owns in the right order,
- coordinate cross-system actions (save-as-component, project save / load, quit-confirm) by dispatching to handlers, not by implementing them inline.

Anything that has its *own* state — components, wires, signals, text boxes, menus, dialogs, undo history, persistence — lives in its own class. `GameManager` stitches them together; it does not implement them. New features that grow large blocks of state belong in a new class, not inside `GameManager`.

**Scenes.** `GameManager` carries a single `_active_scene` flag (`"workspace"` or `"diagrams"`). The flag gates event routing, grid rendering, and which subsystem owns the screen for the frame. The two scenes share the top menu bar; each scene registers its own action map (so e.g. EDIT > UNDO is greyed out while DIAGRAMS is showing) via `TopMenuBar.update_menu_actions(menu_id, actions)`. Adding a third scene means adding a flag value, an action map, and a draw branch — no new orchestrator class needed at this scale.

---

## 2. The frame loop

Each frame, in order:

1. **Event drain.** `pygame.event.get()` is processed and dispatched. Mouse and keyboard events flow first to any active dialog (modal), then to the top menu bar. From there the route forks on `_active_scene`: the **workspace** scene routes to the workspace controller, then component-level handlers; the **diagrams** scene routes to `DiagramViewerScene` (see [section 4.7](#47-diagram_viewerpy--the-diagrams-scene)) and skips workspace handlers entirely. Right-click in the workspace scene is a delete dispatch — it walks the workspace looking for a hit on a component, wire, or text box.
2. **Workspace interaction update.** `WorkspaceInteractionController` advances drags and marquee selection. (Skipped while a non-workspace scene is active.)
3. **Signal propagation.** `SignalManager.update(components, wires)` runs the two-phase tick described in [section 3.2](#32-signalmanager--two-phase-propagation).
4. **Render.** The active scene chooses what to draw. Workspace scene paints bottom-up: workspace grid → wires → components → text boxes → component bank (toolbox) → top menu bar → any active dialog → CRT overlay. Diagrams scene paints its own panel layout instead of the grid + workspace layers, and the top menu bar / dialogs / CRT still draw on top.
5. **`pygame.display.flip()`** then **`clock.tick(FPS)`** caps the frame rate.

The `update` and `draw` methods are split on purpose: simulation is deterministic given the previous frame's state, render is a pure function of state. Per the project rules, an `update` or `run` method should only call other methods on its class — it is a coordinator, not an implementation.

---

## 3. The simulation core (`core/`)

The core is where "what is a circuit" lives. Five files, each owning one concern.

### 3.1 `elements.py` — what's on the workspace

```
Port  ── one input or output stub on a component, has a live (HIGH/LOW) bit.
Component  ── default behavior is NAND. Owns its ports and its rect.
   ├── Switch  ── a toggleable input source (left-click to flip).
   ├── LED     ── a sink that lights when its input is HIGH.
   └── SavedComponent ── a black-box wrapper around a saved sub-circuit.
```

`Component` defaults to **NAND** because every other gate the curriculum teaches (NOT, AND, OR, XOR, latches, adders) can be built from NAND alone. That is the entire pedagogical premise of the project.

`SavedComponent` carries an **embedded definition** of the sub-circuit it represents — the raw components and wires that make up its internals. It does *not* reference an external file or library entry. See [section 5](#5-project-persistence-coreproject_managerpy) for why.

### 3.2 `SignalManager` — two-phase propagation

`SignalManager.update(components, wires)` advances the simulation by one frame using **three** sub-phases inside a single tick:

1. **Compute** — for each component, read its current INPUT ports and write its new OUTPUT values into a temporary buffer. No port is mutated in this phase.
2. **Apply** — flush the buffer to actual OUTPUT ports.
3. **Refresh inputs** — set every INPUT port LOW, then for each wire copy `source.live` to `target.live`.

Two non-obvious decisions live here:

- **The compute / apply split** is what makes feedback circuits work. An SR latch built from two NANDs feeds each gate's output into the other's input. If gates were evaluated in iteration order with direct port writes, the result would depend on which gate happened to be first in the list. Buffering means every gate sees the same snapshot of the previous frame's outputs.
- **Resetting INPUT ports to LOW before re-driving them from wires** is what makes wire deletion behave correctly. Without the reset, an input that lost its wire would latch the last value the (now-removed) wire delivered. Resetting first means a disconnected input reads LOW.

This is why the SR latch in the testing checklist is the canonical "did I break the simulator?" test: it exercises both behaviors at once.

### 3.3 `wires.py` — connections

`Wire` is a directed source-port → target-port edge, drawn as one or more straight segments through optional waypoints. `WireManager` owns:

- **drag-to-connect**: a press on a port starts an in-flight wire that follows the cursor until it lands on a compatible port (different parent, opposite direction) or is cancelled with right-click.
- **multi-segment rendering and hit-testing**: a wire's geometry is a polyline. Hit-test for right-click delete walks each segment.
- **validity**: ports of the same direction or on the same component cannot be connected.

### 3.4 `commands.py` — undo / redo

Every workspace mutation that the user can intuitively "take back" goes through a `commands.py` `Action` subclass:

- `PlaceComponent`, `DeleteComponent`
- `PlaceWire`, `DeleteWire`
- `PlaceTextBox`, `DeleteTextBox`

`History` keeps two stacks (undo and redo). Every concrete `Action` implements `do()` and `undo()` so the same code path that performed the change can reverse it. `GameManager` is the only object that calls `History.do(action)`, which is the project's "communicate through `GameManager`" rule in practice: subsystems hand the manager a description of what changed; the manager records it.

### 3.5 `workspace_controller.py` — pointer interactions

`WorkspaceInteractionController` owns the *interaction state* that doesn't belong to any single component: which thing is being hovered, which thing is being dragged, what the marquee selection currently covers, whether a group drag is in progress. It dispatches mouse events to the right component, wire, or text box and tells `GameManager` what `Action` to record when the interaction ends.

This split exists so `Component` itself is just "a thing on a grid with ports" — it doesn't know about marquees or group drags. That keeps components simple and lets us add new interaction modes (e.g. trash mode in the Pass 2 roadmap, lasso in a future pass) without touching component code.

---

## 4. The workspace UI (`ui/`)

### 4.1 `bank.py` — the toolbox

`ComponentBank` is the bottom strip of templates. Three template kinds live here today:

- **Built-in templates** — NAND, Switch, LED.
- **Saved-component templates** — `CompactSavedTemplate` instances created when the user clicks "Save as Component," each carrying an embedded definition.
- **Text template** — a special "TEXT" tile that spawns a text box rather than a component.

Saved components default to a random color from a curated 8-color palette (see `settings.py`) so the bank doesn't become a wall of identical red tiles.

### 4.2 `top_menu_bar.py` — FILE / EDIT / VIEW / HELP

`TopMenuBar` owns the menu strip across the top: rendering, hit-test, mnemonic handling (`F` / `E` / `V` / `H`), and dispatch back to `GameManager` for the actual file / edit / view / help actions. Menu logic stays here, not in `GameManager`. When a menu item is clicked, the bar calls a callback registered by `GameManager` — it does not reach into other subsystems.

Action maps are **per scene**. `GameManager` builds one map for the workspace and one for the DIAGRAMS scene, and calls `TopMenuBar.update_menu_actions(menu_id, actions)` whenever the active scene changes. Items whose action is `None` render as disabled — that is how EDIT > UNDO greys out while DIAGRAMS is open without the menu bar having to know what a scene is.

### 4.3 `text_boxes.py` — annotation labels

`TextBox` is a draggable, editable rectangle of UI-CAPS text used by students to label their circuits ("THIS IS THE SR LATCH"). `TextBoxManager` owns the list, focus state ("which text box is currently being edited"), and the Esc-to-stop-editing rule. Project save / load round-trips text boxes alongside components and wires.

### 4.4 `save_as_component_handler.py` — the abstraction loop

`SaveAsComponentHandler` is the plumbing behind the project's pedagogical core: turn a finished circuit into a reusable black box.

When the user clicks Save-as-Component:

1. Take a snapshot of the current workspace (components + wires).
2. Infer the new component's INPUT ports from every `Switch` in the workspace and OUTPUT ports from every `LED`, ordered by ascending Y-coordinate (top of workspace = port 0). Y was picked over creation-order because the visual top-to-bottom column is what the student sees and reasons about.
3. Open `SaveComponentDialog` for a name + color.
4. On confirm: package the snapshot as a `SavedComponent` definition and add a `CompactSavedTemplate` to the bank.
5. **Clear the undo / redo history.** Components in the workspace before the save still exist, but their `Action` records would now point at a stale workspace state. Wiping history is safer than carrying around stale references.

### 4.5 Dialogs

`project_dialogs.py` (Save / Load / FileNotFoundWarning), `save_component_dialog.py` (Save-as-Component), and `quit_confirm_dialog.py` are modal: while one is open, it captures all mouse and keyboard input. `GameManager` keeps an "active dialog" reference and routes events to it before any other subsystem sees them.

### 4.6 `crt.py` and `fonts.py`

`CRT` is a post-process scanline + flicker overlay drawn last so it sits on top of everything. `Fonts` is a tiny cache that loads every font face once at boot so the rest of the codebase can pull a `pygame.font.Font` without re-loading from disk.

### 4.7 `diagram_viewer.py` — the DIAGRAMS scene

`DiagramViewerScene` is the HELP > DIAGRAMS reference: a NAND-only construction guide for NOT, AND, OR, and a one-page summary of De Morgan's laws. It is the in-app answer to "why is the project's universal gate NAND?" without yanking the student to a browser.

Layout: a left list panel of entries (NOT / AND / OR / DE MORGAN'S LAWS), a centred image panel, and a description block underneath. A `RETURN` button anchored under the list panel exits the scene; `Esc` does the same. Up/down arrows and direct clicks change the selected entry.

Content lives in `DiagramViewerSettings.DIAGRAM_ENTRIES` in `settings.py` — each entry carries an id, a list label, a title, an image filename, and a description string. Adding a new diagram is a settings edit plus a PNG drop into `assets/graphics/diagrams/`; no scene code needs to change. Images are loaded once at scene construction; missing files render as `None` rather than crashing so a half-finished asset set still launches.

While DIAGRAMS is active:

- The workspace grid is not drawn and workspace event handling is bypassed (see [section 2](#2-the-frame-loop)).
- The top menu bar is still drawn and clickable, but its action map is the diagrams variant (FILE > NEW / LOAD / QUIT and VIEW toggles only; EDIT and HELP entries are disabled). NEW PROJECT and LOAD PROJECT both implicitly switch back to the workspace scene.
- Dialogs (e.g. quit-confirm, file-not-found) still draw and capture input on top, so quitting from DIAGRAMS still routes through the same confirm dialog as the workspace.

This is the realised form of the "Encyclopedia system scaffold" originally planned in [docs/TODO.md](TODO.md): a launchable, exitable reference scene with room to grow. Future passes can add more diagrams (latches, adders, multiplexers) by appending entries to `DIAGRAM_ENTRIES` — the scene scales with the data, not with new code.

---

## 5. Project persistence (`core/project_manager.py`)

`ProjectManager` owns all disk I/O for projects. It is intentionally separate from `GameManager`: project format and migration logic should not live in the main event loop.

A saved project is a single JSON file under `projects/` containing:

- the schema version (planned for Pass 3 — see [docs/TODO.md](TODO.md)),
- every component (type, position, internal state — e.g. a `Switch`'s current toggle),
- every wire (source / target as `(component_id, port_name)` pairs),
- every text box (position + UI-CAPS text),
- **embedded definitions of every saved sub-component** referenced by the project.

**Embed, don't reference.** Sub-circuit definitions live inside the project file rather than pointing at a shared library. This trades file size for portability: a save file from one student's machine opens on another's even if the recipient's bank is empty. It also future-proofs against a saved component being renamed or deleted from a library; the save is self-contained.

**Port ordering by Y-coordinate.** When loading a saved component, its INPUT and OUTPUT ports are ordered top-to-bottom by their Y-coordinate at save time, the same convention used by `SaveAsComponentHandler` ([section 4.4](#44-save_as_component_handlerpy--the-abstraction-loop)).

**Case normalization.** Text-box content is upper-cased on load. The project rule that all UI text is ALL CAPS post-dates the first builds, so older saves may contain lowercase strings; normalizing on load ensures every project displayed in the app conforms to the rule.

---

## 6. Settings as the only knob panel

`settings.py` is the single place every tunable lives. Each class groups one subsystem (`ScreenSettings`, `ComponentSettings`, `PortSettings`, `WireSettings`, `BankSettings`, ...). The rest of the codebase imports from here and never hard-codes a number.

This matters for two reasons:

1. **No magic numbers.** A reviewer reading rendering or interaction code never has to guess what `0.6` means; they look up the constant in `settings.py` and read the comment next to it.
2. **Designer-friendly.** Tuning feel — port hit-radius, wire thickness, bank padding, dialog width — is editing one file with comments next to each value, not hunting through implementation.

Adding a new tunable? Put it in `settings.py` with a comment explaining its **units** and what changing it does. UI display strings also live here (e.g. menu labels) so the ALL-CAPS rule is enforced in a single place.

---

## 7. Input model and accessibility

The simulator is **fully usable with the mouse alone**. Keyboard shortcuts (`Ctrl+Z`, `Ctrl+Y`, `N`, `T`, `F11`, menu mnemonics) exist as a power-user convenience. Any feature that introduces a keyboard-only path needs a parallel mouse path before it ships. This is a hard rule, not a preference: the simulator runs on classroom hardware where a small percentage of students cannot use modifier keys reliably.

The corollary: right-click delete is the single most failure-prone interaction on touchpads and Chromebooks. The Pass 2 roadmap's "trash mode" is the planned mouse-only delete path.

---

## 8. Code conventions worth knowing

Most rules live in [.github/copilot-instructions.md](../.github/copilot-instructions.md). Two are worth surfacing here because they shape how files **look**:

**Section banners.** Inside any file with multiple logical groupings, sections are separated by an all-caps banner comment:

```python
    # -------------------------
    # SECTION NAME
    # -------------------------
```

Match the indentation of the surrounding class body. Keep the dashes the same length and the name in ALL CAPS. The banner describes the role of the methods that follow.

**Function order inside a class.** Functions are grouped by role (setup, actions, rendering, etc.). `update` and `run` go **last** and should only call other functions on the class — they are coordinators, not implementations.

---

## 9. What's *not* here yet

The following systems will get their own sections in this document as they are built. If you are implementing one of these, please add the section as part of your pass:

- **Schema versioning + migration paths** for project save files (Pass 3).
- **Main menu** on startup, with NEW PROJECT / LOAD PROJECT / SETTINGS / ABOUT / QUIT and an app-level state machine that routes between the main menu and the workspace (Pass 3).
- **Tutorial system scaffold** with a launchable walkthrough (Pass 3 minimal, Pass 5+ content).
- **Truth-table auto-detect** ("YOU DISCOVERED NAND!") in the Save-as-Component flow (Pass 3).
- **Color picker** in the Save-as-Component dialog with hex / RGB entry (Pass 3).
- **Options page** (CRT toggle, font choice, background color, sound) (Pass 3).
- **Audio system** (Pass 7+).
- **Wire bending / waypoint editing** (Pass 7+).

See [docs/TODO.md](TODO.md) for the full pass-based roadmap.

---

## 10. Glossary

Terms used throughout this document and the rest of the project's docs.

- **Component** — any object on the workspace with one or more ports. NAND, Switch, LED, and any saved sub-circuit are all components.
- **DIAGRAMS scene** — the HELP > DIAGRAMS reference panel that shows NAND-only constructions of NOT, AND, OR, and De Morgan's laws. Owned by `DiagramViewerScene` (`ui/diagram_viewer.py`); content lives in `DiagramViewerSettings.DIAGRAM_ENTRIES`. The realised form of the original "Encyclopedia" roadmap item.
- **Embedded sub-circuit definition** — the rule that a `SavedComponent` carries its full internal definition with it, rather than referencing a shared library entry. Makes project files self-contained.
- **GameManager** — the orchestrator class in `main.py`. Owns lifecycle and dispatches to subsystems; never a feature container.
- **LED** — a workspace component that visually lights when its input is HIGH. The project's standard "did the signal reach this point?" indicator.
- **NAND** — the project's universal gate. The default behavior of `Component`. Every other gate the curriculum teaches is built from NAND.
- **Pass** — a single iteration through the codebase that touches the systems it needs to and leaves them more usable than before. Used instead of "phase" or "milestone" because there is no fixed deadline; the project cycles.
- **Port** — one input or output stub on a component, holding a single bit (`live = True` for HIGH, `False` for LOW).
- **Scene** — a top-level UI mode held by `GameManager._active_scene`. Currently `"workspace"` and `"diagrams"`. Scenes share the top menu bar but use different action maps; only one scene draws and handles events per frame.
- **SavedComponent** — a component built by the user from other components, packaged as a reusable black box and dropped back into the toolbox.
- **Switch** — a workspace component whose output is toggled by left-clicking it. The project's standard "user-controlled input."
- **Toolbox / Bank** — the bottom strip of templates the user drags into the workspace to spawn components. Owned by `ComponentBank` (`ui/bank.py`).
- **Two-phase propagation** — the rule in `SignalManager.update` that all gate outputs are computed into a buffer first and applied second, so feedback circuits (SR latches) evaluate consistently regardless of iteration order. See [section 3.2](#32-signalmanager--two-phase-propagation).
- **Wire** — a directed connection from one port (source) to another (target). Rendered as a polyline through optional waypoints.
- **Workspace** — the area between the top menu bar and the toolbox where the user builds circuits.
