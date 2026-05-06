# Change Log

This file is an append-only record of every code change made to Circuit Builder
by a human, AI assistant, or copilot tool. Read it before making changes so you
know the current state of the codebase.

## Format

Each entry covers one logical change (which may touch multiple files). Use the
template below, with one `**File:** ... **Why:** ...` block per file touched.

    ## YYYY-MM-DD HH:MM TZ — short summary

    **File:** path/to/file.py
    **Date and Time:** YYYY-MM-DD HH:MM TZ
    **Lines (at time of edit):** 38-52 (modified)
    **Before:**
        [old code]
    **After:**
        [new code]
    **Why:** explanation
    **Editor:** name of human or AI model

### Date and time format

Both the section header and the per-file `Date and Time:` field are
**required** and must follow ISO 8601 calendar date plus a 24-hour clock
and a timezone abbreviation: `YYYY-MM-DD HH:MM TZ`. Examples:

    2026-05-02 16:18 PDT
    2026-05-02 23:18 UTC

The timezone is required so entries from collaborators in different
zones sort and compare correctly. The per-file `Date and Time:` field is
not redundant with the section header — a single logical change may span
hours and touch several files in sequence, and the per-file timestamp
pinpoints when each individual edit landed. Use a 24-hour clock (no AM/PM,
no `@` separator, no slashes); it is unambiguous and sortable as plain text.

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
* Older entries (pre-2026-05-02) predate the timezone-aware format and use
  date-only headers. Do not retroactively edit them; the rule applies to all
  new entries from 2026-05-02 onward.
* **New entries go at the bottom of the file**, oldest-first. The instructions
  and format guide stay at the top so they are the first thing a reader (human
  or AI) sees when opening the file.

---

## 2026-05-06 12:54 UTC — Normalize main.py docstring style

**File:** main.py
**Date and Time:** 2026-05-06 12:54 UTC
**Lines (at time of edit):** 42-655 (modified)
**Before:**
    def __init__(self) -> None:
        """Initialize pygame, core subsystems, and cross-system wiring.
        Returns:
            None
        """

    def _handle_mouse(self, event: pygame.event.Event) -> None:
        """Pass mouse events to the component manager or components directly.
        Args:
            event: Pygame mouse event.
        """
**After:**
    def __init__(self) -> None:
        """Initialize pygame, core subsystems, and cross-system wiring."""

    def _handle_mouse(self, event: pygame.event.Event) -> None:
        """
        Pass mouse events to the component manager or components directly.

        Args:
            event: Pygame mouse event.
        """
**Why:** Applied a consistent docstring style in `main.py` per project preference: single-line docstrings stay single-line when there are no sections, and sectioned docstrings use multiline triple-quote blocks. Removed redundant `Returns: None` sections because `-> None` already communicates return type.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-06 12:57 UTC — Collapse no-section function docstrings to one line

**File:** main.py
**Date and Time:** 2026-05-06 12:57 UTC
**Lines (at time of edit):** 175-213 (modified)
**Before:**
    def save_as_component(self) -> None:
        """Open the SAVE AS COMPONENT dialog.
        ...
        """

    def _clear_workspace(self) -> None:
        """Reset the live workspace to an empty canvas.
        ...
        """
**After:**
    def save_as_component(self) -> None:
        """Open the SAVE AS COMPONENT dialog."""

    def _clear_workspace(self) -> None:
        """Reset the live workspace to an empty canvas."""
**Why:** Enforced the preferred docstring style where functions with no `Args:` and no `Returns:` use a single-line docstring.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-06 18:00 UTC — Wall-anchored IN/OUT, redesigned LED, TOOLBOX + > IN/OUT bank popups

**File:** settings.py
**Date and Time:** 2026-05-06 18:00 UTC
**Lines (at time of edit):** 80, 218-237 (modified); 308-376 (new)
**Before:**
    BANK_LED_SHIFT_X = 10
    ...
    class LedSettings:
        SIZE = 60
        BULB_RADIUS = 20
        BULB_Y_OFFSET = 22
        BASE_WIDTH = 18
        BASE_HEIGHT = 10
        BASE_Y_OFFSET = 46
        BASE_CORNER = 3
        ...
        OFF_BASE_COLOR = (40, 40, 40)
        ON_BASE_COLOR = (175, 145, 25)
**After:**
    BANK_BUTTON_GROUP_GAP = 24
    ...
    class LedSettings:
        SIZE = 60
        BULB_RADIUS = 22
        GLOW_EXTRA_RADIUS = 7
        OFF_GLOBE_COLOR = (55, 55, 55)
        ON_GLOBE_COLOR = (255, 220, 50)
        GLOW_COLOR = (255, 200, 30)
        BORDER_COLOR = ColorSettings.WORD_COLORS["BLACK"]
        BORDER_THICKNESS = 2

    class WallDragBarSettings: ...
    class BankPopupButtonSettings: ...
    class BankToolboxButtonSettings: ...
    class BankIOButtonSettings: ...
**Why:** Dropped the awkward base/lead from the LED visual (the source of the "drooping port" complaint), centered the globe vertically so the INPUT port lines up with its equator, and added shared visual constants for the wall-side drag bar plus the new bottom-bank popup buttons (TOOLBOX, > IN/OUT).
**Editor:** GitHub Copilot (Claude Opus 4.7)

**File:** core/elements.py
**Date and Time:** 2026-05-06 18:00 UTC
**Lines (at time of edit):** 6-15, 18-42 (new helper); 295-410 (Switch overrides); 495-624 (LED rewrite)
**Before:**
    class Switch(Component):
        def __init__(self, x, y): ...
        def _draw_body(self, surface): ...   # body was the drag handle
    class LED(Component):
        def _draw_body(self, surface):
            bulb_cy = r.y + LedSettings.BULB_Y_OFFSET
            ... # globe in upper portion + base/lead rectangle below
**After:**
    def _draw_wall_drag_bar(surface, bar_rect, hovered): ...
    class Switch(Component):
        WALL_SIDE = "LEFT"
        bar_hovered = False
        def _clamp_to_workspace(self):
            self.rect.x = 0
            ...
        @property
        def drag_bar_rect(self): ...
    class LED(Component):
        WALL_SIDE = "RIGHT"
        def _clamp_to_workspace(self):
            self.rect.x = ScreenSettings.WIDTH - self.rect.width
            ...
        def _draw_body(self, surface):
            bulb_cy = r.centery   # globe centered, port on equator
            ...
            _draw_wall_drag_bar(surface, self.drag_bar_rect, self.bar_hovered)
**Why:** IN/OUT components now glue to the wall they belong to (Switch left, LED right) and only move vertically. The wall-side bar is the sole drag handle so a body click on a Switch unambiguously toggles it, and the LED visual drops the awkward base/lead in favor of a centered globe so its INPUT port no longer "droops" below the bulb.
**Editor:** GitHub Copilot (Claude Opus 4.7)

**File:** core/workspace_controller.py
**Date and Time:** 2026-05-06 18:00 UTC
**Lines (at time of edit):** 36-43, 56-72 (modified); 152-180, 195-218, 229-260 (modified/new)
**Before:**
    self._click_candidate_component = None
    ...
    for comp in self._components:
        for port in comp.ports:
            port.hovered = port.rect.collidepoint(mouse_pos)
    ...
    def handle_group_drag_event(self, event):
        ... # no wall-collision pass; on-click fires even if click was on bar
**After:**
    self._click_candidate_component = None
    self._click_started_on_bar = False
    ...
    for comp in self._components:
        for port in comp.ports:
            port.hovered = port.rect.collidepoint(mouse_pos)
        if hasattr(comp, "drag_bar_rect"):
            comp.bar_hovered = comp.drag_bar_rect.collidepoint(mouse_pos)
    ...
    def handle_group_drag_event(self, event):
        ...
        self._resolve_wall_collisions()
        ...
        if not self._group_drag_moved and not self._click_started_on_bar:
            ... # only fire _on_click for body-clicks
    def _resolve_wall_collisions(self): ...
**Why:** Drives the wall drag-bar hover highlight, suppresses Switch toggle when the user grabs the bar, and forbids dragged wall components from passing through other same-wall components (so users must rewire instead of overlapping IN/OUT).
**Editor:** GitHub Copilot (Claude Opus 4.7)

**File:** ui/bank.py
**Date and Time:** 2026-05-06 18:00 UTC
**Lines (at time of edit):** 4-15, 73-104, 127-167, 252-256, 311-330, 358-377, 416-650 (modified/new)
**Before:**
    TEMPLATE_CLASSES = (Switch, Component, LED)
    def __init__(self, text_boxes): ...
    def _build_templates(self):
        ...
        if cls is LED:
            tpl.rect.x += UISettings.BANK_LED_SHIFT_X
**After:**
    TEMPLATE_CLASSES = (Component,)
    def __init__(self, text_boxes, components_provider=None,
                 on_save_component=None, on_spawn_wall_component=None): ...
    def _build_popup_buttons(self): ...      # TOOLBOX + > IN/OUT
    def _draw_popup_buttons(self, surface): ...
    def _handle_popup_event(self, event): ... # consumes clicks ahead of templates
    def _spawn_switch_on_left_wall(self): ...
    def _spawn_led_on_right_wall(self): ...
    def _next_wall_spawn_y(...): ...         # auto-stack non-overlapping
**Why:** Switches and LEDs are no longer loose draggable templates on the bottom bank; they're spawned exclusively through the new > IN/OUT popup. The TOOLBOX popup hosts SAVE COMPONENT (and a placeholder LOAD COMPONENT for a future feature), pushing the remaining template row to the right of the popup-button cluster.
**Editor:** GitHub Copilot (Claude Opus 4.7)

**File:** main.py
**Date and Time:** 2026-05-06 18:00 UTC
**Lines (at time of edit):** 56-63, 96-127, 158-179 (modified)
**Before:**
    self.bank = ComponentBank(self.text_boxes)
    ...
    "items": tuple(
        (item_id, label, "ESC" if item_id == "quit" else "")
        for item_id, label in MenuButtonSettings.ITEMS
    ),
    "actions": {..., "save_as_component": self.save_as_component, ...},
**After:**
    self.bank = ComponentBank(
        self.text_boxes,
        components_provider=lambda: self.components,
        on_save_component=self.save_as_component,
        on_spawn_wall_component=self._on_bank_spawn,
    )
    ...
    file_items = tuple(
        (item_id, label, "ESC" if item_id == "quit" else "")
        for item_id, label in MenuButtonSettings.ITEMS
        if item_id != "save_as_component"
    )
    ...
    def _on_bank_spawn(self, component):
        self.history.push(PlaceComponent(self.components, self.wires, component))
        self.workspace_interaction.set_selected_components([component])
**Why:** Wires the new bank callbacks so > IN/OUT spawns reach the workspace and the spawn is undoable, and removes SAVE AS COMPONENT from the FILE menu so the only entry point is the new TOOLBOX popup (avoiding duplicate affordances).
**Editor:** GitHub Copilot (Claude Opus 4.7)

---

## 2026-05-05 13:58 UTC — Move Fonts module from root into ui package

**File:** ui/fonts.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** (new file)
**Before:**
    (file did not exist)
**After:**
    import pygame
    from settings import ComponentSettings, TextBoxSettings

    class Fonts:
        ...
        @classmethod
        def init(cls):
            pygame.font.init()
            cls.component_label = pygame.font.Font(...)
            cls.port_label = pygame.font.Font(...)
            cls.text_box = pygame.font.Font(...)
**Why:** Moved the shared Fonts module into the ui package so UI concerns are grouped under `ui/` instead of the repository root.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** fonts.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** (deleted)
**Before:**
    import pygame
    from settings import ComponentSettings, TextBoxSettings

    class Fonts:
        ...
        @classmethod
        def init(cls):
            pygame.font.init()
            cls.component_label = pygame.font.Font(...)
            cls.port_label = pygame.font.Font(...)
            cls.text_box = pygame.font.Font(...)
**Why:** Removed the root-level Fonts module after relocating it to `ui/fonts.py`.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** 14 (modified)
**Before:**
    from fonts import Fonts
**After:**
    from ui.fonts import Fonts
**Why:** Updated import path to the relocated Fonts module.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** core/elements.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** 4 (modified)
**Before:**
    from fonts import Fonts
**After:**
    from ui.fonts import Fonts
**Why:** Updated import path to the relocated Fonts module.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/bank.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** 5 (modified)
**Before:**
    from fonts import Fonts
**After:**
    from ui.fonts import Fonts
**Why:** Updated import path to the relocated Fonts module.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/project_dialogs.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** 3 (modified)
**Before:**
    from fonts import Fonts
**After:**
    from ui.fonts import Fonts
**Why:** Updated import path to the relocated Fonts module.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/quit_confirm_dialog.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** 3 (modified)
**Before:**
    from fonts import Fonts
**After:**
    from ui.fonts import Fonts
**Why:** Updated import path to the relocated Fonts module.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/save_component_dialog.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** 3 (modified)
**Before:**
    from fonts import Fonts
**After:**
    from ui.fonts import Fonts
**Why:** Updated import path to the relocated Fonts module.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/text_boxes.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** 4 (modified)
**Before:**
    from fonts import Fonts
**After:**
    from ui.fonts import Fonts
**Why:** Updated import path to the relocated Fonts module.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/top_menu_bar.py
**Date and Time:** 2026-05-05 13:58 UTC
**Lines (at time of edit):** 9 (modified)
**Before:**
    from fonts import Fonts
**After:**
    from ui.fonts import Fonts
**Why:** Updated import path to the relocated Fonts module.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 13:54 UTC — Clarify architecture rules and extract workspace interaction controller from GameManager

**File:** docs/TESTING.md
**Date and Time:** 2026-05-05 13:54 UTC
**Lines (at time of edit):** 19-29 (modified)
**Before:**
    * GameManager must be light, offload responsibilities to other classes
    * When possible classes should comminicate to eachother through GameManager.
**After:**
    * GameManager must be light, offload responsibilities to other classes
    * GameManager is an orchestrator, not a feature container.
    * GameManager should own app lifecycle, high-level state, and subsystem coordination.
    * Feature logic should live in the class that owns that feature.
    * State should live next to the behavior that uses it.
    * Avoid passing the full GameManager into other classes unless absolutely necessary.
    * Prefer explicit dependencies, narrow interfaces, and callbacks over giving a class access to all manager internals.
    * "Communicate through GameManager" means coordination, not global access to shared mutable state.
    * New features should not add large new blocks of logic directly into GameManager if a dedicated subsystem/controller is more appropriate.
    * Event handling, rendering, persistence, and UI state should be separated by responsibility as much as reasonably possible.
    * If a subsystem needs to trigger a cross-system action, prefer returning a result/action, calling a callback, or asking GameManager to coordinate it rather than directly reaching into another subsystem.
    * When possible classes should communicate to each other through GameManager.
**Why:** Clarified the architecture contract so "communicate through GameManager" is interpreted as orchestration and coordination, not broad shared-state access or passing the full manager into subsystems.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** core/workspace_controller.py
**Date and Time:** 2026-05-05 13:54 UTC
**Lines (at time of edit):** (new file)
**Before:**
    (file did not exist)
**After:**
    class WorkspaceInteractionController:
        def prune_selection(self) -> None: ...
        def delete_component_at_index(self, index: int) -> None: ...
        def delete_selected_components(self) -> None: ...
        def start_group_drag(self, mouse_pos: tuple[int, int], click_candidate) -> None: ...
        def handle_group_drag_event(self, event: pygame.event.Event) -> bool: ...
        def start_marquee(self, mouse_pos: tuple[int, int]) -> None: ...
        def handle_marquee_event(self, event: pygame.event.Event) -> bool: ...
        def draw_selection_marquee(self, screen: pygame.Surface) -> None: ...
**Why:** Extracted selection, drag, marquee, and component-delete interaction logic out of GameManager into a dedicated subsystem with explicit dependencies (components, wires, history), reducing GameManager size and coupling.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 13:54 UTC
**Lines (at time of edit):** 13, 24-29, 65-95, 232-239, 326-329, 395-547 (modified), 531-686 (deleted)
**Before:**
    self.selected_components = []
    self._marquee_start = None
    self._group_drag_anchor = None
    ...
    self._prune_selection()
    self._delete_selected_components()
    self._update_port_hover(event.pos)
    self._handle_group_drag_event(event)
    self._handle_marquee_event(event)
    self._draw_selection_marquee()
**After:**
    self.workspace_interaction = WorkspaceInteractionController(
        self.components,
        self.wires,
        self.history,
    )
    ...
    self.workspace_interaction.prune_selection()
    self.workspace_interaction.delete_selected_components()
    self.workspace_interaction.update_port_hover(event.pos, self.bank.templates)
    self.workspace_interaction.handle_group_drag_event(event)
    self.workspace_interaction.handle_marquee_event(event)
    self.workspace_interaction.draw_selection_marquee(self.screen)
**Why:** Reduced GameManager from feature-container behavior to coordinator behavior by delegating workspace interaction responsibilities to a dedicated controller and using explicit subsystem APIs for workspace clear/reset.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/bank.py
**Date and Time:** 2026-05-05 13:54 UTC
**Lines (at time of edit):** 87-114 (modified)
**Before:**
    self._templates_and_spawners = self._build_templates()
    self._protected_template_ids = {
        id(tpl) for tpl, _spawn in self._templates_and_spawners
    }
    self._drag_template = None
    self._drag_template_mouse_anchor = (0, 0)
    self._drag_template_rect_anchor = (0, 0)
**After:**
    self._templates_and_spawners = self._build_templates()
    self._protected_template_ids = set()
    self._refresh_protected_template_ids()
    self._drag_template = None
    self._drag_template_mouse_anchor = (0, 0)
    self._drag_template_rect_anchor = (0, 0)

    def reset_to_default_templates(self):
        self._templates_and_spawners = self._build_templates()
        self._refresh_protected_template_ids()
        self._drag_template = None
**Why:** Replaced GameManager's direct mutation of bank internals with an explicit reset API and ensured protected-template IDs are recomputed on reset, preventing stale protection state.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/text_boxes.py
**Date and Time:** 2026-05-05 13:54 UTC
**Lines (at time of edit):** 391-399 (added)
**Before:**
    # No manager-level clear API; caller had to mutate manager internals.
**After:**
    def clear_all(self):
        """Remove all text boxes and clear focus state."""
        self.text_boxes.clear()
        self._blur()
**Why:** Added an explicit lifecycle API so GameManager can clear text boxes through the owning subsystem instead of mutating internal fields directly.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** core/wires.py
**Date and Time:** 2026-05-05 13:54 UTC
**Lines (at time of edit):** 224-232 (added)
**Before:**
    # No manager-level clear API; caller had to set wire internals directly.
**After:**
    def clear_all(self):
        """Clear committed and in-flight wiring state."""
        self.wires.clear()
        self._cancel_pending_wire()
**Why:** Added an explicit lifecycle API so GameManager clears wiring state via WireManager, keeping state ownership with the subsystem.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 13:45 UTC — Add VIEW option to toggle CRT overlay

**File:** settings.py
**Date and Time:** 2026-05-05 13:45 UTC
**Lines (at time of edit):** 50, 94-99 (modified)
**Before:**
    class ScreenSettings:
        TITLE = "Digital Logic Simulator"
        CRT_ALPHA_RANGE = (75, 90)

    class TopMenuBarSettings:
        VIEW_LABEL = "VIEW"
        FILE_HIGHLIGHT_BG = COLOR_MENU_HIGHLIGHT
