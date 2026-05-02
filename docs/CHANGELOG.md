# Change Log

This file is an append-only record of every code change made to Circuit Builder
by a human, AI assistant, or copilot tool. Read it before making changes so you
know the current state of the codebase.

## Format

Each entry covers one logical change (which may touch multiple files). Use the
template below, with one `**File:** ... **Why:** ...` block per file touched.

    ## YYYY-MM-DD HH:MM — short summary

    **File:** path/to/file.py
    **Lines (at time of edit):** 38-52 (modified)
    **Before:**
        [old code]
    **After:**
        [new code]
    **Why:** explanation
    **Editor:** name of human or AI model

## Conventions

* Line numbers reflect the file as it existed at the moment of the edit. Edits
  above shift line numbers below, so older entries will not match the current
  file. Never go back and "fix" old line numbers.
* Entries are append-only. Never delete history. If a later edit reverts an
  earlier one, write a new entry that references the original.
* For new files, write `(new file)` instead of a line range. The "Before"
  block can be omitted or marked `(file did not exist)`.
* For deletes, write `(deleted)` and put the removed code in "Before" with no
  "After" block.
* Keep "Before" / "After" blocks short. If a change is huge, summarize with a
  diff-style excerpt of the most important lines plus a sentence describing the
  rest, instead of pasting the entire file.

## 2026-05-01 — Rewrite README for a professional tone

**File:** README.md
**Lines (at time of edit):** 1-5 (replaced; file grew to ~55 lines)
**Before:**
    # circuit-builder

    This project is my attempt at creating my own version of Sebastian Lague's digital logic simulator: https://github.com/SebLague/Digital-Logic-Sim

    ^ It is inspired by this original project but I wanted to have creative control and I don't know C# or Unity, so intead of trying to edit it I decided to try recreating it in Python using Pygame and making it my own. This will be used in computer science class as well as IT and coding classes during enrichment to teach students about how logic gates are used in computation.

    Students can drag and drop components onto the mat from the toolbox. Each component has at least one input and one output. We start with a NAND. These NANDs can be wired together to create NOT, OR and AND gates. Once a student has completed their circuit of components, they can save it as a component itself, name it, and it becomes a "black box" abstacted away into a named component that goes into their toobox. They no longer need to worry about the internal circuitry, just wiring up to the inputs and output. Circuits such as the AND-OR-LATCH or a 4-Bit Ripple Adder can be created using this too.
**After:**
    # Circuit Builder

    A digital logic sandbox written in Python with Pygame. Students drag NAND
    gates onto a grid, wire them together, and discover that every other gate
    (NOT, AND, OR, XOR, latches, adders) can be built from that one universal
    block.

    [...sections for Background, Classroom Use, Current Status, Controls,
    Requirements, Project Layout, Contributing...]
**Why:** Original draft read like a private note: typos (intead, abstacted, toobox, too), no install/run steps, no controls reference, no project layout, no link to the roadmap. New version is structured for someone discovering the repo cold, fixes the typos, and points contributors at TESTING.md.
**Editor:** Claude (Opus)

## 2026-05-01 — Extract Port class from Component

**File:** settings.py
**Lines (at time of edit):** 49-54 (modified, ComponentSettings)
**Before:**
        class ComponentSettings:
            COLOR = ColorSettings.WORD_COLORS["MEDIUM_CARMINE"]
            BORDER_COLOR = ColorSettings.WORD_COLORS["GUARDSMEN_RED"]
            BORDER_THICKNESS = 2
            PORT_COLOR = ColorSettings.WORD_COLORS["BLACK"]
            PORT_RADIUS = 10
**After:**
        class ComponentSettings:
            COLOR = ColorSettings.WORD_COLORS["MEDIUM_CARMINE"]
            BORDER_COLOR = ColorSettings.WORD_COLORS["GUARDSMEN_RED"]
            BORDER_THICKNESS = 2
            PORT_COLOR = ColorSettings.WORD_COLORS["BLACK"]
            PORT_RADIUS = 10
            # Vertical inset of the two input ports from the component's top and
            # bottom edges, in pixels. Used by Component when laying out its
            # default ports.
            INPUT_PORT_INSET = 15
**Why:** The literal 15 was a magic number used twice in elements.py to position the input ports. Moved to settings.py per the no-magic-numbers rule so the Port refactor stays clean.
**Editor:** Claude (Opus)

**File:** elements.py
**Lines (at time of edit):** 1-63 (replaced; file grew to ~155 lines)
**Before:**
        class Component:
            def __init__(self, x, y, width=100, height=60, name="NAND"):
                self.rect = pygame.Rect(x, y, width, height)
                ...

            def draw(self, surface):
                # Draw the Port (Circles)
                port_color = ComponentSettings.PORT_COLOR
                radius = ComponentSettings.PORT_RADIUS
                pygame.draw.circle(surface, port_color, (self.rect.left, self.rect.top + 15), radius)
                pygame.draw.circle(surface, port_color, (self.rect.left, self.rect.bottom - 15), radius)
                pygame.draw.circle(surface, port_color, (self.rect.right, self.rect.centery), radius)
                pygame.draw.rect(surface, self.color, self.rect)
                ...
