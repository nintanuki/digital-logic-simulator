# Roadmap

A handoff-friendly task list for circuit-builder. Items are roughly ordered:
do **Now** first, then **Next**, then **Later**, then **Brainstorming**
(design ideas not yet committed to a path), then **Far future** (the
big-picture stretch goals). Each task lists the smallest concrete steps so
the work can be resumed in a fresh session without rebuilding context.
Known bugs live in **Known Issues** at the bottom.

Before starting any item, read `docs/TESTING.md` (refactoring rules + manual
test checklist) and skim recent entries in `docs/CHANGELOG.md`.

**Design principle:** the program must be fully usable with the mouse alone.
Keyboard shortcuts are for power users and exist alongside, never instead
of, a clickable equivalent. Anything new that's only reachable by hotkey is
incomplete.

---

## Now — Bottom-left popup menu (file ops)

Once Save / Load / New Component / Save-as-Component arrive, the toolbar
will have nowhere to put them. Add a Windows-style **MENU** button in the
bottom-left corner of the bank. Clicking it pops up a vertical menu.

- [x] **Visual slot.** New class `MenuButton` in `ui.py` next to
  `TextTemplate`, rendered inside the bank rect at the far left.
  `ComponentBank` owns it as `self.menu_button` and the template row
  anchors its starting x to `menu_button.rect.right` so layout stays
  consistent if MENU's size changes.
- [x] **Click toggles the popup container.** Clicking MENU toggles
  `MenuButton.is_open`; `draw()` paints a placeholder popup body above
  the button while open. `ComponentBank.handle_event` routes the click
  before the template loop. Items inside the popup are still TODO.
- [x] **Esc dismisses the popup.** `GameManager._handle_keydown` checks
  `self.bank.menu_button.is_open` before treating Esc as quit. Mirrors
  the text-box manager pattern (Esc unfocuses the editor) so Esc never
  leaks through an active UI layer to quit the game.
- [x] **Click outside the popup closes it.** *Done 2026-05-02*: a
  left-click that lands outside `popup_rect` while the popup is open
  toggles it closed. Implemented in `ComponentBank.handle_event` between
  the menu-button check and the template loop; the dismiss does not
  consume the event so a stray miss still falls through to the template
  loop / wires / empty space (no penalty click). The matching
  intercept-before-wires step still owes us the case where the click
  lands on a port that's drawn under the popup body — see the bullet
  below.
- [x] **Populate the popup with items.** *Done 2026-05-02:* the five
  labels (NEW PROJECT, LOAD PROJECT, SAVE PROJECT, SAVE AS COMPONENT,
  QUIT) render top-to-bottom in the popup. Each owns a vertical
  ITEM_HEIGHT band as its hit-rect (`MenuButton._item_rects`); enabled
  items render in `ITEM_ENABLED_COLOR` (white) and disabled items in
  `ITEM_DISABLED_COLOR` (grey). Today only QUIT is enabled — the other
  four wait on Save / Load / Save-as-Component in **Later**.
- [x] **Clicking an item runs its action and closes the popup.** *Done
  2026-05-02:* `ComponentBank.handle_event`'s popup-body branch calls
  `MenuButton.item_label_at(pos)` to identify the clicked item, looks
  the label up in the `menu_actions` dict GameManager passed in, and on
  hit closes the popup *before* running the callback (so a callback
  like `close_game` that tears pygame down sees a consistent state).
  Disabled items consume the click but neither run nor dismiss — a
  misclick on a placeholder doesn't lose the menu. QUIT is wired to
  `GameManager.close_game`, which gives the program its first mouse
  path to quit (relevant to the F11/Esc consolidation in **Next**).
- [x] **Popup intercepts events before wires/components.** *Done
  2026-05-02:* two-step landing. (1) `ComponentBank.handle_event`
  consumes (`return True`) any click that lands on the popup body while
  the menu is open, so the click can no longer fall through to the
  template loop. (2) `GameManager._handle_mouse` now early-intercepts
  any `MOUSEBUTTONDOWN` on the popup body (when the menu is open) and
  routes it to `bank.handle_event` before `wires.handle_event` runs,
  mirroring the text-box manager's pre-emption in `_process_events`.
  Net effect: a port that happens to sit under the popup body cannot
  start a wire, and right-clicks on the popup body no longer fall
  through to wire/component delete. The early intercept only fires when
  the popup is actually open AND the click lands on the popup body, so
  every other mouse flow (MENU-button clicks, click-outside dismiss,
  template clicks, wires, component drags) is unchanged.