**After:**
    class ScreenSettings:
        TITLE = "Digital Logic Simulator"
        CRT_ENABLED_DEFAULT = True
        CRT_ALPHA_RANGE = (75, 90)

    class TopMenuBarSettings:
        VIEW_LABEL = "VIEW"
        VIEW_TOGGLE_FULLSCREEN_LABEL = "TOGGLE FULLSCREEN"
        VIEW_TOGGLE_FULLSCREEN_SHORTCUT = "F11"
        VIEW_TOGGLE_CRT_LABEL = "TOGGLE CRT"
        VIEW_TOGGLE_CRT_SHORTCUT = "F10"
        FILE_HIGHLIGHT_BG = COLOR_MENU_HIGHLIGHT
**Why:** Added centralized constants for VIEW menu labels/shortcuts and a default
CRT enabled flag so CRT toggling can be configured without hardcoded display text
in GameManager.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 13:45 UTC
**Lines (at time of edit):** 52, 128-146, 150-157, 447-448, 770-771 (modified)
**Before:**
    self.crt = CRT(self.screen)

    "view": {
        "items": (
            ("toggle_fullscreen", "TOGGLE FULLSCREEN", "F11"),
        ),
        "actions": {
            "toggle_fullscreen": pygame.display.toggle_fullscreen,
        },
    }

    if event.key == pygame.K_F11:
        pygame.display.toggle_fullscreen()

    self.top_menu_bar.draw()
    self.crt.draw()
**After:**
    self.crt = CRT(self.screen)
    self._crt_enabled = ScreenSettings.CRT_ENABLED_DEFAULT

    "view": {
        "items": (
            ("toggle_fullscreen", TopMenuBarSettings.VIEW_TOGGLE_FULLSCREEN_LABEL,
             TopMenuBarSettings.VIEW_TOGGLE_FULLSCREEN_SHORTCUT),
            ("toggle_crt", TopMenuBarSettings.VIEW_TOGGLE_CRT_LABEL,
             TopMenuBarSettings.VIEW_TOGGLE_CRT_SHORTCUT),
        ),
        "actions": {
            "toggle_fullscreen": pygame.display.toggle_fullscreen,
            "toggle_crt": self._toggle_crt,
        },
    }

    def _toggle_crt(self) -> None:
        self._crt_enabled = not self._crt_enabled

    if event.key == pygame.K_F11:
        pygame.display.toggle_fullscreen()
    if event.key == pygame.K_F10:
        self._toggle_crt()

    self.top_menu_bar.draw()
    if self._crt_enabled:
        self.crt.draw()
**Why:** Added a VIEW menu option that toggles the CRT effect at runtime, plus
a matching keyboard shortcut, while preserving fullscreen behavior.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 19:00 UTC — Restructure docs/TODO.md: replace pass-based planning with practical feature categories

**File:** docs/TODO.md
**Date and Time:** 2026-05-05 19:00 UTC
**Lines (at time of edit):** 1-520 (complete restructure)
**Before:** Pass-based organization (Pass 1, Pass 2, Pass 3, Pass 4, Pass 5, Pass 6, Pass 7+) with separate sections for Questions, Ideas, Issues/Bugs, Risks & Notes, Polish & Tech Debt.
**After:** Reorganized into practical feature categories:
  - Next Up (currently in progress)
  - Core Features (Foundation completed, Persistence in progress/planned, Persistence Polish planned)
  - Teaching Features (Tutorial System, Encyclopedia System, Puzzles & Challenges)
  - UI/UX Improvements (Pass 2 Remaining, Pass 6+ Enhancements)
  - Bugs / Issues (actual problems only)
  - Architecture Notes (design decisions and concerns)
  - Tech Debt / Polish (code quality items)
  - Open Questions / Decisions (pending design calls)
  - Ideas / Later (stretch goals)
**Why:** Pass-based structure was creating clutter, duplication, and stale planning artifacts. New feature-based roadmap is easier to scan, update, and maintain. Clearly separated scaffold from full features (tutorial scaffold vs. tutorial content expansion; encyclopedia scaffold vs. encyclopedia content expansion). Fixed encoding artifacts (replacement characters). Clarified Esc/quit behavior as completed with precise layered implementation detail. Removed duplication where items appeared both as completed in passes and as open bugs. Consolidated architecture notes into dedicated section. Improved readability throughout.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

## 2026-05-05 18:25 UTC — Update TODO: add issue for oversized components in toolbox

**File:** docs/TODO.md
**Date and Time:** 2026-05-05 18:25 UTC
**Lines (at time of edit):** 279-291 (added)
**Before:** Issues section ended with TOGGLE FULLSCREEN hardcoding issue.
**After:** Added new issue about components too big for the toolbox:
  - Describes symptom: rendered preview in toolbox may exceed toolbox dimensions
  - Lists possible solutions: scaling, clipping with scrollbar, expansion outside panel, limiting complexity
  - Marks as deferred pending classroom observation
**Why:** Proactive issue tracking for anticipated edge case when students build complex saved components that won't fit in the toolbox preview area. Documented options for future resolution without committing to a specific approach yet. Depends on real-world classroom usage patterns to determine priority and best solution.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

## 2026-05-05 18:20 UTC — Fix: move menu bar setup after history initialization

**File:** main.py
**Date and Time:** 2026-05-05 18:20 UTC
**Lines (at time of edit):** 73-96 (reordered)
**Before:** GameManager.__init__() called _setup_menu_bar() on line 75 before self.history was initialized on line 78, causing AttributeError when menu bar tried to reference self.history.undo and self.history.redo in actions dict.
**After:** Moved _setup_menu_bar() call to after history initialization (line 91). Menu bar setup now depends on history being available.
**Why:** Initialization order dependency bug. The menu bar definition references self.history.undo and self.history.redo in the actions dict, so history must exist before _setup_menu_bar() is called. Added clarifying comment "# -------- Menu bar (must be after history) --------" to document the dependency for future maintainers.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

## 2026-05-05 18:15 UTC — Refactor main.py: extract menu, project, and component handlers to reduce bloat

**File:** main.py
**Date and Time:** 2026-05-05 18:15 UTC
**Lines (at time of edit):** Multiple sections removed and refactored
**Before:** GameManager contains 1,130+ lines with embedded menu rendering, project serialization, component saving, and event handling.
**After:** GameManager delegates to specialized handlers; main.py now ~850 lines with cleaner separation of concerns.
**Why:** Pass 3 architecture refactoring to reduce GameManager bloat per TESTING.md rule "GameManager must be light — offload responsibilities to other classes." Handlers now manage: menu rendering/interaction (TopMenuBar), project disk I/O (ProjectManager), component port inference and serialization (SaveAsComponentHandler). Event handling and drawing refactored to use handlers instead of inline GameManager code.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

**File:** ui/top_menu_bar.py
**Date and Time:** 2026-05-05 18:00 UTC
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** Complete TopMenuBar handler with:
  - Menu state management (_active_top_menu_id, _top_menu_hover_index)
  - Rendering: draw(), _draw_bar(), _draw_popup()
  - Interaction: toggle_menu(), close_menu(), activate_selection()
  - Hit testing: menu_id_at_pos(), menu_item_index_at_pos()
  - Keyboard navigation: move_selection(), sync_hover_with_mouse()
  - Full type hints and comprehensive docstrings
**Why:** Extracted all menu logic from GameManager into dedicated handler. Encapsulates menu rendering, geometry calculations, event routing, and keyboard/mouse interaction. All constants and state kept private; public API provides only necessary operations (toggle, navigate, activate). Decouples menu from game state.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

**File:** core/project_manager.py
**Date and Time:** 2026-05-05 18:05 UTC
**Lines (at time of edit):** (new file)
**Before:** (file did not exist)
**After:** Complete ProjectManager handler with:
  - Disk I/O: save_project(), load_project(), list_project_names()
  - Serialization: serialize_workspace(), deserialize_workspace(), serialize_component(), deserialize_component()
  - Full type hints and comprehensive docstrings for all methods
**Why:** Extracted project serialization and disk I/O from GameManager. Centralizes all JSON-based persistence logic. Handles component type dispatch (Switch, LED, SavedComponent, NAND). Mutates live lists during deserialization (components, wires, text_boxes, bank) to reconstruct workspace state. Decouples GameManager from file system operations.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

**File:** ui/save_as_component_handler.py
**Date and Time:** 2026-05-05 18:02 UTC
**Lines (at time of edit):** (existing file, cleaned up)
**Before:** Partial handler with basic port inference.
**After:** Complete handler with:
  - infer_component_ports(): Auto-detect input/output from workspace (Switches→INPUT, LEDs→OUTPUT, ordered by Y position)
  - snapshot_workspace_definition(): Create component definition using ProjectManager.serialize_component()
  - Full type hints and comprehensive docstrings
**Why:** Finalized save-as-component workflow handler. Uses ProjectManager for component serialization to avoid duplication. Port inference follows "Save-as-Component port inference rule": every Switch is INPUT, every LED is OUTPUT, ordered top-to-bottom (Y position) for spatial correspondence with student's visual layout.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

**File:** main.py
**Date and Time:** 2026-05-05 18:10 UTC
**Lines (at time of edit):** 439-514 (refactored _handle_mouse)
**Before:** _handle_mouse() with inline menu click detection:
  ```python
  clicked_top_menu_id = self._top_menu_id_at(event.pos)
  if clicked_top_menu_id is not None:
      self._toggle_top_menu(clicked_top_menu_id)
      return
  if self._active_top_menu_id is not None:
      popup_rect = self._top_menu_popup_rects[self._active_top_menu_id]
      if popup_rect.collidepoint(event.pos):
          index = self._top_menu_index_at(event.pos)
          if index is not None:
              self._top_menu_hover_index = index
              self._activate_top_menu_selection()
  ```
**After:** _handle_mouse() delegates to top_menu_bar:
  ```python
  clicked_top_menu_id = self.top_menu_bar.menu_id_at_pos(event.pos)
  if clicked_top_menu_id is not None:
      self.top_menu_bar.toggle_menu(clicked_top_menu_id)
      return
  if self.top_menu_bar.is_menu_open():
      index = self.top_menu_bar.menu_item_index_at_pos(event.pos)
      if index is not None:
          self.top_menu_bar.move_selection(0)
          action = self.top_menu_bar.activate_selection()
          if action is not None:
              action()
  ```
**Why:** Refactored mouse event handling to use TopMenuBar API instead of accessing private menu state variables. Mouse motion syncing changed from self._sync_top_menu_hover_with_mouse(event.pos) to self.top_menu_bar.sync_hover_with_mouse(event.pos). All menu interaction now goes through public TopMenuBar methods.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

**File:** main.py
**Date and Time:** 2026-05-05 18:07 UTC
**Lines (at time of edit):** 411-437 (refactored _handle_keydown)
**Before:** _handle_keydown() with inline menu navigation:
  ```python
  if self._active_top_menu_id is not None:
      if event.key == pygame.K_DOWN:
          self._move_top_menu_selection(1)
          return
      if event.key == pygame.K_UP:
          self._move_top_menu_selection(-1)
          return
      if event.key == pygame.K_RETURN:
          self._activate_top_menu_selection()
          return
      if event.key == pygame.K_ESCAPE:
          self._close_top_menu()
          return
  ```
**After:** _handle_keydown() delegates to top_menu_bar:
  ```python
  if self.top_menu_bar.is_menu_open():
      if event.key == pygame.K_DOWN:
          self.top_menu_bar.move_selection(1)
          return
      if event.key == pygame.K_UP:
          self.top_menu_bar.move_selection(-1)
          return
      if event.key == pygame.K_RETURN:
          action = self.top_menu_bar.activate_selection()
          if action is not None:
              action()
          return
      if event.key == pygame.K_ESCAPE:
          self.top_menu_bar.close_menu()
          return
  ```
**Why:** Refactored keyboard event handling for menu navigation. Replaced _active_top_menu_id checks with top_menu_bar.is_menu_open(). Menu selection movement now via top_menu_bar.move_selection(). Menu item activation returns callable from activate_selection() for GameManager to invoke. Closes menu on Escape via top_menu_bar.close_menu().
**Editor:** GitHub Copilot (Claude Haiku 4.5)

**File:** main.py
**Date and Time:** 2026-05-05 18:12 UTC
**Lines (at time of edit):** 1003-1010 (_render_frame)
**Before:** `self._draw_top_menu_bar()`
**After:** `self.top_menu_bar.draw()`
**Why:** Rendering now delegates to TopMenuBar handler. Removed direct call to GameManager's menu drawing code.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

**File:** main.py
**Date and Time:** 2026-05-05 18:13 UTC
**Lines (at time of edit):** 666-900 (deleted)
**Before:** 235 lines of old menu methods:
  - _build_top_menu_item_surfaces()
  - _rebuild_top_menu_geometry()
  - _toggle_top_menu()
  - _close_top_menu()
  - _top_menu_id_at()
  - _top_menu_index_at_pos()
  - _top_menu_index_at()
  - _first_enabled_top_menu_index()
  - _move_top_menu_selection()
  - _activate_top_menu_selection()
  - _sync_top_menu_hover_with_mouse()
  - _draw_top_menu_bar()
  - _draw_top_menu_popup()
**After:** (deleted)
**Why:** All menu functionality now in TopMenuBar handler. Removed inline implementations from GameManager to reduce bloat and improve maintainability. These methods are now TopMenuBar private/public methods.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

**File:** main.py
**Date and Time:** 2026-05-05 18:14 UTC
**Lines (at time of edit):** ~60 (initialization section)
**Before:** GameManager.__init__() initialized ~10 menu state variables:
  - self._active_top_menu_id
  - self._top_menu_hover_index
  - self._top_menu_button_rects
  - self._top_menu_popup_rects
  - self._top_menu_item_rects
  - self._top_menu_label_surfs
  - self._top_menu_label_surfs_highlight
  - self._top_menu_item_surfs
  - self._top_menu_defs
  - self._top_menu_order
**After:** Removed all menu state from GameManager. Only keep:
  - self.top_menu_bar = TopMenuBar(self.screen, menu_defs)
  - Menu definitions moved to _setup_menu_bar() helper method
**Why:** All menu state now owned by TopMenuBar handler. GameManager only instantiates and holds reference to handler. Definitions constructed in _setup_menu_bar() and passed to TopMenuBar constructor. Reduces GameManager's initialization complexity and state footprint.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

## 2026-05-05 17:30 UTC — Architecture pass: update docs for current state + new roadmap

**File:** README.md
**Date and Time:** 2026-05-05 17:30 UTC
**Lines (at time of edit):** 28-48 (modified), 78-91 (modified), 110-128 (modified)
**Before:**
    ## Current Status
    
    Working prototype. Drag-and-drop, wiring, port logic, live signal propagation, the Switch / LED input-output components, and free-floating annotation text boxes are all in.
    
    **Next up: Pass 1 — Save as Component (in-session).** The selling point...
    
    (and Project Layout section was outdated with old structure)
    
**After:**
    ## Current Status
    
    Working prototype with Pass 1 and Pass 2 complete. The full abstraction loop is functional: build a circuit from NANDs, save it as a named component, drop it back into the toolbox, and build with it. Undo/redo, multi-segment wiring, visual polish (Switch redesign, LED redesign, random colors for saved components), and error recovery are all in place.
    
    **Pass 2 Progress:** Most items done. Remaining items (F11 fullscreen mouse path, trash delete mode, comprehensive menu test) are low priority pending classroom validation.
    
    **Next up: Pass 3 — Persistence.** Disk save/load so work survives across sessions. Also planned for Pass 3: project main menu on startup, options page, truth-table auto-detect, and color picker for components...
    
    (and updated Project Layout with current structure, added keyboard shortcuts including Ctrl+Z/Y, Ctrl+Shift+Z, Delete, F/E/V mnemonics)
    
**Why:** README was significantly out of date after Pass 1 and Pass 2 completion. Updated to reflect current capabilities, completed features, and next priorities. Also documented current keyboard shortcuts and updated project structure to match actual codebase organization (core/ and ui/ subdirectories).
**Editor:** GitHub Copilot (Claude Haiku 4.5)

**File:** docs/TODO.md
**Date and Time:** 2026-05-05 17:31 UTC
**Lines (at time of edit):** 63-100 (modified), 278-285 (modified)
**Before:**
    ## Pass 3 — Persistence
    
    Disk save/load so work survives across sessions and machines.
    
    - [ ] **Save / load a project (disk).** ...
    - [ ] **Project main menu (program startup).** Before the workspace
      opens, show a menu screen with: **New Project**, **Load Project**,
      **Options**, **Quit**. Replaces the current "drop straight into the
      workspace" startup.
    - [ ] **Options page.** Reachable from the main menu...
    
    (and missed Issues section at end)
    
**After:**
    ## Pass 3 — Persistence
    
    Disk save/load so work survives across sessions and machines. Also: app-level state management, startup menu, and tutorial/encyclopedia scaffolding.
    
    - [ ] **Save / load a project (disk).** ...
    - [ ] **Main menu on program startup.** Before dropping into the
      workspace, show a menu screen with: **NEW PROJECT**, **LOAD PROJECT**,
      **SETTINGS**, **ABOUT**, **QUIT**. App-level state machine to route
      between main menu ↔ workspace...
      - [ ] **New Project flow:** Clear workspace and show tutorial prompt (see below).
      - [ ] **Load Project flow:** Open load dialog, switch to workspace.
      - [ ] **In-game Quit behavior:** Pressing Esc or selecting Quit from FILE menu returns to main menu (not to desktop).
      - [ ] **Settings / About stubs:** Placeholder menu items for future passes.
    - [ ] **Tutorial prompt on new project.** When starting a new project from the main menu, ask tutorial prompt. **Only on new-project-from-menu; not in-game.**
    - [ ] **Tutorial system scaffold.** Extensible structure for interactive tutorials. Launchable from prompt and from FILE menu TUTORIAL option.
    - [ ] **Encyclopedia system scaffold.** Extensible reference system. Launchable from FILE menu ENCYCLOPEDIA option.
    - [ ] **Options page.** Reachable from main menu and in-workspace popup...
    
    (and added new issue: TOGGLE FULLSCREEN text hardcoded + overlaps F11 hint, violates settings.py constant rule)
    
**Why:** Pass 3 planning pass to document new product requirements (main menu, tutorial/encyclopedia systems, in-game quit returning to menu). Clarified scope and behavior for startup flow, tutorial prompt flow, and menu architecture. Added specific note about TOGGLE FULLSCREEN text being hardcoded instead of in settings.py, which is an architecture rule violation and quick future cleanup target.
**Editor:** GitHub Copilot (Claude Haiku 4.5)

## 2026-05-05 16:11 UTC — Add sticky multi-segment wire routing

**File:** core/wires.py
**Date and Time:** 2026-05-05 16:11 UTC
**Lines (at time of edit):** 17-97, 130-199, 228-247, 272-332 (modified)
**Before:**
    class Wire:
        def __init__(self, source, target):
            self.source = source
            self.target = target

        def hit(self, pos):
            # point-to-single-segment distance source->target
            ...

        def draw(self, surface):
            pygame.draw.line(surface, color, self.source.center, self.target.center, ...)

    class WireManager:
        def __init__(self):
            self.pending_source = None

        def handle_event(self, event, components):
            # start on LEFT down, commit/cancel on LEFT up
            ...