**After:**
        class Port:
            INPUT  = "INPUT"
            OUTPUT = "OUTPUT"

            def __init__(self, parent, offset_x, offset_y, name, direction): ...
            @property
            def center(self): ...   # (parent.rect.x + offset_x, parent.rect.y + offset_y)
            @property
            def rect(self):   ...   # square hit-rect of side 2 * PORT_RADIUS
            def draw(self, surface): ...

        class Component:
            def __init__(self, ...):
                ...
                self.ports = self._build_ports()

            def _build_ports(self):
                inset = ComponentSettings.INPUT_PORT_INSET
                return [
                    Port(self, 0,               inset,                    "A",   Port.INPUT),
                    Port(self, 0,               self.rect.height - inset, "B",   Port.INPUT),
                    Port(self, self.rect.width, self.rect.height // 2,    "OUT", Port.OUTPUT),
                ]

            def draw(self, surface):
                for port in self.ports:
                    port.draw(surface)
                # body, border, and label drawn after, unchanged
**Why:** Ports were previously three hardcoded circles inside `Component.draw` with no identity, name, direction, or hit rect. The next four roadmap items (port highlighting, hover labels, wiring, live state) all need ports to be real objects, so this extracts them into a `Port` class with relative offsets, name, direction, a screen-space `center`, and a hit `rect`. Visual output is preserved pixel-for-pixel: ports are drawn before the body so their inner halves are still covered by the rectangle, and offsets resolve to the same coordinates as the original literals (rect.left/top+15, rect.left/bottom-15, rect.right/centery). No public API changed: `Component(x, y, name=...)`, `comp.draw(surface)`, and `comp.handle_event(event)` are all the same.
**Editor:** Claude (Opus)

## 2026-05-01 — Fix right-click delete deleting the wrong component

**File:** elements.py
**Lines (at time of edit):** 148-155 (Component.handle_event)
**Before:**
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == InputSettings.LEFT_CLICK and self.rect.collidepoint(event.pos):
                self.dragging = True
                self.offset_x = self.rect.x - event.pos[0]
                self.offset_y = self.rect.y - event.pos[1]
            elif event.button == InputSettings.RIGHT_CLICK:
                    return "DELETE"
**After:**
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == InputSettings.LEFT_CLICK and self.rect.collidepoint(event.pos):
                self.dragging = True
                self.offset_x = self.rect.x - event.pos[0]
                self.offset_y = self.rect.y - event.pos[1]
            elif event.button == InputSettings.RIGHT_CLICK and self.rect.collidepoint(event.pos):
                return "DELETE"
**Why:** The right-click branch was missing the `collidepoint(event.pos)` hit-test that the left-click branch already had, so every Component returned "DELETE" on every right-click. main.py iterates components in reverse and breaks on the first delete, which meant the most recently placed component was always the one deleted, regardless of cursor position. Reported by user. Also fixed the spurious extra indentation on the `return "DELETE"` line that was a hint the logic was incomplete.
**Editor:** Claude (Opus)

## 2026-05-01 — Curate TODO.md as a session-handoff roadmap

**File:** docs/TODO.md
**Lines (at time of edit):** 1-10 (replaced; file grew to ~110 lines)
**Before:**
        - [ ] Add port highlighting
        - [ ] Add port text on hover (INPUT A, INPUT B, OUT, etc)
        - [ ] Ports should be connectable with wires
        - [ ] Add logic for when ports are "live"
        - [ ] Allow text boxes that can be dragged, dropped and edited.
        - [ ] Allow ports to connect
        - [ ] Allow student to save a project
        - [ ] Add menu that allows the student to start a new project or load a new one
        - [ ] Shrink and simplify components on toolbox for a cleaner more compact UI
        - [ ] Add Menu button to toolbox for saving components and creating new workspace to make a new component
**After:**
        # Roadmap
        ## Now — Port highlighting
        ## Next — Port hover labels
        ## Next — Wiring
        ## Next — Live signal state
        ## Later
        ## Polish / tech debt
        ## Known issues
        (each section has concrete substeps; full text in the file)
**Why:** Original list was a flat bag of intent — fine for the author mid-flow, hard to resume in a fresh session. New layout phases the work (Now / Next / Later) and breaks each item into substeps small enough that future-me can pick one up cold. Removed the duplicate "Allow ports to connect" entry. Added a "Polish / tech debt" section capturing items raised but not addressed this session (font init in Component, implicit return in handle_event, magic widths/heights, redundant super().__init__ in CRT). Added a "Known issues" section with the toolbox-occlusion bug reported by the user (components can currently be dragged below `UISettings.BANK_RECT.top`).
**Editor:** Claude (Opus)

## 2026-05-01 — Port hover highlighting

**File:** settings.py
**Lines (at time of edit):** 53-58 (added)
**Before:**
    PORT_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    PORT_RADIUS = 10
**After:**
    PORT_COLOR = ColorSettings.WORD_COLORS["BLACK"]
    PORT_HIGHLIGHT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    PORT_RADIUS = 10
**Why:** Highlight color picked here so Port.draw can branch on it without
embedding a literal. White was chosen for strong contrast against both the
black resting color and the dark red body; green/red are reserved for the
upcoming live-signal phase per the roadmap.
**Editor:** Claude (Opus)

**File:** elements.py
**Lines (at time of edit):** 33, 67-72 (Port.__init__ and Port.draw)
**Before:**
    self.direction = direction

    def draw(self, surface):
        ...
        pygame.draw.circle(surface, ComponentSettings.PORT_COLOR,
                           self.center, ComponentSettings.PORT_RADIUS)
**After:**
    self.direction = direction
    self.hovered = False

    def draw(self, surface):
        ...
        color = (ComponentSettings.PORT_HIGHLIGHT_COLOR
                 if self.hovered else ComponentSettings.PORT_COLOR)
        pygame.draw.circle(surface, color, self.center,
                           ComponentSettings.PORT_RADIUS)
**Why:** First step of the roadmap "Now" item. Port now carries hover state
and uses it to switch fill color, leaving GameManager free to drive that
state with whatever input source it likes.
**Editor:** Claude (Opus)

**File:** main.py
**Lines (at time of edit):** 79-127 (GameManager._handle_mouse + new
_update_port_hover helper)
**Before:**
    def _handle_mouse(self, event):
        if self.bank.handle_event(event, self.components):
            return
        for i in range(len(self.components) - 1, -1, -1):
            ...
**After:**
    def _handle_mouse(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._update_port_hover(event.pos)
        ...

    def _update_port_hover(self, mouse_pos):
        for comp in self.components:
            for port in comp.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)
        for port in self.bank.template.ports:
            port.hovered = port.rect.collidepoint(mouse_pos)
**Why:** Hover state lives on Port but only GameManager owns both the
workspace components and the toolbox template, so it's the natural place
to drive every port from a single MOUSEMOTION. Toolbox template ports are
included per the roadmap so a hovered port lights up wherever it lives.
**Editor:** Claude (Opus)

## 2026-05-01 — Centralize Font loading in Fonts class

**File:** fonts.py
**Lines (at time of edit):** (new file)
**After:**
    class Fonts:
        component_label = None
        port_label = None

        @classmethod
        def init(cls):
            pygame.font.init()
            cls.component_label = pygame.font.Font(...FONT_SIZE)
            cls.port_label     = pygame.font.Font(...PORT_LABEL_FONT_SIZE)
**Why:** Component.__init__ used to call pygame.font.init() and load the
.ttf every time a gate was spawned, which is wasteful and made it impossible
to share a single port-label face across every Port. Fonts is a tiny
class-level cache loaded once at boot. Keeps GameManager light per the
project's architectural rules (init() runs there, but no font state lives
there).
**Editor:** Claude (Opus)

