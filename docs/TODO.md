# Roadmap

A living task list for Digital Logic Simulator, organized by practical feature areas
rather than abstract passes. The project cycles through the codebase; each pass leaves
it more usable and polished than the last.

**Before starting any item:**
- Read `docs/TESTING.md` and skim recent entries in `docs/CHANGELOG.md`
- Full descriptions of completed work live in the changelog

**Design principle:** fully usable with the mouse alone. Keyboard shortcuts exist
alongside, never instead of, a clickable equivalent.

**The core loop:** build a circuit, save it as a named component, drop it into the
next circuit as a black box, save that, and repeat. This abstraction loop is the
entire pedagogical point.

---

## Next Up

Items currently in progress or immediate priority.

- [ ] **Finalize Pass 3 refactoring (architecture).** Clean up GameManager bloat by
  extracting menu rendering, project I/O, and save-as-component logic into
  dedicated handlers (TopMenuBar, ProjectManager, SaveAsComponentHandler). Goal:
  keep GameManager light per TESTING.md architecture rules.
  - Estimated: Already mostly complete per May 5 CHANGELOG entries.


## Core Features

The essential teaching loop and foundational user workflows.

### Foundation (Completed)

- [x] **Save-as-component dialog and workflow.** Students can save a finished
  circuit as a named, reusable black box and spawn it from the toolbox.
- [x] **Saved components render with dynamic sizing.** Accounts for varying
  input/output port counts without overlap or truncation.
- [x] **Undo and redo.** Ctrl+Z / Ctrl+Y with six command types in `commands.py`.
- [x] **Polish Pass 2 visual redesign.** Switch = sliding toggle. LED = bulb silhouette.
  Random colors for saved components (8-color curated palette in `settings.py`).
- [x] **Esc behavior is safe, not silent.** Layered per-priority: if a dialog is
  open, dialog handles Esc; if editing text, Esc stops editing; otherwise, Esc
  opens a quit-confirmation dialog (not immediate exit). Only YES closes the app.
- [x] **Menu button vs TEXT template visual distinction.** MENU is visually
  distinguishable so it reads as a control surface, not a draggable component.
- [x] **Error recovery.** Per-frame try/except wraps the event loop and keeps
  the app alive on unhandled exceptions, flashing a banner instead of crashing.
- [x] **Top hotkey-hint bar.** Always-on strip showing keyboard shortcuts.

### Persistence (In Progress / Planned)

- [ ] **Save and load projects to disk.** JSON file containing components
  (type, position, internal state e.g. Switch toggle), wires (source/target as
  `(component_id, port_name)` pairs), text boxes (position + text), and embedded
  definitions of every saved sub-component.
  - **Schema versioning from day one:** every save file includes `"schema_version": 1`
  - **Embed don't reference:** sub-circuit definitions live inside the project save
  - **Case normalization:** apply `.upper()` to every text-box string when loading
    so old saves with lowercase characters conform to uppercase rule

- [ ] **Main menu on startup.** Before the workspace opens, show a menu screen with
  NEW PROJECT, LOAD PROJECT, SETTINGS, ABOUT, QUIT. App-level state machine routes
  between main menu and workspace.
  - New Project flow: clear workspace and show tutorial prompt (see below)
  - Load Project flow: open load dialog, switch to workspace
  - Settings/About stubs: placeholder menu items for future passes
  - **Note:** decide whether to keep menu logic refactored out of main.py into
    TopMenuBar handler (already mostly done per May 5) or consolidate back if
    architecture feels over-engineered

- [ ] **Tutorial prompt on new project.** When starting a new project from the
  main menu, ask "WOULD YOU LIKE TO START THE TUTORIAL?" If yes, launch tutorial.
  If no, proceed to blank workspace. Prompt appears only on new-project-from-menu,
  not during in-game play.

- [ ] **Options page.** Reachable from main menu and in-workspace popup menu.
  - CRT effect on/off
  - Pixelated vs system font (requires per-face size constants in `settings.py`)
  - Background color (pale blue current, circuit-board green, or student-picked swatch)
  - Sound effects on/off (placeholder until audio lands in later pass)

