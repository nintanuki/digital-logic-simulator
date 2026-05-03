# Roadmap

Forward-looking task list for circuit-builder, organized into **Passes**.
Each pass goes through the codebase and leaves it more usable than the
last; nothing is "done" in one shot. Pass 1 builds a rough version of the
core feature, Pass 2 polishes it, Pass 3 adds the next layer of
functionality, Pass 4 polishes that, and so on. The project is "useful"
after Pass 1, "presentable" after Pass 2, "shareable" after Pass 4, and
"complete" only if and when you decide it should be — there is no
deadline and no obligation to reach the end.

Standalone sections below the passes capture **Questions**, **Ideas**,
**Issues / Bugs**, **Risks & Notes**, and **Polish & Tech Debt**.

Before starting any item, read `docs/TESTING.md` (refactoring rules +
manual test checklist) and skim recent entries in `docs/CHANGELOG.md`.
Completed work is no longer mirrored here — the changelog is the single
source of truth for what has shipped.

**Design principle:** the program must be fully usable with the mouse
alone. Keyboard shortcuts are for power users and exist alongside, never
instead of, a clickable equivalent. Anything new that's only reachable by
hotkey is incomplete.

**The selling point:** the abstraction loop — build a circuit, save it
as a named component, drop it into the next circuit as a black box, save
that, build with it, and so on up the layers. Every pass is judged by
whether it strengthens or distracts from that loop.

---

## Pass 1 — Spine (the abstraction loop, rough)

Get the core teaching loop working end-to-end, as rough as it needs to
be. By the end of this pass a student can build a NOT from a NAND, save
it as a component, drag it into a new workspace, build an AND from two
NANDs (or one NAND and one of their saved NOT components), save that,
and keep climbing the abstraction ladder. **In-session only — closing
the program loses everything.** That's a deliberate Pass-1 trade-off; disk
persistence comes in Pass 3.

- [x] **Save-as-Component dialog (rough).** Triggered from the
  bottom-left popup menu (the SAVE AS COMPONENT item is already there,
  disabled). The rough dialog only needs four things: a name field, a
  picker for which Switches become INPUT ports (and in what order), a
  picker for which LEDs become OUTPUT ports, and Save / Cancel buttons.
  Skip color choice, skip truth-table auto-detect, skip the "you
  discovered NAND!" celebration — those are Pass 3.
  *(Done 2026-05-03. Dialog ships in `save_component_dialog.py`; payload
  stashes on `GameManager.saved_components` as a dict awaiting Pass 1
  steps 2-3.)*
- [ ] **Saved component appears as a new template in the toolbox.** The
  bank already supports `(template_drawable, spawn_fn)` pairs (see the
  TEXT template), so a saved component is just a new pair appended to
  the bank's template list. Body color = `MEDIUM_CARMINE` for now, label
  = the saved name.
- [ ] **Spawning a saved component creates a working component.** The
  saved definition holds the embedded sub-circuit (components + wires +
  the input/output port mappings). Spawning instantiates a fresh copy of
  the sub-circuit hidden inside a single Component-shaped wrapper that
  exposes only the chosen external ports. SignalManager already does
  two-phase propagation, so the wrapped sub-circuit just runs as part of
  the same per-frame pass — no new simulator work needed.
- [ ] **Dynamic component sizing.** Once Save-as-Component starts
  producing components with more than the default 2 inputs / 1 output,
  bodies need to grow tall enough to fit all ports without overlap.
  Pick a per-port vertical pitch and recompute height from
  `max(inputs, outputs) * pitch + padding`. Width can grow too if the
  name is wide, but height is the urgent one for port spacing. **This
  has to land in Pass 1, not later** — a 4-input adder with stacked
  ports breaks the magic.

End of Pass 1: a student in one class period can build NOT, AND, OR,
XOR, and an SR latch entirely from NANDs, with each one saved as a
reusable component. They lose it all when they close the program. That's
fine for now.

---

## Pass 2 — Polish the spine

Fix the things students would notice in five seconds and add the safety
net that lets them experiment without fear of losing work.

- [ ] **Undo / redo.** Now that Pass 1 lets students invest real effort
  into building components, an accidental delete is the most painful
  possible bug. Cleanest model: every mutating action (place, delete,
  wire, unwire, edit text, save-as-component) routes through a Command
  object with `do()` and `undo()`. Manager pushes to a deque; Ctrl+Z
  pops, Ctrl+Y replays. Mouse equivalent: undo/redo arrows on a future
  toolbar, or the bottom-left menu — pick when the dispatch lands.