**File:** main.py
**Lines (at time of edit):** 6 (import) and 18-20 (init call)
**Before:**
    pygame.init()
**After:**
    pygame.init()
    Fonts.init()
**Why:** Must run before ComponentBank instantiates its template Component,
which calls Component.draw indirectly only after this point.
**Editor:** Claude (Opus)

**File:** elements.py
**Lines (at time of edit):** 3 (import), 89-94 (Component.__init__),
166 (Component.draw label render)
**Before:**
    pygame.font.init()
    self.font = pygame.font.Font(ComponentSettings.FONT,
                                 ComponentSettings.FONT_SIZE)
    ...
    text_surf = self.font.render(self.name, True, WHITE)
**After:**
    # font init removed; per-instance self.font removed entirely
    ...
    text_surf = Fonts.component_label.render(self.name, True, WHITE)
**Why:** Drops the redundant per-spawn font work and lets every Component
share the same Font object loaded once by Fonts.init().
**Editor:** Claude (Opus)

## 2026-05-01 — Port hover labels

**File:** settings.py
**Lines (at time of edit):** 69-74 (added under ComponentSettings)
**After:**
    PORT_LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    PORT_LABEL_FONT_SIZE = 12
    PORT_LABEL_OFFSET = PORT_RADIUS + 6
**Why:** Constants for the hover label so Port.draw_label has no magic
numbers. OFFSET is the gap between the port center and the closest edge
of the rendered text, keeping the label clear of the circle.
**Editor:** Claude (Opus)

**File:** fonts.py
**Lines (at time of edit):** 18, 28-31 (port_label cache)
**After:**
    cls.port_label = pygame.font.Font(ComponentSettings.FONT,
                                      ComponentSettings.PORT_LABEL_FONT_SIZE)
**Why:** Smaller cached face used by every Port for its name label, so we
don't spin one up per port (the polish item this is paired with).
**Editor:** Claude (Opus)

**File:** elements.py
**Lines (at time of edit):** 82-106 (new Port.draw_label) and 177-179
(Component.draw calls draw_label after the body)
**After:**
    def draw_label(self, surface):
        if not self.hovered:
            return
        ...
        if self.direction == Port.INPUT:
            label_rect.midright = (cx - offset, cy)
        else:
            label_rect.midleft = (cx + offset, cy)
        surface.blit(label_surf, label_rect)
    ...
    # In Component.draw, after the body and component name:
    for port in self.ports:
        port.draw_label(surface)
**Why:** Split label render off from Port.draw so Component.draw can render
labels last, after the body and border, guaranteeing labels stay on top
regardless of port position. INPUT ports anchor right (label sits to the
left of the port); OUTPUT ports anchor left (label sits to the right) so
labels point outward from the body.
**Editor:** Claude (Opus)

## 2026-05-01 — Clamp dragged components to the workspace + explicit return None