- [ ] **Truth-table auto-detect ("You discovered NAND!").** When saving a component,
  brute-force compare its truth table against known gates (NOT, AND, OR, NAND, NOR,
  XOR, XNOR). If match found, dialog pre-fills recognized name and pops banner.
  Cheap to compute (4 inputs covers entire list), runs once on save, not per frame.
  - Add auto-naming handoff: when a user-built component is recognized (e.g. OR gate),
    suggest/apply the discovered label automatically in the save flow.

- [ ] **Color picker for saved components.** Save dialog grows a color picker:
  small palette swatch AND/OR RGB/hex entry field. Hex/RGB option is a deliberate
  teaching moment so students see how digital colors are encoded. Color saves into
  component definition, not the project.

- [ ] **Rename the program.** "Circuit Builder" is misleading. Pick a name from
  candidates (Digital Logic Simulator, Logic Sandbox, Logic Bench, NAND Lab) and
  migrate before this pass ships so save files reference new name from day one.

### Persistence Polish (Planned)

- [ ] **Schema migration paths.** Each version bump gets a migration function that
  loads old format and produces new one. Refuse to load future-version files with
  clear error rather than guessing.

- [ ] **Error recovery for malformed save files.** Truncated or hand-edited saves
  shouldn't crash—fall back to empty workspace with banner explaining what went wrong.

- [ ] **Toolbox overflow handling.** By the time students accumulate many custom
  components, the bank will overflow. Choose approach once we have real usage data:
  - Horizontal scroll on the bank
  - Shrink template icons + "More..." popup
  - Move full library to bottom-left menu, keep smaller "favorites" row in bank
  - Vertical sidebar instead of bottom bar
  - Categories with tabs (gates, latches, custom)

- [ ] **Pin-to-toolbar for saved components.** Right-click a saved component in
  menu library to "Pin to toolbar" / "Unpin." Natural fit if toolbox-overflow
  answer is "library + favorites row."

- [ ] **Lit wire color decision.** Currently green. Now that Save-as-Component
  palettes exist and we can see colors students pick, decide whether green stays
  or moves to amber/cyan (see Open Questions).


## Teaching Features

Tutorials, encyclopedia, puzzles, and curriculum design.

### Tutorial System (Planned)

- [ ] **Tutorial system scaffold** (for Pass 3). Extensible structure for interactive
  tutorials. Start minimal: basic "welcome" screen + exit path. Design so future
  passes can add tutorial steps easily (highlighting, constraints, validation).
  Launchable from:
  - Tutorial prompt when starting new project from main menu
  - TUTORIAL option in in-game FILE menu
  - Can exit anytime via Esc, returns to workspace

- [ ] **Tutorial content expansion** (for Pass 5+). Interactive walkthroughs that
  introduce concepts in order: "wire a NAND so its output is HIGH," "build a NOT
  gate from a NAND," "build an AND gate from two NANDs." Each tutorial highlights
  relevant toolbox template and verifies truth table on completion.

### Encyclopedia System (Planned)

- [ ] **Encyclopedia system scaffold** (for Pass 3). Extensible reference system
  for gates, circuits, concepts. Start minimal: navigation between entries + exit
  path. Design for future expansion with diagrams, worked examples. Launchable from:
  - ENCYCLOPEDIA option in in-game FILE menu
  - Can exit anytime via Esc, returns to workspace

- [ ] **Encyclopedia content expansion** (for Pass 6). Built-in glossary students
  can flip open: each gate, each common circuit (latch, flip-flop, adder,
  multiplexer) with short definition and worked example.

### Puzzles & Challenges (Planned)

- [ ] **Puzzle system.** "Build an XOR gate using only NANDs in 5 components or
  fewer." "Make an SR latch hold state." Auto-graded by truth-table comparison.
  Optional leaderboard / star rating per puzzle. (Depends on Pass 3 persistence
  so puzzles can ship as project files.)


## UI/UX Improvements

Menu polish, keyboard shortcuts, visual design.

### Pass 2 Remaining Items

