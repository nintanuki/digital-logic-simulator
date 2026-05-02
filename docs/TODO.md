# Roadmap

Forward-looking task list for circuit-builder. Work is organized into
**Milestones** (numbered, dependency-ordered) followed by standalone
**Questions**, **Ideas**, **Issues / Bugs**, and **Polish & Tech Debt**
sections. Each milestone groups items that ship together and unblock the
next one. Items inside a milestone are roughly ordered top-to-bottom.

Before starting any item, read `docs/TESTING.md` (refactoring rules +
manual test checklist) and skim recent entries in `docs/CHANGELOG.md`.
Completed work is no longer mirrored here — the changelog is the single
source of truth for what has shipped.

**Design principle:** the program must be fully usable with the mouse
alone. Keyboard shortcuts are for power users and exist alongside, never
instead of, a clickable equivalent. Anything new that's only reachable by
hotkey is incomplete.

---

## Milestone 1 — Mouse-First Polish

Closing the last few gaps in the mouse-first contract before shifting to
new features. Small, high-leverage UX fixes.

- [ ] **Manual test the bottom-left popup menu.** Open the menu, click
  each item, confirm the popup closes and the action runs. Click outside
  — popup closes, no spurious wire/component side effects. Currently
  exercisable for QUIT (game quits) and the four disabled placeholders
  (click consumed, popup stays open, no side effect). The other four
  items become testable as their backing actions land in M2 / M3.
- [ ] **F11 needs a mouse path.** Fullscreen is keyboard-only today,
  which violates the mouse-first design principle. Add a clickable
  equivalent — most likely an entry on the bottom-left popup menu, or an
  icon on the future top hotkey-hint bar (M4).
- [ ] **Esc should not quit silently.** Currently Esc exits the game
  without warning, swallowing whatever the student was building. Layered
  behavior, in priority order:
  1. If a popup / dialog is open, Esc dismisses it. *(MenuButton popup
     case already landed; future dialogs reuse the same gate.)*
  2. Else if the game is fullscreen, Esc exits fullscreen (mirroring F11).
  3. Else Esc shows an in-game "Are you sure you want to quit?" confirm
     dialog. Only "Yes" actually quits.

---

## Milestone 2 — Persistence

Saving, loading, and the project-level shell that wraps them. Unblocks
Save-as-Component (M3): a saved component definition needs a project to
embed in, and a project needs an Options page to host the retro-mode
toggles already accumulating.

- [ ] **Save / load a project.** JSON file containing components (type,
  position, internal state e.g. Switch toggle), wires (source/target as
  `(component_id, port_name)` pairs), and text boxes (position + text).
  Pick a `schema_version` field early so future formats can migrate.
  **Important:** when Save-as-Component lands (M3), embed sub-circuit
  definitions inside the project save, don't reference them by name —
  otherwise sharing a project file breaks the moment the recipient is
  missing one of the saved components. **Also:** apply `.upper()` once to
  every text-box string when loading, so an old save file with lowercase
  characters comes back conformant to the uppercase rule (the rule is
  "text boxes are uppercase," not "new characters are uppercase").
- [ ] **Project main menu (program startup).** Before the workspace
  opens, show a menu screen with: **New Project**, **Load Project**,
  **Options**, **Quit**. Replaces the current "drop straight into the
  workspace" startup.
- [ ] **Options page.** Reachable from the main menu and (later) from
  the in-workspace popup menu. Settings already shaping up:
  - **CRT effect on/off.** Some students find scanlines distracting or
    hard on the eyes — keep the retro aesthetic available, not mandatory.
  - **Pixelated vs system font.** Same reasoning — the retro face is
    charming but harder to read than Arial. *Implementation note:* the
    pixelated face renders much larger than Arial at the same nominal
    size, so swapping fonts requires per-face size constants in
    `settings.py`, not one shared FONT_SIZE.
  - **Background color.** Pale blue (current), circuit-board green
    (cutting-mat aesthetic), or a small swatch the student picks.
  - **Sound effects on/off** (placeholder until audio lands; pairs with
    the Sound design item in Milestone 6).
  - See Questions section: "CRT + font: one toggle or two?"

---

## Milestone 3 — Save-as-Component (the keystone)

The pedagogical centerpiece. Lets students package a working circuit as
a reusable named component that drops back into the toolbox as a "black
box." Everything in M2 is a prerequisite — the saved component embeds
inside a project file.

- [ ] **Save as Component dialog.** Triggered from the bottom-left popup
  menu. Wraps the rest of the bullets below.