- [ ] **IN / OUT visual redesign.** Switch and LED currently render as
  circles with different fill colors, which reads as "the same component
  in two states" and confuses students. Redesign:
  - **Switch** as a physical toggle: rectangle with a sliding handle
    that visibly moves left/right (or up/down) when toggled, plus an
    ON/OFF label. Reads as "input you control."
  - **LED** as a bulb: circle with a base/lead silhouette so it reads as
    a bulb that's on or off. Maybe a halo/glow ring when HIGH.
- [ ] **Fix MENU button vs TEXT template visual confusion.** Both are
  small dark squares with a four-letter white label, so it's not obvious
  which is a control and which is a draggable component. Give MENU a
  distinct treatment — different color, a `≡` / `☰` icon, or a
  different shape — so it reads as a control surface, not an element.
- [ ] **Fix text inside components (alignment + size).** Text needs to be
  vertically and horizontally centered. The word "OUT" barely fits inside
  the OUT component, and the circle can barely fit three letters. Either
  shrink the font dynamically to fit the body, or resolve as part of the
  IN/OUT visual redesign above (which changes the body shape anyway).
- [ ] **F11 needs a mouse path.** Fullscreen is keyboard-only today.
  Most likely answer: an entry on the bottom-left popup menu. (A future
  top hotkey-hint bar in Pass 6 will add a second mouse path.)
- [ ] **Esc should not quit silently.** Layered behavior, in priority
  order:
  1. If a popup / dialog is open, Esc dismisses it. *(MenuButton popup
     case already landed; future dialogs reuse the same gate.)*
  2. Else if the game is fullscreen, Esc exits fullscreen (mirroring F11).
  3. Else Esc shows an in-game "Are you sure you want to quit?" confirm
     dialog. Only "Yes" actually quits.
- [ ] **Trash mode / delete button.** Right-click on a touchpad
  (Chromebook, single-button mouse) is hard for kids. Optional toolbar
  trash icon that puts the cursor into "delete mode" until the next
  click. Combined with undo/redo above, this gives mouse-only students
  a complete safe-delete workflow. **Check classroom hardware before
  building** — see Risks & Notes.
- [ ] **Wrap the per-frame loop in a top-level try/except** that flashes
  a banner and keeps the app alive. Crashes mid-class are the worst
  possible UX, and Pass 2 is the right time to add the seatbelt.
- [ ] **Manual test the bottom-left popup menu.** Open the menu, click
  each item, confirm the popup closes and the action runs. Click outside
  — popup closes, no spurious wire/component side effects. (Carried
  over from Pass 1; testable end-to-end once SAVE AS COMPONENT is wired
  up and the other items get their backing actions in Pass 3.)

End of Pass 2: looks decent, doesn't crash, doesn't quit on you, doesn't
lose work to a stray click. The abstraction loop is now genuinely
classroom-presentable, just only within a single session.

---

## Pass 3 — Persistence

Now disk save/load matters: students can keep their saved components
across class periods, between days, and between machines. Also adds the
project-level shell that wraps the workspace.

- [ ] **Save / load a project (disk).** JSON file containing components
  (type, position, internal state e.g. Switch toggle), wires
  (source/target as `(component_id, port_name)` pairs), text boxes
  (position + text), and the embedded definitions of every saved
  sub-component. **Schema version field from day one** so future formats
  can migrate cleanly. **Embed don't reference** — sub-circuit
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
  Cheap to compute — ≤4 inputs covers the entire list, and the check
  runs once on save, not per frame.
- [ ] **Color picker for saved components.** The save dialog grows a
  color picker. Small palette swatch AND/OR an RGB / hex entry field —
  the hex/RGB option is a deliberate teaching moment so students see how
  digital colors are encoded. Color saves into the component definition,
  not the project.
- [ ] **Rename the program.** "Circuit Builder" is a misnomer — there's
  no analog circuitry. Pick a name (see Questions) and migrate before
  Pass 3 ships, so save files reference the new name from day one.

End of Pass 3: a student's work survives across sessions and machines.
Components they save can be shared as part of a project file.

---

## Pass 4 — Polish persistence

Make the persistence layer robust enough to share with other CS
teachers, not just survive a single classroom.

- [ ] **Schema migration paths.** Each version bump gets a migration
  function that loads the old format and produces the new one. Refuse to
  load a future-version file with a clear error rather than guessing.
- [ ] **Error recovery for malformed save files.** A truncated or
  hand-edited save shouldn't crash the program — it should fall back to
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

## Pass 5 — Curriculum (rough)

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

End of Pass 5: rough. The lessons exist; the discoverability/UX layer
comes in Pass 6.

---

## Pass 6 — Polish curriculum + add discoverability

Make the program teach itself. Smooths the rough Pass-5 lessons and
adds the surfaces that lower the floor for a cold-start student.

