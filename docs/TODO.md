# Roadmap

Forward-looking task list for circuit-builder, organized into **Passes**.
Each pass leaves the codebase more usable than the last. The project is "useful"
after Pass 1, "presentable" after Pass 2, "shareable" after Pass 4. No deadline.

Before starting any item, read `docs/TESTING.md` and skim recent entries in
`docs/CHANGELOG.md`. Full descriptions of completed work live in the changelog.

**Design principle:** fully usable with the mouse alone. Keyboard shortcuts exist
alongside, never instead of, a clickable equivalent.

**The selling point:** the abstraction loop � build a circuit, save it as a named
component, drop it into the next circuit as a black box, save that, and repeat.

---

## Pass 1 � Spine (the abstraction loop, rough)

Get the core teaching loop working end-to-end, rough as needed. By the end a
student can build NOT, AND, OR, XOR, and SR latch from NANDs � each saved and
reusable. **In-session only** � closing the program loses everything. Deliberate.

- [x] **Save-as-Component dialog.**
- [x] **Saved component appears as a new template in the toolbox.**
- [x] **Spawning a saved component creates a working component.**
- [x] **Dynamic component sizing.**

---

## Pass 2 � Polish the spine

Fix things a student would notice in five seconds. Add the safety net.

- [x] **Undo / redo.** Ctrl+Z / Ctrl+Y. Six command types in `commands.py`.
- [x] **Switch / LED visual redesign.** Switch = sliding toggle. LED = bulb silhouette.
- [x] **Random color for saved components.** 8-color curated palette in `ColorSettings`.
- [x] **Wrap the per-frame loop in a try/except** that flashes a banner and keeps
  the app alive on unhandled exceptions.
- [ ] **Esc should not quit silently.** Layered behavior, in priority
  order:
  1. If a popup / dialog is open, Esc dismisses it. *(MenuButton popup
     case already landed; future dialogs reuse the same gate.)*
  2. Else if the game is fullscreen, Esc exits fullscreen (mirroring F11).
  3. Else Esc shows an in-game "Are you sure you want to quit?" confirm
     dialog. Only "Yes" actually quits.
- [ ] **Fix MENU button vs TEXT template visual confusion.** Both are
  small dark squares with a four-letter white label, so it's not obvious
  which is a control and which is a draggable component. Give MENU a
  distinct treatment � different color, a `=` / `?` icon, or a
  different shape � so it reads as a control surface, not an element.
- [ ] **F11 needs a mouse path.** Fullscreen is keyboard-only today.
  Most likely answer: an entry on the bottom-left popup menu. (A future
  top hotkey-hint bar in Pass 6 will add a second mouse path.)
- [ ] **Trash mode / delete button.** Right-click on a touchpad
  (Chromebook, single-button mouse) is hard for kids. Optional toolbar
  trash icon that puts the cursor into "delete mode" until the next
  click. Combined with undo/redo above, this gives mouse-only students
  a complete safe-delete workflow. **Check classroom hardware before
  building** � see Risks & Notes.
- [ ] **Manual test the bottom-left popup menu.** Open the menu, click
  each item, confirm the popup closes and the action runs. Click outside
  � popup closes, no spurious wire/component side effects. (Carried
  over from Pass 1; testable end-to-end once SAVE AS COMPONENT is wired
  up and the other items get their backing actions in Pass 3.)

---

## Pass 3 � Persistence

Disk save/load so work survives across sessions and machines.

- [ ] **Save / load a project (disk).** JSON file containing components
  (type, position, internal state e.g. Switch toggle), wires
  (source/target as `(component_id, port_name)` pairs), text boxes
  (position + text), and the embedded definitions of every saved
  sub-component. **Schema version field from day one** so future formats
  can migrate cleanly. **Embed don't reference** � sub-circuit
  definitions live inside the project save, otherwise sharing a project
  breaks the moment the recipient is missing one of the saved
  components. **Apply `.upper()` once to every text-box string when
  loading**, so an old save with lowercase characters comes back
  conformant to the uppercase rule.
