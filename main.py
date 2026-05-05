from __future__ import annotations

import os
import pygame
import sys
import traceback as _traceback
from copy import deepcopy
from typing import Tuple

from core.elements import Component, LED, SavedComponent, Switch
from core.project_manager import ProjectManager
from core.signals import SignalManager
from fonts import Fonts
from ui.bank import ComponentBank
from ui.crt import CRT
from ui.project_dialogs import FileNotFoundWarningDialog, LoadProjectDialog, SaveProjectDialog
from ui.quit_confirm_dialog import QuitConfirmDialog
from ui.save_as_component_handler import SaveAsComponentHandler
from ui.save_component_dialog import SaveComponentDialog
from ui.text_boxes import TextBoxManager
from ui.top_menu_bar import TopMenuBar
from core.wires import WireManager
from core.commands import (
    History,
    PlaceComponent, DeleteComponent,
    PlaceWire, DeleteWire,
    PlaceTextBox, DeleteTextBox,
)
from settings import *

_PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "projects")


class GameManager:
    """Main game manager coordinating all gameplay systems.
    
    Manages the game loop, event handling, rendering, and high-level state.
    Delegates menu, project, and component-specific logic to handler classes
    to keep this class light and focused on orchestration.
    """
    
    def __init__(self):
        # -------- Pygame core --------
        pygame.init()
        Fonts.init()

        # -------- Display --------
        self.screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
        pygame.display.set_caption(ScreenSettings.TITLE)
        self.clock = pygame.time.Clock()
        self.crt = CRT(self.screen)
        self._crt_enabled = ScreenSettings.CRT_ENABLED_DEFAULT

        # -------- UI state --------
        self.text_boxes = TextBoxManager()
        self.dialog = None
        self.bank = ComponentBank(self.text_boxes)
        
        # -------- Workspace state --------
        self.components = []
        self.wires = WireManager()
        self.signals = SignalManager()
        self.saved_components = []
        self.selected_components = []
        
        # -------- Selection/drag state --------
        self._marquee_start = None
        self._marquee_end = None
        self._group_drag_anchor = None
        self._group_drag_start_positions = {}
        self._group_drag_moved = False
        self._click_candidate_component = None
        
        # -------- Handlers --------
        self.project_manager = ProjectManager(_PROJECTS_DIR)
        self._current_project_name: str | None = None
        
        # -------- Undo / redo --------
        self.history = History()
        self.wires.on_commit = (
            lambda wire, displaced: self.history.push(PlaceWire(self.wires, wire, displaced))
        )
        self.wires.on_delete = (
            lambda wire: self.history.push(DeleteWire(self.wires, wire))
        )
        self.text_boxes.on_spawn = (
            lambda box: self.history.push(PlaceTextBox(self.text_boxes, box))
        )
        self.text_boxes.on_delete = (
            lambda box, idx: self.history.push(DeleteTextBox(self.text_boxes, box, idx))
        )
        
        # -------- Menu bar (must be after history) --------
        self._setup_menu_bar()
        
        # Error banner display state
        self._error_info = None
    
    def _setup_menu_bar(self):
        """Initialize the top menu bar with FILE/EDIT/VIEW menus."""
        menu_defs = {
            "file": {
                "label": TopMenuBarSettings.FILE_LABEL,
                "items": tuple(
                    (item_id, label, "ESC" if item_id == "quit" else "")
                    for item_id, label in MenuButtonSettings.ITEMS
                ),
                "actions": {
                    "new_project": self._new_project,
                    "load_project": self._open_load_project_dialog,
                    "save_project": self._save_project,
                    "save_project_as": self._open_save_as_dialog,
                    "save_as_component": self.save_as_component,
                    "quit": self.close_game,
                },
            },
            "edit": {
                "label": TopMenuBarSettings.EDIT_LABEL,
                "items": (
                    ("undo", "UNDO", "CTRL+Z"),
                    ("redo", "REDO", "CTRL+Y"),
                ),
                "actions": {
                    "undo": self.history.undo,
                    "redo": self.history.redo,
                },
            },
            "view": {
                "label": TopMenuBarSettings.VIEW_LABEL,
                "items": (
                    (
                        "toggle_fullscreen",
                        TopMenuBarSettings.VIEW_TOGGLE_FULLSCREEN_LABEL,
                        TopMenuBarSettings.VIEW_TOGGLE_FULLSCREEN_SHORTCUT,
                    ),
                    (
                        "toggle_crt",
                        TopMenuBarSettings.VIEW_TOGGLE_CRT_LABEL,
                        TopMenuBarSettings.VIEW_TOGGLE_CRT_SHORTCUT,
                    ),
                ),
                "actions": {
                    "toggle_fullscreen": pygame.display.toggle_fullscreen,
                    "toggle_crt": self._toggle_crt,
                },
            },
        }
        self.top_menu_bar = TopMenuBar(self.screen, menu_defs)

    def _toggle_crt(self) -> None:
        """Toggle whether the CRT overlay is drawn each frame.

        Returns:
            None
        """
        self._crt_enabled = not self._crt_enabled

    # -------------------------
    # BOOT / LIFECYCLE
    # -------------------------

    def close_game(self):
        """Quit pygame and exit the process."""
        pygame.quit()
        sys.exit()

    # -------------------------
    # GAMEPLAY ACTIONS
    # -------------------------

    def save_as_component(self) -> None:
        """Open the SAVE AS COMPONENT dialog.
        
        Bound into the FILE menu. The dialog collects the component name and
        color; workspace snapshot happens in _finalize_save_as_component at
        Save time. Reading the workspace at finalize is safe because the
        dialog is modal — events that could mutate components are blocked.
        
        Returns:
            None
        """
        self.dialog = SaveComponentDialog(
            on_save=self._finalize_save_as_component,
            on_cancel=self._dismiss_dialog,
        )

    def _finalize_save_as_component(self, name: str, color: Tuple[int, int, int]) -> None:
        """Auto-infer ports from the workspace, stash the record, dismiss.
        
        Per the "Save-as-Component port inference rule": every Switch in the
        workspace becomes an INPUT port and every LED becomes an OUTPUT port;
        ordering is ascending Y so the top-of-screen IN is port 0, the next one
        down is port 1, and so on.
        
        Args:
            name: Saved component's display name (uppercase, already trimmed).
            color: Saved wrapper body color (RGB tuple).
        
        Returns:
            None
        """
        input_switches, output_leds = SaveAsComponentHandler.infer_component_ports(self.components)
        definition = SaveAsComponentHandler.snapshot_workspace_definition(
            self.components,
            self.wires.wires,
            input_switches,
            output_leds,
        )
        record = {
            "name": name,
            "color": color,
            "inputs": input_switches,
            "outputs": output_leds,
            "definition": definition,
        }
        self.saved_components.append(record)
        self.bank.add_saved_component_template(
            name,
            record["color"],
            deepcopy(definition),
        )
        self._clear_workspace()
        self._dismiss_dialog()

    def _clear_workspace(self) -> None:
        """Reset the live workspace to an empty canvas.

        Clears placed components, committed/pending wires, and text-box
        annotations. Used after Save-as-Component so the student can start
        the next abstraction layer immediately.
        
        Returns:
            None
        """
        self.components.clear()
        self.wires.wires.clear()
        self.wires.pending_source = None
        self.text_boxes.text_boxes.clear()
        self.text_boxes.focused = None
        self._set_selected_components([])
        self._cancel_marquee()
        self._cancel_group_drag()
        # History holds references to the old components and wires.  Clear
        # it so undo can't resurrect objects from the previous workspace.
        self.history.clear()

    # -------------------------
    # PROJECT SAVE / LOAD
    # -------------------------

    def _save_project(self) -> None:
        """Save directly if a project name is already set; otherwise open Save As.
        
        Returns:
            None
        """
        if self._current_project_name is not None:
            self._finalize_save_project(self._current_project_name)
        else:
            self._open_save_as_dialog()

    def _open_save_as_dialog(self) -> None:
        """Open the SAVE AS dialog (list of existing projects + name input).
        
        Returns:
            None
        """
        existing = self.project_manager.list_project_names()
        self.dialog = SaveProjectDialog(
            existing_names=existing,
            on_save=self._finalize_save_project,
            on_cancel=self._dismiss_dialog,
        )

    # Keep old name as alias so any future callers still work.
    def _open_save_project_dialog(self) -> None:
        """Alias for _open_save_as_dialog for backward compatibility."""
        self._open_save_as_dialog()

    def _finalize_save_project(self, name: str) -> None:
        """Serialize the workspace to projects/<name>.json and remember the name.
        
        Args:
            name: Project name to save as.
        """
        workspace_data = ProjectManager.serialize_workspace(
            name,
            self.components,
            self.wires.wires,
            self.text_boxes.text_boxes,
            self.saved_components,
        )
        self._current_project_name = self.project_manager.save_project(name, workspace_data)
        self._dismiss_dialog()

    def _open_load_project_dialog(self) -> None:
        """Open the LOAD PROJECT dialog listing all saved projects."""
        names = self.project_manager.list_project_names()
        self.dialog = LoadProjectDialog(
            project_names=names,
            on_load=self._finalize_load_project,
            on_cancel=self._dismiss_dialog,
        )

    def _finalize_load_project(self, safe_name: str) -> None:
        """Load a project from disk and replace the current workspace.
        
        Args:
            safe_name: Sanitized project name to load.
        """
        payload = self.project_manager.load_project(safe_name)
        if payload is None:
            self._dismiss_dialog()
            self.dialog = FileNotFoundWarningDialog(
                on_dismiss=self._dismiss_dialog,
            )
            return
        self._dismiss_dialog()
        self._current_project_name = safe_name
        ProjectManager.deserialize_workspace(
            payload,
            self.components,
            self.wires,
            self.text_boxes,
            self.bank,
            self.saved_components,
        )

    def _new_project(self) -> None:
        """Clear the workspace to start a fresh project."""
        self._clear_workspace()
        # Also reset the in-session saved-components library and bank templates.
        self.saved_components.clear()
        self.bank._templates_and_spawners = self.bank._build_templates()
        self._current_project_name = None

    # -------------------------
    # DIALOG MANAGEMENT
    # -------------------------

    def _dismiss_dialog(self):
        """Close whichever dialog is currently open.

        Reaching this with `self.dialog is None` should not happen in
        practice — both Cancel and Esc paths inside the dialog go
        through here, and a no-op is the right safe default if a
        future caller somehow double-dismisses.
        """
        self.dialog = None

    def _show_quit_confirm(self):
        """Open the quit-confirmation dialog; only YES closes the app."""
        self.dialog = QuitConfirmDialog(
            on_confirm=self.close_game,
            on_cancel=self._dismiss_dialog,
        )

    # -------------------------
    # AUDIO / VOLUME ACTIONS
    # -------------------------

    # -------------------------
    # EVENT HANDLING
    # -------------------------

    def _process_events(self) -> None:
        """Pump the event queue and route each event to the right handler."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_game()
                continue

            # Top menu captures focus while open.
            if self.top_menu_bar.is_menu_open():
                if event.type == pygame.KEYDOWN:
                    self._handle_keydown(event)
                    continue
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                    self._handle_mouse(event)
                    continue

            # Modal dialog owns all events while open.
            if self.dialog is not None:
                self.dialog.handle_event(event)
                continue

            # Text boxes claim keystrokes and clicks before wires/components.
            if self.text_boxes.handle_event(event):
                continue

            # Route logic to specialized handlers
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                self._handle_mouse(event)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Route a single keyboard press.
        
        Args:
            event: Pygame keyboard event.
        """
        self._prune_selection()
        mods = pygame.key.get_mods()
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

        if event.key in (pygame.K_f, pygame.K_e, pygame.K_v) and not (mods & (pygame.KMOD_CTRL | pygame.KMOD_ALT)):
            menu_id = {
                pygame.K_f: "file",
                pygame.K_e: "edit",
                pygame.K_v: "view",
            }[event.key]
            self.top_menu_bar.toggle_menu(menu_id)
            return

        if event.key == pygame.K_z and (mods & pygame.KMOD_CTRL):
            if mods & pygame.KMOD_SHIFT:
                self.history.redo()
            else:
                self.history.undo()
            return
        if event.key == pygame.K_y and (mods & pygame.KMOD_CTRL):
            self.history.redo()
            return

        if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
            self._delete_selected_components()
            return

        # Global keys (always honored regardless of run state).
        if event.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
        if event.key == pygame.K_F10:
            self._toggle_crt()
        if event.key == pygame.K_ESCAPE:
            # Layered Esc behavior (priority order):
            # 1. Dialog/popup already open -> dialog handles its own Esc
            #    (self.dialog routes events before _handle_keydown runs).
            # 2. Fullscreen -> exit fullscreen.
            if pygame.display.get_surface().get_flags() & pygame.FULLSCREEN:
                pygame.display.toggle_fullscreen()
                return
            # 3. Show quit confirm dialog; only YES actually quits.
            self._show_quit_confirm()
        if event.key == pygame.K_t:
            self.text_boxes.spawn_at(pygame.mouse.get_pos())

    def _handle_mouse(self, event: pygame.event.Event) -> None:
        """Pass mouse events to the component manager or components directly.
        
        Args:
            event: Pygame mouse event.
        """
        self._prune_selection()
        workspace_rect = pygame.Rect(
            0,
            TopMenuBarSettings.HEIGHT,
            ScreenSettings.WIDTH,
            UISettings.BANK_RECT.top - TopMenuBarSettings.HEIGHT,
        )

        if event.type == pygame.MOUSEMOTION:
            self.top_menu_bar.sync_hover_with_mouse(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            clicked_top_menu_id = self.top_menu_bar.menu_id_at_pos(event.pos)
            if clicked_top_menu_id is not None:
                self.top_menu_bar.toggle_menu(clicked_top_menu_id)
                return
            if self.top_menu_bar.is_menu_open():
                index = self.top_menu_bar.menu_item_index_at_pos(event.pos)
                if index is not None:
                    self.top_menu_bar.move_selection(0)  # Align keyboard selection with mouse
                    action = self.top_menu_bar.activate_selection()
                    if action is not None:
                        action()
                    return
                self.top_menu_bar.close_menu()
                return

        if event.type == pygame.MOUSEMOTION:
            self._update_port_hover(event.pos)

        if self._group_drag_anchor is not None:
            self._handle_group_drag_event(event)
            return

        if self._marquee_start is not None:
            self._handle_marquee_event(event)
            return

        # Wires get the event before bank/components: a click that lands on a
        # port should start a wire, not drag the underlying component.
        if self.wires.handle_event(event, self.components, workspace_rect):
            return

        before = len(self.components)
        if self.bank.handle_event(event, self.components):
            if len(self.components) > before:
                spawned_component = self.components[-1]
                self.history.push(PlaceComponent(self.components, self.wires, spawned_component))
                self._set_selected_components([spawned_component])
                # Spawned components should drag immediately if the mouse is held.
                self._start_group_drag(event.pos, click_candidate=None)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            clicked = self._component_at(event.pos)
            if clicked is None:
                self._set_selected_components([])
                self._start_marquee(event.pos)
                return
            if clicked in self.selected_components:
                self._start_group_drag(event.pos, click_candidate=clicked)
                return
            self._set_selected_components([clicked])
            self._start_group_drag(event.pos, click_candidate=clicked)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.RIGHT_CLICK:
            for i in range(len(self.components) - 1, -1, -1):
                comp = self.components[i]
                action = comp.handle_event(event)
                if action == "DELETE":
                    self._delete_component_at_index(i)
                    break

    def _update_port_hover(self, mouse_pos) -> None:
        """Refresh the hovered flag on every port given the current cursor.

        Walks all workspace components plus the toolbox template so a port in
        either place lights up under the cursor. Callers must invoke this on
        MOUSEMOTION; ports do not poll their own state.

        Args:
            mouse_pos (tuple[int, int]): Cursor position in screen space.
        """
        for comp in self.components:
            for port in comp.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)
        for tpl in self.bank.templates:
            for port in tpl.ports:
                port.hovered = port.rect.collidepoint(mouse_pos)

    def _component_at(self, pos):
        """Return the top-most workspace component under the cursor."""
        for comp in reversed(self.components):
            if comp.rect.collidepoint(pos):
                return comp
        return None

    def _set_selected_components(self, components):
        """Set the active component selection and sync visual flags."""
        selected = [comp for comp in components if comp in self.components]
        selected_ids = set(selected)
        for comp in self.components:
            comp.selected = comp in selected_ids
        self.selected_components = selected

    def _prune_selection(self):
        """Drop stale selections when undo/redo removes selected components."""
        live = [comp for comp in self.selected_components if comp in self.components]
        if len(live) != len(self.selected_components):
            self._set_selected_components(live)

    def _delete_component_at_index(self, index):
        """Delete one component and record undo history for it."""
        comp = self.components[index]
        affected_wires = [
            w for w in self.wires.wires
            if w.source.parent is comp or w.target.parent is comp
        ]
        self.wires.drop_wires_for_component(comp)
        self.components.pop(index)
        self.history.push(DeleteComponent(self.components, self.wires, comp, affected_wires, index))
        if comp in self.selected_components:
            self._set_selected_components(
                [selected for selected in self.selected_components if selected is not comp]
            )

    def _delete_selected_components(self):
        """Delete every selected component in one keypress."""
        if not self.selected_components:
            return
        selected_ids = set(self.selected_components)
        for index in range(len(self.components) - 1, -1, -1):
            if self.components[index] in selected_ids:
                self._delete_component_at_index(index)
        self._set_selected_components([])
        self._cancel_group_drag()
        self._cancel_marquee()

    def _start_group_drag(self, mouse_pos, click_candidate):
        """Begin dragging all currently selected components together."""
        if not self.selected_components:
            return
        self._group_drag_anchor = mouse_pos
        self._group_drag_start_positions = {
            comp: (comp.rect.x, comp.rect.y)
            for comp in self.selected_components
        }
        self._group_drag_moved = False
        self._click_candidate_component = click_candidate

    def _cancel_group_drag(self):
        self._group_drag_anchor = None
        self._group_drag_start_positions = {}
        self._group_drag_moved = False
        self._click_candidate_component = None

    def _handle_group_drag_event(self, event):
        """Update or complete a multi-component drag gesture."""
        if self._group_drag_anchor is None:
            return
        if event.type == pygame.MOUSEMOTION:
            dx = event.pos[0] - self._group_drag_anchor[0]
            dy = event.pos[1] - self._group_drag_anchor[1]
            if dx or dy:
                self._group_drag_moved = True
            for comp, (start_x, start_y) in self._group_drag_start_positions.items():
                comp.rect.x = start_x + dx
                comp.rect.y = start_y + dy
                comp._clamp_to_workspace()
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == InputSettings.LEFT_CLICK:
            # Preserve click-without-drag behavior for single-component Switch toggles.
            if (not self._group_drag_moved
                    and self._click_candidate_component is not None
                    and len(self.selected_components) == 1
                    and self.selected_components[0] is self._click_candidate_component):
                self._click_candidate_component._on_click()
            self._cancel_group_drag()

    def _start_marquee(self, mouse_pos):
        """Start drawing a marquee selection rectangle."""
        self._marquee_start = mouse_pos
        self._marquee_end = mouse_pos

    def _cancel_marquee(self):
        self._marquee_start = None
        self._marquee_end = None

    def _current_marquee_rect(self):
        """Return normalized marquee rect from the current drag endpoints."""
        if self._marquee_start is None or self._marquee_end is None:
            return pygame.Rect(0, 0, 0, 0)
        x0, y0 = self._marquee_start
        x1, y1 = self._marquee_end
        left = min(x0, x1)
        top = min(y0, y1)
        width = abs(x1 - x0)
        height = abs(y1 - y0)
        return pygame.Rect(left, top, width, height)

    def _handle_marquee_event(self, event):
        """Update or complete a marquee selection gesture."""
        if event.type == pygame.MOUSEMOTION:
            self._marquee_end = event.pos
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == InputSettings.LEFT_CLICK:
            self._marquee_end = event.pos
            marquee = self._current_marquee_rect()
            if (marquee.width < SelectionBoxSettings.MIN_DRAG_PIXELS
                    and marquee.height < SelectionBoxSettings.MIN_DRAG_PIXELS):
                self._set_selected_components([])
                self._cancel_marquee()
                return
            selected = [
                comp for comp in self.components
                if marquee.colliderect(comp.rect)
            ]
            self._set_selected_components(selected)
            self._cancel_marquee()

    # -------------------------
    # PER-FRAME UPDATE / RENDER
    # -------------------------

    def _draw(self):
        """Draw all workspace layers in back-to-front order."""
        for comp in self.components:
            comp.draw(self.screen)
        self.wires.draw(self.screen)
        self.text_boxes.draw(self.screen)
        self._draw_selection_marquee()
        self.bank.draw(self.screen)
        if self.dialog is not None:
            self.dialog.draw(self.screen)

    def _draw_selection_marquee(self):
        """Draw the active marquee rectangle while drag-selecting."""
        if self._marquee_start is None:
            return
        rect = self._current_marquee_rect()
        if rect.width == 0 or rect.height == 0:
            return
        fill = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        fill.fill(SelectionBoxSettings.FILL_COLOR)
        self.screen.blit(fill, rect.topleft)
        pygame.draw.rect(
            self.screen,
            SelectionBoxSettings.BORDER_COLOR,
            rect,
            SelectionBoxSettings.BORDER_THICKNESS,
        )

    def _draw_grid(self):
        """Draw the background grid lines."""
        grid_color = ColorSettings.WORD_COLORS["WHITE"]
        grid_size = ScreenSettings.GRID_SIZE
        for x in range(0, ScreenSettings.WIDTH, grid_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, ScreenSettings.HEIGHT), 1)
        for y in range(0, ScreenSettings.HEIGHT, grid_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (ScreenSettings.WIDTH, y), 1)

    def _draw_error_banner(self):
        """Draw a red error banner below the shortcut bar when an error occurred.

        Reads self._error_info (set by the run() try/except) and renders a
        dark-red strip showing the exception type and message. Clears
        self._error_info automatically once ErrorBannerSettings.DISPLAY_MS
        has elapsed, so the banner flashes briefly then disappears without
        any extra bookkeeping in the caller.
        """
        if self._error_info is None:
            return
        exc_type, message, timestamp = self._error_info
        elapsed = pygame.time.get_ticks() - timestamp
        if elapsed > ErrorBannerSettings.DISPLAY_MS:
            self._error_info = None
            return
        bar = pygame.Rect(
            0,
            TopMenuBarSettings.HEIGHT,
            ScreenSettings.WIDTH,
            ErrorBannerSettings.HEIGHT,
        )
        pygame.draw.rect(self.screen, ErrorBannerSettings.BG_COLOR, bar)
        label = f"ERROR \u2014 {exc_type}: {message}"
        font = Fonts.text_box
        if font is None:
            return
        surf = font.render(label, True, ErrorBannerSettings.TEXT_COLOR)
        self.screen.blit(
            surf,
            (bar.x + ErrorBannerSettings.PADDING_X,
             bar.y + (bar.height - surf.get_height()) // 2),
        )

    def _render_frame(self):
        """Clear the screen and draw all layers for this frame."""
        self.screen.fill(ScreenSettings.BG_COLOR)
        self._draw_grid()
        self._draw()
        self.top_menu_bar.draw()
        if self._crt_enabled:
            self.crt.draw()
        # Error banner draws after the CRT overlay so it's always legible.
        self._draw_error_banner()

    def run(self):
        """Run the main event loop, keeping the app alive on recoverable errors.

        Wraps the per-frame update + render in a try/except so an unhandled
        exception during simulation or rendering stores a brief error record
        instead of crashing the process. The error banner (drawn by
        _draw_error_banner via _render_frame) then flashes for a few seconds
        before clearing, leaving the workspace in whatever state it was in.
        """
        while True:
            try:
                self._process_events()
                self.signals.update(self.components, self.wires.wires)
                self._render_frame()
            except Exception as exc:
                _traceback.print_exc()
                self._error_info = (
                    type(exc).__name__,
                    str(exc),
                    pygame.time.get_ticks(),
                )
                # Best-effort minimal draw so the user sees a banner even if
                # _render_frame itself threw (e.g. a bad draw call).
                try:
                    self.screen.fill(ScreenSettings.BG_COLOR)
                    self._draw_error_banner()
                except Exception:
                    pass
            pygame.display.flip()
            self.clock.tick(ScreenSettings.FPS)


# Main execution
if __name__ == '__main__':
    game_manager = GameManager()
    game_manager.run()

