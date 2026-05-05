"""Top menu bar handler for FILE/EDIT/VIEW menus.

Manages menu rendering, geometry, interaction state, and hover/selection tracking.
Decouples menu logic from GameManager to reduce its size and complexity.
"""

from typing import Callable, Dict, Optional, Tuple
import pygame
from fonts import Fonts
from settings import (
    TopMenuBarSettings,
    MenuButtonSettings,
    ScreenSettings,
    InputSettings,
    COLOR_MENU_HIGHLIGHT,
    COLOR_MENU_HIGHLIGHT_TEXT,
)


class TopMenuBar:
    """Handles top menu bar rendering and interaction.
    
    Manages the FILE/EDIT/VIEW menu system including geometry calculation,
    item surface rendering, hover/selection state, and all drawing operations.
    
    Args:
        screen: Pygame display surface to render to.
        menu_defs: Menu definitions with structure {menu_id: {label, items, actions}}
    """
    
    def __init__(self, screen: pygame.Surface, menu_defs: Dict) -> None:
        """Initialize the top menu bar.
        
        Args:
            screen: Pygame display surface to render to.
            menu_defs: Menu definitions dict with menu_id keys and dicts containing label, items, and actions.
        """
        self.screen = screen
        self.menu_defs = menu_defs
        self._top_menu_order: Tuple[str, ...] = ("file", "edit", "view")
        self._active_top_menu_id: Optional[str] = None
        self._top_menu_hover_index: int = 0
        
        # Cached surfaces for menu labels and items
        self._top_menu_label_surfs: Dict[str, pygame.Surface] = {}
        self._top_menu_label_surfs_highlight: Dict[str, pygame.Surface] = {}
        self._top_menu_item_surfs: Dict[str, list] = {}
        
        # Cached geometry for menu buttons and popup
        self._top_menu_button_rects: Dict[str, pygame.Rect] = {}
        self._top_menu_popup_rects: Dict[str, pygame.Rect] = {}
        self._top_menu_item_rects: Dict[str, list] = {}
        
        self._build_surfaces()
        self._rebuild_geometry()
    
    def _build_surfaces(self) -> None:
        """Render and cache per-item label/shortcut surfaces for top menus."""
        text_font = Fonts.text_box
        if text_font is None:
            raise RuntimeError("Fonts.init() must run before top menu text render")
        
        for menu_id in self._top_menu_order:
            # Cache menu label surfaces (normal and highlighted)
            self._top_menu_label_surfs[menu_id] = text_font.render(
                self.menu_defs[menu_id]["label"],
                True,
                TopMenuBarSettings.TEXT_COLOR,
            )
            self._top_menu_label_surfs_highlight[menu_id] = text_font.render(
                self.menu_defs[menu_id]["label"],
                True,
                COLOR_MENU_HIGHLIGHT_TEXT,
            )
            
            # Cache per-item label and shortcut surfaces
            actions = self.menu_defs[menu_id]["actions"]
            self._top_menu_item_surfs[menu_id] = [
                {
                    "label": text_font.render(
                        label,
                        True,
                        MenuButtonSettings.ITEM_ENABLED_COLOR
                        if actions.get(item_id) is not None
                        else MenuButtonSettings.ITEM_DISABLED_COLOR,
                    ),
                    "shortcut": (
                        text_font.render(
                            shortcut,
                            True,
                            TopMenuBarSettings.SHORTCUT_TEXT_COLOR,
                        )
                        if shortcut
                        else None
                    ),
                }
                for item_id, label, shortcut in self.menu_defs[menu_id]["items"]
            ]
    
    def _rebuild_geometry(self) -> None:
        """Build top-menu button and popup geometry for FILE/EDIT/VIEW."""
        x = 0
        for menu_id in self._top_menu_order:
            label_surf = self._top_menu_label_surfs[menu_id]
            button_rect = pygame.Rect(
                x,
                0,
                label_surf.get_width() + TopMenuBarSettings.PADDING_X * 2,
                TopMenuBarSettings.HEIGHT,
            )
            self._top_menu_button_rects[menu_id] = button_rect
            items = self.menu_defs[menu_id]["items"]
            popup_rect = pygame.Rect(
                button_rect.left,
                TopMenuBarSettings.HEIGHT,
                MenuButtonSettings.POPUP_WIDTH,
                len(items) * MenuButtonSettings.ITEM_HEIGHT,
            )
            self._top_menu_popup_rects[menu_id] = popup_rect
            self._top_menu_item_rects[menu_id] = [
                pygame.Rect(
                    popup_rect.left,
                    popup_rect.top + index * MenuButtonSettings.ITEM_HEIGHT,
                    popup_rect.width,
                    MenuButtonSettings.ITEM_HEIGHT,
                )
                for index in range(len(items))
            ]
            x = button_rect.right + TopMenuBarSettings.MENU_GAP_X
    
    def toggle_menu(self, menu_id: str) -> None:
        """Toggle a top menu, switching menus when a different one is clicked.
        
        Args:
            menu_id: The menu identifier to toggle.
        """
        if self._active_top_menu_id == menu_id:
            self.close_menu()
            return
        self._active_top_menu_id = menu_id
        self._top_menu_hover_index = self._first_enabled_menu_index(menu_id)
    
    def close_menu(self) -> None:
        """Close active top menu and return focus to workspace."""
        self._active_top_menu_id = None
    
    def is_menu_open(self) -> bool:
        """Return True if any menu is currently open."""
        return self._active_top_menu_id is not None
    
    def get_active_menu_id(self) -> Optional[str]:
        """Return the currently open menu id, or None."""
        return self._active_top_menu_id
    
    def menu_id_at_pos(self, pos: Tuple[int, int]) -> Optional[str]:
        """Return the menu id whose button contains pos, else None.
        
        Args:
            pos: Screen position as (x, y) tuple.
        """
        for menu_id, rect in self._top_menu_button_rects.items():
            if rect.collidepoint(pos):
                return menu_id
        return None
    
    def menu_item_index_at_pos(self, pos: Tuple[int, int]) -> Optional[int]:
        """Return popup-item index at pos for active menu, else None.
        
        Args:
            pos: Screen position as (x, y) tuple.
        """
        if self._active_top_menu_id is None:
            return None
        for index, rect in enumerate(self._top_menu_item_rects[self._active_top_menu_id]):
            if rect.collidepoint(pos):
                return index
        return None
    
    def move_selection(self, step: int) -> None:
        """Move active menu selection by step over enabled items only.
        
        Args:
            step: Direction and distance to move (-1 or 1).
        """
        if self._active_top_menu_id is None:
            return
        menu_items = self.menu_defs[self._active_top_menu_id]["items"]
        menu_actions = self.menu_defs[self._active_top_menu_id]["actions"]
        enabled_indices = [
            index
            for index, (item_id, _label, _shortcut) in enumerate(menu_items)
            if menu_actions.get(item_id) is not None
        ]
        if not enabled_indices:
            return
        if self._top_menu_hover_index not in enabled_indices:
            self._top_menu_hover_index = enabled_indices[0]
            return
        current = enabled_indices.index(self._top_menu_hover_index)
        self._top_menu_hover_index = enabled_indices[(current + step) % len(enabled_indices)]
    
    def sync_hover_with_mouse(self, mouse_pos: Tuple[int, int]) -> None:
        """Mirror mouse hover into keyboard selection state for active menu.
        
        Args:
            mouse_pos: Current mouse position as (x, y) tuple.
        """
        if self._active_top_menu_id is None:
            return
        index = self.menu_item_index_at_pos(mouse_pos)
        if index is None:
            return
        self._top_menu_hover_index = index
    
    def activate_selection(self) -> Optional[Callable]:
        """Run currently highlighted menu action and close menu.
        
        Returns the action callable to invoke, or None if no action.
        """
        if self._active_top_menu_id is None:
            return None
        menu_items = self.menu_defs[self._active_top_menu_id]["items"]
        if not menu_items:
            self.close_menu()
            return None
        item_id, _label, _shortcut = menu_items[self._top_menu_hover_index]
        action = self.menu_defs[self._active_top_menu_id]["actions"].get(item_id)
        if action is None:
            return None
        self.close_menu()
        return action
    
    def _first_enabled_menu_index(self, menu_id: str) -> int:
        """Return index of first menu item with a wired action.
        
        Args:
            menu_id: The menu identifier.
        """
        menu_items = self.menu_defs[menu_id]["items"]
        menu_actions = self.menu_defs[menu_id]["actions"]
        for index, (item_id, _label, _shortcut) in enumerate(menu_items):
            if menu_actions.get(item_id) is not None:
                return index
        return 0
    
    def draw(self) -> None:
        """Draw top FILE/EDIT/VIEW menu bar with highlighted active affordance."""
        bar_rect = pygame.Rect(0, 0, ScreenSettings.WIDTH, TopMenuBarSettings.HEIGHT)
        pygame.draw.rect(self.screen, TopMenuBarSettings.BG_COLOR, bar_rect)
        pygame.draw.line(
            self.screen,
            TopMenuBarSettings.BORDER_COLOR,
            (0, bar_rect.bottom - 1),
            (ScreenSettings.WIDTH, bar_rect.bottom - 1),
            1,
        )
        
        text_font = Fonts.text_box
        if text_font is None:
            return
        mouse_pos = pygame.mouse.get_pos()
        for menu_id in self._top_menu_order:
            rect = self._top_menu_button_rects[menu_id]
            is_highlighted = (
                self._active_top_menu_id == menu_id
                or rect.collidepoint(mouse_pos)
            )
            button_bg = (
                TopMenuBarSettings.FILE_HIGHLIGHT_BG
                if is_highlighted
                else TopMenuBarSettings.BG_COLOR
            )
            pygame.draw.rect(self.screen, button_bg, rect)
            label_surf = (
                self._top_menu_label_surfs_highlight[menu_id]
                if is_highlighted
                else self._top_menu_label_surfs[menu_id]
            )
            label_rect = label_surf.get_rect(center=rect.center)
            self.screen.blit(label_surf, label_rect)
            
            # Underline each menu's mnemonic letter (first character).
            label_text = self.menu_defs[menu_id]["label"]
            if label_text:
                mnemonic_width = text_font.size(label_text[0])[0]
                underline_y = (
                    rect.bottom - TopMenuBarSettings.FILE_UNDERLINE_BOTTOM_INSET
                )
                underline_x0 = label_rect.x
                underline_color = (
                    COLOR_MENU_HIGHLIGHT_TEXT
                    if is_highlighted
                    else TopMenuBarSettings.TEXT_COLOR
                )
                pygame.draw.line(
                    self.screen,
                    underline_color,
                    (underline_x0, underline_y),
                    (underline_x0 + mnemonic_width, underline_y),
                    TopMenuBarSettings.FILE_UNDERLINE_THICKNESS,
                )
        
        if self._active_top_menu_id is not None:
            self._draw_popup()
    
    def _draw_popup(self) -> None:
        """Draw active top-menu dropdown and shared hover/selection highlight."""
        if self._active_top_menu_id is None:
            return
        popup_rect = self._top_menu_popup_rects[self._active_top_menu_id]
        pygame.draw.rect(self.screen, MenuButtonSettings.POPUP_BODY_COLOR, popup_rect)
        pygame.draw.rect(
            self.screen,
            MenuButtonSettings.POPUP_BORDER_COLOR,
            popup_rect,
            MenuButtonSettings.POPUP_BORDER_THICKNESS,
        )
        text_font = Fonts.text_box
        if text_font is None:
            return
        menu_items = self.menu_defs[self._active_top_menu_id]["items"]
        item_surfs = self._top_menu_item_surfs[self._active_top_menu_id]
        popup_right = popup_rect.right - MenuButtonSettings.ITEM_PADDING_X
        for index, (rect, surf_set) in enumerate(zip(self._top_menu_item_rects[self._active_top_menu_id], item_surfs)):
            label_surf = surf_set["label"]
            shortcut_surf = surf_set["shortcut"]
            if index == self._top_menu_hover_index:
                pygame.draw.rect(self.screen, COLOR_MENU_HIGHLIGHT, rect)
                _item_id, label, shortcut = menu_items[index]
                selected_surf = text_font.render(label, True, COLOR_MENU_HIGHLIGHT_TEXT)
                label_y = rect.y + (rect.height - selected_surf.get_height()) // 2
                self.screen.blit(
                    selected_surf,
                    (rect.left + MenuButtonSettings.ITEM_PADDING_X, label_y),
                )
                if shortcut:
                    selected_shortcut_surf = text_font.render(
                        shortcut,
                        True,
                        TopMenuBarSettings.SHORTCUT_HIGHLIGHT_TEXT_COLOR,
                    )
                    shortcut_rect = selected_shortcut_surf.get_rect()
                    shortcut_rect.right = popup_right
                    shortcut_rect.centery = rect.centery
                    self.screen.blit(selected_shortcut_surf, shortcut_rect)
                continue
            label_y = rect.y + (rect.height - label_surf.get_height()) // 2
            self.screen.blit(
                label_surf,
                (rect.left + MenuButtonSettings.ITEM_PADDING_X, label_y),
            )
            if shortcut_surf is not None:
                shortcut_rect = shortcut_surf.get_rect()
                shortcut_rect.right = popup_right
                shortcut_rect.centery = rect.centery
                self.screen.blit(shortcut_surf, shortcut_rect)
