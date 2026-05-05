from __future__ import annotations

import json
import os
import pygame
import sys
import traceback as _traceback
from copy import deepcopy

from core.elements import Component, LED, SavedComponent, Switch
from fonts import Fonts
from ui.project_dialogs import FileNotFoundWarningDialog, LoadProjectDialog, SaveProjectDialog
from ui.save_component_dialog import SaveComponentDialog
from ui.quit_confirm_dialog import QuitConfirmDialog
from settings import *

_PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "projects")
from core.signals import SignalManager
from ui.text_boxes import TextBoxManager
from ui.bank import ComponentBank
from ui.crt import CRT
from core.wires import WireManager
from core.commands import (
    History,
    PlaceComponent, DeleteComponent,
    PlaceWire, DeleteWire,
    PlaceTextBox, DeleteTextBox,
)


class GameManager:
    def __init__(self):
        # -------- Pygame core --------
        pygame.init()
        Fonts.init()

        # -------- Display --------
        self.screen = pygame.display.set_mode(ScreenSettings.RESOLUTION)
        pygame.display.set_caption(ScreenSettings.TITLE)
        self.clock = pygame.time.Clock()
        self.crt = CRT(self.screen)

        self.text_boxes = TextBoxManager()
        # Active modal dialog, or None.
        self.dialog = None
        # In-session only; disk persistence is Pass 3.
        self.saved_components = []
        # Name of the currently loaded/saved project, or None for a fresh unsaved project.
        self._current_project_name: str | None = None
        self._menu_actions = {
            "new_project": self._new_project,
            "load_project": self._open_load_project_dialog,
            "save_project": self._save_project,
            "save_project_as": self._open_save_as_dialog,
            "save_as_component": self.save_as_component,
            "quit": self.close_game,
        }
        self.bank = ComponentBank(self.text_boxes)
        self.components = []
        self.wires = WireManager()
        self.signals = SignalManager()
        self.selected_components = []
        self._marquee_start = None
        self._marquee_end = None
        self._group_drag_anchor = None
        self._group_drag_start_positions = {}
        self._group_drag_moved = False
        self._click_candidate_component = None

        # -------- Undo / redo --------
        self.history = History()
        # Lambdas kept here so command objects reference self.* without coupling subsystems to commands.py.
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
        text_font = Fonts.text_box
        if text_font is None:
            raise RuntimeError("Fonts.init() must run before UI text render")
        # Pre-render static hotkey hint text once; blit each frame.
        self._hotkey_hint_surfs = self._build_hotkey_bar_text_surfaces()
        self._file_menu_item_surfs = self._build_file_menu_item_surfaces()
        self._file_label_surf = text_font.render(
            TopMenuBarSettings.FILE_LABEL,
            True,
            TopMenuBarSettings.TEXT_COLOR,
        )
        self._file_menu_open = False
        self._file_menu_hover_index = 0
        self._file_button_rect = pygame.Rect(0, 0, 0, 0)
        self._file_menu_rect = pygame.Rect(0, 0, 0, 0)
        self._file_menu_item_rects = []
        self._rebuild_file_menu_geometry()
        # Recoverable-error state. Set to (exc_type_name, message, timestamp_ms)
        # by the per-frame try/except in run(); cleared automatically after
        # ErrorBannerSettings.DISPLAY_MS so it only flashes briefly.
        self._error_info = None

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

    def save_as_component(self):
        """Open the SAVE AS COMPONENT dialog.

        Bound into the bottom-left popup's menu_actions for the SAVE AS
        COMPONENT label. The dialog itself only collects the name; the
        workspace snapshot (switches → INPUTs, LEDs → OUTPUTs, both
        ordered by Y) happens here in `_finalize_save_as_component` at
        Save time. Reading the workspace at finalize is safe because
        the dialog is modal — events that could mutate `self.components`
        are blocked while the dialog is open.
        """
        self.dialog = SaveComponentDialog(
            on_save=self._finalize_save_as_component,
            on_cancel=self._dismiss_dialog,
        )

    def _finalize_save_as_component(self, name, color):
        """Auto-infer ports from the workspace, stash the record, dismiss.

        Per the "Save-as-Component port inference rule" in TODO Risks &
        Notes: every Switch in the workspace becomes an INPUT port and
        every LED becomes an OUTPUT port; ordering is ascending Y so
        the top-of-screen IN is port 0, the next one down is port 1,
        and so on. Y was picked over component-creation-order because
        the visual top-to-bottom column is what the student actually
        sees — picking the order from something invisible would break
        the spatial intuition.

        Pass 1 step 1 (v2) keeps this stub minimal: capture the
        inferred record and dismiss. Pass 1 step 2 (toolbox template)
        will consume `saved_components` to materialize each record as
        a clickable bank template, and step 3 (spawn-as-working-
        component) will turn that template into a usable sub-circuit.

        Args:
            name (str): Saved component's display name (uppercase,
                already trimmed by the dialog).
            color (tuple[int, int, int]): Saved wrapper body color from
                the dialog's RGB fields.
        """
        # `sorted(...)` returns a fresh list; the workspace's own
        # `self.components` ordering is left alone so the user's
        # bottom-of-stack drag/draw priority isn't disturbed.
        input_switches = sorted(
            (c for c in self.components if isinstance(c, Switch)),
            key=lambda s: s.rect.y,
        )
        output_leds = sorted(
            (c for c in self.components if isinstance(c, LED)),
            key=lambda l: l.rect.y,
        )
        definition = self._snapshot_workspace_definition(
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

    def _clear_workspace(self):
        """Reset the live workspace to an empty canvas.

        Clears placed components, committed/pending wires, and text-box
        annotations. Used after Save-as-Component so the student can start
        the next abstraction layer immediately.
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

    def _snapshot_workspace_definition(self, input_switches, output_leds):
        """Serialize the current workspace into a saved-component definition.

        Args:
            input_switches (list[Switch]): Switches selected as external inputs.
            output_leds (list[LED]): LEDs selected as external outputs.

        Returns:
            dict: Serialized sub-circuit payload for SavedComponent runtime.
        """
        component_indices = {
            comp: idx for idx, comp in enumerate(self.components)
        }
        component_defs = [
            self._serialize_component(comp) for comp in self.components
        ]
        wire_defs = []
        for wire in self.wires.wires:
            source_parent = wire.source.parent
            target_parent = wire.target.parent
            if source_parent not in component_indices:
                continue
            if target_parent not in component_indices:
                continue
            wire_defs.append({
                "source_component_index": component_indices[source_parent],
                "source_port_index": source_parent.ports.index(wire.source),
                "target_component_index": component_indices[target_parent],
                "target_port_index": target_parent.ports.index(wire.target),
            })
        return {
            "components": component_defs,
            "wires": wire_defs,
            "input_component_indices": [
                component_indices[switch]
                for switch in input_switches
                if switch in component_indices
            ],
            "output_component_indices": [
                component_indices[led]
                for led in output_leds
                if led in component_indices
            ],
        }

    @staticmethod
    def _serialize_component(comp):
        """Serialize one workspace component into a definition record.

        Args:
            comp (Component): Component instance to serialize.

        Returns:
            dict: Serialized component payload.
        """
        if isinstance(comp, Switch):
            return {
                "type": "switch",
                "x": comp.rect.x,
                "y": comp.rect.y,
                "state": comp._state,
            }
        if isinstance(comp, LED):
            return {
                "type": "led",
                "x": comp.rect.x,
                "y": comp.rect.y,
            }
        if isinstance(comp, SavedComponent):
            return {
                "type": "saved_component",
                "x": comp.rect.x,
                "y": comp.rect.y,
                "name": comp.name,
                "color": list(comp.color),
                "definition": deepcopy(comp.definition),
            }
        return {
            "type": "nand",
            "x": comp.rect.x,
            "y": comp.rect.y,
        }

    # -------------------------
    # PROJECT SAVE / LOAD
    # -------------------------

    def _save_project(self):
        """Save directly if a project name is already set; otherwise open Save As."""
        if self._current_project_name is not None:
            self._finalize_save_project(self._current_project_name)
        else:
            self._open_save_as_dialog()

    def _open_save_as_dialog(self):
        """Open the SAVE AS dialog (list of existing projects + name input)."""
        existing = self._list_project_names()
        self.dialog = SaveProjectDialog(
            existing_names=existing,
            on_save=self._finalize_save_project,
            on_cancel=self._dismiss_dialog,
        )

    # Keep old name as alias so any future callers still work.
    def _open_save_project_dialog(self):
        self._open_save_as_dialog()

    def _finalize_save_project(self, name):
        """Serialize the workspace to projects/<name>.json and remember the name."""
        os.makedirs(_PROJECTS_DIR, exist_ok=True)
        safe_name = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name
        ).strip()
        payload = self._serialize_project(safe_name)
        path = os.path.join(_PROJECTS_DIR, safe_name + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        self._current_project_name = safe_name
        self._dismiss_dialog()

    def _serialize_project(self, name):
        """Return a JSON-serializable dict for the entire current workspace."""
        component_indices = {comp: idx for idx, comp in enumerate(self.components)}
        component_defs = [self._serialize_component(comp) for comp in self.components]
        wire_defs = []
        for wire in self.wires.wires:
            src = wire.source.parent
            tgt = wire.target.parent
            if src not in component_indices or tgt not in component_indices:
                continue
            wire_defs.append({
                "source_component_index": component_indices[src],
                "source_port_index": src.ports.index(wire.source),
                "target_component_index": component_indices[tgt],
                "target_port_index": tgt.ports.index(wire.target),
            })
        text_box_defs = [
            {"x": tb.rect.x, "y": tb.rect.y, "text": tb.text}
            for tb in self.text_boxes.text_boxes
        ]
        saved_component_defs = [
            {
                "name": rec["name"],
                "color": list(rec["color"]),
                "definition": deepcopy(rec["definition"]),
            }
            for rec in self.saved_components
        ]
        return {
            "version": 1,
            "name": name,
            "components": component_defs,
            "wires": wire_defs,
            "text_boxes": text_box_defs,
            "saved_components": saved_component_defs,
        }

    def _open_load_project_dialog(self):
        """Open the LOAD PROJECT dialog listing all saved projects."""
        names = self._list_project_names()
        self.dialog = LoadProjectDialog(
            project_names=names,
            on_load=self._finalize_load_project,
            on_cancel=self._dismiss_dialog,
        )

    def _list_project_names(self):
        """Return sorted list of project names available on disk."""
        if not os.path.isdir(_PROJECTS_DIR):
            return []
        names = []
        for filename in os.listdir(_PROJECTS_DIR):
            if filename.lower().endswith(".json"):
                names.append(os.path.splitext(filename)[0])
        return sorted(names)

    def _finalize_load_project(self, safe_name):
        """Load a project from disk and replace the current workspace."""
        path = os.path.join(_PROJECTS_DIR, safe_name + ".json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except FileNotFoundError:
            self._dismiss_dialog()
            self.dialog = FileNotFoundWarningDialog(
                on_dismiss=self._dismiss_dialog,
            )
            return
        self._dismiss_dialog()
        self._current_project_name = safe_name
        self._load_project_payload(payload)

    def _load_project_payload(self, payload):
        """Reconstruct the workspace from a serialized project dict."""
        self._clear_workspace()

        # Reset the saved-component library and bank templates so loading
        # twice doesn't accumulate duplicate toolbox entries.
        self.saved_components.clear()
        self.bank._templates_and_spawners = self.bank._build_templates()

        # Restore saved-component library first so spawned SavedComponents
        # in the workspace exist in the bank toolbox.
        for rec in payload.get("saved_components", []):
            definition = rec["definition"]
            color = tuple(rec["color"])
            name = rec["name"]
            self.saved_components.append({
                "name": name,
                "color": color,
                "definition": definition,
            })
            self.bank.add_saved_component_template(name, color, deepcopy(definition))

        # Restore components.
        for comp_def in payload.get("components", []):
            comp = self._deserialize_component(comp_def)
            self.components.append(comp)

        # Restore wires.
        from core.wires import Wire
        for wire_def in payload.get("wires", []):
            src_comp = self.components[wire_def["source_component_index"]]
            tgt_comp = self.components[wire_def["target_component_index"]]
            src_port = src_comp.ports[wire_def["source_port_index"]]
            tgt_port = tgt_comp.ports[wire_def["target_port_index"]]
            self.wires.wires.append(Wire(src_port, tgt_port))

        # Restore text boxes.
        for tb_def in payload.get("text_boxes", []):
            tb = self.text_boxes.spawn_at(
                (tb_def["x"], tb_def["y"]), focus=False
            )
            if tb is not None:
                tb.text = tb_def.get("text", "")
                tb._layout_to_text()

    @staticmethod
    def _deserialize_component(comp_def):
        """Build a workspace Component from a serialized record."""
        comp_type = comp_def["type"]
        if comp_type == "switch":
            comp = Switch(comp_def["x"], comp_def["y"])
            comp._state = comp_def.get("state", False)
            return comp
        if comp_type == "led":
            return LED(comp_def["x"], comp_def["y"])
        if comp_type == "saved_component":
            return SavedComponent(
                comp_def["x"],
                comp_def["y"],
                comp_def["name"],
                tuple(comp_def["color"]),
                comp_def["definition"],
            )
        return Component(comp_def["x"], comp_def["y"])

    def _new_project(self):
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

            # FILE menu captures focus while open.
            if self._file_menu_open:
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
        """Route a single keyboard press."""
        self._prune_selection()
        mods = pygame.key.get_mods()
        if self._file_menu_open:
            if event.key == pygame.K_DOWN:
                self._move_file_menu_selection(1)
                return
            if event.key == pygame.K_UP:
                self._move_file_menu_selection(-1)
                return
            if event.key == pygame.K_RETURN:
                self._activate_file_menu_selection()
                return
            if event.key == pygame.K_ESCAPE:
                self._close_file_menu()
                return

        if event.key == pygame.K_f and not (mods & (pygame.KMOD_CTRL | pygame.KMOD_ALT)):
            if self._file_menu_open:
                self._close_file_menu()
            else:
                self._open_file_menu()
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
        """Pass mouse events to the component manager or components directly."""
        self._prune_selection()

        if event.type == pygame.MOUSEMOTION:
            self._sync_file_menu_hover_with_mouse(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == InputSettings.LEFT_CLICK:
            if self._file_button_rect.collidepoint(event.pos):
                if self._file_menu_open:
                    self._close_file_menu()
                else:
                    self._open_file_menu()
                return
            if self._file_menu_open:
                if self._file_menu_rect.collidepoint(event.pos):
                    index = self._file_menu_index_at(event.pos)
                    if index is not None:
                        self._file_menu_hover_index = index
                        self._activate_file_menu_selection()
                    return
                self._close_file_menu()
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
        if self.wires.handle_event(event, self.components):
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

    def _build_hotkey_bar_text_surfaces(self):
        """Render and cache per-hint text surfaces for the bottom bar."""
        hotkey_hints = (
            "CTRL+Z UNDO",
            "CTRL+Y REDO",
            "T TEXT",
            "F11 FULLSCREEN",
            "ESC QUIT",
        )
        font = Fonts.text_box
        if font is None:
            raise RuntimeError("Fonts.init() must run before hotkey bar text render")
        return [
            font.render(hint, True, ShortcutBarSettings.TEXT_COLOR)
            for hint in hotkey_hints
        ]

    def _draw_hotkey_bar(self):
        """Draw an old-school bottom status strip listing keyboard shortcuts."""
        bar_rect = pygame.Rect(
            0,
            ScreenSettings.HEIGHT - ShortcutBarSettings.HEIGHT,
            ScreenSettings.WIDTH,
            ShortcutBarSettings.HEIGHT,
        )
        pygame.draw.rect(self.screen, ShortcutBarSettings.BG_COLOR, bar_rect)
        pygame.draw.line(
            self.screen,
            ShortcutBarSettings.BORDER_COLOR,
            (0, bar_rect.top),
            (ScreenSettings.WIDTH, bar_rect.top),
            1,
        )
        hint_surfs = self._hotkey_hint_surfs
        if not hint_surfs:
            return

        # Space-evenly: equal gap before, between, and after each hint.
        total_width = sum(surf.get_width() for surf in hint_surfs)
        gap_count = len(hint_surfs) + 1
        gap = max(0.0, (ScreenSettings.WIDTH - total_width) / gap_count)
        x = gap
        for surf in hint_surfs:
            text_rect = surf.get_rect()
            text_rect.x = round(x)
            text_rect.centery = bar_rect.centery
            self.screen.blit(surf, text_rect)
            x += surf.get_width() + gap

    def _build_file_menu_item_surfaces(self):
        """Render and cache FILE menu item labels once at startup."""
        font = Fonts.text_box
        if font is None:
            raise RuntimeError("Fonts.init() must run before FILE menu text render")
        return [
            font.render(
                label,
                True,
                MenuButtonSettings.ITEM_ENABLED_COLOR
                if self._menu_actions.get(item_id) is not None
                else MenuButtonSettings.ITEM_DISABLED_COLOR,
            )
            for item_id, label in MenuButtonSettings.ITEMS
        ]

    def _rebuild_file_menu_geometry(self):
        """Build FILE button and popup item rects anchored to the top bar."""
        self._file_button_rect = pygame.Rect(
            0,
            0,
            self._file_label_surf.get_width() + TopMenuBarSettings.PADDING_X * 2,
            TopMenuBarSettings.HEIGHT,
        )
        self._file_menu_rect = pygame.Rect(
            self._file_button_rect.left,
            TopMenuBarSettings.HEIGHT,
            MenuButtonSettings.POPUP_WIDTH,
            MenuButtonSettings.POPUP_HEIGHT,
        )
        self._file_menu_item_rects = [
            pygame.Rect(
                self._file_menu_rect.left,
                self._file_menu_rect.top + index * MenuButtonSettings.ITEM_HEIGHT,
                self._file_menu_rect.width,
                MenuButtonSettings.ITEM_HEIGHT,
            )
            for index in range(len(MenuButtonSettings.ITEMS))
        ]

    def _open_file_menu(self):
        """Open FILE menu and seed selection to the first enabled item."""
        self._file_menu_open = True
        self._file_menu_hover_index = self._first_enabled_file_menu_index()

    def _close_file_menu(self):
        """Close FILE menu and return keyboard focus to the workspace."""
        self._file_menu_open = False

    @staticmethod
    def _file_menu_index_at_pos(item_rects, pos):
        """Return the popup-item index containing pos, else None."""
        for index, rect in enumerate(item_rects):
            if rect.collidepoint(pos):
                return index
        return None

    def _file_menu_index_at(self, pos):
        """Return the popup-item index at pos for the active FILE menu."""
        return self._file_menu_index_at_pos(self._file_menu_item_rects, pos)

    def _first_enabled_file_menu_index(self):
        """Return index of first menu item that has an action wired."""
        for index, (item_id, _label) in enumerate(MenuButtonSettings.ITEMS):
            if self._menu_actions.get(item_id) is not None:
                return index
        return 0

    def _move_file_menu_selection(self, step):
        """Move FILE menu selection by step over enabled items only."""
        enabled_indices = [
            index
            for index, (item_id, _label) in enumerate(MenuButtonSettings.ITEMS)
            if self._menu_actions.get(item_id) is not None
        ]
        if not enabled_indices:
            return
        if self._file_menu_hover_index not in enabled_indices:
            self._file_menu_hover_index = enabled_indices[0]
            return
        current = enabled_indices.index(self._file_menu_hover_index)
        self._file_menu_hover_index = enabled_indices[(current + step) % len(enabled_indices)]

    def _activate_file_menu_selection(self):
        """Run the currently highlighted FILE menu action and close menu."""
        if not MenuButtonSettings.ITEMS:
            self._close_file_menu()
            return
        item_id, _label = MenuButtonSettings.ITEMS[self._file_menu_hover_index]
        action = self._menu_actions.get(item_id)
        if action is None:
            return
        self._close_file_menu()
        action()

    def _sync_file_menu_hover_with_mouse(self, mouse_pos):
        """Mirror mouse hover into keyboard selection state while menu is open."""
        if not self._file_menu_open:
            return
        index = self._file_menu_index_at(mouse_pos)
        if index is None:
            return
        self._file_menu_hover_index = index

    def _draw_top_menu_bar(self):
        """Draw top FILE menu bar with highlighted FILE affordance."""
        bar_rect = pygame.Rect(0, 0, ScreenSettings.WIDTH, TopMenuBarSettings.HEIGHT)
        pygame.draw.rect(self.screen, TopMenuBarSettings.BG_COLOR, bar_rect)
        pygame.draw.line(
            self.screen,
            TopMenuBarSettings.BORDER_COLOR,
            (0, bar_rect.bottom - 1),
            (ScreenSettings.WIDTH, bar_rect.bottom - 1),
            1,
        )

        file_bg = TopMenuBarSettings.BG_COLOR
        mouse_over_file = self._file_button_rect.collidepoint(pygame.mouse.get_pos())
        if self._file_menu_open or mouse_over_file:
            file_bg = TopMenuBarSettings.FILE_HIGHLIGHT_BG
        pygame.draw.rect(self.screen, file_bg, self._file_button_rect)
        label_rect = self._file_label_surf.get_rect(center=self._file_button_rect.center)
        self.screen.blit(self._file_label_surf, label_rect)

        # Underline only the leading F to mimic a classic mnemonic affordance.
        text_font = Fonts.text_box
        if text_font is None:
            return
        f_width = text_font.size("F")[0]
        underline_y = (
            self._file_button_rect.bottom
            - TopMenuBarSettings.FILE_UNDERLINE_BOTTOM_INSET
        )
        underline_x0 = label_rect.x
        pygame.draw.line(
            self.screen,
            TopMenuBarSettings.TEXT_COLOR,
            (underline_x0, underline_y),
            (underline_x0 + f_width, underline_y),
            TopMenuBarSettings.FILE_UNDERLINE_THICKNESS,
        )

        if self._file_menu_open:
            self._draw_file_menu_popup()

    def _draw_file_menu_popup(self):
        """Draw FILE dropdown menu and shared hover/selection highlight."""
        pygame.draw.rect(self.screen, MenuButtonSettings.POPUP_BODY_COLOR, self._file_menu_rect)
        pygame.draw.rect(
            self.screen,
            MenuButtonSettings.POPUP_BORDER_COLOR,
            self._file_menu_rect,
            MenuButtonSettings.POPUP_BORDER_THICKNESS,
        )
        text_font = Fonts.text_box
        if text_font is None:
            return
        for index, (rect, surf) in enumerate(zip(self._file_menu_item_rects, self._file_menu_item_surfs)):
            if index == self._file_menu_hover_index:
                pygame.draw.rect(self.screen, COLOR_MENU_HIGHLIGHT, rect)
                _item_id, label = MenuButtonSettings.ITEMS[index]
                selected_surf = text_font.render(label, True, COLOR_MENU_HIGHLIGHT_TEXT)
                label_y = rect.y + (rect.height - selected_surf.get_height()) // 2
                self.screen.blit(
                    selected_surf,
                    (rect.left + MenuButtonSettings.ITEM_PADDING_X, label_y),
                )
                continue
            label_y = rect.y + (rect.height - surf.get_height()) // 2
            self.screen.blit(surf, (rect.left + MenuButtonSettings.ITEM_PADDING_X, label_y))

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
        self._draw_top_menu_bar()
        self.crt.draw()
        self._draw_hotkey_bar()
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