**File:** elements.py
**Lines (at time of edit):** 4-11 (settings imports), 200-223
(Component.handle_event MOUSEMOTION + new _clamp_to_workspace)
**Before:**
    elif event.type == pygame.MOUSEMOTION:
        if self.dragging:
            self.rect.x = event.pos[0] + self.offset_x
            self.rect.y = event.pos[1] + self.offset_y
**After:**
    elif event.type == pygame.MOUSEMOTION:
        if self.dragging:
            self.rect.x = event.pos[0] + self.offset_x
            self.rect.y = event.pos[1] + self.offset_y
            self._clamp_to_workspace()
    return None

    def _clamp_to_workspace(self):
        max_x = ScreenSettings.WIDTH - self.rect.width
        max_y = UISettings.BANK_RECT.top - self.rect.height
        # clamp x and y into [0, max]
**Why:** Fixes the known-issue bug where a dragged component could be
dropped behind the toolbox or off any screen edge. Helper reads bounds
from ScreenSettings and UISettings.BANK_RECT.top so the workspace bottom
is the toolbox top, not the screen bottom. Also added the explicit
`return None` from the polish list so the docstring's `str | None` contract
is honest at a glance.
**Editor:** Claude (Opus)

## 2026-05-01 — Wiring (Wire + WireManager)

**File:** settings.py
**Lines (at time of edit):** 76-85 (new WireSettings class)
**After:**
    class WireSettings:
        COLOR = ColorSettings.WORD_COLORS["BLACK"]
        GHOST_COLOR = ColorSettings.WORD_COLORS["GRAY"]
        THICKNESS = 3
        HIT_THRESHOLD = 6
**Why:** Constants for wire rendering and right-click hit-test, kept out
of code per the no-magic-numbers rule.
**Editor:** Claude (Opus)

**File:** wires.py
**Lines (at time of edit):** (new file, ~255 lines)
**After:**
    class Wire:
        # source: OUTPUT port, target: INPUT port. Stores Port refs only,
        # never cached coordinates, so the line follows when either parent
        # is dragged. hit() implements point-to-segment distance.

    class WireManager:
        # Owns committed wires + an in-flight pending_source + cursor_pos.
        # handle_event:
        #   MOUSEMOTION  -> tracks cursor for ghost line, never consumes
        #   LEFT_DOWN    -> if a port is hit, start wiring, consume
        #   LEFT_UP      -> if pending_source: try to commit on a valid
        #                   target port (output<->input, different parents),
        #                   replacing any prior wire on the same input.
        #                   Drop pending_source either way.
        #   RIGHT_DOWN   -> cancel pending, else delete wire under cursor.
        # drop_wires_for_component(comp): purge wires touching a deleted
        # component so wires don't dangle on freed Port refs.
**Why:** Implements the "Next — Wiring" roadmap item end-to-end: ghost
line during drag, output↔input validation with auto-swap so the user can
drag from either end, one-incoming-per-input enforcement, right-click
delete on a wire (with hit threshold so the user doesn't have to land on
the line exactly), and right-click cancel of an in-flight drag.
WireManager keeps wiring concerns off GameManager per the architectural
rules.
**Editor:** Claude (Opus)

**File:** main.py
**Lines (at time of edit):** 10 (import), 35 (own self.wires),
89-91 (route events to wires first), 107-109 (drop wires on component
delete), 142 (draw wires above components and below the bank)
**Why:** Hooks WireManager into GameManager: events go through wires
before bank/components so a click on a port starts a wire (not a drag),
deleting a component drops its attached wires, and wires render on top
of components but under the toolbox bank rectangle.
**Editor:** Claude (Opus)

## 2026-05-02 — Live signal state: Port.live, SignalManager, Switch + LED

**File:** settings.py
**Lines (at time of edit):** 38-48 (UISettings), 67-70 (ComponentSettings),
88-101 (WireSettings), 104-127 (new SwitchSettings + LedSettings)
**Before:**
    class UISettings:
        BANK_HEIGHT = 100
        ...
        BANK_RECT = pygame.Rect(...)

    class ComponentSettings:
        ...
        PORT_HIGHLIGHT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
        PORT_RADIUS = 10

    class WireSettings:
        COLOR = ColorSettings.WORD_COLORS["BLACK"]
        GHOST_COLOR = ColorSettings.WORD_COLORS["GRAY"]
        THICKNESS = 3
        HIT_THRESHOLD = 6
**After:**
    class UISettings:
        ...
        BANK_PADDING_X = 20
        BANK_TEMPLATE_GAP = 20

    class ComponentSettings:
        ...
        PORT_HIGHLIGHT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
        PORT_LIVE_COLOR = ColorSettings.WORD_COLORS["GREEN"]
        PORT_RADIUS = 10

    class WireSettings:
        COLOR = ...
        LIVE_COLOR = ColorSettings.WORD_COLORS["GREEN"]
        ...

    class SwitchSettings:  # SIZE/OFF_COLOR/ON_COLOR/BORDER...
    class LedSettings:     # SIZE/OFF_COLOR/ON_COLOR/BORDER...