- [ ] **Manual test.** Open the menu, click each item, confirm the popup
  closes and the action runs. Click outside — popup closes, no spurious
  wire/component side effects. *(Now exercisable for QUIT (game quits)
  and the four disabled placeholders (click consumed, popup stays open,
  no side effect). The other four items become testable as their backing
  actions land in **Later**.)*

---

## Next — F11 / Esc consolidation

Two related mouse-first gaps reported alongside the popup-menu work.
Implement after the popup menu so the dismiss step can share the same
dispatch.

- [ ] **F11 needs a mouse path.** Fullscreen is keyboard-only today,
  which violates the mouse-first design principle. Add a clickable
  equivalent — most likely a menu item once the bottom-left popup
  populates, or an icon on a future top hotkey-hint bar.
- [ ] **Esc should not quit silently.** Currently Esc exits the game
  without warning, swallowing whatever the student was building. Layered
  behavior:
  1. If a popup / dialog is open, Esc dismisses it. *(MenuButton popup
     case landed 2026-05-02; future dialogs reuse the same gate.)*
  2. Else if the game is fullscreen, Esc exits fullscreen (mirroring F11).
  3. Else Esc shows an in-game "Are you sure you want to quit?" confirm
     dialog. Only "Yes" actually quits.

---

## Done — Toolbar TEXT button (2026-05-02)

Right now a text box can only be spawned by pressing **T**. The classroom
target is mouse-only, so it also needs a clickable template on the bank
alongside Switch / NAND / LED.

- [x] Add a new toolbox template that reads "TEXT" centered on its body.
  Square is fine (matches Switch/LED size); it's a label, not a circuit
  element, so no ports.
- [x] In `ui.py::ComponentBank`, special-case it: clicking the template
  spawns a `TextBox` (not a `Component` subclass), so add a small adapter
  rather than shoving TextBox into `TEMPLATE_CLASSES`. Option 1 picked —
  the bank now stores `(template_drawable, spawn_fn)` pairs and the TEXT
  spawner closes over the `TextBoxManager` passed into the bank at
  construction time, so adding a non-Component spawnable was a one-line
  append in `_build_templates`.
- [x] Spawned `TextBox` should immediately focus so the student can start
  typing without an extra click. (Free — `TextBoxManager.spawn_at` already
  focused; the new spawn closure just calls it.)
- [x] Update the **N** / **T** hotkeys in `main.py::_handle_keydown` to
  call the same spawn paths the bank uses, not duplicate them. Keeps the
  two entry points honest. **N** now routes through a new public
  `ComponentBank.spawn_component(cls, pos, components_list)` that delegates
  to the same closure a toolbox click runs (cursor-centered, drag primed,
  `_moved_while_dragging` set), so a NAND from the keyboard now follows
  the cursor exactly like a NAND from the bank. **T** was already calling
  `text_boxes.spawn_at(...)` — the same line the bank's text spawner
  calls — so it stayed direct rather than threading a passthrough through
  the bank (would have added a middleman, not removed duplication).
- [X] Manual test: click the TEXT template, drag a box onto the workspace,
  type, drop. Then keyboard-spawn another with **T**. Both work the same.

---

## Done — Force uppercase in text boxes (2026-05-02)

- [x] In `text_boxes.py::TextBox.handle_key`, uppercase `event.unicode`
  before appending. `str.upper()` on a single character is safe for ASCII
  and a no-op for symbols.
- [X] Manual test: pressing 'a' shows 'A'. Pressing Shift+'a' also shows
  'A' (no double-shift glitch). Numbers and symbols pass through unchanged.
  *(needs a human at a keyboard)*