**After:**
    class Wire:
        def __init__(self, source, target, points=None):
            self.source = source
            self.target = target
            self.points = list(points or [])

        def hit(self, pos):
            # point-to-polyline distance across every segment
            ...

        def draw(self, surface):
            pygame.draw.lines(surface, color, False, [source, *points, target], ...)

    class WireManager:
        def __init__(self):
            self.pending_source = None
            self.pending_points = []

        def handle_event(self, event, components, workspace_rect=None):
            # sticky mode: click port to start, click workspace to add bends,
            # click valid port to commit, right-click/outside click to cancel
            ...
**Why:** Replaced hold-to-draw behavior with sticky routing so users can click
to place bend segments in empty workspace and build flexible wire paths before
committing to a target port.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 16:11 UTC
**Lines (at time of edit):** 638-643, 677 (modified)
**Before:**
    if self.wires.handle_event(event, self.components):
        return
**After:**
    workspace_rect = pygame.Rect(
        0,
        TopMenuBarSettings.HEIGHT,
        ScreenSettings.WIDTH,
        UISettings.BANK_RECT.top - TopMenuBarSettings.HEIGHT,
    )
    if self.wires.handle_event(event, self.components, workspace_rect):
        return
**Why:** Provides explicit workspace bounds to the wire manager so empty
workspace clicks create routing segments while clicks outside the workspace
cancel the in-flight sticky wire.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 12:01 UTC — Remove bottom hotkey bar and lower toolbox

**File:** main.py
**Date and Time:** 2026-05-05 12:01 UTC
**Lines (at time of edit):** 852-865, 1189-1196 (modified)
**Before:**
    def _draw_hotkey_bar(self):
        ...
    def _render_frame(self):
        ...
        self._draw_hotkey_bar()
        self._draw_error_banner()
**After:**
    [Removed _draw_hotkey_bar]
    def _render_frame(self):
        ...
        self.crt.draw()
        self._draw_error_banner()
**Why:** The bottom hint strip became obsolete after shortcut hints moved into
the top menus, so the empty black bar was removed from rendering.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** settings.py
**Date and Time:** 2026-05-05 12:01 UTC
**Lines (at time of edit):** 10, 65-73, 83-92 (modified)
**Before:**
    HOTKEY_BAR_HEIGHT = 28
    ...
    BANK_RECT = pygame.Rect(
        0,
        ScreenSettings.HEIGHT - HOTKEY_BAR_HEIGHT - BANK_BOTTOM_GAP - BANK_HEIGHT,
        ScreenSettings.WIDTH,
        BANK_HEIGHT,
    )
    ...
    class ShortcutBarSettings:
        ...
**After:**
    [Removed HOTKEY_BAR_HEIGHT]
    ...
    BANK_RECT = pygame.Rect(
        0,
        ScreenSettings.HEIGHT - BANK_BOTTOM_GAP - BANK_HEIGHT,
        ScreenSettings.WIDTH,
        BANK_HEIGHT,
    )
    ...
    [Removed ShortcutBarSettings]
**Why:** Re-anchored the toolbox to the bottom edge and deleted unused shortcut
bar constants/settings now that the bottom bar no longer exists.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 11:59 UTC — Move shortcut hints into top menus and underline EDIT/VIEW mnemonics

**File:** settings.py
**Date and Time:** 2026-05-05 11:59 UTC
**Lines (at time of edit):** 110-111 (modified)
**Before:**
    FILE_UNDERLINE_THICKNESS = 2
    FILE_UNDERLINE_BOTTOM_INSET = 6
**After:**
    FILE_UNDERLINE_THICKNESS = 2
    FILE_UNDERLINE_BOTTOM_INSET = 6
    SHORTCUT_TEXT_COLOR = (178, 178, 178)
    SHORTCUT_HIGHLIGHT_TEXT_COLOR = (95, 95, 95)
**Why:** Added centralized constants for lighter popup shortcut hint colors in
normal and highlighted menu states.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 11:59 UTC
**Lines (at time of edit):** 88-117, 640-644, 852-906, 1017-1128 (modified)
**Before:**
    self._hotkey_hints = (
        ("CTRL+Z=UNDO", "undo"),
        ("CTRL+Y=REDO", "redo"),
        ("T=TEXT", "text"),
        ("F11=FULLSCREEN", "fullscreen"),
        ("ESC=QUIT", "quit"),
    )
    ...
    if menu_id == "file":
        # Underline only the leading F ...
    ...
    self.screen.blit(surf, (rect.left + MenuButtonSettings.ITEM_PADDING_X, label_y))
**After:**
    file_shortcuts = {"quit": "ESC"}
    ...
    "items": (("undo", "UNDO", "CTRL+Z"), ("redo", "REDO", "CTRL+Y"))
    "items": (("toggle_fullscreen", "TOGGLE FULLSCREEN", "F11"),)
    ...
    # Underline each menu's mnemonic letter (first character).
    label_text = self._top_menu_defs[menu_id]["label"]
    ...
    shortcut_rect.right = popup_right
    shortcut_rect.centery = rect.centery

    def _draw_hotkey_bar(self):
        """Draw a bottom status strip without inline shortcut labels."""
**Why:** Removed bottom shortcut hint text and click handling, then moved
shortcut hints into the top context menu rows with right-aligned, lighter hint
text (e.g. QUIT ... ESC). Also added mnemonic underlines for EDIT and VIEW to
match FILE's keyboard-affordance style.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 13:09 UTC — Add EDIT and VIEW to top menu bar

**File:** settings.py
**Date and Time:** 2026-05-05 13:09 UTC
**Lines (at time of edit):** 101-104 (modified)
**Before:**
    class TopMenuBarSettings:
        PADDING_X = 10
        FILE_LABEL = "FILE"
        FILE_HIGHLIGHT_BG = COLOR_MENU_HIGHLIGHT
**After:**
    class TopMenuBarSettings:
        PADDING_X = 10
        MENU_GAP_X = 2
        FILE_LABEL = "FILE"
        EDIT_LABEL = "EDIT"
        VIEW_LABEL = "VIEW"
        FILE_HIGHLIGHT_BG = COLOR_MENU_HIGHLIGHT
**Why:** Added labels and spacing settings needed to render multiple top-level
menu buttons (FILE, EDIT, VIEW) in a contiguous top bar.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 13:09 UTC
**Lines (at time of edit):** 108-149, 559-668, 923-1149 (modified)
**Before:**
    Top menu logic was FILE-only (`_file_menu_open`, `_file_button_rect`,
    `_file_menu_item_rects`) with FILE keyboard toggle and FILE dropdown
    rendering/selection helpers.
**After:**
    Replaced FILE-only state with generic top-menu state:
    `_top_menu_order = ("file", "edit", "view")`, `_top_menu_defs`,
    `_active_top_menu_id`, shared geometry and item-surface maps.

    Added EDIT menu items: `UNDO`, `REDO` (wired to history undo/redo).
    Added VIEW menu item: `TOGGLE FULLSCREEN`.

    Updated keyboard handling:
    - `F` toggles FILE menu
    - `E` toggles EDIT menu
    - `V` toggles VIEW menu
    - Up/Down/Enter/Esc navigate/activate/close the currently open top menu

    Updated mouse handling and drawing to support all top menus through shared
    helpers (`_toggle_top_menu`, `_top_menu_id_at`, `_draw_top_menu_popup`).
**Why:** Implements requested top-level EDIT and VIEW menus next to FILE while
keeping one shared interaction model for click and keyboard navigation.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 12:57 UTC — Decouple shortcut left inset from item spacing

**File:** settings.py
**Date and Time:** 2026-05-05 12:57 UTC
**Lines (at time of edit):** 90 (modified)
**Before:**
    class ShortcutBarSettings:
        PADDING_X = 8
        ITEM_MIN_GAP = 12
**After:**
    class ShortcutBarSettings:
        LEFT_PADDING_X = 8
        PADDING_X = 8
        ITEM_MIN_GAP = 12
**Why:** Added a dedicated left inset constant so increasing `PADDING_X` no
longer shifts the first hint group away from the left edge.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 12:57 UTC
**Lines (at time of edit):** 885-892 (modified)
**Before:**
    x = ShortcutBarSettings.PADDING_X
    ...
    x += surf.get_width() + ShortcutBarSettings.ITEM_MIN_GAP
**After:**
    x = ShortcutBarSettings.LEFT_PADDING_X
    item_gap = max(ShortcutBarSettings.PADDING_X, ShortcutBarSettings.ITEM_MIN_GAP)
    ...
    x += surf.get_width() + item_gap
**Why:** `PADDING_X` now controls inter-item spacing only, while left anchoring
is controlled independently by `LEFT_PADDING_X`.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 12:49 UTC — Left-align bottom hint groups with fixed spacing

**File:** main.py
**Date and Time:** 2026-05-05 12:49 UTC
**Lines (at time of edit):** 871-881 (modified)
**Before:**
    # Space-evenly: equal gap before, between, and after each hint.
    total_width = sum(surf.get_width() for surf in hint_surfs)
    gap_count = len(hint_surfs) + 1
    gap = max(0.0, (ScreenSettings.WIDTH - total_width) / gap_count)
    x = gap
    ...
    x += surf.get_width() + gap
**After:**
    # Left-aligned flow with fixed spacing between hint groups.
    x = ShortcutBarSettings.PADDING_X
    ...
    x += surf.get_width() + ShortcutBarSettings.ITEM_MIN_GAP
**Why:** Anchors `CTRL+Z=UNDO` at the left side and keeps all hint groups
left-aligned with consistent spacing between items instead of centered spread.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 12:47 UTC — Top FILE polish and clickable KEY=ACTION bottom hints

**File:** settings.py
**Date and Time:** 2026-05-05 12:47 UTC
**Lines (at time of edit):** 11 (modified)
**Before:**
    TOP_MENU_BAR_HEIGHT = 32
**After:**
    TOP_MENU_BAR_HEIGHT = 34
**Why:** Extended the top FILE bar down slightly so the mnemonic underline has
more visual room and no longer feels cramped.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 12:47 UTC
**Lines (at time of edit):** 89-108, 608-609, 820-865, 1012-1032 (modified)
**Before:**
    Bottom hints used labels like "T TEXT" and were display-only.
    FILE label used only white text surface, which disappeared on white hover.
**After:**
    Added `self._hotkey_hints` with `KEY=ACTION` labels:
    `CTRL+Z=UNDO`, `CTRL+Y=REDO`, `T=TEXT`, `F11=FULLSCREEN`, `ESC=QUIT`.
    Added clickable hint handling (`_handle_hotkey_hint_click`) and action
    dispatch (`_run_hotkey_hint_action`) so clicking a hint triggers the same
    behavior as the corresponding keyboard shortcut.
    Added highlighted FILE text surface (`self._file_label_surf_highlight`) and
    dynamic FILE text/underline color so FILE remains readable when highlighted.
**Why:** Makes the bottom hint bar interactive and updates label style to the
requested `KEY=ACTION` format while fixing FILE visibility on white highlight.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 12:40 UTC — FILE underline/menu highlight polish and toolbox template editability

**File:** settings.py
**Date and Time:** 2026-05-05 12:40 UTC
**Lines (at time of edit):** 8-10, 80, 104-105 (modified)
**Before:**
    COLOR_MENU_HIGHLIGHT = (255, 255, 255)
    HOTKEY_BAR_HEIGHT = 28
    TOP_MENU_BAR_HEIGHT = 32
    ...
    BANK_LED_SHIFT_X [not present]
    ...
    FILE_UNDERLINE_THICKNESS / FILE_UNDERLINE_BOTTOM_INSET [not present]
**After:**
    COLOR_MENU_HIGHLIGHT = (255, 255, 255)
    COLOR_MENU_HIGHLIGHT_TEXT = (0, 0, 0)
    ...
    BANK_LED_SHIFT_X = 10
    ...
    FILE_UNDERLINE_THICKNESS = 2
    FILE_UNDERLINE_BOTTOM_INSET = 2
**Why:** Added explicit constants for selected-menu text color (black on white
highlight), moved the initial LED toolbox template slightly right toward TEXT,
and made FILE underline placement tunable/visible.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/bank.py
**Date and Time:** 2026-05-05 12:40 UTC
**Lines (at time of edit):** 84-92, 120-126, 262-355 (modified)
**Before:**
    ComponentBank supported template spawn only.
    No toolbox-template drag state.
    No template delete path.
    No starter-template protection.
**After:**
    Added `_protected_template_ids` seeded from initial four templates.
    Added middle-click drag support for toolbox templates (move inside bank).
    Added right-click delete support for non-protected toolbox templates.
    Kept left-click spawn behavior unchanged.
    Applied LED initial x offset via `UISettings.BANK_LED_SHIFT_X`.
**Why:** Allows users to move and delete editable toolbox templates while
preventing deletion of the four starter templates (IN, NAND, OUT, TEXT).
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 12:40 UTC
**Lines (at time of edit):** 982-997, 1005-1028 (modified)
**Before:**
    FILE underline used a single-pixel line based on label bottom.
    Selected FILE menu row used red/white style and white text surfaces.
**After:**
    FILE underline now anchors to button bottom inset and uses configurable
    thickness from settings for reliable visibility.
    Selected FILE menu row now uses white highlight with black rendered text.
**Why:** Restores visible FILE mnemonic underline and aligns selected-menu
visual style to the requested white-highlight/black-text look.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 12:28 UTC — Adjust top bar height and remove toolbox-bottom gap

**File:** settings.py
**Date and Time:** 2026-05-05 12:28 UTC
**Lines (at time of edit):** 10, 63, 95 (modified)
**Before:**
    HOTKEY_BAR_HEIGHT = 28

    class UISettings:
        BANK_BOTTOM_GAP = 8

    class TopMenuBarSettings:
        HEIGHT = HOTKEY_BAR_HEIGHT
**After:**
    HOTKEY_BAR_HEIGHT = 28
    TOP_MENU_BAR_HEIGHT = 32

    class UISettings:
        BANK_BOTTOM_GAP = 0

    class TopMenuBarSettings:
        HEIGHT = TOP_MENU_BAR_HEIGHT
**Why:** Increased the top menu bar height so the underlined "F" sits
cleanly within the bar and removed the visual gap between the toolbox and
the bottom hotkey bar for a flush stacked layout.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 12:20 UTC — Refactor UI layout to retro TUI bars and top FILE menu

**File:** settings.py
**Date and Time:** 2026-05-05 12:20 UTC
**Lines (at time of edit):** 4-9, 61-75, 80-100 (modified)
**Before:**
    class UISettings:
        BANK_HEIGHT = 100
        BANK_COLOR = (30, 30, 30)
        BANK_RECT = pygame.Rect(0, ScreenSettings.HEIGHT - BANK_HEIGHT, ScreenSettings.WIDTH, BANK_HEIGHT)

    class ShortcutBarSettings:
        HEIGHT = 28
        BG_COLOR = ColorSettings.WORD_COLORS["BLACK"]
        TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
**After:**
    COLOR_BAR_BG = (0, 0, 0)
    COLOR_BAR_TEXT = (255, 255, 255)
    COLOR_TOOLBOX_BG = (45, 45, 48)
    TOOLBOX_BG_COLOR = COLOR_TOOLBOX_BG
    COLOR_MENU_HIGHLIGHT = (173, 42, 42)

    class UISettings:
        BANK_BOTTOM_GAP = 8
        BANK_COLOR = TOOLBOX_BG_COLOR
        BANK_RECT = pygame.Rect(... ScreenSettings.HEIGHT - HOTKEY_BAR_HEIGHT - BANK_BOTTOM_GAP - BANK_HEIGHT ...)

    class TopMenuBarSettings:
        FILE_LABEL = "FILE"
        FILE_HIGHLIGHT_BG = COLOR_MENU_HIGHLIGHT
**Why:** Added explicit TUI color constants, introduced a top menu-bar config,
and moved the toolbox up so it is visually separated from the new bottom
hotkey bar while using a distinct toolbox background color.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui/bank.py
**Date and Time:** 2026-05-05 12:20 UTC
**Lines (at time of edit):** 61-287 (modified)
**Before:**
    from settings import (..., MenuButtonSettings, ...)

    class MenuButton:
        ...

    class ComponentBank:
        def __init__(self, text_boxes, menu_actions):
            self.menu_button = MenuButton(...)
        def _build_templates(self):
            x = self.menu_button.rect.right + UISettings.BANK_TEMPLATE_GAP
        def draw(self, surface):
            self.menu_button.draw(surface)
        def handle_event(...):
            [button toggle + popup dispatch + template spawn]
**After:**
    from settings import (... no MenuButtonSettings ...)

    class ComponentBank:
        def __init__(self, text_boxes):
            self._templates_and_spawners = self._build_templates()
        def _build_templates(self):
            x = self.rect.x + UISettings.BANK_PADDING_X
        def draw(self, surface):
            [bank background + template draw only]
        def handle_event(...):
            [template spawn only]
**Why:** Removed the old toolbox MENU button and popup interaction path so
the toolbox is now dedicated to component templates only; FILE menu control
was moved to the top menu bar.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-05 12:20 UTC
**Lines (at time of edit):** 50-103, 503-626, 810-1031 (modified)
**Before:**
    self.bank = ComponentBank(self.text_boxes, menu_actions={...})
    if self.bank.menu_button.is_open: self.bank.menu_button.toggle()
    if self.bank.menu_button.popup_rect.collidepoint(event.pos): ...
    _draw_hotkey_bar() drew at y=0 (top strip)
**After:**
    self._menu_actions = {...}
    self.bank = ComponentBank(self.text_boxes)
    self._file_menu_open / _file_menu_hover_index state added
    _draw_top_menu_bar() + _draw_file_menu_popup() added
    FILE menu keyboard focus: UP/DOWN, ENTER, ESC while open
    F key opens/closes FILE menu
    _draw_hotkey_bar() now draws at bottom (y = HEIGHT - bar height)
**Why:** Implemented the top FILE bar and dropdown behavior, moved hotkey
hints to a full-width bottom bar, captured keyboard focus for open menu,
and unified mouse-hover and keyboard-selection to drive the same highlight
state.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-05 — Pass 2: Fix MENU button vs TEXT template visual confusion

**File:** settings.py
**Date and Time:** 2026-05-05 00:00 CDT
**Lines (at time of edit):** 275-295 (MenuButtonSettings body)
**Before:**
    BODY_COLOR = (60, 60, 60)
    BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    BORDER_THICKNESS = 1
    LABEL = "MENU"
    LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
**After:**
    BODY_COLOR = (30, 45, 70)          # dark navy
    BORDER_COLOR = (90, 140, 210)      # blue accent
    BORDER_THICKNESS = 2
    LABEL = "MENU"
    LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    ICON_LINE_WIDTH = 22
    ICON_LINE_HEIGHT = 3
    ICON_LINE_GAP = 4
    ICON_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    ICON_Y_OFFSET = 12
    LABEL_Y_OFFSET = 47
**Why:** MENU and TEXT were both small dark squares with a 4-letter white
label, making it unclear which was a control and which was a draggable
component. A dark-navy body + blue border visually separates MENU from the
near-black component templates; the three hamburger bars are a universally
recognized "open menu" affordance so the button reads as a control surface
at a glance.
**Editor:** Claude Sonnet 4.6 (GitHub Copilot)