- [ ] **Project main menu (program startup).** Before the workspace
  opens, show a menu screen with: **New Project**, **Load Project**,
  **Options**, **Quit**. Replaces the current "drop straight into the
  workspace" startup.
- [ ] **Options page.** Reachable from the main menu and from the
  in-workspace popup menu.
  - **CRT effect on/off.**
  - **Pixelated vs system font.** *Implementation note:* the pixelated
    face renders much larger than Arial at the same nominal size, so
    swapping fonts requires per-face size constants in `settings.py`,
    not one shared `FONT_SIZE`. Worth refactoring `Fonts` to take a
    target pixel-height and pick the size for each face that hits it
    (see Risks & Notes).
  - **Background color.** Pale blue (current), circuit-board green
    (cutting-mat aesthetic), or a small swatch the student picks.
  - **Sound effects on/off** (placeholder until audio lands in Pass 7+).
  - See Questions: "CRT + font: one toggle or two?"
- [ ] **Truth-table auto-detect ("you discovered NAND!").** When the
  student saves a component, brute-force compare its truth table against
  the known gates (NOT, AND, OR, NAND, NOR, XOR, XNOR). If a match, the
  dialog pre-fills the recognized name and pops a "You discovered
  <NAME>!" banner. Student can override; this is a hint, not a lock.
  Cheap to compute � =4 inputs covers the entire list, and the check
  runs once on save, not per frame.
- [ ] **Color picker for saved components.** The save dialog grows a
  color picker. Small palette swatch AND/OR an RGB / hex entry field �
  the hex/RGB option is a deliberate teaching moment so students see how
  digital colors are encoded. Color saves into the component definition,
  not the project.
- [ ] **Rename the program.** "Circuit Builder" is a misnomer � there's
  no analog circuitry. Pick a name (see Questions) and migrate before
  Pass 3 ships, so save files reference the new name from day one.

---

## Pass 4 � Polish persistence

Make the persistence layer robust enough to share with other CS
teachers, not just survive a single classroom.

- [ ] **Schema migration paths.** Each version bump gets a migration
  function that loads the old format and produces the new one. Refuse to
  load a future-version file with a clear error rather than guessing.
- [ ] **Error recovery for malformed save files.** A truncated or
  hand-edited save shouldn't crash the program � it should fall back to
  an empty workspace with a banner explaining what went wrong.
- [ ] **Toolbox redesign for many components.** By Pass 4 the bank will
  overflow with saved components. Decide approach (see Questions:
  "Toolbox-overflow approach"). Candidates: horizontal scroll on the
  bank; shrink template icons + a "More..." popup; move the full library
  to the bottom-left menu and keep a smaller "favorites" row in the
  bank; vertical sidebar instead of bottom bar; categories with tabs
  (gates, latches, custom).
- [ ] **Pin-to-toolbar for saved components.** Right-click a saved
  component in the menu library, "Pin to toolbar" / "Unpin." A natural
  fit if the toolbox-overflow answer is "library + favorites row."
- [ ] **Lit wire color decision.** Currently green. Now that
  Save-as-Component palettes exist and we can see what colors students
  actually pick, decide whether green stays or moves to amber / cyan.
  See Questions.

---

## Pass 5 � Curriculum (rough)

The teach-with-it features. Built on top of Save-as-Component (truth-
table verification reuses Pass 3's machinery) and Persistence (puzzles
ship as project files).

- [ ] **Tutorials.** Interactive walkthroughs that introduce concepts in
  order: "wire a NAND so its output is HIGH," "build a NOT gate from a
  NAND," "build an AND gate from two NANDs." Each tutorial highlights
  the relevant toolbox template and verifies the truth table on
  completion.