**Why:** PORT_LIVE_COLOR and WIRE LIVE_COLOR drive the green-when-HIGH
visual feedback added in this pass. Switch/LedSettings keep all the new
component constants (size, ON/OFF body colors, border) out of code per
the no-magic-numbers rule. UISettings.BANK_PADDING_X / BANK_TEMPLATE_GAP
replace the literal 20 / 25 that ComponentBank used to hard-code for
positioning a single template — needed now that the bank holds three
templates side-by-side. Also dropped the obsolete "Reserve green/red for
future live-signal phase" line from PORT_HIGHLIGHT_COLOR's comment since
this commit is that future.
**Editor:** Claude (Opus 4.7)

**File:** elements.py
**Lines (at time of edit):** 5-13 (imports), 43-49 (Port.__init__),
73-93 (Port.draw), 146-150 (Component.__init__),
168-193 (new Component.update_logic + _on_click hook),
195-234 (Component.draw split into draw + _draw_body),
245-269 (Component.handle_event click-vs-drag tracking),
291-415 (new Switch + LED classes)
**Before:**
    class Port:
        ...
        self.hovered = False        # only hover state lived here

        def draw(self, surface):
            color = (PORT_HIGHLIGHT_COLOR
                     if self.hovered else PORT_COLOR)
            pygame.draw.circle(...)

    class Component:
        # had: __init__, _build_ports, draw, handle_event, _clamp_to_workspace
        # draw drew rect body inline; no update_logic, no click hook.
**After:**
    class Port:
        ...
        self.hovered = False
        self.live = False           # NEW: per-frame HIGH/LOW state

        def draw(self, surface):
            if self.hovered:    color = PORT_HIGHLIGHT_COLOR
            elif self.live:     color = PORT_LIVE_COLOR
            else:               color = PORT_COLOR
            pygame.draw.circle(...)

    class Component:
        ...
        self._moved_while_dragging = False  # NEW: click-vs-drag tracker

        def update_logic(self, output_buffer):
            a, b, out = self.ports
            output_buffer[out] = not (a.live and b.live)

        def _on_click(self):  # default no-op
            pass

        def draw(self, surface):
            for port in self.ports: port.draw(surface)
            self._draw_body(surface)         # NEW: delegated body
            ...                              # name + hover labels unchanged

        def _draw_body(self, surface):       # NEW
            pygame.draw.rect(...)            # rect body + border

        def handle_event(self, event):
            # MOUSEBUTTONDOWN now resets _moved_while_dragging
            # MOUSEMOTION sets it True while dragging
            # MOUSEBUTTONUP fires _on_click() iff dragging and not moved

    class Switch(Component):                 # NEW
        # one OUTPUT port, circle body, _on_click toggles _state,
        # update_logic writes _state to its OUTPUT port.

    class LED(Component):                    # NEW
        # one INPUT port, circle body whose color reflects port.live,
        # update_logic is a no-op (no OUTPUT to drive).
**Why:** Implements the "Now — Live signal state" roadmap item end-to-end.
Port gains a per-frame `live` flag drawn green when HIGH so signal
propagation reads at a glance. Component grows update_logic (default 2-
input NAND) and a `_draw_body` hook so the rectangular default can be
swapped for a circle without rewriting draw(). The `_on_click` hook plus
`_moved_while_dragging` tracker lets Switch toggle on a stationary click
while still allowing drag, without duplicating Component.handle_event.
Switch + LED are concrete subclasses fulfilling the user's "dedicated IN
and OUT components" requirement (see TODO.md "Now" item) — circles for
now, replacing the original "click an unconnected input port to toggle"
plan from the same bullet because Switch/LED are clearer to students and
support multiple drives without ambiguity. update_logic is overridden in
Switch (drives output from `_state`) and in LED (no-op so the inherited
NAND code doesn't run on a single-port component).
**Editor:** Claude (Opus 4.7)

**File:** signals.py
**Lines (at time of edit):** (new file)
**After:**
    class SignalManager:
        def update(self, components, wires):
            output_buffer = {}
            for comp in components:
                comp.update_logic(output_buffer)        # phase 1: read
            for port, value in output_buffer.items():
                port.live = value                        # phase 2: write
            for comp in components:
                for port in comp.ports:
                    if port.direction == Port.INPUT:
                        port.live = False                # reset inputs
            for wire in wires:
                wire.target.live = wire.source.live      # phase 3: wires
**Why:** Two-phase propagation as spec'd in TODO.md so SR latches and
other feedback circuits behave (gate evaluation order would otherwise
change the result). Inputs are reset before wire propagation so a port
that lost its wire reads LOW instead of latching its prior value.
SignalManager is its own class per the architectural rule that
GameManager stay light — main.py just calls self.signals.update(...) in
_update_world.
**Editor:** Claude (Opus 4.7)

**File:** wires.py
**Lines (at time of edit):** 53-69 (Wire.draw)
**Before:**
    pygame.draw.line(surface, WireSettings.COLOR,
                     self.source.center, self.target.center,
                     WireSettings.THICKNESS)
**After:**
    color = (WireSettings.LIVE_COLOR
             if self.source.live else WireSettings.COLOR)
    pygame.draw.line(surface, color, ...)
**Why:** A wire whose source is HIGH should read as continuous green from
output port, through the wire, into the receiving input port. Same color
as PORT_LIVE_COLOR by design.
**Editor:** Claude (Opus 4.7)

**File:** ui.py
**Lines (at time of edit):** 1-95 (full rewrite of ComponentBank for
multi-template support; was a 28-line single-template class)
**Before:**
    class ComponentBank:
        def __init__(self):
            self.rect = UISettings.BANK_RECT
            self.template = Component(20, self.rect.y + 25, name="NAND")

        def draw(self, surface):
            ...
            self.template.draw(surface)

        def handle_event(self, event, components_list):
            if click on self.template:
                spawn Component at event.pos
**After:**
    class ComponentBank:
        TEMPLATE_CLASSES = (Switch, Component, LED)
        # __init__ builds self.templates via _build_templates
        # _build_templates lays them left-to-right, vertically centered
        # draw iterates self.templates
        # handle_event iterates self.templates, uses type(tpl)(x, y) so
        # the spawned component matches the clicked template's class.
        # Spawn forces _moved_while_dragging=True so a stationary click
        # on a template doesn't trigger _on_click on the spawned Switch.
**Why:** Live signal state needs Switch and LED to be addable to the
workspace, which means the toolbox has to hold more than one template.
The class-tuple + type(tpl) factory keeps it data-driven so adding a
fourth/fifth template later is one tuple entry. The
_moved_while_dragging suppression prevents an off-by-one UX bug where a
Switch dropped via a click-without-drag would immediately toggle ON;
spawn drags aren't initiated by the component's own MOUSEBUTTONDOWN so
they should never fire _on_click.
**Editor:** Claude (Opus 4.7)

**File:** main.py
**Lines (at time of edit):** 8 (import), 37 (own self.signals),
128-130 (_update_port_hover walks self.bank.templates instead of
self.bank.template), 136-143 (_update_world drives the simulation)
**Before:**
    from ui import ComponentBank
    ...
    self.wires = WireManager()

    def _update_port_hover(self, mouse_pos):
        ...
        for port in self.bank.template.ports:
            port.hovered = port.rect.collidepoint(mouse_pos)

    def _update_world(self):
        pass
**After:**
    from signals import SignalManager
    from ui import ComponentBank
    ...
    self.signals = SignalManager()

    def _update_port_hover(self, mouse_pos):
        ...
        for tpl in self.bank.templates:
            for port in tpl.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)

    def _update_world(self):
        self.signals.update(self.components, self.wires.wires)