**File:** ui/bank.py
**Date and Time:** 2026-05-05 00:00 CDT
**Lines (at time of edit):** 175-202 (MenuButton.draw)
**Before:**
    pygame.draw.rect(surface, MenuButtonSettings.BODY_COLOR, self.rect)
    pygame.draw.rect(surface, MenuButtonSettings.BORDER_COLOR, self.rect,
                     MenuButtonSettings.BORDER_THICKNESS)
    label_rect = self._label_surf.get_rect(center=self.rect.center)
    surface.blit(self._label_surf, label_rect)
**After:**
    [body + border unchanged except new color values from settings]
    # Three hamburger bars in upper portion of button
    for bar_index in range(3):
        pygame.draw.rect(surface, ICON_COLOR, Rect(icon_x, icon_y + bar_index * bar_step,
                         ICON_LINE_WIDTH, ICON_LINE_HEIGHT))
    label_rect = self._label_surf.get_rect(centerx=..., centery=rect.top + LABEL_Y_OFFSET)
    surface.blit(self._label_surf, label_rect)
**Why:** Renders the hamburger icon above the MENU label so the button's
purpose is legible before the student reads the text.
**Editor:** Claude Sonnet 4.6 (GitHub Copilot)

## 2026-05-05 — Pass 2: Per-frame try/except seatbelt

**File:** settings.py
**Lines (at time of edit):** After ShortcutBarSettings class body (new class)
**Before:**
    [No ErrorBannerSettings; no recoverable-error visual constants.]
**After:**
    Added `ErrorBannerSettings` with DISPLAY_MS = 5000, HEIGHT = 36,
    BG_COLOR (dark red), TEXT_COLOR (white), PADDING_X = 16.
**Why:** Centralizes error-banner visual constants so _draw_error_banner
has no magic numbers.
**Editor:** Claude Sonnet 4.6 (GitHub Copilot)

**File:** main.py
**Lines (at time of edit):** imports (traceback), __init__ (_error_info field),
_draw_error_banner (new method), _render_frame (docstring + banner call),
run (try/except wrapper)
**Before:**
    import sys (no traceback import)
    __init__: no _error_info field
    _render_frame: fill / grid / draw / hotkey_bar / crt — no error banner
    run(): bare while True: _process_events / _update_world / _render_frame /
           flip / tick — any exception crashes the process
**After:**
    import traceback as _traceback added.
    self._error_info = None in __init__ (stores (exc_type, message, timestamp)
    or None).
    _draw_error_banner(): reads _error_info, draws a dark-red strip below the
    shortcut bar with "ERROR — <type>: <message>", auto-clears after
    ErrorBannerSettings.DISPLAY_MS.
    _render_frame(): calls _draw_error_banner() after crt.draw() so the
    banner is always on top.
    run(): wraps _process_events + _update_world + _render_frame in
    try/except; on exception prints traceback to stderr, stores _error_info,
    and runs a best-effort minimal draw (fill + _draw_error_banner) in case
    _render_frame itself threw.
**Why:** Crashes mid-class are the worst possible UX. This seatbelt keeps
the app alive on unhandled exceptions and flashes a brief diagnostic banner
so the student can keep working.
**Editor:** Claude Sonnet 4.6 (GitHub Copilot)

## 2026-05-05 — Pass 2: Switch / LED visual redesign

**File:** settings.py
**Lines (at time of edit):** SwitchSettings + LedSettings class bodies
**Before:**
    class SwitchSettings:
        SIZE = 60
        OFF_COLOR = ColorSettings.WORD_COLORS["GRAY"]
        ON_COLOR  = ColorSettings.WORD_COLORS["GREEN"]
        BORDER_COLOR = ...; BORDER_THICKNESS = 2

    class LedSettings:
        SIZE = 60
        OFF_COLOR = ...; ON_COLOR = ...; BORDER_COLOR = ...; BORDER_THICKNESS = 2
**After:**
    class SwitchSettings:   # toggle sliding knob
        WIDTH = 80; HEIGHT = 44; KNOB_RADIUS = 16; KNOB_MARGIN = 6
        BODY_CORNER = 10
        BODY_OFF_COLOR / BODY_ON_COLOR  (dark gray / dark green tint)
        TRACK_COLOR; TRACK_HEIGHT = 14
        KNOB_OFF_COLOR / KNOB_ON_COLOR  (gray / green)
        BORDER_COLOR / BORDER_THICKNESS = 2
        LABEL_COLOR = (210, 210, 210)

    class LedSettings:      # bulb silhouette
        SIZE = 60; BULB_RADIUS = 20; BULB_Y_OFFSET = 22
        BASE_WIDTH = 18; BASE_HEIGHT = 10; BASE_Y_OFFSET = 46; BASE_CORNER = 3
        GLOW_EXTRA_RADIUS = 7
        OFF_GLOBE_COLOR / ON_GLOBE_COLOR (dark gray / warm yellow)
        OFF_BASE_COLOR / ON_BASE_COLOR
        GLOW_COLOR = (255, 200, 30)
        BORDER_COLOR / BORDER_THICKNESS = 2
**Why:** Both Switch and LED were circles that differed only by fill color,
making them look like "the same component in two states." Giving Switch
a distinct toggle affordance and LED a bulb silhouette makes their roles
immediately legible.
**Editor:** Claude Sonnet 4.6 (GitHub Copilot)

**File:** elements.py
**Lines (at time of edit):** Switch.__init__, Switch._on_click, Switch._draw_body,
Switch.draw (new), LED.update_logic, LED._draw_body, LED.draw (new)
**Before:**
    class Switch(Component):
        def __init__: size = SwitchSettings.SIZE; super().__init__(w=size, h=size)
        def _draw_body: circle, color = ON_COLOR/OFF_COLOR

    class LED(Component):
        def _draw_body: circle, color = ON_COLOR/OFF_COLOR
**After:**
    class Switch(Component):
        def __init__: super().__init__(w=SwitchSettings.WIDTH, h=SwitchSettings.HEIGHT)
        def draw: ports + _draw_body + selection outline (no center name label)
        def _draw_body:
            - Rounded-rect background (BODY_ON/OFF_COLOR)
            - Recessed horizontal track (TRACK_COLOR, TRACK_HEIGHT)
            - Knob circle left (OFF) or right (ON); color KNOB_OFF/ON_COLOR
            - "0" or "1" state label on the empty side of the knob (Fonts.port_label)

    class LED(Component):
        def draw: ports + _draw_body + selection outline (no center name label)
        def _draw_body:
            - Glow ring (GLOW_COLOR, radius = BULB_RADIUS + GLOW_EXTRA_RADIUS) when HIGH
            - Globe circle (OFF/ON_GLOBE_COLOR, BULB_RADIUS) with border
            - Base rect (OFF/ON_BASE_COLOR, BASE_WIDTH × BASE_HEIGHT) below globe
**Why:** Implement the "Switch / LED visual redesign" Pass 2 bullet. Switch
now has a sliding-knob affordance (80×44, knob travels left↔right) with a
"0"/"1" label on the idle side. LED is a light-bulb silhouette: round globe
(upper rect) + rectangular base (lower rect) + yellow glow ring when HIGH.
Neither class renders the center name label anymore — the shapes speak for
themselves. SwitchSettings.SIZE is gone; WIDTH and HEIGHT replace it.
**Editor:** Claude Sonnet 4.6 (GitHub Copilot)



**File:** commands.py
**Date and Time:** 2026-05-04 02:10 UTC
**Lines (at time of edit):** 1-258 (new file)
**Before:**
    [No centralized command-history module; undo/redo behavior not
    represented in changelog for users/reviewers.]
**After:**
    Added `History` (bounded two-stack undo/redo manager) and reversible
    Action classes for component place/delete, wire place/delete, and text
    box place/delete.
**Why:** Implements Pass 2's safety net so users can recover from mistakes
without rebuilding work from scratch.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-04 02:10 UTC
**Lines (at time of edit):** 14-20 (imports), 84-103 (history wiring),
334-349 (Ctrl+Z/Ctrl+Y/Ctrl+Shift+Z), 436-475 (hotkey strip helpers),
522 (`_render_frame`)
**Before:**
    No in-app shortcut legend at the top of the screen; users had to infer
    hotkeys from docs or source.
**After:**
    Added an old-school top shortcut strip (black bar, small white text)
    rendered every frame with: UNDO/REDO, NAND spawn, TEXT spawn,
    fullscreen, and Esc behavior.
**Why:** Improves discoverability so users can see keyboard affordances in
the running app instead of digging through code.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** settings.py
**Date and Time:** 2026-05-04 02:10 UTC
**Lines (at time of edit):** 65-75 (`ShortcutBarSettings`)
**Before:**
    [No dedicated constants for top hotkey strip styling/layout.]
**After:**
    Added `ShortcutBarSettings` (`HEIGHT`, `BG_COLOR`, `TEXT_COLOR`,
    `BORDER_COLOR`, `PADDING_X`).
**Why:** Keeps hotkey-strip styling centralized and avoids magic numbers in
rendering code.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-04 01:08 UTC — Save clears workspace + reduce saved-wrapper flicker + VS Code pygame env fix

**File:** main.py
**Date and Time:** 2026-05-04 01:08 UTC
**Lines (at time of edit):** 149-169 (`_finalize_save_as_component` + new `_clear_workspace`)
**Before:**
    Save-as-Component appended the new saved template and dismissed the
    dialog, but left the current workspace contents in place.
**After:**
    `_finalize_save_as_component` now calls `_clear_workspace()` after
    registering the saved template and before dismissing the dialog.
    `_clear_workspace` clears placed components, committed/pending wires,
    and text-box annotations/focus.
**Why:** Matches the user-observed UX expectation that saving a component
should reset the canvas so the next abstraction layer starts immediately.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** elements.py
**Date and Time:** 2026-05-04 01:08 UTC
**Lines (at time of edit):** 588-605 (`SavedComponent.update_logic`)
**Before:**
    Internal saved sub-circuit simulation executed one pass per frame.
**After:**
    Internal simulation now executes `settle_steps = max(1, len(inner_components))`
    passes per frame before exporting wrapper outputs.
**Why:** Reduces visible output flicker on feedback-heavy saved circuits by
allowing internal values to settle before wrapper outputs are published.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** Python environment (terminal)
**Date and Time:** 2026-05-04 01:08 UTC
**Before:**
    VS Code workspace interpreter (`.venv`) did not have pygame installed,
    causing `ModuleNotFoundError: No module named 'pygame'` in editor runs.
**After:**
    Ran:
    `c:/Users/bryan/Desktop/code/repos/digital-logic-simulator/.venv/Scripts/python.exe -m pip install pygame`
    Verified with:
    `... -m pip show pygame` (version 2.6.1).
**Why:** Explorer launch used a different Python install that already had
pygame; VS Code was using `.venv`, so imports failed only inside VS Code.
Installing pygame into `.venv` resolves the mismatch.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** repository verification (diagnostics + terminal)
**Date and Time:** 2026-05-04 01:08 UTC
**Before:**
    [No verification pass for this behavior-fix batch.]
**After:**
    1) VS Code diagnostics: no errors in `main.py` and `elements.py`.
    2) Ran:
       `c:/Users/bryan/Desktop/code/repos/digital-logic-simulator/.venv/Scripts/python.exe -m compileall c:/Users/bryan/Desktop/code/repos/digital-logic-simulator`
       Result: compile completed with no syntax errors reported for changed files.
**Why:** Keeps with TESTING.md verification discipline after each code-edit batch.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-04 00:52 UTC — Pass 1 step 4: dynamic saved-component sizing

**File:** settings.py
**Date and Time:** 2026-05-04 00:52 UTC
**Lines (at time of edit):** 75-80 (new saved-wrapper sizing constants)
**Before:**
    [No dedicated constants for multi-port saved-wrapper sizing.]
**After:**
    ComponentSettings.SAVED_PORT_PITCH = 18
    ComponentSettings.SAVED_PORT_VERTICAL_PADDING = 15
**Why:** Moves dynamic sizing knobs into settings so `SavedComponent` can
compute stable per-port spacing without magic numbers.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** elements.py
**Date and Time:** 2026-05-04 00:52 UTC
**Lines (at time of edit):** 447-477 (`SavedComponent.__init__` + `_compute_body_size`), 499-501 (`_port_y_offsets`)
**Before:**
    SavedComponent inherited default 100x60 size regardless of exposed
    port count, so high-fanout wrappers could overlap ports.
**After:**
    width, height = self._compute_body_size(name)
    super().__init__(..., width=width, height=height, ...)
    ...
    dynamic_height = (max_ports - 1) * SAVED_PORT_PITCH +
                     2 * SAVED_PORT_VERTICAL_PADDING
    width = max(DEFAULT_WIDTH, rendered_label_width + 24)
    ...
    _port_y_offsets now uses SAVED_PORT_VERTICAL_PADDING for top/bottom anchors.
**Why:** Implements Pass 1's dynamic sizing requirement so wrappers grow tall
enough for many inputs/outputs and optionally widen for long labels.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui.py
**Date and Time:** 2026-05-04 00:52 UTC
**Lines (at time of edit):** 428-429 (`add_saved_component_template`)
**Before:**
    Template y-position assumed `ComponentSettings.DEFAULT_HEIGHT`.
**After:**
    Template is instantiated first and then vertically centered using
    `template.rect.height`.
**Why:** Keeps bank-row centering correct after SavedComponent became
dynamically sized.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** docs/TODO.md
**Date and Time:** 2026-05-04 00:52 UTC
**Lines (at time of edit):** 90-101 (dynamic sizing checkbox + done note)
**Before:**
    Pass 1 dynamic sizing task was unchecked.
**After:**
    Pass 1 dynamic sizing task is checked with implementation details.
**Why:** Roadmap status now matches shipped behavior.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** repository verification (diagnostics + terminal)
**Date and Time:** 2026-05-04 00:52 UTC
**Before:**
    [No verification run for this dynamic sizing batch.]
**After:**
    1) VS Code diagnostics: no errors in `elements.py`, `ui.py`, `settings.py`.
    2) Ran:
       `c:/Users/bryan/Desktop/code/repos/digital-logic-simulator/.venv/Scripts/python.exe -m compileall c:/Users/bryan/Desktop/code/repos/digital-logic-simulator`
       Result: compile completed with no syntax errors reported for changed files.
**Why:** Follows TESTING.md post-change verification intent in this
non-interactive environment.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-04 00:40 UTC — Pass 1 step 3: saved components spawn as working wrappers

**File:** elements.py
**Date and Time:** 2026-05-04 00:40 UTC
**Lines (at time of edit):** 2 (new deepcopy import), 416-621 (replace stub with SavedComponent runtime)
**Before:**
    class SavedComponentStub(Component):
        [name/color only, no ports, no logic]
**After:**
    class _InternalWire: ...
    class SavedComponent(Component):
        def __init__(..., definition): ...
        def _build_ports(...): ...
        def _build_internal_runtime(...): ...
        def _instantiate_component(...): ...
        def update_logic(...): ...
**Why:** Implements the working sub-circuit wrapper model from Pass 1 step 3.
Each spawned saved component now owns a hidden clone of the saved definition,
runs a local two-phase simulation each frame, maps wrapper INPUT ports into
the saved input switches, and publishes saved LED states out through wrapper
OUTPUT ports. `_InternalWire` avoids importing `wires.py` from `elements.py`,
which would create a circular import.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-04 00:40 UTC
**Lines (at time of edit):** 6-9 (imports), 139-228 (`_finalize_save_as_component` + new serializers)
**Before:**
    Save finalized only with inferred switch/LED lists and registered a
    visual-only saved template.
**After:**
    definition = self._snapshot_workspace_definition(...)
    record = {"name", "color", "inputs", "outputs", "definition"}
    self.bank.add_saved_component_template(name, color, deepcopy(definition))
    ...
    def _snapshot_workspace_definition(...):
        [serialize components, wires, IO mappings]
    def _serialize_component(...):
        [switch/led/nand/saved_component records]
**Why:** Save now captures an executable sub-circuit definition (components,
wires, and external IO mapping) so spawn can build working wrappers rather
than visual placeholders. Serializer supports nesting by recursively storing
`SavedComponent` definitions.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** ui.py
**Date and Time:** 2026-05-04 00:40 UTC
**Lines (at time of edit):** 2 (new deepcopy import), 4 (SavedComponent import), 414-451
**Before:**
    add_saved_component_template(name, color)
    [spawned SavedComponentStub placeholders]
**After:**
    add_saved_component_template(name, color, definition)
    [template + spawn now create SavedComponent with the serialized definition]
**Why:** Connects bank templates to the new runtime wrapper type so clicking a
saved template places a functioning component instance immediately.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** docs/TODO.md
**Date and Time:** 2026-05-04 00:40 UTC
**Lines (at time of edit):** 73-90 (step-2 note adjusted, step-3 checked with done note)
**Before:**
    Step 2 note still said spawn path was a `SavedComponentStub`; step 3 unchecked.
**After:**
    Step 2 note now references `SavedComponent` runtime completion.
    Step 3 is checked with an implementation summary note.
**Why:** Keeps roadmap state aligned with shipped behavior and removes stale
notes that would mislead the next pass.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** repository verification (terminal)
**Date and Time:** 2026-05-04 00:40 UTC
**Before:**
    [No post-change syntax verification run for this edit batch.]
**After:**
    Ran:
    `c:/Users/bryan/Desktop/code/repos/digital-logic-simulator/.venv/Scripts/python.exe -m compileall c:/Users/bryan/Desktop/code/repos/digital-logic-simulator`
    Result: compile completed for changed modules (`elements.py`, `main.py`,
    `ui.py`) with no syntax errors reported.
**Why:** Follows TESTING.md's post-change verification intent in this
headless environment where interactive pygame manual checks cannot be
executed from chat.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-04 00:20 UTC — Pass 1 step 2: saved components appear in toolbox

**File:** ui.py
**Date and Time:** 2026-05-04 00:20 UTC
**Lines (at time of edit):** 3 (imports), 427-485 (new saved-template append API + drag-priming helper)
**Before:**
    [ComponentBank built a fixed startup list of templates (Switch, NAND,
     LED, TEXT). There was no runtime API to append new templates after
     SAVE AS COMPONENT completed.]
**After:**
    from elements import Component, LED, SavedComponentStub, Switch
    ...
    class ComponentBank:
        ...
        @staticmethod
        def _prime_spawn_drag(new_comp, event_pos): ...

        def add_saved_component_template(self, name, color):
            ...
            template = SavedComponentStub(x, y, name, color)
            def spawn(event_pos, components_list):
                new_comp = SavedComponentStub(..., name, color)
                self._prime_spawn_drag(new_comp, event_pos)
                components_list.append(new_comp)
            self._templates_and_spawners.append((template, spawn))
**Why:** Implements Pass 1 step 2 exactly where the roadmap says it should
land: appending a `(template_drawable, spawn_fn)` pair into the bank's
existing list model. `add_saved_component_template` uses the same row
layout and drag-on-spawn behavior as built-in templates so the new saved
template immediately reads as first-class UI. The spawned runtime object is
a step-2 placeholder (`SavedComponentStub`) so this landing stays scoped to
"you can see and place what you saved" while leaving working sub-circuit
behavior for Pass 1 step 3.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** main.py
**Date and Time:** 2026-05-04 00:20 UTC
**Lines (at time of edit):** 139-146 (`_finalize_save_as_component`)
**Before:**
    self.saved_components.append({...})
    self._dismiss_dialog()