- [ ] **F11 fullscreen needs a mouse path.** Fullscreen toggle is keyboard-only today.
  Add entry on bottom-left popup menu. (Future top hotkey-hint bar in Pass 6 will
  add a second mouse path.)

- [ ] **Trash mode / delete button.** Right-click on touchpad (Chromebook,
  single-button mouse) is hard for kids. Optional toolbar trash icon puts cursor
  into "delete mode" until next click. Combined with undo/redo, gives mouse-only
  students complete safe-delete workflow. **Check classroom hardware before
  building** (see Risks & Notes).

- [ ] **Manual test bottom-left popup menu.** Open menu, click each item, confirm
  popup closes and action runs. Click outside popup—popup closes, no spurious
  wire/component side effects.

### Pass 6+ Enhancements

- [ ] **Keyboard shortcut overlay.** Press `?` to flash translucent cheat-sheet of
  every shortcut. Layers with hint bar above—bar is always-on, overlay is on-demand
  and exhaustive.

- [ ] **Easy mode.** Optional starter set: students begin with AND, OR, NOT, NAND
  already in toolbox so they can build interesting circuits before finishing NAND-only
  progression. Off by default—universal-NAND moment is the main pedagogical point.

- [ ] **Dynamic text-box width.** Currently `TextBoxSettings.WIDTH` is fixed and
  box wraps text into it. Better: width = min(WIDTH, font.size(longest_line) +
  2*PADDING). See Open Questions for the wrap/width fixed-point question.


## Bugs / Issues

Actual problems, listed by priority.

- [ ] **Wires only go in straight lines, can't be bent or curved.** If a user wants
  to connect two components with another component in between, or create a loop,
  the result is ugly straight lines crossing through other components. Proposed
  fix: allow waypoints during wire drag; right-click waypoint to delete. (Scheduled
  as Pass 7+ item "Wire bending / segments".)

- [ ] **Port highlighting active inside toolbox.** Hovering over ports of a template
  in the toolbox lights them up as if they were in the workspace. Low priority;
  cosmetic only.

- [ ] **"TOGGLE FULLSCREEN" text is hardcoded and overlaps F11 hint.** The VIEW menu
  shows "TOGGLE FULLSCREEN" which is too long and overlaps keyboard shortcut hint.
  Should be shortened to "FULLSCREEN" and moved to `settings.py` as a constant per
  architecture rules (all display text in settings). Low priority; good refactoring
  target for future cleanup.

- [ ] **Components too big for the toolbox.** If a student builds a complex saved
  component and saves it, the rendered preview in the toolbox may exceed toolbox
  dimensions. No clear solution yet—options: scaling/shrinking preview, clipping
  with scrollbar, expansion outside panel, limiting component complexity. Deferred
  pending classroom observation; may become critical depending on typical usage patterns.


## Architecture Notes

Design decisions and architectural concerns worth preserving and monitoring.

- [ ] **Keep GameManager light.** Offload responsibilities to dedicated handlers
  rather than embedding all logic in the main event loop. By May 5, menu rendering,
  project I/O, and save-as-component logic have been (or are being) extracted to
  TopMenuBar, ProjectManager, and SaveAsComponentHandler. Continue this pattern
  for future additions.

- [ ] **Save-as-Component is the keystone risk.** Three things must be true at once
  for the abstraction loop to feel right:
  1. Embedded sub-circuit definition round-trips cleanly through spawn
  2. Dynamic component sizing handles 3+ inputs without overlap
  3. Saved component visually distinguishable from built-in NAND so students see
     their work apart from the library

- [ ] **Schema versioning from day one.** When Pass 3 lands, the very first save
  file must already have `"schema_version": 1`. Adding it later means first batch
  of saves have no version stamp and every loader has to special-case "no field = version 0."

- [ ] **Save file portability across class years.** A save file from this year must
  load next year. Combined with schema-version point: every pass that touches save
  format MUST add a migration function for previous version, never just bump the number.