**Why:** Hooks SignalManager into the per-frame loop and updates the
hover walker for the new multi-template bank. _update_world used to be
a pass; now it drives the simulation, leaving the rest of the game
loop unchanged.
**Editor:** Claude (Opus 4.7)

## 2026-05-01 — Polish: default width/height constants, drop super() in CRT

**File:** settings.py
**Lines (at time of edit):** 49-52 (added under ComponentSettings)
**Before:**
    class ComponentSettings:
        COLOR = ...
**After:**
    class ComponentSettings:
        DEFAULT_WIDTH = 100
        DEFAULT_HEIGHT = 60
        COLOR = ...
**Why:** Polish item — the literal 100/60 in Component.__init__ defaults
were magic numbers per the no-magic-numbers rule.
**Editor:** Claude (Opus)

**File:** elements.py
**Lines (at time of edit):** 112-126 (Component.__init__ defaults)
**Before:**
    def __init__(self, x, y, width=100, height=60, name="NAND"):
        ...
        self.rect = pygame.Rect(x, y, width, height)
**After:**
    def __init__(self, x, y, width=None, height=None, name="NAND"):
        ...
        if width is None:  width  = ComponentSettings.DEFAULT_WIDTH
        if height is None: height = ComponentSettings.DEFAULT_HEIGHT
        self.rect = pygame.Rect(x, y, width, height)
**Why:** Default-to-None keeps the sentinel out of the call signature
while still letting callers pass an explicit size (ComponentBank does).
Backwards compatible with both `Component(x, y)` and
`Component(x, y, w, h)`.
**Editor:** Claude (Opus)

**File:** crt.py
**Lines (at time of edit):** 17 (deleted)
**Before:**
        super().__init__()
        self.screen = screen
**After:**
        self.screen = screen
**Why:** CRT inherits from object implicitly, so super().__init__() is a
no-op. Polish item from the TODO. Removed.
**Editor:** Claude (Opus)
## 2026-05-02 — Annotation text boxes (TextBox + TextBoxManager)

**File:** settings.py
**Lines (at time of edit):** 130-163 (new TextBoxSettings class appended above AudioSettings)
**After:**
    class TextBoxSettings:
        WIDTH = 180
        MIN_HEIGHT = 32
        PADDING = 6
        BODY_COLOR = (40, 40, 40)
        BORDER_COLOR = ColorSettings.WORD_COLORS["GRAY"]
        BORDER_THICKNESS = 1
        BORDER_FOCUSED_COLOR = ColorSettings.WORD_COLORS["WHITE"]
        TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
        PLACEHOLDER_COLOR = ColorSettings.WORD_COLORS["GRAY"]
        PLACEHOLDER_TEXT = "Type here..."
        FONT = AssetPaths.FONT
        FONT_SIZE = 12
        CARET_COLOR = ColorSettings.WORD_COLORS["WHITE"]
        CARET_WIDTH = 2
        CARET_BLINK_MS = 1000
