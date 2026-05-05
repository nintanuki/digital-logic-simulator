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
from core.workspace_controller import WorkspaceInteractionController
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
    PlaceComponent,
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

        # -------- Workspace interaction controller --------
        self.workspace_interaction = WorkspaceInteractionController(
            self.components,
            self.wires,
            self.history,
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
        self.wires.clear_all()
        self.text_boxes.clear_all()
        self.workspace_interaction.clear_interaction_state()
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
        self.bank.reset_to_default_templates()
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
        self.workspace_interaction.prune_selection()
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
            self.workspace_interaction.delete_selected_components()
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
        self.workspace_interaction.prune_selection()
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
            self.workspace_interaction.update_port_hover(event.pos, self.bank.templates)

        if self.workspace_interaction.is_group_drag_active():
            self.workspace_interaction.handle_group_drag_event(event)
            return

        if self.workspace_interaction.is_marquee_active():
            self.workspace_interaction.handle_marquee_event(event)
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
                self.workspace_interaction.set_selected_components([spawned_component])
                # Spawned components should drag immediately if the mouse is held.
                self.workspace_interaction.start_group_drag(event.pos, click_candidate=None)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            clicked = self.workspace_interaction.component_at(event.pos)
            if clicked is None:
                self.workspace_interaction.set_selected_components([])
                self.workspace_interaction.start_marquee(event.pos)
                return
            if clicked in self.workspace_interaction.selected_components:
                self.workspace_interaction.start_group_drag(event.pos, click_candidate=clicked)
                return
            self.workspace_interaction.set_selected_components([clicked])
            self.workspace_interaction.start_group_drag(event.pos, click_candidate=clicked)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.RIGHT_CLICK:
            for i in range(len(self.components) - 1, -1, -1):
                comp = self.components[i]
                action = comp.handle_event(event)
                if action == "DELETE":
                    self.workspace_interaction.delete_component_at_index(i)
                    break

    # -------------------------
    # PER-FRAME UPDATE / RENDER
    # -------------------------

    def _draw(self):
        """Draw all workspace layers in back-to-front order."""
        for comp in self.components:
            comp.draw(self.screen)
        self.wires.draw(self.screen)
        self.text_boxes.draw(self.screen)
        self.workspace_interaction.draw_selection_marquee(self.screen)
        self.bank.draw(self.screen)
        if self.dialog is not None:
            self.dialog.draw(self.screen)

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