- [ ] **The "you discovered NAND!" moment is the entire pedagogical payoff.** Don't
  let truth-table auto-detect slip out of Pass 3. Without it, Save-as-Component is
  "save your work"; with it, it's "discover the building blocks of computation."

- [ ] **Save-as-Component port inference rule.** At save time, every Switch becomes
  an INPUT port and every LED becomes an OUTPUT port. Ordering is **ascending Y**
  (top of workspace = port 0). Y was picked over component-creation-order because
  the visual top-to-bottom column is what students see.

- [ ] **Sub-step splits should stay end-to-end testable.** When splitting a
  pass-level bullet into multiple landings, each landing must produce visible
  user-facing change, even if stub-quality. Don't split "input form" from "output
  appears" into separate cuts.

- [ ] **Architecture Decision Log (ADR).** Meaningful design pivots are buried in
  changelog as `Why:` prose. Worth starting a `docs/DECISIONS.md` ADR log when
  Pass 3 begins so those are findable as one-paragraph entries instead of buried
  in changelog diffs.

- [ ] **Fonts refactor (target pixel-height).** The current `Fonts` class hardcodes
  nominal sizes per face. Adding system-font option in Pass 3 means tuning each
  face's size separately. Better: have `Fonts` take target pixel-height and pick
  size that hits it. Worth doing as part of Options page work.

- [ ] **Classroom hardware assumption.** If target machines are Chromebooks or
  laptops without real two-button mouse, right-click delete is hard for kids and
  program currently has no other path to delete wire/text box. "Trash mode" is in
  Pass 2 roadmap because of this—but verify hardware reality before Pass 1 ships,
  because it might bump trash mode earlier.


## Tech Debt / Polish

Code-quality items worth fixing the next time surrounding code is touched. Not bugs.

- [ ] **Add unit tests for logic-only modules.** Pygame is hard to test, but
  `signals.py`, `wires._is_valid`, and `Wire.hit` are pure Python and trivial to
  cover. Three tests would catch next signal refactor:
  1. NAND truth table
  2. Wire validation rejects same-direction / same-parent
  3. SR latch built in code holds state across two `SignalManager.update` calls

  *(Optional—changelog discipline is doing most regression-prevention work that
  tests would. Add when/if you want belt-and-suspenders.)*


## Open Questions / Decisions

Design decisions pending before (or as part of) work that depends on them.

- [ ] **CRT + font toggle: one switch or two?** Should "Pixelated font" and "CRT
  effect" become a single "Retro mode" master switch, or stay as two independent
  options? Decide before Pass 3's Options page.

- [ ] **Toolbox-overflow approach.** Five candidates listed in Core Features. Pick
  one—or decide to layer two—once we have real data on how many components a
  typical session produces. Don't pre-build all five.

- [ ] **Lit wire color.** Currently green (matches `PORT_LIVE_COLOR`). Could go to
  amber, neon cyan, etc. Decide alongside Pass 4 once Save-as-Component palette
  work has produced real data.

- [ ] **Rename the program.** "Circuit Builder" is a misnomer. Candidates: Digital
  Logic Simulator, Logic Sandbox, Logic Bench, NAND Lab. Pick before Pass 3 so
  save files reference new name from day one.

- [ ] **Dynamic text-box width—wrap/width fixed point.** Width depends on wrap, wrap
  depends on width. Resolve by either picking longest unbroken line as width seed,
  or iterating to fixed point. Pick before Pass 7+ idea gets implemented.


## Ideas / Later

Stretch goals for future passes or deferred until proven necessary.

- [ ] **Sound design.** Subtle click on placement, faint hum on HIGH signal, small
  "snap" when wire commits. CRT scanlines already set toy-computer mood; audio would
  land rest of it. Pair with Options sound-effects toggle. (Pass 7+)

- [ ] **Multi-bit ports / busses.** Once students build 4-bit adder they'll want to
  bundle four wires into one visual line. Big semantic lift; park until adders
  happen. (Pass 7+)

- [ ] **Component library sharing.** Export a saved component as shareable file
  students can email or hand off. Pairs with embed-don't-reference save-file
  decision in Pass 3. (Pass 7+)