**After:**
    self.saved_components.append({...})
    self.bank.add_saved_component_template(
        name,
        ColorSettings.WORD_COLORS["MEDIUM_CARMINE"],
    )
    self._dismiss_dialog()
**Why:** Wires save finalization to visible UI output in the same code path
that already computes inferred ports. This closes the "did save work?"
feedback gap from the prior split landing: clicking Save now causes an
immediate observable toolbox change in-session.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** elements.py
**Date and Time:** 2026-05-04 00:20 UTC
**Lines (at time of edit):** 421-456 (new `SavedComponentStub` class)
**Before:**
    [File ended after LED class; no saved-component placeholder type existed.]
**After:**
    class SavedComponentStub(Component):
        """Pass-1 placeholder for a user-saved component."""
        def __init__(self, x, y, name, color): ...
        def update_logic(self, output_buffer):
            return
**Why:** Adds a dedicated step-2 runtime type with clear constraints: custom
name/color, no ports, no simulation logic. That avoids accidentally giving
saved templates NAND behavior by reusing `Component` directly before Pass 1
step 3's real wrapped-subcircuit runtime lands.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

**File:** docs/TODO.md
**Date and Time:** 2026-05-04 00:20 UTC
**Lines (at time of edit):** 64-76 (Pass 1 step 2 checkbox + done note)
**Before:**
    - [ ] **Saved component appears as a new template in the toolbox.** ...
**After:**
    - [x] **Saved component appears as a new template in the toolbox.** ...
      *(Done 2026-05-04. ... appended via ComponentBank API; spawn remains
      a step-2 stub and Pass 1 step 3 stays open.)*
**Why:** Keeps roadmap state aligned with shipped behavior and explicitly
documents what is complete vs intentionally deferred.
**Editor:** GitHub Copilot (GPT-5.3-Codex)

## 2026-05-03 00:45 UTC — Save-as-Component dialog v2: strip pickers, name only