- [ ] **Top hotkey-hint bar.** Old-school computer-program style: a
  thin bar across the top of the screen showing
  "F11 fullscreen | Esc back | ?: shortcuts | …". Mouse-first reachable
  summary so students don't need the docs to discover the keyboard
  path.
- [ ] **Keyboard shortcut overlay.** Press `?` to flash a translucent
  cheat-sheet of every shortcut. Layers with the hint bar above — bar
  is always-on, overlay is on-demand and exhaustive.
- [ ] **Easy mode.** Optional starter set: students begin with AND,
  OR, NOT, NAND already in the toolbox so they can build interesting
  circuits before they've finished the NAND-only progression. Off by
  default — the universal-NAND moment is the main pedagogical point.
- [ ] **Encyclopedia / dictionary.** Built-in glossary students can
  flip open: each gate, each common circuit (latch, flip-flop, adder,
  multiplexer) with a short definition and a worked example.

---

## Pass 7+ — Treats

Stretch goals. Take them in any order, or not at all. None of these
strengthen the abstraction loop — they decorate it.

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
  underlying complaint. Promote here as the proposed fix when ready —
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
  Pick one — or decide to layer two — once we have real data on how
  many components a typical session produces. Don't pre-build all five.
- [ ] **Lit wire color.** Currently green (matches `PORT_LIVE_COLOR`).
  Could go to amber, neon cyan, etc. Decide alongside Pass 4 once the
  Save-as-Component palette work has produced real data.
- [ ] **Rename the program.** "Circuit Builder" is a misnomer.
  Candidates so far: "Digital Logic Simulator," "Logic Sandbox," "Logic
  Bench," "NAND Lab." Pick before Pass 3 so save files reference the
  new name from day one.
- [ ] **Dynamic text-box width — wrap/width fixed point.** Width
  depends on the wrap, the wrap depends on the width. Resolve by either
  picking the longest unbroken line as the width seed, or iterating to
  a fixed point. Pick before the Pass-7+ idea gets implemented.

---

## Ideas

Uncommitted designs that have a shape but no owner or pass yet. The
roadmap above absorbed most of the prior Brainstorming entries; this
section will fill back up as new ones come in.

*(currently empty — promote ideas back here from the passes if their
case for shipping weakens, or add new ones as they come up)*

---

## Issues / Bugs

Bugs that affect behavior. Repro → fix → log in `docs/CHANGELOG.md` →
re-run the manual checklist in `docs/TESTING.md`.

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

Forward-looking concerns that aren't tasks but are worth re-reading at
the start of each pass. Promote into the relevant pass when they become
actionable.

- [ ] **Classroom hardware = touchpads?** If the target machines are
  Chromebooks or laptops without a real two-button mouse, right-click
  delete is hard for kids and the program currently has no other path
  to delete a wire or text box. "Trash mode" is in Pass 2 because of
  this — but verify the hardware reality before Pass 1 ships, because
  it might bump trash mode earlier.
- [ ] **Save-as-Component is the keystone risk.** Three things have to
  be true at once for Pass 1 to feel right: (1) the embedded sub-
  circuit definition has to round-trip cleanly through spawn, (2)
  dynamic component sizing has to handle ≥3 inputs without overlap,
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
  design pivots are buried in the changelog as `Why:` prose (Switch/
  LED replacing port-toggle, two-step popup routing, Option 1 for the
  bank generalization). Pass 3 will generate four or five more
  (embed-don't-reference for saves, schema version + migration
  approach, sub-component runtime model). Worth starting a
  `docs/DECISIONS.md` ADR log when Pass 3 begins so those are
  findable as one-paragraph entries instead of buried in changelog
  diffs.
- [ ] **Save file portability across class years.** A save file from
  this year has to load next year. Combined with the schema-version
  point above: every Pass that touches the save format MUST add a
  migration function for the previous version, never just bump the
  number.
- [ ] **The "you discovered NAND!" moment is the entire pedagogical
  payoff.** Don't let the truth-table auto-detect slip out of Pass 3.
  Without it, Save-as-Component is "save your work"; with it, it's
  "discover the building blocks of computation." Big difference.

---

## Polish & Tech Debt

Code-quality items worth fixing the next time the surrounding code is
touched. Not bugs.

- [ ] **Add a few unit tests for the logic-only modules.** Pygame is
  hard to test, but `signals.py`, `wires._is_valid`, and `Wire.hit`
  are pure Python and trivial to cover. Three tests would catch the
  next signal refactor: NAND truth table, wire validation rejects
  same-direction / same-parent, and an SR latch built in code holds
  state across two `SignalManager.update` calls. *(Optional — the
  changelog discipline is doing most of the regression-prevention
  work that tests would. Add when/if you want belt-and-suspenders.)*