**Why:** All visual + interaction constants for the new annotation text box
component, kept out of code per the no-magic-numbers rule. WIDTH is fixed
because the box wraps text and grows downward; MIN_HEIGHT keeps an empty
box visibly grabbable. BORDER_FOCUSED_COLOR (white vs. resting gray) gives
the user obvious feedback about which box is receiving keystrokes. CARET
constants drive the half-period blink in TextBox._caret_visible.
**Editor:** Claude (Opus 4.7)

**File:** fonts.py
**Lines (at time of edit):** 3 (import), 21 (class attr), 39-42 (init body)
**Before:**
    from settings import ComponentSettings
    ...
    component_label = None
    port_label = None
    ...
        cls.port_label = pygame.font.Font(
            ComponentSettings.FONT,
            ComponentSettings.PORT_LABEL_FONT_SIZE,
        )
**After:**
    from settings import ComponentSettings, TextBoxSettings
    ...
    component_label = None
    port_label = None
    text_box = None
    ...
        cls.text_box = pygame.font.Font(
            TextBoxSettings.FONT,
            TextBoxSettings.FONT_SIZE,
        )
**Why:** Same one-load-shared-everywhere pattern already used for
component_label and port_label. Every TextBox renders many lines per
frame; loading one Font shared across the whole game means we don't pay
the .ttf parse cost per box.
**Editor:** Claude (Opus 4.7)

**File:** text_boxes.py
**Lines (at time of edit):** (new file, ~475 lines)
**After:**
    class TextBox:
        # Owns: rect (draggable), text (editable string), focused, dragging,
        # offset_x/y, _focus_tick (for caret blink), _lines (cached wrap).
        # API for the manager: focus / blur / start_drag / end_drag /
        # handle_motion / handle_key / hit / draw.
        # _wrap_lines: greedy word-wrap into WIDTH - 2*PADDING, force-breaks
        # words wider than the inner width so nothing overflows.
        # _resize_to_lines: rect.height = max(MIN_HEIGHT, lines * lineh + 2*pad).
        # _clamp_to_workspace: same recipe as Component (above the bank).

    class TextBoxManager:
        # Owns: text_boxes list (oldest first / newest on top), focused box.
        # spawn_at(pos): create + clamp + focus.
        # handle_event(event):
        #   KEYDOWN  -> forward to focused (Esc unfocuses); consume if focused.
        #   MOTION   -> forward to dragging box; never consume (port hover
        #              and wire ghost both depend on seeing every motion).
        #   LEFT_DOWN-> focus + start drag on topmost hit; consume on hit,
        #              else blur and let the click fall through.
        #   RIGHT_DOWN -> delete topmost hit; blur if it was focused.
        #   LEFT_UP  -> end drag on every box; never consume.
        # Topmost-first iteration so a box drawn on top wins clicks.