- [ ] **Pick external pins.** Designate which internal Switches become
  the new component's INPUT ports and which internal LEDs become its
  OUTPUT ports. Order on the body matches order picked.
- [ ] **Choose a color.** Default body color is the existing
  `MEDIUM_CARMINE`, but the save dialog should offer a small palette
  swatch AND/OR an RGB / hex entry field — the hex/RGB option is a
  deliberate teaching moment so students see how digital colors are
  encoded. Color saves into the component definition, not the project.
- [ ] **Rename + auto-detect known gates.** Default name is whatever the
  student typed in the dialog. **But:** if the saved component matches
  the truth table of a known gate (NOT, AND, OR, NAND, NOR, XOR, XNOR),
  the dialog pre-fills the recognized name as a reward for figuring it
  out. Student can override; this is a hint, not a lock. Pop a
  celebratory "You discovered <NAME>!" banner so the moment is named,
  not just silently auto-filled.
- [ ] **Detect known gates (mechanism).** Brute-force truth-table
  comparison on save. The space is small (≤4 inputs covers everything
  in this list) and the comparison runs once on save, not per frame.
- [ ] **Dynamic component sizing.** Once Save-as-Component starts
  producing components with more than the default 2 inputs / 1 output,
  their bodies need to grow tall enough to fit all ports without
  overlap. Pick a per-port vertical pitch and recompute height from
  `max(inputs, outputs) * pitch + padding`. Width can grow too if the
  name is wide, but height is the urgent one for port spacing.
- [ ] **Toolbox redesign for many components.** Once Save-as-Component
  lands, the bank will overflow. Decide approach (see Questions:
  "Toolbox-overflow approach"). Options on the table: horizontal scroll
  on the bank; shrink template icons + a "More..." popup; move the full
  library to the bottom-left menu and keep a smaller "favorites" row in
  the bank; vertical sidebar instead of bottom bar; categories with
  tabs (gates, latches, custom).

---

## Milestone 4 — Discoverability & Onboarding

Making the program teach itself. None of these are blocking, but they
compound the value of M3 by lowering the floor for new students.

- [ ] **Top hotkey-hint bar.** Old-school computer-program style: a thin
  bar across the top of the screen showing
  "F11 fullscreen | Esc back | ?: shortcuts | …". Mouse-first reachable
  summary so students don't need the docs to discover the keyboard path.
  Pairs with the Keyboard shortcut overlay idea below — pick one, or
  layer them, when the layout settles.
- [ ] **Easy mode.** Optional starter set: students begin with AND, OR,
  NOT, NAND already in the toolbox so they can build interesting
  circuits before they've finished the NAND-only progression. Off by
  default — the universal-NAND moment is the main pedagogical point.

---

## Milestone 5 — Curriculum Layer

The teach-with-it features. Built on top of Save-as-Component (truth-table
verification reuses the same machinery) and Persistence (puzzles ship as
project files).

- [ ] **Tutorials.** Interactive walkthroughs that introduce concepts in
  order: "wire a NAND so its output is HIGH," "build a NOT gate from a
  NAND," "build an AND gate from two NANDs." Each tutorial highlights
  the relevant toolbox template and verifies the truth table on
  completion.
- [ ] **Puzzles / challenges.** "Build an XOR gate using only NANDs in 5
  components or fewer." "Make an SR latch hold state." Auto-graded by
  truth-table comparison. Optional leaderboard / star rating per puzzle.
- [ ] **Encyclopedia / dictionary.** Built-in glossary students can flip
  open: each gate, each common circuit (latch, flip-flop, adder,
  multiplexer) with a short definition and a worked example. Pairs with
  tutorials and puzzles as a reference layer.

---

## Milestone 6 — Far Future

Stretch goals — explicitly not for the next several sessions, but worth
parking here so we don't lose them.

- [ ] **Component library sharing.** Export a saved component as a
  shareable file students can email or hand off. Pairs with the
  "embed-don't-reference" save-file decision in M2.
- [ ] **Sound design.** Subtle click on placement, faint hum on HIGH
  signal, a small "snap" when a wire commits. CRT scanlines already set
  the toy-computer mood; audio would land the rest of it. Pair with the
  Options sound-effects toggle in M2.
- [ ] **Multi-bit ports / busses.** Once students build a 4-bit adder
  they'll want a way to bundle four wires into one visual line. Big
  semantic lift; park until adders happen.

---

## Questions

Open design decisions that need an answer before (or as part of) the
work that depends on them. Promote into the relevant milestone once the
call is made.

- [ ] **CRT + font toggle: one switch or two?** Should "Pixelated font"
  and "CRT effect" become a single "Retro mode" master switch, or stay
  as two independent options? Decide before the Options page (M2) ships.