**File:** docs/TODO.md
**Date and Time:** 2026-05-03 00:45 UTC
**Lines (at time of edit):** 42-58 (Pass 1 step 1 bullet rewritten +
done-note rewritten), 61-67 (Pass 1 step 2 bullet gains a "land
together" instruction), Risks & Notes appended with two new bullets
(port inference rule + sub-step splits should be end-to-end testable)
**Before:**
    [Pass 1 step 1 bullet described the v1 picker design — name field
     plus pickers for which Switches / LEDs to use and in what order;
     done-note pointed only at the v1 module location. Pass 1 step 2
     bullet had no instruction about pairing with future redesigns.
     Risks & Notes ended at "you discovered NAND!"]
**After:**
    [Pass 1 step 1 bullet now describes the v2 minimum-viable design —
     name field + Save/Cancel only; whatever Switches/LEDs are in the
     workspace at save time become the new component's INPUT/OUTPUT
     ports, ordered ascending Y. Done-note records the v1→v2 pivot.
     Pass 1 step 2 bullet gains: "Land this together with any future
     change to the save dialog or its callback — keeping save and 'you
     can see the result' in the same cut means each landing is end-to-
     end testable." Two new Risks & Notes bullets: (i) the port
     inference rule pinned to ascending Y because top-to-bottom
     position is what the student sees, with ties left undefined for
     Pass 1 use; (ii) sub-step splits must produce a visible user-
     facing change per landing — Pass 1 step 1 shipping without step 2
     produced a black box that forced the in-flight redesign this
     entry documents.]
**Why:** Roadmap correction in response to a first-light test of the
v1 dialog. User reported three problems: (1) overlapping section
labels (the "INPUTS — CLICK SWITCHES IN ORDER" / "OUTPUTS — CLICK LEDS
IN ORDER" captions ran into each other at the column boundary), (2)
the picker UX read as busywork — for the common case (e.g. AND-from-
NANDs with 2 INs and 1 OUT) there's nothing to pick, the answer is
already obvious from the workspace, and (3) Save did nothing visible,
so the user couldn't tell whether the click had any effect. (1) is a
mechanical bug that goes away once the captions go away. (2) is a
real design wrong-turn: the original spec assumed the picker earned
its keep, but seeing it in motion showed the picker only matters in
edge cases (unused IN/OUT components, non-spatial port order) that
deserve an opt-in path, not the default. (3) is a process problem
about how Pass 1 was sliced — splitting "the form" from "the result"
left no testable surface for the form alone. Captured the decisions
in TODO before any code changes, per the user's explicit instruction,
so the design call is durable even if the code edits don't all land.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** settings.py
**Date and Time:** 2026-05-03 00:45 UTC
**Lines (at time of edit):** 242-313 (SaveComponentDialogSettings:
shrunk from ~93 lines to ~72; picker-related constants and the
INPUTS/OUTPUTS section labels removed; WIDTH 520→420, HEIGHT 400→200)
**Before:**
    class SaveComponentDialogSettings:
        ...
        WIDTH = 520
        HEIGHT = 400
        ...
        # Section header labels (e.g. "NAME", "INPUTS", "OUTPUTS").
        SECTION_LABEL_COLOR = (180, 180, 180)
        NAME_SECTION_LABEL = "NAME"
        INPUTS_SECTION_LABEL = "INPUTS — CLICK SWITCHES IN ORDER"
        OUTPUTS_SECTION_LABEL = "OUTPUTS — CLICK LEDS IN ORDER"
        ...
        # Picker (used for both INPUTS and OUTPUTS).
        PICKER_HEIGHT = 168
        PICKER_ROW_HEIGHT = 28
        PICKER_ROW_BG = (60, 60, 60)
        PICKER_ROW_BG_SELECTED = (90, 60, 60)
        PICKER_ROW_BORDER = (120, 120, 120)
        PICKER_ROW_TEXT_COLOR = ColorSettings.WORD_COLORS["WHITE"]
        PICKER_ROW_TEXT_DIM = (140, 140, 140)
        PICKER_BADGE_COLOR = ColorSettings.WORD_COLORS["WHITE"]
        PICKER_EMPTY_TEXT = "(NONE IN WORKSPACE)"
        PICKER_COLUMN_GAP = 16
        PICKER_COLUMN_WIDTH = (WIDTH - 2 * PADDING - PICKER_COLUMN_GAP) // 2
        ...
**After:**
    class SaveComponentDialogSettings:
        """[...v2 docstring noting the pivot and the click-outside-no-op
        modal contract...]"""
        WIDTH = 420
        HEIGHT = 200
        ...
        # [no SECTION_LABEL_*, no PICKER_*]
        # Title, name field, save/cancel buttons, backdrop only.
**Why:** Drops every constant the picker UI used and shrinks the
dialog footprint to match the smaller content set. Title + name
field + button row + paddings comes out to ~158px of vertical
content, so 200 is a comfortable HEIGHT with room to breathe.
WIDTH 420 keeps Save (120) + Cancel (120) + GAP (12) + 2*PADDING
(32) = 284px of fixed real estate with 136px of name-field room
either side, and reads as a "small dialog" rather than the big
form the v1 footprint did. The picker color set (PICKER_ROW_BG_*,
PICKER_BADGE_COLOR, etc.) is gone in full — keeping it for "future
advanced save" would be premature, and the future opt-in path can
re-derive whatever palette it actually needs once the use case
shows up. NAME_SECTION_LABEL was removed because the placeholder
"TYPE A NAME..." inside the field plus the "SAVE AS COMPONENT" title
already says what the field is for; a separate "NAME" caption above
it is redundant noise.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** save_component_dialog.py
**Date and Time:** 2026-05-03 00:45 UTC
**Lines (at time of edit):** 1-296 (full rewrite — file shrunk from
576 lines to ~296)
**Before:**
    [v1 module: SaveComponentDialog took (components, on_save, on_cancel)
     and instantiated two _Picker widgets plus a _NameField. on_save
     fired with (name, ordered input switches, ordered output LEDs).
     ~576 lines including _Picker.]
**After:**
    [v2 module: SaveComponentDialog takes (on_save, on_cancel) only —
     no `components` parameter. Internal sub-widgets shrink to one
     (_NameField); the _Picker class is gone in full. on_save now
     fires with just `(name)` — auto-inference moved to the manager.
     Validation: name non-empty after strip. ~296 lines.]
**Why:** Mirrors the redesigned settings. The dialog no longer needs
to know about Switch / LED — auto-inference happens at the manager
which already owns `self.components`, so the dialog is decoupled
from element types and the `from elements import LED, Switch` line
is gone. on_save's signature shrinks from three values to one,
which means callers that only have a name (e.g. a future
quick-save shortcut) wire up trivially without faking out the
ports lists. Modal contract is unchanged: handle_event still claims
every event, click-outside-the-body is still a no-op (and the
docstring explicitly contrasts this against the popup's
click-outside-cancels — losing a typed name is a much worse
footgun than losing a tiny menu). The Pass-1-limitation comment
about row truncation is gone because there are no rows. _Picker
deletion is "less code is better" applied at full force — a 100-
line internal class disappears with no replacement because the
feature it supported was the wrong feature.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** main.py
**Date and Time:** 2026-05-03 00:45 UTC
**Lines (at time of edit):** 5 (import gains LED, Switch),
87-141 (save_as_component / _finalize_save_as_component bodies
rewritten — dialog constructor loses `components`, finalize gains
the auto-inference logic and now takes only `name`)
**Before:**
    from elements import Component
    ...
    def save_as_component(self):
        """Open the SAVE AS COMPONENT dialog over the current workspace."""
        self.dialog = SaveComponentDialog(
            self.components,
            on_save=self._finalize_save_as_component,
            on_cancel=self._dismiss_dialog,
        )

    def _finalize_save_as_component(self, name, input_switches, output_leds):
        """[v1 stub — appended a record using whatever the dialog
         passed back]"""
        self.saved_components.append({
            "name": name,
            "inputs": input_switches,
            "outputs": output_leds,
        })
        self._dismiss_dialog()
**After:**
    from elements import Component, LED, Switch
    ...
    def save_as_component(self):
        """Open the SAVE AS COMPONENT dialog. ..."""
        self.dialog = SaveComponentDialog(
            on_save=self._finalize_save_as_component,
            on_cancel=self._dismiss_dialog,
        )

    def _finalize_save_as_component(self, name):
        """Auto-infer ports from the workspace, stash the record,
        dismiss. ..."""
        input_switches = sorted(
            (c for c in self.components if isinstance(c, Switch)),
            key=lambda s: s.rect.y,
        )
        output_leds = sorted(
            (c for c in self.components if isinstance(c, LED)),
            key=lambda l: l.rect.y,
        )
        self.saved_components.append({
            "name": name,
            "inputs": input_switches,
            "outputs": output_leds,
        })
        self._dismiss_dialog()
**Why:** Wires the v2 dialog's narrower contract into the manager and
moves the workspace snapshot from open-time (v1 dialog __init__) to
save-time (here). Reading `self.components` at finalize is safe
because the dialog is modal — events that could mutate the workspace
are blocked while the dialog is open, so open-time and save-time see
the same set. Sort by `rect.y` ascending implements the rule
documented in TODO Risks & Notes: top-of-screen IN is port 0, the
next one down is port 1, etc. Generator expressions fed into
`sorted(...)` are cheaper than building intermediate lists and let
Python sort with the `key=` directly. The `from elements import`
gains LED + Switch (Component was already there) — these are now
referenced by `isinstance` here. The dialog itself no longer
imports element types, completing the "dialog doesn't know about
component kinds" decoupling. Manual test still owed (sandbox has no
pygame); the user observed the v1 bugs on hardware and this entry
covers the redesign that fixes them. Once the user confirms the v2
dialog renders cleanly and Save/Cancel/Esc all behave, the next
landing should bundle Pass 1 step 2 (toolbox template) with any
future tweaks so each cut stays end-to-end testable.
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-03 00:30 UTC — Pass 1 step 1: rough Save-as-Component dialog

**File:** settings.py
**Date and Time:** 2026-05-03 00:30 UTC
**Lines (at time of edit):** 242-334 (new SaveComponentDialogSettings class
inserted before AudioSettings)
**Before:**
    [no SaveComponentDialogSettings class — the previous bottom of the
    file went straight from MenuButtonSettings to AudioSettings]
**After:**
    class SaveComponentDialogSettings:
        """Visual + interaction constants for the SAVE AS COMPONENT
        dialog. ..."""
        WIDTH = 520
        HEIGHT = 400
        BODY_COLOR = (40, 40, 40)
        ...
        # Picker (used for both INPUTS and OUTPUTS).
        PICKER_HEIGHT = 168
        PICKER_ROW_HEIGHT = 28
        ...
        PICKER_COLUMN_WIDTH = (WIDTH - 2 * PADDING - PICKER_COLUMN_GAP) // 2
        ...
        BUTTON_BG_ENABLED = (70, 110, 70)
        BUTTON_BG_DISABLED = (60, 60, 60)
        BUTTON_BG_CANCEL = (110, 60, 60)
        ...
        BACKDROP_COLOR = (0, 0, 0)
        BACKDROP_ALPHA = 140
**Why:** All the dialog's geometry, colors, copy strings, and behavioral
caps (NAME_MAX_LENGTH, NAME_CARET_BLINK_MS) live in settings per the
no-magic-numbers rule. Class docstring captures the two design calls
that aren't obvious from the constants: (1) modal — every event the
dialog sees is consumed, mirroring the text-box manager's pre-emption
in `_process_events`, and (2) click-outside is a no-op rather than a
dismiss, deliberately diverging from the bottom-left popup's
click-outside-cancels because losing a multi-field form to a stray
click is a much worse footgun than losing a tiny menu. PICKER_COLUMN_WIDTH
is computed from the dialog WIDTH so the two side-by-side pickers always
fit; PICKER_BG_SELECTED uses a carmine-family tint so a selected row
reads as "live" against the dark backdrop without screaming. BACKDROP_ALPHA
of 140 (out of 255) pushes the workspace back enough to read as paused
without flattening the dialog into a void. NAME_MAX_LENGTH=24 fits
"FULL ADDER" / "RIPPLE CARRY ADDER 4BIT" with room to spare; longer is a
smell anyway. Two BUTTON_BG_* tints (green for Save, red for Cancel) and
a third for disabled-Save (matches PICKER_ROW_BG so disabled-Save reads
as a placeholder rather than a live affordance). The full set sits in one
class so a future palette pass touches one place.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** save_component_dialog.py
**Date and Time:** 2026-05-03 00:30 UTC
**Lines (at time of edit):** (new file)
**Before:**
    (file did not exist)
**After:**
    Module exposing `SaveComponentDialog` plus two private helpers
    `_NameField` and `_Picker`. Public class layout:
        SaveComponentDialog(components, on_save, on_cancel)
            .handle_event(event) -> bool   # always True (modal)
            .draw(surface)
    Sub-widgets: a single-line _NameField (uppercase printable input,
    backspace, blink caret, NAME_MAX_LENGTH cap), and two _Pickers (one
    for Switches → INPUT ports, one for LEDs → OUTPUT ports; click order
    determines port order; selected rows show a `#N` badge). Save button
    stays disabled until the form is valid (non-empty trimmed name AND
    ≥1 input AND ≥1 output) and consumes its click without firing
    on_save when disabled — same disabled-vs-enabled discipline the
    bottom-left popup uses for unwired items. Esc and the Cancel button
    both call on_cancel; the dialog itself does not auto-dismiss after
    on_save (the caller's `_finalize_save_as_component` is what triggers
    `_dismiss_dialog`), so close-vs-stay-open policy stays with the
    caller, not the dialog.
**Why:** Pass 1 step 1 of the Save-as-Component spine. Lifted into its own
module rather than inlined in ui.py because the dialog is multi-widget
state with its own event routing and its own draw order — same separation
text_boxes.py earned for the same reasons. Two private helpers
(_NameField, _Picker) keep the dialog class itself short and let each
widget own its hit-test, render, and (where applicable) keystroke
handling. Picker rows past `picker_height // row_height` are truncated
rather than scrolled — Pass 4's toolbox-overflow work will produce a
reusable list/scroll pattern this picker can adopt; until then,
truncation is the right rough trade-off because Pass 1 use cases (NOT,
AND, OR, XOR, SR latch) all stay well under six switches/LEDs. The
on_save callback signature is `(name, ordered input switches, ordered
output LEDs)` — Pass 1 steps 2 (toolbox template) and 3
(spawn-as-working-component) will reshape this to also pass the
embedded sub-circuit (components + wires + port mapping); leaving that
out here was deliberate so the dialog ships and tests in isolation
before the sub-circuit packaging machinery lands. Picker rows are
labelled "IN 1" / "OUT 1" by workspace order, not by component
position — a position-string was tempting for disambiguation but reads
as noise on a list of three switches; a 1-based ordinal matches the
mental model students already have from the existing IN/OUT components
on the workspace. The selected-row badge `#N` reflects current order
in `selected`, so deselecting + reselecting visibly renumbers — the
re-numbering IS the feedback that ordering changed, no separate
"reorder" affordance needed in the rough cut. Backdrop is a one-time
alpha surface built at construction and blit per frame, not
re-rendered on every draw — same render-once / blit-per-frame
discipline used by MenuButton's pre-rendered label surfaces.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** main.py
**Date and Time:** 2026-05-03 00:30 UTC
**Lines (at time of edit):** 7 (new import), 41-70 (constructor:
self.dialog, self.saved_components, expanded menu_actions),
87-138 (new save_as_component / _finalize_save_as_component /
_dismiss_dialog methods), 154-163 (modal pre-empt in _process_events),
303-309 (dialog.draw call in _draw)
**Before:**
    from elements import Component
    from fonts import Fonts
    from settings import *
    ...
        self.text_boxes = TextBoxManager()
        self.bank = ComponentBank(
            self.text_boxes,
            menu_actions={"QUIT": self.close_game},
        )
    ...
    [no save_as_component / _finalize_save_as_component / _dismiss_dialog]
    ...
    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()
                continue
            if self.text_boxes.handle_event(event):
                continue
            ...
    ...
    def _draw(self):
        ...
        self.bank.draw(self.screen)
**After:**
    from elements import Component
    from fonts import Fonts
    from save_component_dialog import SaveComponentDialog
    from settings import *
    ...
        self.text_boxes = TextBoxManager()
        # Active modal dialog, or None when no dialog is open.
        self.dialog = None
        # Saved component records produced by the SAVE AS COMPONENT
        # dialog. Pass 1 step 1 stub.
        self.saved_components = []
        self.bank = ComponentBank(
            self.text_boxes,
            menu_actions={
                "SAVE AS COMPONENT": self.save_as_component,
                "QUIT": self.close_game,
            },
        )
    ...
    def save_as_component(self):
        """Open the SAVE AS COMPONENT dialog over the current workspace."""
        self.dialog = SaveComponentDialog(
            self.components,
            on_save=self._finalize_save_as_component,
            on_cancel=self._dismiss_dialog,
        )

    def _finalize_save_as_component(self, name, input_switches, output_leds):
        """Stash the user's dialog inputs and dismiss the dialog. ..."""
        self.saved_components.append({
            "name": name,
            "inputs": input_switches,
            "outputs": output_leds,
        })
        self._dismiss_dialog()

    def _dismiss_dialog(self):
        """Close whichever dialog is currently open."""
        self.dialog = None
    ...
    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()
                continue
            # Modal dialog claims every event before text_boxes.
            if self.dialog is not None:
                self.dialog.handle_event(event)
                continue
            if self.text_boxes.handle_event(event):
                continue
            ...
    ...
    def _draw(self):
        ...
        self.bank.draw(self.screen)
        if self.dialog is not None:
            self.dialog.draw(self.screen)
**Why:** Wires the dialog into the GameManager surface that the bottom-
left popup's SAVE AS COMPONENT item now reaches. Five concrete moves:
(1) the menu_actions dict gains a second enabled entry, so MenuButton
renders SAVE AS COMPONENT in the live (white) color and the bank's
dispatch path runs `save_as_component` on click. The popup itself
already closes-then-runs-the-action (see the 2026-05-02 popup-dispatch
entry), so the popup → dialog hand-off is one toggle + one bound-method
call. (2) `self.dialog` and `self.saved_components` join the GameManager
state. The dialog slot is initialized before `bank` because the bank's
menu_actions dict references `self.save_as_component`, which dereferences
`self.dialog` — even though no callback fires before the first event
loop tick, ordering them defensively is cheaper than tracing a
NameError later. (3) Three new methods isolate the dialog lifecycle:
`save_as_component` opens, `_finalize_save_as_component` is the on_save
callback (stubbed for Pass 1 step 1 — appends a dict to
`saved_components`; Pass 1 steps 2-3 will reshape the record to embed
the sub-circuit), and `_dismiss_dialog` is the on_cancel callback (and
also the tail of finalize so the dialog goes away whether the user
saved or cancelled). (4) `_process_events` gets a modal pre-empt ahead
of `text_boxes.handle_event` — same shape the text-box manager uses
when a box is focused, just one layer up. The dialog's `handle_event`
always claims the event (returns True) so a click on a text box that
happens to lie under the dimmed backdrop edits the dialog, not the
box. (5) `_draw` blits the dialog above the bank so its backdrop
covers the whole workspace including the toolbox; CRT still draws on
top in `_render_frame` so the retro overlay is consistent. The Esc
chain in `_handle_keydown` (popup → quit) is intentionally NOT
extended to include the dialog — the dialog never lets Esc reach
`_handle_keydown` because the modal pre-empt in `_process_events`
swallows the KEYDOWN first. Splitting the dispatch this way (modal
intercept up top, layered-Esc lower down) keeps the layers from
fighting over which one owns Esc.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** docs/TODO.md
**Date and Time:** 2026-05-03 00:30 UTC
**Lines (at time of edit):** 42-48 (the Pass 1 "Save-as-Component
dialog (rough)" bullet)
**Before:**
    - [ ] **Save-as-Component dialog (rough).** Triggered from the
      bottom-left popup menu (the SAVE AS COMPONENT item is already there,
      disabled). The rough dialog only needs four things: a name field, a
      picker for which Switches become INPUT ports (and in what order), a
      picker for which LEDs become OUTPUT ports, and Save / Cancel buttons.
      Skip color choice, skip truth-table auto-detect, skip the "you
      discovered NAND!" celebration — those are Pass 3.
**After:**
    - [x] **Save-as-Component dialog (rough).** [...same body — bullet
      checked off; payload stashed on GameManager.saved_components as a
      dict for Pass 1 steps 2-3 to consume.]
**Why:** Marks the bullet done in the roadmap. Manual test of the
TESTING.md checklist (game loads, drag-and-drop, wire, IO logic,
right-click delete) plus the dialog-specific paths (open / type / pick
inputs / pick outputs / Save with valid form / Cancel / Esc / disabled
Save with empty form / no-switches empty-state) is owed in a follow-up
session — pygame is not installable in the sandbox this entry was
written from, so the runtime check needs to happen on hardware that
has pygame.
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-03 00:11 UTC — Pivot TODO from milestones to passes

**File:** docs/TODO.md
**Date and Time:** 2026-05-03 00:11 UTC
**Lines (at time of edit):** 1-298 (full rewrite, second one in ~45 minutes)
**Before:**
    Six numbered Milestones (M1 Mouse-First Polish → M6 Far Future) with
    Save/Load (M2) listed as the prerequisite to Save-as-Component (M3).
    Implicit deadline framing — "ship a complete classroom-ready product"
    after M3. Issues / Bugs and Polish & Tech Debt as standalone sections.
    Idea bucket carried IN/OUT visual redesign, undo/redo, trash mode,
    pin-to-toolbar, dynamic text-box width, keyboard shortcut overlay.
**After:**
    Seven Passes (Pass 1 Spine → Pass 7+ Treats) with explicit "do this
    rough first, polish later" framing. Save-as-Component reframed as
    Pass 1 (in-session only, no disk persistence). Pass 2 polishes the
    spine AND adds the safety net (undo/redo, IN/OUT redesign, trash
    mode, try/except seatbelt, MENU-vs-TEXT visual fix, F11 mouse path,
    Esc layered behavior). Disk persistence pushed to Pass 3 alongside
    the Options page, project main menu, truth-table auto-detect, color
    picker, and the program rename. Curriculum split across Pass 5
    (rough lessons) and Pass 6 (polish + discoverability layer). New
    Risks & Notes section captures forward-looking concerns that aren't
    tasks (classroom hardware reality, schema versioning from day one,
    Fonts refactor, ADR log, the "you discovered NAND!" pedagogical
    payoff being non-negotiable). Ideas section drained to empty — the
    rewrite absorbed every prior idea into a pass.
**Why:** User explicitly framed the project as a no-deadline enrichment
side-project ("I don't care when this will be 'done' if ever") and
asked for a pass-based plan that gets something stable and rough first,
then refines and polishes in waves. Milestones implied a finish line
that doesn't exist for this project; passes admit the iteration cycle
honestly. The single biggest reframe: Save-as-Component is Pass 1, not
a downstream milestone, because the user identified the abstraction
loop (build → save → use in next circuit → save → repeat) as the
literal selling point. In-session-only is good enough to prove the loop;
disk persistence is a separate concern that can wait. Three scope
calls confirmed via AskUserQuestion before writing: undo/redo lands in
Pass 2 (after the spine, before more features), IN/OUT visual redesign
lands in Pass 2 (Switch and LED looking identical is a real teaching
obstacle), disk persistence lands in Pass 3 (after the in-session
spine + polish). The new Risks & Notes section is the place for "I'm
worried about X" entries that aren't tasks but should be re-read at
the start of each pass — captures my forward-looking concerns from the
analysis without polluting the task list.
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-02 23:18 UTC — Date+time format and TODO restructure

**File:** docs/CHANGELOG.md
**Date and Time:** 2026-05-02 23:18 UTC
**Lines (at time of edit):** 716-746 (Format + Conventions sections rewritten)
**Before:**
    ## Format
    ...
        ## YYYY-MM-DD HH:MM — short summary
        **File:** path/to/file.py
        **Date and Time* e.g. 5/2/2026 @ 3:43PM
        ...
    ## Conventions
    [no rule about timezones; older entries use date-only headers and a mix
     of `5/2/2026` US-style values for the per-file `Date and Time` field —
     no entry to date has ever included an actual clock time]
**After:**
    ## Format
    ...
        ## YYYY-MM-DD HH:MM TZ — short summary
        **File:** path/to/file.py
        **Date and Time:** YYYY-MM-DD HH:MM TZ
        ...
    ### Date and time format
    [requires ISO 8601 date + 24-hour clock + timezone abbreviation, e.g.
     `2026-05-02 16:18 PDT`, on BOTH the section header and per-file field]
    ## Conventions
    [+ rule: pre-2026-05-02 entries are not retroactively edited]
**Why:** The old template promised "Date and Time" but every real entry
filled it with a date-only `5/2/2026` value (US-style, ambiguous, not
sortable as text), and the section header was inconsistent — sometimes
ISO date, never a clock time. Two problems compound: (1) collaborators
in different timezones can't sort the file deterministically; (2) within
a single working session several entries land within minutes of each
other and the day-only stamp can't tell them apart. ISO 8601 with a
24-hour clock and timezone abbreviation fixes both, and is the format
most engineering teams settle on for this exact reason. Per-file field
stays alongside the header on purpose — a single logical change can span
hours when it touches three files, and the per-file timestamp pinpoints
when each landed. Old entries are explicitly grandfathered: backfilling
guesses would be worse than leaving the gap visible.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** docs/TODO.md
**Date and Time:** 2026-05-02 23:18 UTC
**Lines (at time of edit):** 1-432 (full rewrite)
**Before:**
    Sections: Now / Next / Done x7 / Later / Brainstorming / Far future
    / Polish / Known issues. Seven "Done — ..." sections inline at the top
    of the file capturing already-shipped work (Toolbar TEXT button, Force
    uppercase, Live signal state, Text boxes, Wiring, Port hover labels,
    Port highlighting). "Brainstorming" was a single bucket mixing open
    design questions (rename the program, lit-wire-color decision pending
    palette) with uncommitted ideas (undo/redo, IN/OUT visual redesign,
    pin-to-toolbar). Bugs lived under "Known Issues" at the bottom.
**After:**
    Sections: Milestone 1 (Mouse-First Polish) → Milestone 6 (Far Future),
    plus standalone Questions, Ideas, Issues / Bugs, and Polish & Tech
    Debt sections. All seven inline "Done — ..." sections removed;
    "Brainstorming" split into Questions (open decisions) and Ideas
    (uncommitted designs); Issues / Bugs promoted to its own top-level
    section adjacent to Polish & Tech Debt.
**Why:** The TODO had grown to ~430 lines, the majority of which was
historical "Done" sections duplicating content already captured in this
changelog. Removing them recovers the file's purpose (forward-looking
roadmap) without losing history (the changelog has the diffs, the
rationale, and the editor for every shipped item — see the themes
covered between 2026-05-01 and 2026-05-02 below). The phase rename from
Now/Next/Later/Far-future to numbered Milestones with thematic titles
makes the dependency story explicit: persistence (M2) unblocks the
Save-as-Component keystone (M3), which unblocks the toolbox-overflow
discussion that has been parked under "Brainstorming." Brainstorming as
one bucket conflated two different shapes of work — questions need an
answer, ideas need an owner — so splitting them lets each be triaged on
its own terms. Issues / Bugs gets its own peer section so a regression
report doesn't hide at the bottom under "Known Issues" alongside polish
items.

Context preserved here that would otherwise vanish with the deleted
"Done" sections (anything not already represented in earlier changelog
entries):

  * **Live signals — design pivot.** The original "Live signal state"
    spec called for clicking an unconnected INPUT port to manually toggle
    it HIGH/LOW. That bullet was scrapped mid-flight and replaced with
    dedicated `Switch` and `LED` components (both circles for now), so
    inputs are driven by an explicit toggle widget rather than by
    overloading the port itself. This decision shaped the rest of the
    component model — every future "input source" or "output sink" is a
    full Component subclass, not a port mode — and is the reason
    `update_logic` is the override surface (Switch overrides to mirror
    its toggle to the OUTPUT port; LED overrides to no-op).

  * **TEXT toolbox template — architecture choice ("Option 1").** Two
    paths existed for adding a non-Component spawnable to the bank:
    (Option 1) extend `ComponentBank` to store `(template_drawable,
    spawn_fn)` pairs, with the TEXT spawner closing over a
    `TextBoxManager` reference passed in at construction; (Option 2)
    shoehorn `TextBox` into the existing `TEMPLATE_CLASSES` mapping by
    making it look like a `Component` subclass. Option 1 was picked.
    Adding any future non-Component spawnable (e.g. a future Annotation,
    a Probe widget) is a one-line append in `_build_templates` rather
    than a subclass workaround.

  * **Text boxes — uppercase rule scope.** The rule is "text boxes are
    uppercase," not "new characters are uppercase." Implication for the
    future Save/Load loader: apply `.upper()` once to every text-box
    string at load time, so an old save with lowercase characters comes
    back conformant. (This rule is also restated inside the Save/Load
    bullet in TODO M2 so the loader implementor sees it in context.)

  * **Popup menu — two-step routing.** The bottom-left popup intercepts
    mouse events at two layers: (1) `ComponentBank.handle_event`
    consumes any click that lands on the popup body, blocking it from
    falling through to the template loop; (2) `GameManager._handle_mouse`
    early-intercepts `MOUSEBUTTONDOWN` on the popup body BEFORE
    `wires.handle_event` runs, so a port that happens to sit under the
    popup body cannot start a wire and a right-click on the popup body
    cannot delete the wire underneath it. Both layers gate on
    `menu_button.is_open AND popup_rect.collidepoint(event.pos)`. This
    pattern is the template for any future popup/dialog and is worth
    preserving as the architectural reference.

  * **Esc layered behavior — first layer landed.** The Esc dismiss for
    the MenuButton popup was the first concrete example of the
    "Esc never leaks through an active UI layer" pattern. The TextBoxManager
    already used this for editor unfocus; future dialogs reuse the same
    gate. The roadmap's "F11 / Esc consolidation" milestone (now M1)
    extends this pattern to fullscreen-exit and confirm-quit layers.

**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-02 — Popup item dispatch (QUIT wired up)

**File:** settings.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 217-224 (MenuButtonSettings: enabled-color
constant added next to ITEM_DISABLED_COLOR)
**Before:**
    # Greyed-out label color used while the item has no action wired up.
    # Dimmer than the white MENU label so a future "enabled" item reads
    # as the active affordance against this disabled baseline.
    ITEM_DISABLED_COLOR = (140, 140, 140)
**After:**
    # Greyed-out label color used while the item has no action wired up.
    # Dimmer than the white MENU label so an enabled item reads as the
    # active affordance against this disabled baseline.
    ITEM_DISABLED_COLOR = (140, 140, 140)
    # Label color used for an item that has an action wired up. Matches
    # the white MENU button label so the affordance reads as part of the
    # same control surface.
    ITEM_ENABLED_COLOR = ColorSettings.WORD_COLORS["WHITE"]
**Why:** Closes the two folded-together "Now" bullets in TODO ("Populate
the popup with items" — per-item hit-rects + dispatch — and "Clicking an
item runs its action and closes the popup"). MenuButton needed a second
color so an enabled item visibly differs from a disabled placeholder;
adding ITEM_ENABLED_COLOR alongside the existing ITEM_DISABLED_COLOR
keeps both in one place rather than borrowing LABEL_COLOR (the MENU
button label) and tying the item palette to the button's. White matches
the active MENU label so a live item reads as part of the same control.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** ui.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 60-200 (MenuButton: constructor takes
`enabled_labels`; new `_item_rects`; new `item_label_at`; draw uses the
rects directly) and 215-280 (ComponentBank: constructor takes
`menu_actions`; popup-click branch in `handle_event` dispatches by label)
**Before (MenuButton.__init__ signature, label rendering, draw loop):**
    def __init__(self, x, y):
        ...
        self._item_label_surfs = [
            Fonts.text_box.render(
                label,
                True,
                MenuButtonSettings.ITEM_DISABLED_COLOR,
            )
            for label in MenuButtonSettings.ITEM_LABELS
        ]
    ...
            for index, surf in enumerate(self._item_label_surfs):
                label_y = (
                    self.popup_rect.top
                    + index * MenuButtonSettings.ITEM_HEIGHT
                    + (MenuButtonSettings.ITEM_HEIGHT - surf.get_height()) // 2
                )
                surface.blit(
                    surf,
                    (
                        self.popup_rect.left + MenuButtonSettings.ITEM_PADDING_X,
                        label_y,
                    ),
                )
**After (MenuButton.__init__ signature, hit-rect array, color-aware
rendering, label-at-pos lookup, draw loop using the rects):**
    def __init__(self, x, y, enabled_labels):
        ...
        self._item_rects = [
            pygame.Rect(
                self.popup_rect.left,
                self.popup_rect.top + index * MenuButtonSettings.ITEM_HEIGHT,
                MenuButtonSettings.POPUP_WIDTH,
                MenuButtonSettings.ITEM_HEIGHT,
            )
            for index in range(len(MenuButtonSettings.ITEM_LABELS))
        ]
        self._item_label_surfs = [
            Fonts.text_box.render(
                label,
                True,
                MenuButtonSettings.ITEM_ENABLED_COLOR
                if label in enabled_labels
                else MenuButtonSettings.ITEM_DISABLED_COLOR,
            )
            for label in MenuButtonSettings.ITEM_LABELS
        ]
    ...
    def item_label_at(self, pos):
        for rect, label in zip(self._item_rects, MenuButtonSettings.ITEM_LABELS):
            if rect.collidepoint(pos):
                return label
        return None
    ...
            for rect, surf in zip(self._item_rects, self._item_label_surfs):
                label_y = rect.y + (rect.height - surf.get_height()) // 2
                surface.blit(
                    surf,
                    (rect.left + MenuButtonSettings.ITEM_PADDING_X, label_y),
                )
**Before (ComponentBank.__init__ signature, popup-click branch):**
    def __init__(self, text_boxes):
        ...
        self.menu_button = MenuButton(
            UISettings.BANK_PADDING_X,
            self.rect.y + (self.rect.height - MenuButtonSettings.SIZE) // 2,
        )
    ...
        if self.menu_button.is_open:
            if self.menu_button.popup_rect.collidepoint(event.pos):
                return True
            self.menu_button.toggle()
**After (ComponentBank.__init__ signature, popup-click branch with
dispatch):**
    def __init__(self, text_boxes, menu_actions):
        ...
        self._menu_actions = menu_actions
        self.menu_button = MenuButton(
            UISettings.BANK_PADDING_X,
            self.rect.y + (self.rect.height - MenuButtonSettings.SIZE) // 2,
            set(menu_actions),
        )
    ...
        if self.menu_button.is_open:
            if self.menu_button.popup_rect.collidepoint(event.pos):
                label = self.menu_button.item_label_at(event.pos)
                action = self._menu_actions.get(label) if label else None
                if action is not None:
                    # Close the popup before running the action so any
                    # state the action mutates (e.g. close_game tears
                    # pygame down) sees the popup as already dismissed.
                    self.menu_button.toggle()
                    action()
                return True
            self.menu_button.toggle()
**Why:** This is the rest of "Populate the popup with items" + "Clicking
an item runs its action and closes the popup" from TODO's Now section,
folded together as the bullet predicted. MenuButton owns hit-rects and
label color (presentational); ComponentBank owns the action dispatch
(behavioral); GameManager owns the actual callbacks (mirrors the
"classes communicate through GameManager" rule in TESTING.md). The
hit-rects are built once at construction because the popup's geometry is
fixed; rebuilding them on every click would have been a needless cost.
`item_label_at` is the single bridge between the two — it answers "which
label was clicked?" without leaking the rect array. Disabled items
consume their click but do not close the popup or run anything: a
misclick on a placeholder shouldn't lose the menu the user just opened.
Enabled items close the popup *before* running the action so a callback
that tears state down (close_game in particular) sees a consistent state.
The old comment in the popup-click branch ("Items run no action yet —
per-item dispatch will plug in here once at least one action exists") is
gone because dispatch now exists. ITEM_LABELS remains the single source
of truth for the item set; the actions dict keys against those labels by
exact string. ITEM_ENABLED_COLOR is reached through `MenuButtonSettings`
so a future palette change touches one constant.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** main.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 39-50 (GameManager.__init__: bank built
with the new `menu_actions` argument)
**Before:**
        # Text boxes are pure annotations — no signal, no ports. Built
        # before the bank so the TEXT template can capture this manager
        # in its spawn closure. Spawnable from the bank's TEXT template
        # and from the T keyboard shortcut at the cursor position.
        self.text_boxes = TextBoxManager()
        self.bank = ComponentBank(self.text_boxes)
**After:**
        # Text boxes are pure annotations — no signal, no ports. Built
        # before the bank so the TEXT template can capture this manager
        # in its spawn closure. Spawnable from the bank's TEXT template
        # and from the T keyboard shortcut at the cursor position.
        self.text_boxes = TextBoxManager()
        # Menu actions: only QUIT has a backing path today (close_game),
        # so it's the only enabled item in the bottom-left popup. The
        # other four items (NEW PROJECT, LOAD PROJECT, SAVE PROJECT,
        # SAVE AS COMPONENT) ship disabled until the Save/Load and
        # Save-as-Component features land in TODO's Later section. The
        # dict's keys mirror MenuButtonSettings.ITEM_LABELS exactly so
        # MenuButton can pre-render each label in the right color.
        self.bank = ComponentBank(
            self.text_boxes,
            menu_actions={"QUIT": self.close_game},
        )
**Why:** Wires the only available action — close_game — into the bank's
new menu_actions parameter. QUIT was the obvious first item to enable
because the underlying behavior already exists (Esc has called
close_game from day one) and the F11/Esc consolidation Next bullet
already named "a menu item once the bottom-left popup populates" as the
intended mouse path for quitting. The other four items stay disabled —
their backing features (Save / Load project, Save as Component) are in
TODO's Later section, and pre-creating no-op callbacks would have lit
them up visually without a behavior to back the affordance. The
callback is bound directly (`self.close_game`) rather than wrapped in a
lambda so a future "are you sure?" confirm dialog can be added by
swapping the bound method for a different method on GameManager
(matches TODO's Next bullet on Esc-confirms-quit, which the menu QUIT
will inherit through the same callback).
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-02 — Popup-body clicks intercepted before wires in main

**File:** main.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 114-136 (GameManager._handle_mouse: early
popup-body intercept inserted before `wires.handle_event`)
**Before:**
    def _handle_mouse(self, event: pygame.event.Event) -> None:
        """Pass mouse events to the component manager or components directly."""
        # Hover updates ride along with motion events. Done here (not inside
        # Component) because every port in the world — workspace and toolbox
        # template alike — needs to reflect the same cursor, and only
        # GameManager owns both collections.
        if event.type == pygame.MOUSEMOTION:
            self._update_port_hover(event.pos)

        # Wires get the event before bank/components: a click that lands on a
        # port should start a wire, not drag the underlying component.
        if self.wires.handle_event(event, self.components):
            return
**After:**
    def _handle_mouse(self, event: pygame.event.Event) -> None:
        """Pass mouse events to the component manager or components directly."""
        # Hover updates ride along with motion events. Done here (not inside
        # Component) because every port in the world — workspace and toolbox
        # template alike — needs to reflect the same cursor, and only
        # GameManager owns both collections.
        if event.type == pygame.MOUSEMOTION:
            self._update_port_hover(event.pos)

        # When the bottom-left popup menu is open, any mouse-button press
        # that lands on the popup body belongs to the popup — intercept it
        # before wires/components can react so a port that happens to sit
        # under the popup can't start a wire. Mirrors the text-box manager
        # pattern in `_process_events` (an active UI layer claims its
        # clicks before anything else). The bank's own handler owns the
        # left-click semantics (item dispatch lands here next); the
        # unconditional `return` also swallows right-clicks on the popup
        # body so the menu reads as opaque to the cursor while open.
        if (event.type == pygame.MOUSEBUTTONDOWN
                and self.bank.menu_button.is_open
                and self.bank.menu_button.popup_rect.collidepoint(event.pos)):
            self.bank.handle_event(event, self.components)
            return

        # Wires get the event before bank/components: a click that lands on a
        # port should start a wire, not drag the underlying component.
        if self.wires.handle_event(event, self.components):
            return
**Why:** Closes the second half of the "Popup intercepts events before
wires/components" bullet in TODO. The first half (consume popup-body
clicks inside `ComponentBank.handle_event`) landed earlier today, but
because `wires.handle_event` runs before `bank.handle_event` in the
default mouse pipeline, a port that happened to sit under the popup
body could still start a wire on a click that the popup was supposed
to swallow. The new early-intercept block runs only when the popup is
actually open AND the click lands on the popup body, so the normal
mouse flow is untouched in every other case (no double-call to
`bank.handle_event`, no change to MENU-button or click-outside
dismiss). Pattern is intentionally the same shape as the text-box
manager's pre-emption in `_process_events` so the "active UI layer
claims its clicks first" rule reads consistently across the two
subsystems. Today the popup body has no items wired up, so the
observable change is limited to that wire-blocking case; once
per-item dispatch lands inside `ComponentBank.handle_event` (the
remaining "Clicking an item runs its action and closes the popup"
bullet), the same intercept will deliver those clicks to the bank
without the wires layer getting a look.
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-02 — Popup-body clicks consumed by ComponentBank

**File:** ui.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 414-428 (ComponentBank.handle_event:
popup-body click consumption)
**Before:**
        # Click-outside-dismiss: while the popup is open, any click that
        # misses both the popup body and the MENU button itself closes the
        # popup. Mouse parallel of the Esc dismiss in
        # `GameManager._handle_keydown`. We don't return — the click still
        # falls through to the template loop / wires / empty space so a
        # stray miss isn't punished with a second click.
        if self.menu_button.is_open and not self.menu_button.popup_rect.collidepoint(event.pos):
            self.menu_button.toggle()
**After:**
        # While the popup is open, route the click through the menu before
        # the template loop. A click on the popup body is consumed so it
        # can't fall through to templates (or to wires/components once
        # main.py routes menu clicks ahead of those — see the "Popup
        # intercepts events before wires/components" bullet in TODO).
        # Items run no action yet — per-item dispatch will plug in here
        # once at least one action exists. A click that misses the popup
        # body dismisses it but does NOT consume — a stray miss still
        # falls through to the template loop / wires / empty space so the
        # user isn't punished with a second click. Mouse parallel of the
        # Esc dismiss in `GameManager._handle_keydown`.
        if self.menu_button.is_open:
            if self.menu_button.popup_rect.collidepoint(event.pos):
                return True
            self.menu_button.toggle()
**Why:** Smallest forward step in the "Now — Bottom-left popup menu"
section of TODO. The next two pending bullets ("Clicking an item runs
its action and closes the popup", "Popup intercepts events before
wires/components") fold together; this change takes the half that
doesn't need any backing action: a click on the popup body is now
consumed by `ComponentBank.handle_event` (returns True) instead of
falling through to the template loop. Observable behavior is unchanged
today — the popup floats above the bank rect and the templates sit
inside it, so a popup-body click was already a visual no-op via
fall-through — but the bank's contract is now correct: while the popup
is the topmost UI layer, popup-body clicks belong to the popup, not to
whatever happens to lie underneath. This locks in the consumption slot
that per-item dispatch will plug into next (one `if label == "X":
action()` branch per wired item, before the `return True`). The
wires-before-bank reordering in main.py — needed so a click on a port
that happens to sit under the popup body can't start a wire — is still
owed and stays under the same TODO bullet; doing it here would change
event ordering for components that have nothing to do with the menu,
which is a separate, larger move. Click-outside semantics are
preserved verbatim (toggle without consume) so a stray miss still
falls through to wires / templates / empty space without penalty.
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-02 — Popup menu items rendered (disabled state)

**File:** settings.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 197-235 (MenuButtonSettings: items + popup
geometry)
**Before:**
    LABEL = "MENU"
    LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    # Popup container that appears above the button when the menu is open.
    # Width/height are placeholders for an empty popup; once menu items
    # exist, height will be derived from the item count instead of pinned
    # here. Color matches the button body so the popup reads as an
    # extension of the same control.
    POPUP_WIDTH = 180
    POPUP_HEIGHT = 160
**After:**
    LABEL = "MENU"
    LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    # Items shown in the popup, top-to-bottom. All disabled (greyed out)
    # in this cut — backing actions and click dispatch arrive in the
    # follow-up step, so labels exist now to lock the popup's height and
    # let the layout be verified independently of the wiring.
    ITEM_LABELS = (
        "NEW PROJECT",
        "LOAD PROJECT",
        "SAVE PROJECT",
        "SAVE AS COMPONENT",
        "QUIT",
    )
    # Vertical pitch per item inside the popup. The label baseline and
    # (once it lands) each item's hit-rect both anchor to this value, so
    # bumping it shifts both in sync.
    ITEM_HEIGHT = 32
    # Horizontal inset for an item label from the popup's left edge, so
    # text doesn't kiss the popup border.
    ITEM_PADDING_X = 10
    # Greyed-out label color used while the item has no action wired up.
    # Dimmer than the white MENU label so a future "enabled" item reads
    # as the active affordance against this disabled baseline.
    ITEM_DISABLED_COLOR = (140, 140, 140)
    # Popup container that appears above the button when the menu is open.
    # Width is sized to fit the longest item label ("SAVE AS COMPONENT"
    # measures ~197px in the Pixeled face at FONT_SIZE 12) with the
    # ITEM_PADDING_X inset on the left and a small visual margin on the
    # right; height is derived from the item count so adding/removing
    # entries only requires touching ITEM_LABELS. Color matches the
    # button body so the popup reads as an extension of the same control.
    POPUP_WIDTH = 220
    POPUP_HEIGHT = len(ITEM_LABELS) * ITEM_HEIGHT
**Why:** The next bullet under Now in the roadmap is "Populate the popup
with items." Took the smallest cut of that bullet — render the five item
labels inside the popup in a disabled (greyed-out) state — so layout and
geometry can be verified independently of click dispatch. ITEM_LABELS is
the single source of truth for which items exist; deriving POPUP_HEIGHT
from `len(ITEM_LABELS) * ITEM_HEIGHT` cashes in the comment that already
flagged this ("once menu items exist, height will be derived from the
item count instead of pinned here") so future add/remove only touches
ITEM_LABELS. Width was bumped from 180 to 220 because "SAVE AS COMPONENT"
measures ~197px in the Pixeled face at FONT_SIZE 12 (verified via PIL +
fontTools against `assets/font/Pixeled.ttf`); 180 - 10 (ITEM_PADDING_X) =
170 of usable text width would have clipped the right edge by ~27px.
220 leaves ~13px of right margin so the longest label doesn't visually
kiss the border. ITEM_DISABLED_COLOR is a mid-grey (140,140,140) chosen
to read as "present but inactive" against the (60,60,60) popup body
without disappearing — once an item gains an action it can swap to white
without disturbing the disabled baseline.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** ui.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 60-74 (MenuButton docstring), 102-122
(MenuButton.__init__: pre-render item labels), 133-181 (MenuButton.draw:
blit items inside popup)
**Before:**
- Class docstring said "Menu items, click-outside dismissal, and Esc
  dismissal arrive in follow-up steps" (stale — both dismissals already
  shipped earlier today, and items now exist).
- `__init__` rendered only `self._label_surf` for the MENU button label
  itself; no per-item surfaces.
- `draw` painted the popup body and border but no items inside; its
  docstring claimed "no menu items would be (none yet)".
**After:**
- Class docstring rewritten to reflect current scope: items render in
  disabled state, click-outside + Esc dismissal already ship elsewhere,
  click dispatch lands next.
- `__init__` additionally pre-renders one surface per `ITEM_LABELS`
  entry in `ITEM_DISABLED_COLOR` and stashes them in
  `self._item_label_surfs`. Same render-once / blit-per-frame discipline
  the existing `_label_surf` uses, so the cost is paid once and a future
  step can swap individual surfaces (e.g. an enabled-state render) without
  reworking the layout.
- `draw` now, when `is_open`, iterates `self._item_label_surfs` after the
  popup body+border so labels layer on top of the fill but stay inside
  the border. Each item owns a vertical band of `ITEM_HEIGHT` starting
  at `popup_rect.top`; its label is left-padded by `ITEM_PADDING_X` and
  vertically centered inside its band. No hit-test math here — click
  dispatch is the next bullet.
**Why:** Smallest concrete progress on the Now/"Populate the popup with
items" bullet without coupling to click dispatch (the next bullet, which
needs a per-item rect + action map and was deliberately deferred so the
visual layer could be reviewed in isolation). Kept the rendering
piggybacked on `MenuButton` rather than introducing a `MenuItem` class
because there's no behavior to model yet — once items gain hit-rects,
hover state, and enabled/disabled toggles, that's the right moment to
extract. `_item_label_surfs` mirrors `_label_surf`'s lifecycle so
consistency reads at a glance. Vertical centering inside an `ITEM_HEIGHT`
band keeps the layout robust to future font/size changes — the label just
re-centers in whatever band it gets. Updated two stale docstrings (class
+ `draw`) so a fresh-session reader doesn't see contradictions between
what the code does and what the docstring claims. Manual visual
verification still owed (needs a human at a keyboard); checklist in
`docs/TESTING.md` continues to apply.
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-02 — Roadmap reorder + popup-menu overlap fix

**File:** docs/TODO.md
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 134-209 (Done blocks), 396-413 (Known issues)
**Why:** Two reorganization passes plus the corresponding bug fix below.
First, the Done blocks had drifted out of chronological order — the
2026-05-02 "Live signal state" and "Text boxes" sections were sitting
underneath the 2026-05-01 "Port highlighting / Port hover labels /
Wiring" trio, so a fresh reader scanning Done was getting last week's
work before yesterday's. Sorted Done newest-first within section so the
top of Done is the most recent work and the bottom is the oldest.
Second, dropped the resolved "Popup menu overlaps the toolbar" bullet
from Known issues per the file's convention ("they live in this
CHANGELOG, no need to keep ghost entries in the active roadmap"). The
remaining Now/Next/Later/Brainstorming/Far future/Polish-tech-debt/
Known-issues skeleton was intact and didn't need touching.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** ui.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 85-99 (MenuButton.__init__, popup_rect)
**Before:**
    # Popup rect floats above the button with a small gap so the two
    # don't visually fuse. Anchored to the button's left edge so the
    # popup grows up-and-right, matching the Windows Start menu shape.
    self.popup_rect = pygame.Rect(
        x,
        y - MenuButtonSettings.POPUP_GAP - MenuButtonSettings.POPUP_HEIGHT,
        MenuButtonSettings.POPUP_WIDTH,
        MenuButtonSettings.POPUP_HEIGHT,
    )
**After:**
    # Popup rect rests flush above the toolbox bank with a small gap.
    # Anchoring to BANK_RECT.top (rather than the button's top) keeps
    # the popup's bottom edge aligned with the top of the bank no
    # matter how the button is vertically centered inside it —
    # otherwise the popup spills down across the bank's top edge by
    # whatever inset the button uses. Anchored to the button's left
    # edge so the popup grows up-and-right, matching the Windows
    # Start menu shape.
    self.popup_rect = pygame.Rect(
        x,
        UISettings.BANK_RECT.top - MenuButtonSettings.POPUP_GAP - MenuButtonSettings.POPUP_HEIGHT,
        MenuButtonSettings.POPUP_WIDTH,
        MenuButtonSettings.POPUP_HEIGHT,
    )
**Why:** Reported bug: the popup's bottom edge overlapped the toolbar by
a few pixels instead of resting flush on it. Root cause was using the
button's top as the popup's anchor — because the button is vertically
centered inside the bank (`(BANK_HEIGHT - SIZE) // 2 == 20px` of inset),
`button.top - GAP - POPUP_HEIGHT` placed the popup's bottom edge 16px
*below* `BANK_RECT.top` (one inset minus one gap), which is the overlap
the user saw. Anchoring to `BANK_RECT.top` directly removes the inset
from the equation, so the popup's bottom now sits exactly `POPUP_GAP`
above the bank regardless of how the button is laid out inside it. No
new constants needed — `UISettings` is already imported and
`BANK_RECT.top` is the right reference point. The button itself
(`self.rect`) is unaffected, so the click-target geometry doesn't
change. Manual visual verification still owed (needs a human at a
keyboard); checklist in `docs/TESTING.md` continues to apply.
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-02 — Roadmap cleanup + click-outside closes the popup menu

**File:** docs/TODO.md
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 20-52 (Now section), 359-364 (Polish/tech debt),
386-389 (Known issues)
**Why:** Housekeeping pass. The "Now — Bottom-left popup menu" section had
drifted: one bullet packed two unrelated actions ("click outside closes" +
"click an item runs its action"), the placeholder-popup work was buried
inside an unchecked item with a "*Half-done*" annotation, and the manual-
test bullet was checked even though the items it describes don't exist
yet. Reshaped Now into one bullet per concrete step, marked the placeholder-
popup work explicitly done, split out the items-populate work, split out
"click an item runs its action," and unchecked the manual-test bullet so
it actually reflects shippability. Also dropped four strikethrough-done
entries from Polish/tech-debt and two from Known issues — they live in
this CHANGELOG, no need to keep ghost entries in the active roadmap. Net
effect: a fresh-session reader can scan Now top-to-bottom and the next
unchecked bullet is the actual next thing to do.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** ui.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 363-387 (ComponentBank.handle_event)
**Before:**
    if self.menu_button.rect.collidepoint(event.pos):
        self.menu_button.toggle()
        return True
    for tpl, spawn_fn in self._templates_and_spawners:
        if tpl.rect.collidepoint(event.pos):
            spawn_fn(event.pos, components_list)
            return True
    return False
**After:**
    if self.menu_button.rect.collidepoint(event.pos):
        self.menu_button.toggle()
        return True
    # Click-outside-dismiss: while the popup is open, any click that
    # misses both the popup body and the MENU button itself closes the
    # popup. Mouse parallel of the Esc dismiss in
    # `GameManager._handle_keydown`. We don't return — the click still
    # falls through to the template loop / wires / empty space so a
    # stray miss isn't punished with a second click.
    if self.menu_button.is_open and not self.menu_button.popup_rect.collidepoint(event.pos):
        self.menu_button.toggle()
    for tpl, spawn_fn in self._templates_and_spawners:
        if tpl.rect.collidepoint(event.pos):
            spawn_fn(event.pos, components_list)
            return True
    return False
**Why:** Smallest next step in the bottom-left popup-menu work and the
mouse parallel of the Esc dismiss landed earlier today. Until this
change, the only ways to close the popup were clicking MENU again or
pressing Esc — clicking anywhere else left the popup hovering over the
workspace, which is unusual UX for a Windows-style start menu and out of
step with the project's mouse-first design principle. Implementation
sits in `ComponentBank.handle_event` next to the existing menu-button
check (single source of truth for bank-area click routing) and
deliberately does not consume the event, so a click that misses the
popup still flows into the template-spawn / wire / empty-space paths.
The remaining edge case — a click that misses the popup but happens to
land on a port drawn underneath — falls under the still-open
"intercept events before wires/components" bullet in TODO.md, which is a
separate architectural step that becomes load-bearing once items live
inside the popup. Marked the corresponding TODO bullet done with that
caveat noted inline.
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-02 — Roadmap reorganization + Esc closes the popup menu

**File:** docs/TODO.md
**Date and Time:** 5/2/2026
**Lines (at time of edit):** whole-file rewrite (~340 lines → ~340 lines)
**Why:** The previous TODO had grown a "More Ideas / Issues" brain-dump
section at the bottom that the user wanted distributed into proper
categories, and the completed "Now — Toolbar TEXT button" section needed
to be promoted to a Done block so the next pickup point at the top of
the file is the active work. Specific moves: TEXT button → Done; popup
menu → Now; F11 mouse-path + dynamic-Esc behavior → new Next section;
CRT/font/background-color/sound toggles → Options sub-bullets under the
existing "Project main menu" Later item; dynamic component sizing →
Later (tied to Save-as-Component); top hotkey-hint bar + easy mode →
Later; lit-wire color + program rename → Brainstorming;
encyclopedia/dictionary → Far future; popup-menu cosmetic bugs (overlap,
MENU/TEXT visual collision) → Known Issues. Also checked off the "Esc
closes the popup" sub-bullet under Now to match the code change below.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** main.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 91-100 (GameManager._handle_keydown, K_ESCAPE branch)
**Before:**
    if event.key == pygame.K_ESCAPE:
        self.close_game()
**After:**
    if event.key == pygame.K_ESCAPE:
        # Esc dismisses the bottom-left popup if it's open before it
        # ever counts as a quit. Mirrors the text-box manager pattern
        # (Esc unfocuses an active editor) so Esc never leaks through
        # an open UI layer to kill the game. Future popups / dialogs
        # should add their dismiss check here, in priority order.
        if self.bank.menu_button.is_open:
            self.bank.menu_button.toggle()
            return
        self.close_game()
**Why:** Smallest meaningful step in the in-progress "Now — Bottom-left
popup menu" task. Esc was unconditionally quitting the game even when a
UI layer was open, which both breaks the in-progress popup work (you
can't dismiss the popup with the keyboard at all today — only by
clicking MENU again) and is the same anti-pattern the text-box manager
already solves for focused editors. Routing Esc through the popup
gate first keeps that pattern uniform: any future modal dialog (the
Save / Load picker, the Save-as-Component dialog, the in-game "Are you
sure you want to quit?" confirm planned under "Next — F11 / Esc
consolidation") just adds another check above `self.close_game()`.
The mouse equivalent (clicking MENU again toggles the popup closed)
already works, so this is a power-user alias, not a hotkey-only path —
the design principle is satisfied.
**Editor:** Claude (Opus 4.7, via Cowork)

## 2026-05-02 — MENU button click toggles a placeholder popup

**File:** settings.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 182-198 (modified, class grew by ~12 lines)
**Before:**
    class MenuButtonSettings:
        """...The button itself only renders for now; clicking it will eventually open
        a vertical popup..."""
        SIZE = 60
        BODY_COLOR = (60, 60, 60)
        BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
        BORDER_THICKNESS = 1
        LABEL = "MENU"
        LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
**After:**
    [docstring updated to reflect that the button now toggles a popup]
    [...existing fields unchanged...]
    POPUP_WIDTH = 180
    POPUP_HEIGHT = 160
    POPUP_BODY_COLOR = (60, 60, 60)
    POPUP_BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
    POPUP_BORDER_THICKNESS = 1
    POPUP_GAP = 4
**Why:** Smallest concrete progress on the "Next — Bottom-left popup menu"
TODO bullet. Constants for the popup container are added now so the
button-click toggle has somewhere to draw to. Items will populate the
popup in a follow-up step.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** ui.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** 60-105 (MenuButton class body modified)
**Before:**
    class MenuButton:
        """Bottom-left bank button — visual anchor for the future file-ops popup..."""
        def __init__(self, x, y):
            ...
            self.rect = pygame.Rect(x, y, size, size)
            self.ports = ()
            self._label_surf = Fonts.text_box.render(...)
        def draw(self, surface):
            [draws body + border + label only]
**After:**
    class MenuButton:
        """Bottom-left bank button + the popup it toggles above the bank..."""
        def __init__(self, x, y):
            ...
            self.rect = pygame.Rect(x, y, size, size)
            self.ports = ()
            self.popup_rect = pygame.Rect(x, y - POPUP_GAP - POPUP_HEIGHT,
                                          POPUP_WIDTH, POPUP_HEIGHT)
            self.is_open = False
            self._label_surf = Fonts.text_box.render(...)
        def toggle(self):
            self.is_open = not self.is_open
        def draw(self, surface):
            [draws body + border + label, plus popup body+border when is_open]
**Why:** Adds the popup container + open/closed state to MenuButton so the
click toggle can show/hide it. `toggle()` is a method (not a direct
attribute flip) so future open-side-effects (focus stealing, item state
refresh) have one place to land.
**Editor:** Claude (Opus 4.7, via Cowork)

**File:** ui.py
**Date and Time:** 5/2/2026
**Lines (at time of edit):** ~325-340 (ComponentBank.handle_event)
**Before:**
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != InputSettings.LEFT_CLICK:
        return False
    for tpl, spawn_fn in self._templates_and_spawners:
        if tpl.rect.collidepoint(event.pos):
            spawn_fn(event.pos, components_list)
            return True
    return False
**After:**
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != InputSettings.LEFT_CLICK:
        return False
    if self.menu_button.rect.collidepoint(event.pos):
        self.menu_button.toggle()
        return True
    for tpl, spawn_fn in self._templates_and_spawners:
        ...
**Why:** Click routing for the MENU button. Checked before the template
loop so a click on MENU always toggles the popup, never falls through to
a template (defensive — current layout already puts MENU at x=BANK_PADDING_X
so there's no overlap, but spacing might shrink later).
**Editor:** Claude (Opus 4.7, via Cowork)

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

## 2026-05-02 — Force uppercase in text boxes

**File:** text_boxes.py
**Lines (at time of edit):** 92-113 (TextBox.handle_key)
**Before:**
        elif event.unicode and event.unicode.isprintable():
            self.text += event.unicode
**After:**
        elif event.unicode and event.unicode.isprintable():
            # str.upper() is a no-op for digits, punctuation, and already-
            # uppercase letters, so this is safe to call unconditionally.
            self.text += event.unicode.upper()
**Why:** Text boxes were the only editable surface in the workspace that
accepted lowercase input. Every other label (component names, port labels,
IN/OUT) is uppercase, so a hand-typed annotation looked visually out of
place against the rest of the circuit. Uppercasing at the keystroke
boundary keeps `self.text` canonical so the wrap, render, and any future
serializer all see the same value — no need to re-case at draw time. Tracked
the load-from-save half of the same rule under the Save/Load bullet in
TODO.md "Later" since there's no loader to hook into yet. Docstring updated
to reflect the new behavior; the inline comment explains *why* the call
is unconditional rather than restating *what* `.upper()` does.
**Editor:** Claude (Opus 4.7)

**File:** docs/TODO.md
**Lines (at time of edit):** ~50-65 (removed Now section), ~88-103 (new
Done — Force uppercase block), ~165-175 (Save/Load bullet extended),
~315 (Known Issues row removed)
**Why:** Mirrors the file change — promotes the completed work into the
Done log, parks the load-from-save half of the decision inside the
Save/Load Later bullet so it isn't lost when that work begins, and drops
the now-resolved "Text boxes accept lowercase input" entry from Known
Issues.
**Editor:** Claude (Opus 4.7)

## 2026-05-02 — Generalize bank templates to (drawable, spawn_fn) pairs

**File:** ui.py
**Lines (at time of edit):** 1-101 (whole file rewritten in place; ~145
lines after)
**Before:**
    TEMPLATE_CLASSES = (Switch, Component, LED)
    ...
    self.templates = self._build_templates()
    ...
    # _build_templates returned list[Component]
    ...
    # handle_event inlined the spawn protocol:
    new_comp = type(tpl)(
        event.pos[0] - tpl.rect.width // 2,
        event.pos[1] - tpl.rect.height // 2,
    )
    new_comp.dragging = True
    new_comp.offset_x = new_comp.rect.x - event.pos[0]
    new_comp.offset_y = new_comp.rect.y - event.pos[1]
    new_comp._moved_while_dragging = True
    components_list.append(new_comp)
**After:**
    # Internal storage is now list[(template_drawable, spawn_fn)] held on
    # self._templates_and_spawners. Build pairs each template with a
    # closure produced by _make_component_spawner(tpl, cls). draw and
    # handle_event iterate the tuples; handle_event delegates the actual
    # placement to spawn_fn(event.pos, components_list). A `templates`
    # @property still returns just the drawables for back-compat with
    # GameManager._update_port_hover.
**Why:** First step of the "Now — Toolbar TEXT button" task in
docs/TODO.md. The plan there explicitly chose Option 1 ("Generalize
TEMPLATE_CLASSES to a list of (template_drawable, spawn_fn) pairs") so a
TEXT label — which spawns a TextBox via the manager, not a Component
into components_list — can drop into the bank without special-casing,
and so the same generalization will carry the future Save-as-Component
templates. This commit is behavior-preserving: no new template added,
no signature change to ComponentBank.handle_event, no change to
GameManager wiring. The new TEXT entry plus the N/T hotkey
consolidation are deliberate follow-ups.
**Editor:** Claude (Opus 4.7)

## 2026-05-02 — Add TEXT template to the toolbox bank

**File:** settings.py
**Lines (at time of edit):** 166-179 (new TextTemplateSettings appended above AudioSettings)
**After:**
    class TextTemplateSettings:
        SIZE = 60
        BODY_COLOR = TextBoxSettings.BODY_COLOR
        BORDER_COLOR = TextBoxSettings.BORDER_COLOR
        BORDER_THICKNESS = TextBoxSettings.BORDER_THICKNESS
        LABEL = "TEXT"
        LABEL_COLOR = TextBoxSettings.TEXT_COLOR
**Why:** Visual constants for the bank-side TEXT template, kept out of
code per the no-magic-numbers rule. Mirrors TextBoxSettings (body, border,
text colors) so the template visually previews what a click will spawn.
SIZE matches Switch/LED so the four templates read as one row.
**Editor:** Claude (Opus 4.7)

**File:** ui.py
**Lines (at time of edit):** 1-10 (imports), 13-56 (new TextTemplate class),
73-91 (ComponentBank.__init__ now takes text_boxes), 126-133
(_build_templates appends TEXT entry), 178-198 (new _make_textbox_spawner)
**Before:**
    from elements import Component, LED, Switch
    from settings import InputSettings, ScreenSettings, UISettings

    class ComponentBank:
        TEMPLATE_CLASSES = (Switch, Component, LED)

        def __init__(self):
            self.rect = UISettings.BANK_RECT
            self._templates_and_spawners = self._build_templates()

        def _build_templates(self):
            x = UISettings.BANK_PADDING_X
            entries = []
            for cls in self.TEMPLATE_CLASSES:
                tpl = cls(x, 0)
                tpl.rect.y = ...
                entries.append((tpl, self._make_component_spawner(tpl, cls)))
                x += tpl.rect.width + UISettings.BANK_TEMPLATE_GAP
            return entries
**After:**
    from elements import Component, LED, Switch
    from fonts import Fonts
    from settings import (InputSettings, ScreenSettings,
                          TextTemplateSettings, UISettings)

    class TextTemplate:
        # rect, ports=() (no signal), pre-rendered "TEXT" label surf,
        # draws body + border + label. Matches the (rect, ports, draw)
        # surface every other bank template exposes so the hover walker
        # and bank.draw don't need a special case.

    class ComponentBank:
        TEMPLATE_CLASSES = (Switch, Component, LED)

        def __init__(self, text_boxes):
            self.rect = UISettings.BANK_RECT
            self._text_boxes = text_boxes
            self._templates_and_spawners = self._build_templates()

        def _build_templates(self):
            ... (existing component loop)
            text_tpl = TextTemplate(x, 0)
            text_tpl.rect.y = ... (vertically centered)
            entries.append((text_tpl, self._make_textbox_spawner()))
            return entries

        def _make_textbox_spawner(self):
            text_boxes = self._text_boxes  # closed-over reference
            def spawn(event_pos, components_list):
                # ignores components_list; routes through the manager
                text_boxes.spawn_at(event_pos)
            return spawn
**Why:** Closes the "Now — Toolbar TEXT button" gap so text boxes are
mouse-spawnable per the mouse-first design principle. The architectural
refactor that introduced (drawable, spawn_fn) pairs landed earlier today;
this commit is the follow-up that uses that infrastructure to add the
actual TEXT entry. TextTemplate is its own tiny class (not a Component
subclass) because it has no ports, no signal, and no workspace lifecycle —
it's a static button. ports=() is an empty tuple (not list) so a stray
.append in the hover walker would fail loud. The label surf is rendered
once in __init__ and blitted per frame; the template never changes so a
re-render every frame would be wasted work. ComponentBank.__init__ now
takes the TextBoxManager so the TEXT spawner closure can route a click
straight to text_boxes.spawn_at without bank.handle_event growing a wider
signature. TextBoxManager.spawn_at already focuses the new box, so
"Spawned TextBox should immediately focus" comes for free.
**Editor:** Claude (Opus 4.7)

**File:** main.py
**Lines (at time of edit):** 35-43 (subsystem init reordered)
**Before:**
    self.bank = ComponentBank()
    self.components = []
    self.wires = WireManager()
    self.signals = SignalManager()
    self.text_boxes = TextBoxManager()
**After:**
    self.text_boxes = TextBoxManager()
    self.bank = ComponentBank(self.text_boxes)
    self.components = []
    self.wires = WireManager()
    self.signals = SignalManager()
**Why:** ComponentBank now needs the TextBoxManager at construction time
(its TEXT spawner closes over the reference), so text_boxes has to be
built first. The other three subsystems (components, wires, signals) are
unchanged — only the relative order of bank vs. text_boxes flipped.
**Editor:** Claude (Opus 4.7)

**File:** docs/TODO.md
**Lines (at time of edit):** ~26-46 (Now section), ~315 (Known issues row)
**Why:** Marks items 1-3 of "Now — Toolbar TEXT button" as done (template
added, special-case routing live, immediate focus inherited from
spawn_at). Item 4 (N/T hotkey consolidation) is intentionally still open —
that's a separate refactor and orthogonal to the mouse-path gap closed
here. Also drops the resolved "Text boxes are mouse-inaccessible" Known
Issues entry.
**Editor:** Claude (Opus 4.7)

## 2026-05-02 — Route N hotkey through the bank's spawn path

Closes the last open item under "Now — Toolbar TEXT button" — N now
shares ComponentBank's spawn closure with toolbox clicks instead of
reimplementing it. T was already calling `text_boxes.spawn_at(...)`,
the same line the bank's text spawner runs, so it was left alone (a
`bank.spawn_text_box` passthrough would add a middleman, not remove
duplication).

**File:** ui.py
**Lines (at time of edit):** 200-228 (new `spawn_component` method on
ComponentBank, inserted between `_make_textbox_spawner` and `draw`)
**Before:**
    (no public API for spawning a component by class — the
    spawner closures lived only inside `_templates_and_spawners`
    and were reachable only via a left-click on a template rect)
**After:**
    def spawn_component(self, cls, event_pos, components_list):
        for tpl, spawn_fn in self._templates_and_spawners:
            if type(tpl) is cls:
                spawn_fn(event_pos, components_list)
                return
        raise KeyError(f"No bank template for {cls.__name__}")
**Why:** Lifts a single, narrow public method onto the bank so external
callers (currently just `main.py`'s K_n handler, eventually any other
hotkey or future palette) can spawn through the same closure a click
runs — cursor-centered, drag-primed, `_moved_while_dragging` set. Uses
`type(tpl) is cls` rather than `isinstance` so a Switch template never
shadows a request for `Component` (Switch subclasses Component). Raises
`KeyError` for an unknown class so a typo at the call site fails loudly
instead of silently no-op'ing. `handle_event`'s template loop deliberately
stays separate: it dispatches by rect-collision, not by class, and
collapsing the two would force collision logic into both call paths.
**Editor:** Claude (Opus 4.7)

**File:** main.py
**Lines (at time of edit):** 93-98 (K_n handler in `_handle_keydown`)
**Before:**
    # Centralized place to spawn components
    if event.key == pygame.K_n:
        self.components.append(Component(50, 50))
**After:**
    # N spawns a NAND through the bank's own spawn path so the hotkey
    # and the toolbox click stay in lock-step (cursor-centered, drag
    # primed, _moved_while_dragging set). Keeping the duplicate here
    # would re-introduce drift the moment the bank's spawner changes.
    if event.key == pygame.K_n:
        self.bank.spawn_component(Component, pygame.mouse.get_pos(), self.components)
**Why:** The old handler appended a raw `Component(50, 50)` — no cursor
centering, no drag priming, no `_moved_while_dragging` flag — so a
keyboard-spawned NAND landed at a fixed corner and just sat there until
the user grabbed it, while a bank-spawned NAND followed the cursor and
dropped on the next click. Routing through `bank.spawn_component` makes
both entry points identical, which matches the design principle that
keyboard shortcuts are aliases for clickable equivalents, never a
parallel implementation. Import of `Component` from `elements` is
unchanged — still needed as the `cls` argument.
**Editor:** Claude (Opus 4.7)

**File:** docs/TODO.md
**Lines (at time of edit):** ~39-41 (Now section, the N/T hotkey item)
**Why:** Checks off the last open item under "Now — Toolbar TEXT button"
and records the design call (N routed through the bank, T left direct
because it was already honest). With this entry the entire "Now" section
is complete; the next session should pick up at "Next — Bottom-left popup
menu (file ops)".
**Editor:** Claude (Opus 4.7)

## 2026-05-02 — Add MENU button slot to bottom-left of toolbox bank

**File:** settings.py
**Lines (at time of edit):** 182-198 (new MenuButtonSettings inserted before AudioSettings)
**Before:**
    (no MenuButtonSettings class)
**After:**
    class MenuButtonSettings:
        SIZE = 60
        BODY_COLOR = (60, 60, 60)
        BORDER_COLOR = ColorSettings.WORD_COLORS["WHITE"]
        BORDER_THICKNESS = 1
        LABEL = "MENU"
        LABEL_COLOR = ColorSettings.WORD_COLORS["WHITE"]
**Why:** First step of the bottom-left popup menu task in TODO Next. The
popup itself, click handling, and menu items are out of scope for this
edit — only the visual slot is added so the button can be placed in the
bank without changing event flow.
**Editor:** Claude (Opus 4.6)

**File:** ui.py
**Lines (at time of edit):** 5-11 (imports), 60-105 (new MenuButton class),
135-142 (ComponentBank.__init__ instantiates menu_button), 174-178
(_build_templates anchors x to menu_button.rect.right), 305-307 (draw)
**Before:**
    # _build_templates started templates flush at BANK_PADDING_X.
    x = UISettings.BANK_PADDING_X
    # ComponentBank.draw drew only the bank rect, separator, and templates.
**After:**
    # New MenuButton class (rect + label + draw, no click handling yet).
    # ComponentBank.__init__ builds self.menu_button at BANK_PADDING_X,
    # vertically centered. _build_templates starts at
    # menu_button.rect.right + BANK_TEMPLATE_GAP so [MENU] [Switch] [NAND]
    # [LED] [TEXT] reads as one row with no overlap. ComponentBank.draw
    # blits the menu button before the templates.
**Why:** Adds the visual anchor for the bottom-left popup menu (TODO
Next). Anchoring the template row to menu_button.rect.right keeps the
layout self-consistent if MENU's size ever changes — no second magic
number to keep in sync. Click handling and the popup arrive in the
next bullet.
**Editor:** Claude (Opus 4.6)