**Why:** Implements the "Text boxes" item from TODO.md "Later". TextBox is
its own class with its own rect/text/focus/drag state, kept off Component
because it has no ports, no signal, no toolbox template, and its event
model (focus + keystroke editing + click-to-blur-on-empty-space) doesn't
match Component's. TextBoxManager owns the collection plus focus routing
so GameManager stays light per the architectural rules. Routing every
event through the manager first lets it intercept keys when a box is
focused (so typing 'n' in a label doesn't spawn a NAND) and intercept
clicks that land on a box (so a label sitting over a port edits the
label rather than starting a wire underneath). MOUSEMOTION never gets
consumed because the wire ghost cursor and the port hover loop both
depend on seeing every motion event, regardless of whether a text box
is mid-drag.
**Editor:** Claude (Opus 4.7)

**File:** main.py
**Lines (at time of edit):** 9 (import), 41 (own self.text_boxes),
63-82 (_process_events routes events through text_boxes first),
98-99 (K_t spawn shortcut in _handle_keydown),
172-177 (text_boxes.draw above wires, below bank in _draw)
**Before:**
    from signals import SignalManager
    from ui import ComponentBank
    ...
    self.signals = SignalManager()
    ...
    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type in (...mouse...):
                self._handle_mouse(event)
    ...
    def _handle_keydown(self, event):
        ...
        if event.key == pygame.K_n:
            self.components.append(Component(50, 50))
    ...
    def _draw(self):
        ...
        self.wires.draw(self.screen)
        self.bank.draw(self.screen)
**After:**
    from signals import SignalManager
    from text_boxes import TextBoxManager
    from ui import ComponentBank
    ...
    self.signals = SignalManager()
    self.text_boxes = TextBoxManager()
    ...
    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game(); continue
            if self.text_boxes.handle_event(event):
                continue   # box absorbed it (focused KEYDOWN, click on a box)
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type in (...mouse...):
                self._handle_mouse(event)
    ...
    def _handle_keydown(self, event):
        ...
        if event.key == pygame.K_t:
            self.text_boxes.spawn_at(pygame.mouse.get_pos())
    ...
    def _draw(self):
        ...
        self.wires.draw(self.screen)
        self.text_boxes.draw(self.screen)   # above wires, below bank
        self.bank.draw(self.screen)
**Why:** Hooks the new manager into the game loop. Routing every event
through text_boxes.handle_event first is what keeps focused-box typing
from leaking into the keyboard shortcuts (and what stops a click on a
box from starting a wire on a port underneath). The K_t shortcut mirrors
the existing K_n NAND-spawn pattern so the muscle memory carries over.
Drawing above wires/components ensures labels stay legible even if a
wire passes under them; drawing below the bank costs nothing since
text boxes are clamped out of the bank area but keeps the toolbox
visually authoritative.
**Editor:** Claude (Opus 4.7)

## 2026-05-02 — Roadmap refresh + README catch-up (docs only, no code)

**File:** docs/TODO.md
**Lines (at time of edit):** 1-11 (intro), full restructure to ~314 lines
**Before:**
    # Roadmap
    ## Done — Port highlighting / Port hover labels / Wiring / Live signal state / Text boxes
    ## Later  (5 bullets: save/load, main menu, save-as-component, toolbox redesign, toolbox menu button)
    ## Polish / tech debt
    ## Known issues
**After:**
    # Roadmap (intro now states the mouse-first design principle)
    ## Now — Toolbar TEXT button   (mouse path for what was hotkey-only)
    ## Now — Force uppercase in text boxes
    ## Next — Bottom-left popup menu (file ops home)
    ## Done — (existing five Done sections, unchanged)
    ## Later — save/load (with embed-don't-reference note),
              project main menu (New/Load/Options/Quit),
              Save-as-Component (with pin selection, color picker,
                                 rename, AND/OR/NOT auto-detect sub-bullets),
              Toolbox redesign (with brainstormed approaches inline)
    ## Brainstorming — dynamic text-box width, IN/OUT visual redesign
                       (Switch as toggle, LED as bulb), pin-to-toolbar,
                       wire bending, undo/redo, trash mode, shortcut overlay
    ## Far future — tutorials, puzzles, library sharing, sound,
                    multi-bit busses
    ## Polish / tech debt — added unit-test bullet + try/except wrapper
    ## Known issues — added "text boxes accept lowercase" and
                      "text boxes are mouse-inaccessible" tied back to
                      the new Now items
**Why:** User feedback after the text-box session: (1) mouse-first is the
design principle, hotkeys are bonus — every keyboard-only entry point
needs a clickable equivalent (immediate gap: text boxes can't be spawned
without **T**); (2) text boxes should be uppercase only to match every
other label in the workspace; (3) the toolbar will eventually need a
companion menu in the bottom-left for file ops, and the toolbox itself
will need a redesign (scroll vs shrink vs sidebar — left as
brainstorming until we have real component-count data); (4) the project
needs a main-menu front door (New / Load / Options / Quit); (5)
Save-as-Component should let students pick color, override the name,
but auto-default to the recognized gate name if the truth table matches
NOT/AND/OR/NAND/NOR/XOR/XNOR — a discoverable reward; (6) tutorials
and puzzles are explicitly far-future. Also added new sections
("Brainstorming" for design ideas not yet committed, "Far future" for
stretch goals) so the TODO can keep absorbing ideas without losing the
near-term ordering. Reordered so Now / Next sit above Done, making it
obvious at a glance what to pick up.
**Editor:** Claude (Opus 4.7)

**File:** README.md
**Lines (at time of edit):** 20-34 (Current Status + Controls), 47-59 (Project Layout)
**Before:**
    ## Current Status
    Early prototype. The workspace, toolbox, NAND component and drag-and-drop
    are in place. Wiring, port logic, and saving are not yet implemented...

    ## Controls
    | Action | Input |
    | Spawn a NAND from the toolbox | Left-click the toolbox template |
    | Move a component | Left-click and drag |
    | Delete a component | Right-click |
    | Spawn a NAND at (50, 50) | `N` |
    | Toggle fullscreen | `F11` |
    | Quit | `Esc` |

    ## Project Layout
    main.py / elements.py / ui.py / crt.py / settings.py / assets/ / docs/
**After:**
    ## Current Status
    Working prototype. Drag-and-drop, wiring, port logic, live signal
    propagation, the Switch / LED input-output components, and free-floating
    annotation text boxes are all in. Save / load and Save as Component
    (the keystone feature) are next; see docs/TODO.md...
    The program is designed to be fully usable with the mouse alone.
    Keyboard shortcuts exist as a convenience for power users but never
    replace a clickable equivalent.

    ## Controls
    ### Mouse
    (rows for: spawn from toolbox, move, toggle Switch, wire two ports,
     cancel in-flight wire, delete component/wire/text-box, edit text box,
     stop editing)
    ### Keyboard (power user)
    (rows for: N=NAND-at-50-50, T=text-box-at-cursor, F11=fullscreen,
     Esc=quit-when-no-textbox-focused)

    ## Project Layout
    main.py / elements.py / wires.py / signals.py / text_boxes.py /
    ui.py / fonts.py / crt.py / settings.py / assets/ / docs/
**Why:** The Current Status paragraph claimed wiring / port logic / saving
were unimplemented; wiring and port logic shipped 2026-05-01 and live
signal state + text boxes shipped 2026-05-02. Controls table was missing
every interaction added since v0 (wiring, Switch toggle, text editing,
right-click wire delete). Project Layout was missing four files. Split
Controls into Mouse and Keyboard tables to make the mouse-first design
principle visible — students see the Mouse table first; the keyboard
table is explicitly labeled "power user" and exists alongside, not
instead of, the mouse path. Quit row notes the "only when no text box is
focused" caveat that's already in the implementation.
**Editor:** Claude (Opus 4.7)