- [ ] **Puzzles / challenges.** "Build an XOR gate using only NANDs in 5
  components or fewer." "Make an SR latch hold state." Auto-graded by
  truth-table comparison. Optional leaderboard / star rating per puzzle.

---

## Pass 6 � Polish curriculum + discoverability

Make the program teach itself. Smooths the rough Pass-5 lessons and
adds the surfaces that lower the floor for a cold-start student.

- [x] **Top hotkey-hint bar.** Always-on strip showing keyboard shortcuts.
- [ ] **Keyboard shortcut overlay.** Press `?` to flash a translucent
  cheat-sheet of every shortcut. Layers with the hint bar above � bar
  is always-on, overlay is on-demand and exhaustive.
- [ ] **Easy mode.** Optional starter set: students begin with AND,
  OR, NOT, NAND already in the toolbox so they can build interesting
  circuits before they've finished the NAND-only progression. Off by
  default � the universal-NAND moment is the main pedagogical point.
- [ ] **Encyclopedia / dictionary.** Built-in glossary students can
  flip open: each gate, each common circuit (latch, flip-flop, adder,
  multiplexer) with a short definition and a worked example.

---

## Pass 7+ � Treats

Stretch goals. Take them in any order, or not at all. None of these
strengthen the abstraction loop � they decorate it.

- [ ] **Sound design.** Subtle click on placement, faint hum on HIGH
  signal, a small "snap" when a wire commits. CRT scanlines already
  set the toy-computer mood; audio would land the rest of it. Pair
  with the Options sound-effects toggle.
- [ ] **Multi-bit ports / busses.** Once students build a 4-bit adder
  they'll want a way to bundle four wires into one visual line. Big
  semantic lift; park until adders happen.
- [ ] **Component library sharing.** Export a saved component as a
  shareable file students can email or hand off. Pairs with the
  embed-don't-reference save-file decision in Pass 3.
- [ ] **Wire bending / segments.** Already in Issues / Bugs as the
  underlying complaint. Promote here as the proposed fix when ready �
  click waypoints during the wire drag to add bend points; delete a
  waypoint by right-clicking it.
- [ ] **Dynamic text-box width.** Right now `TextBoxSettings.WIDTH` is
  fixed and the box wraps text into it. Better: width = min(WIDTH,
  font.size(longest_line) + 2*PADDING). See Questions for the
  wrap/width fixed-point question.

---

## Questions

Open design decisions that need an answer before (or as part of) the
work that depends on them. Promote into the relevant pass once the
call is made.

- [ ] **CRT + font toggle: one switch or two?** Should "Pixelated font"
  and "CRT effect" become a single "Retro mode" master switch, or stay
  as two independent options? Decide before Pass 3's Options page.
- [ ] **Toolbox-overflow approach.** Five candidates listed in Pass 4.
  Pick one � or decide to layer two � once we have real data on how
  many components a typical session produces. Don't pre-build all five.
- [ ] **Lit wire color.** Currently green (matches `PORT_LIVE_COLOR`).
  Could go to amber, neon cyan, etc. Decide alongside Pass 4 once the
  Save-as-Component palette work has produced real data.
- [ ] **Rename the program.** "Circuit Builder" is a misnomer.
  Candidates so far: "Digital Logic Simulator," "Logic Sandbox," "Logic
  Bench," "NAND Lab." Pick before Pass 3 so save files reference the
  new name from day one.
- [ ] **Dynamic text-box width � wrap/width fixed point.** Width
  depends on the wrap, the wrap depends on the width. Resolve by either
  picking the longest unbroken line as the width seed, or iterating to
  a fixed point. Pick before the Pass-7+ idea gets implemented.

---

## Ideas

*(Promote ideas here if their case for shipping weakens, or add new ones.)*

---

## Issues / Bugs

- [x] **User must click the name field to start typing** in the save dialog.
- [ ] **Wires only go in a straight line, can't be bent or curved.** If
  a user wants to connect two components and there is another component
  between them, or they want to create a loop, the result is ugly
  straight lines crossing through other components. Proposed fix lives
  under Pass 7+ ("Wire bending / segments").