The "uppercase existing text loaded from a save" half of this decision is
now parked under the Save/Load bullet in **Later** — there is no loader to
hook into yet, but the rule ("text boxes are uppercase," not "new
characters are uppercase") is recorded so it isn't lost.

---

## Done — Live signal state (2026-05-02)

- [x] Add `self.live = False` to `Port`. Add `PORT_LIVE_COLOR` to settings.
- [x] Each frame, propagate signals: for each gate, compute `output = NOT (A.live AND B.live)`; for each wire, copy `source.live` to `target.live`. *(Implemented in `signals.py::SignalManager.update`. NAND logic lives on `Component.update_logic` (default 2-input NAND); subclasses override.)*
- [x] Use a two-phase update (read all inputs into a temp buffer, then write all outputs) so SR latches and other feedback circuits behave. *(Phase 1 reads inputs into `output_buffer`. Phase 2 writes buttons to ports. Phase 3 resets every INPUT to LOW then propagates `wire.target.live = wire.source.live`, so a disconnected input falls back to LOW instead of latching.)*
- [x] ~~Click an unconnected input port to toggle it manually...~~ Replaced per the user's note in the same bullet: dedicated `Switch` and `LED` components, both circles for now. Switch has one OUTPUT port and toggles on a stationary click; LED has one INPUT port and lights up green when HIGH. Both spawn from the toolbox alongside NAND.
- [X] Manual test: a single NAND with both inputs HIGH outputs LOW; with either input LOW outputs HIGH. An SR latch built from two NANDs holds state. *(needs a human at a keyboard)*

---

## Done — Text boxes (2026-05-02)

Free-floating annotation labels students can drop on the workspace to
explain their circuits. No signal, no port, never on the toolbox bank.

- [x] New `TextBox` class in `text_boxes.py`. Owns a rect, the editable
  string, focus + drag state, and a cached wrap. Width is fixed
  (`TextBoxSettings.WIDTH`); height grows downward as the wrap needs
  more lines, never below `MIN_HEIGHT`. Caret blinks at the end of the
  text while focused.
- [x] `TextBoxManager` (separate class — focus + multi-box stack grew
  enough state to deserve one). GameManager owns it as `self.text_boxes`.
- [x] Spawn shortcut: press **T** to drop a text box at the cursor and
  immediately focus it. Mirrors the existing **N** = NAND pattern.
- [x] Manager intercepts events before wires/bank/components: KEYDOWN
  while a box is focused goes to the box (so typing 'n' doesn't spawn a
  NAND), left-click on a box focuses + starts drag, click on empty space
  blurs (without consuming, so wires still work), Esc unfocuses,
  right-click on a box deletes.
- [x] Word-wrap honors explicit `\n` line breaks first, then greedy-wraps
  paragraphs word by word, then force-breaks single words wider than the
  inner width so nothing overflows.
- [x] Drag is clamped to the workspace (above the toolbox bank) the same
  way `Component._clamp_to_workspace` does it, including a re-clamp after
  a keystroke grows the box.
- [X] Manual test: press T, type a multi-line label, drag it around, and
  drop a NAND on top to confirm wires under it still work when the label
  is moved aside. *(needs a human at a keyboard)*

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

## Done — Port hover labels (2026-05-01)

- [x] Add `PORT_LABEL_COLOR`, `PORT_LABEL_FONT_SIZE`, and `PORT_LABEL_OFFSET` to `ComponentSettings`.
- [x] Cache one `pygame.font.Font` for port labels at the `GameManager` level. *(Implemented as a dedicated `Fonts` class — exposes `Fonts.component_label` and `Fonts.port_label`, init'd once at boot.)*
- [x] Split out `Port.draw_label`. INPUT anchors right (label sits to the left of the port), OUTPUT anchors left. Called from Component.draw after the body so labels stay on top.
- [X] Manual test: hover each port on a NAND, see "A", "B", "OUT". *(needs a human at a keyboard)*

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

## Later

Bigger features, in roughly the order they unlock student workflows.

- [ ] **Save / load a project.** JSON file containing components (type,
  position, internal state e.g. Switch toggle), wires (source/target as
  `(component_id, port_name)` pairs), and text boxes (position + text).
  Pick a `schema_version` field early so future formats can migrate.
  **Important:** when Save-as-Component lands, embed sub-circuit
  definitions inside the project save, don't reference them by name —
  otherwise sharing a project file breaks the moment the recipient is
  missing one of the saved components. **Also:** apply `.upper()` once to
  every text-box string when loading, so an old save file with lowercase
  characters comes back conformant to the uppercase rule (the rule is
  "text boxes are uppercase," not "new characters are uppercase").
- [ ] **Project main menu (program startup).** Before the workspace opens,
  show a menu screen with: **New Project**, **Load Project**, **Options**,
  **Quit**. Replaces the current "drop straight into the workspace"
  startup. **Options** items already shaping up — carry these into the
  Options page once the main menu lands:
  - **CRT effect on/off.** Some students find scanlines distracting or
    hard on the eyes — keep the retro aesthetic available, not mandatory.
  - **Pixelated vs system font.** Same reasoning — the retro face is
    charming but harder to read than Arial. *Implementation note:* the
    pixelated face renders much larger than Arial at the same nominal
    size, so swapping fonts requires per-face size constants in
    `settings.py`, not one shared FONT_SIZE.
  - **Decide whether CRT + font toggle together** as one "retro mode"
    switch, or as two independent options. Tracking under one bullet so
    the call gets made before either ships.
  - **Background color.** Pale blue (current), circuit-board green
    (cutting-mat aesthetic), or a small swatch the student picks.
  - **Sound effects on/off** (placeholder until audio lands; pairs with
    the Sound design item in **Far future**).
- [ ] **Save as Component** (the keystone feature). Package the current
  workspace as a reusable named component that drops into the toolbox as a
  new template — a "black box" abstraction. Sub-features:
  - [ ] **Pick external pins.** Designate which internal Switches become
    the new component's INPUT ports and which internal LEDs become its
    OUTPUT ports. Order on the body matches order picked.
  - [ ] **Choose a color.** Default body color is the existing
    `MEDIUM_CARMINE`, but the save dialog should offer a small palette
    swatch AND/OR an RGB / hex entry field — the hex/RGB option is a
    deliberate teaching moment so students see how digital colors are
    encoded. Color saves into the component definition, not the project.
  - [ ] **Rename.** Default name is whatever the student typed in the
    "Save as..." dialog. **But:** if the saved component happens to match
    the truth table of a known gate (NOT, AND, OR, NAND, NOR, XOR, XNOR),
    the dialog pre-fills the recognized name as a reward for figuring it
    out. Student can override; this is a hint, not a lock. Pop a
    celebratory "You discovered <NAME>!" banner so the moment is named,
    not just silently auto-filled.
  - [ ] **Detect known gates.** Brute-force truth-table comparison on
    save. The space is small (≤4 inputs covers everything in this list)
    and the comparison runs once on save, not per frame.
- [ ] **Dynamic component sizing.** Once Save-as-Component starts
  producing components with more than the default 2 inputs / 1 output,
  their bodies need to grow tall enough to fit all ports without overlap.
  Pick a per-port vertical pitch and recompute height from
  `max(inputs, outputs) * pitch + padding`. Width can grow too if the
  name is wide, but height is the urgent one for port spacing.
- [ ] **Toolbox redesign for many components.** Once Save-as-Component
  lands, the bank will overflow. Brainstorming options:
  - Horizontal scroll on the bank.
  - Shrink template icons + overflow into a "More..." popup.
  - Move the full library to the bottom-left menu and keep a smaller
    "favorites" row in the bank that students pin items into.
  - Vertical sidebar instead of bottom bar for more real estate.
  - Categories with tabs (gates, latches, custom).

  Pick after we have real data on how many components a typical session
  produces.
- [ ] **Top hotkey-hint bar.** Old-school computer-program style: a thin
  bar across the top of the screen showing
  "F11 fullscreen | Esc back | ?: shortcuts | …". Mouse-first reachable
  summary so students don't need the docs to discover the keyboard path.
  Pairs with the **Keyboard shortcut overlay** Brainstorming entry below
  — pick one, or layer them, when the layout settles.
- [ ] **Easy mode.** Optional starter set: students begin with AND, OR,
  NOT, NAND already in the toolbox so they can build interesting
  circuits before they've finished the NAND-only progression. Off by
  default — the universal-NAND moment is the main pedagogical point.

---

## Brainstorming

Design ideas not yet committed to a path. Promote into Later when the
shape is clearer.

- [ ] **Dynamic text-box width.** Right now `TextBoxSettings.WIDTH` is
  fixed and the box wraps text into it. If a student types just "A" they
  get a wide box with one letter in it. Better: width = min(WIDTH,
  font.size(longest_line) + 2*PADDING). Tricky parts: the wrap depends on
  width, width depends on the wrap → either pick longest unbroken line or
  iterate to a fixed point. Probably keep MAX_WIDTH so a paragraph still
  wraps, but shrink for short labels.
- [ ] **IN / OUT visual redesign.** Both Switch and LED currently render
  as circles with different fill colors, which is confusing — they look
  like the same component in two states. Better:
  - **Switch** as a physical toggle: a rectangle with a sliding handle
    that visibly moves left/right (or up/down) when toggled, plus a
    ON/OFF label. Reads as "input you control."
  - **LED** as a bulb: circle with a base/lead silhouette so it reads as
    a bulb that's on or off. Maybe a halo/glow ring when HIGH.
- [ ] **Pin-to-toolbar for saved components.** Right-click a saved
  component in the menu library, "Pin to toolbar" / "Unpin." Solves the
  toolbox-overflow question without committing to scroll.
- [ ] **Wire bending / segments.** Already in Known Issues — restating
  here for visibility because it overlaps with the toolbox-redesign
  discussion (both are about visual clarity in dense circuits). Possible
  approach: click waypoints during the wire drag to add bend points;
  delete a waypoint by right-clicking it.
- [ ] **Undo / redo.** Students will lose work to accidental deletes.
  Even a 10-step undo would absorb most of the pain. Cleanest model:
  every mutating action (place, delete, wire, unwire, edit text) routes
  through a Command object with a `do()` and `undo()`. Manager pushes to
  a deque, Ctrl+Z pops.
- [ ] **Trash mode / delete button.** Right-click on a touchpad
  (Chromebook, single-button mouse) is hard for kids. Optional toolbar
  trash icon that puts the cursor into "delete mode" until the next
  click would be more discoverable.
- [ ] **Keyboard shortcut overlay.** Press `?` to flash a translucent
  cheat-sheet of every shortcut. Lets the keyboard-curious discover the
  hotkeys without the docs being mandatory.
- [ ] **Lit wire color.** Currently green (matches `PORT_LIVE_COLOR`).
  Could go to amber, neon cyan, etc. — pick once we have the
  Save-as-Component palette work to compare against, so the live signal
  doesn't clash with the most popular custom-component colors.
- [ ] **Rename the program.** "Circuit Builder" is a misnomer — there's
  no analog circuitry, no resistors / capacitors. "Digital Logic
  Simulator" or "Logic Sandbox" reads more accurately. Promote when
  there's a candidate name we like.

---

## Far future

Stretch goals — explicitly not for the next few sessions, but worth
parking here so we don't lose them.

- [ ] **Tutorials.** Interactive walkthroughs that introduce concepts in
  order: "wire a NAND so its output is HIGH," "build a NOT gate from a
  NAND," "build an AND gate from two NANDs." Each tutorial highlights
  the relevant toolbox template and verifies the truth table on
  completion.
- [ ] **Puzzles / challenges.** "Build an XOR gate using only NANDs in 5
  components or fewer." "Make an SR latch hold state." Auto-graded by
  truth-table comparison. Optional leaderboard / star rating per puzzle.
- [ ] **Component library sharing.** Export a saved component as a
  shareable file students can email or hand off. Pairs with the
  "embed-don't-reference" save-file decision above.
- [ ] **Sound design.** Subtle click on placement, faint hum on HIGH
  signal, a small "snap" when a wire commits. CRT scanlines already set
  the toy-computer mood; audio would land the rest of it. Pair with an
  **Options toggle** (see the Project main menu Later bullet) so users
  who don't want sound can turn it off.
- [ ] **Multi-bit ports / busses.** Once students build a 4-bit adder
  they'll want a way to bundle four wires into one visual line. Big
  semantic lift; park until adders happen.
- [ ] **Encyclopedia / dictionary.** Built-in glossary students can flip
  open: each gate, each common circuit (latch, flip-flop, adder,
  multiplexer) with a short definition and a worked example. Pairs with
  tutorials and puzzles as a reference layer.

---

## Polish / tech debt

Not bugs, just code-quality items worth fixing the next time the surrounding
code is touched.

- [ ] **Add a few unit tests for the logic-only modules.** Pygame is hard
  to test, but `signals.py`, `wires._is_valid`, and `Wire.hit` are pure
  Python and trivial to cover. Three tests would catch the next signal
  refactor: NAND truth table, wire validation rejects same-direction /
  same-parent, and an SR latch built in code holds state across two
  `SignalManager.update` calls.
- [ ] **Wrap the per-frame loop in a top-level try/except** that flashes
  a banner and keeps the app alive. Crashes mid-class are the worst
  possible UX.

---

## Known issues

Bugs that affect behavior. Repro → fix → log in `docs/CHANGELOG.md` → re-run
the manual checklist in `docs/TESTING.md`.

- [ ] **Wires only go in a straight line, can't be bent or curved.** Right now if a user wants to connect two components and there is another component between them, or they want to create a loop, this results in ugly straight lines everywhere. Perhaps allow them to create the wire in "segments" — see Brainstorming entry above for a sketch.
- [ ] **Port highlighting is active inside the toolbox.** When hovering over the ports of a component in the toolbox, port highlighting works as if it was in the workspace. Low priority.
- [ ] **MENU button looks too similar to the TEXT template.** Both are
  small dark squares with a four-letter white label, so it's not obvious
  which is a control and which is a draggable component. Fix: give MENU
  a distinct treatment — a different color, an icon (≡ / ☰), or a
  different shape — so it reads as a control surface, not an element.
  Reported by user 2026-05-02.
- [ ] **Text inside components is not aligned or too large.** Text inside components need to be vertically and horizontally centered. Might be to be shrunk slightly as the word OUT barely fits insoude the OUT component. But text in IN and NAND are good and readable. Problem is the circle can barely fit three letters. Can the text size be dynamic to fit inside the component? Or can we resolve this when we change the shape and look of the INPUT switches and OUTPUT LEDs?