- [ ] **Toolbox-overflow approach.** Five candidates listed in M3
  ("Toolbox redesign for many components"). Pick one — or decide to
  layer two — once we have real data on how many components a typical
  session produces. Don't pre-build all five.
- [ ] **Lit wire color.** Currently green (matches `PORT_LIVE_COLOR`).
  Could go to amber, neon cyan, etc. — pick once we have the
  Save-as-Component palette work (M3) to compare against, so the live
  signal doesn't clash with the most popular custom-component colors.
- [ ] **Rename the program.** "Circuit Builder" is a misnomer — there's
  no analog circuitry, no resistors / capacitors. "Digital Logic
  Simulator" or "Logic Sandbox" reads more accurately. Promote when
  there's a candidate name we like.
- [ ] **Dynamic text-box width — wrap/width fixed point.** Width depends
  on the wrap, the wrap depends on the width. Resolve by either picking
  the longest unbroken line as the width seed, or iterating to a fixed
  point. Pick before the Idea below gets implemented.

---

## Ideas

Uncommitted designs that have a shape but no owner or milestone yet.
Promote into a milestone when the case for shipping is clear.

- [ ] **Dynamic text-box width.** Right now `TextBoxSettings.WIDTH` is
  fixed and the box wraps text into it. If a student types just "A" they
  get a wide box with one letter in it. Better: width = min(WIDTH,
  font.size(longest_line) + 2*PADDING). Probably keep MAX_WIDTH so a
  paragraph still wraps, but shrink for short labels. See Question above
  about the wrap/width fixed point.
- [ ] **IN / OUT visual redesign.** Both Switch and LED currently render
  as circles with different fill colors, which is confusing — they look
  like the same component in two states. Better:
  - **Switch** as a physical toggle: a rectangle with a sliding handle
    that visibly moves left/right (or up/down) when toggled, plus an
    ON/OFF label. Reads as "input you control."
  - **LED** as a bulb: circle with a base/lead silhouette so it reads as
    a bulb that's on or off. Maybe a halo/glow ring when HIGH.
- [ ] **Pin-to-toolbar for saved components.** Right-click a saved
  component in the menu library, "Pin to toolbar" / "Unpin." Solves the
  toolbox-overflow question without committing to scroll.
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
  hotkeys without the docs being mandatory. Might supersede or layer
  with the Top hotkey-hint bar in M4.

---

## Issues / Bugs

Bugs that affect behavior. Repro → fix → log in `docs/CHANGELOG.md` →
re-run the manual checklist in `docs/TESTING.md`.

- [ ] **Wires only go in a straight line, can't be bent or curved.** If
  a user wants to connect two components and there is another component
  between them, or they want to create a loop, the result is ugly
  straight lines crossing through other components. Possible approach:
  click waypoints during the wire drag to add bend points; delete a
  waypoint by right-clicking it. Overlaps visually with the
  toolbox-redesign discussion in M3 — both are about clarity in dense
  circuits.
- [ ] **Port highlighting is active inside the toolbox.** Hovering over
  the ports of a template in the toolbox lights them up as if they were
  in the workspace. Low priority; cosmetic only.
- [ ] **MENU button looks too similar to the TEXT template.** Both are
  small dark squares with a four-letter white label, so it's not obvious
  which is a control and which is a draggable component. Fix: give MENU
  a distinct treatment — a different color, an icon (≡ / ☰), or a
  different shape — so it reads as a control surface, not an element.
  Reported by user 2026-05-02.
- [ ] **Text inside components is not aligned or too large.** Text inside
  components needs to be vertically and horizontally centered. May need
  to be shrunk slightly — the word OUT barely fits inside the OUT
  component, and the circle can barely fit three letters. Text in IN and
  NAND are fine. Options: dynamic text size to fit inside the component,
  or resolve as part of the IN/OUT visual redesign idea above (which
  changes the body shape anyway).

---

## Polish & Tech Debt

Not bugs, just code-quality items worth fixing the next time the
surrounding code is touched.

- [ ] **Add a few unit tests for the logic-only modules.** Pygame is
  hard to test, but `signals.py`, `wires._is_valid`, and `Wire.hit` are
  pure Python and trivial to cover. Three tests would catch the next
  signal refactor: NAND truth table, wire validation rejects
  same-direction / same-parent, and an SR latch built in code holds
  state across two `SignalManager.update` calls.
- [ ] **Wrap the per-frame loop in a top-level try/except** that
  flashes a banner and keeps the app alive. Crashes mid-class are the
  worst possible UX.