- [ ] **Port highlighting is active inside the toolbox.** Hovering over
  the ports of a template in the toolbox lights them up as if they
  were in the workspace. Low priority; cosmetic only.
- [ ] **MENU button looks too similar to the TEXT template.** Now
  scheduled as a Pass 2 polish item; entry kept here for repro
  reference until it ships.
- [ ] **Text inside components is not aligned or too large.** Now
  scheduled as a Pass 2 polish item; entry kept here for repro
  reference until it ships.

---

## Risks & Notes

Re-read at the start of each pass.

- [ ] **Classroom hardware = touchpads?** If the target machines are
  Chromebooks or laptops without a real two-button mouse, right-click
  delete is hard for kids and the program currently has no other path
  to delete a wire or text box. "Trash mode" is in Pass 2 because of
  this � but verify the hardware reality before Pass 1 ships, because
  it might bump trash mode earlier.
- [ ] **Save-as-Component is the keystone risk.** Three things have to
  be true at once for Pass 1 to feel right: (1) the embedded sub-
  circuit definition has to round-trip cleanly through spawn, (2)
  dynamic component sizing has to handle =3 inputs without overlap,
  (3) the saved component has to be visually distinguishable from a
  built-in NAND so students can tell their work apart. Plan time for
  all three, not just the dialog.
- [ ] **Schema versioning from day one.** When Pass 3 lands, the very
  first save file should already have `"schema_version": 1`. Adding it
  later means the first batch of save files have no version stamp and
  every loader has to special-case "no field = version 0."
- [ ] **Fonts refactor (target pixel-height).** The current `Fonts`
  class hardcodes nominal sizes per face. Adding a system-font option
  in Pass 3 means tuning each face's size separately. Better: have
  `Fonts` take a target pixel-height and pick the size that hits it.
  Worth doing as part of the Options page work.
- [ ] **Architecture decision log (ADR).** A handful of meaningful
  design pivots are buried in the changelog as `Why:` prose. Pass 3
  will generate more. Worth starting a `docs/DECISIONS.md` ADR log
  when Pass 3 begins so those are findable as one-paragraph entries
  instead of buried in changelog diffs.
- [ ] **Save file portability across class years.** A save file from
  this year has to load next year. Combined with the schema-version
  point above: every Pass that touches the save format MUST add a
  migration function for the previous version, never just bump the
  number.
- [ ] **The "you discovered NAND!" moment is the entire pedagogical
  payoff.** Don't let the truth-table auto-detect slip out of Pass 3.
  Without it, Save-as-Component is "save your work"; with it, it's
  "discover the building blocks of computation." Big difference.
- [ ] **Save-as-Component port inference rule.** At save time, every
  Switch in the workspace becomes an INPUT port and every LED becomes
  an OUTPUT port; ordering is **ascending Y** (top of the workspace =
  port 0). Y was picked over component-creation-order because the
  visual top-to-bottom column is what the student actually sees.
- [ ] **Sub-step splits should stay end-to-end testable.** When
  splitting a pass-level bullet into multiple landings, each landing
  must produce a visible user-facing change, even if stub-quality.
  Don't split "input form" from "output appears" into separate cuts.

---

## Polish & Tech Debt

Code-quality items worth fixing the next time the surrounding code is
touched. Not bugs.

- [ ] **Add a few unit tests for the logic-only modules.** Pygame is
  hard to test, but `signals.py`, `wires._is_valid`, and `Wire.hit`
  are pure Python and trivial to cover. Three tests would catch the
  next signal refactor: NAND truth table, wire validation rejects
  same-direction / same-parent, and an SR latch built in code holds
  state across two `SignalManager.update` calls. *(Optional � the
  changelog discipline is doing most of the regression-prevention
  work that tests would. Add when/if you want belt-and-suspenders.)*