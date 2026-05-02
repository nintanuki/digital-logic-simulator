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