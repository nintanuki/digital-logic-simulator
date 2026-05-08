"""Diagram viewer scene for HELP > DIAGRAMS."""

from __future__ import annotations

import os

import pygame

from settings import (
    AssetPaths,
    BankPopupButtonSettings,
    DiagramViewerSettings,
    ScreenSettings,
    TopMenuBarSettings,
)
from ui.fonts import Fonts


class DiagramViewerScene:
    """Render and handle interaction for the diagram reference scene.

    Args:
        screen: Main pygame surface used by the game.
    """

    def __init__(self, screen: pygame.Surface, on_return=None) -> None:
        """Initialize scene state and load diagram images."""
        self.screen = screen
        self.on_return = on_return
        self._selected_index = 0
        self._hover_index = -1
        self._return_hovered = False
        self._entries = DiagramViewerSettings.DIAGRAM_ENTRIES
        self._images = self._load_images()

    def _load_images(self) -> list[pygame.Surface | None]:
        """Load each configured diagram image from disk.

        Returns:
            List aligned with DIAGRAM_ENTRIES, with None for missing files.
        """
        diagrams_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            AssetPaths.DIAGRAMS_DIR,
        )
        images: list[pygame.Surface | None] = []
        for entry in self._entries:
            image_path = os.path.normpath(
                os.path.join(diagrams_dir, entry["image_file"])
            )
            if not os.path.exists(image_path):
                images.append(None)
                continue
            images.append(pygame.image.load(image_path).convert_alpha())
        return images

    @property
    def selected_entry(self) -> dict:
        """Return metadata for the currently selected diagram."""
        return self._entries[self._selected_index]

    def move_selection(self, step: int) -> None:
        """Move list selection by one or more rows.

        Args:
            step: Signed selection delta.
        """
        if not self._entries:
            return
        self._selected_index = (self._selected_index + step) % len(self._entries)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle diagram-scene local input.

        Args:
            event: Pygame input event.

        Returns:
            True if the scene consumed the event.
        """
        if event.type == pygame.MOUSEMOTION:
            self._hover_index = self._list_index_at(event.pos)
            self._return_hovered = self._return_button_rect().collidepoint(event.pos)
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._return_button_rect().collidepoint(event.pos):
                if self.on_return is not None:
                    self.on_return()
                return True
            clicked_index = self._list_index_at(event.pos)
            if clicked_index is not None:
                self._selected_index = clicked_index
            return True

        return False

    def _content_rect(self) -> pygame.Rect:
        """Return the full scene content rectangle below the top menu."""
        top = TopMenuBarSettings.HEIGHT + DiagramViewerSettings.CONTENT_TOP_GAP
        bottom = self._return_button_rect().top - DiagramViewerSettings.CONTENT_GAP
        return pygame.Rect(
            DiagramViewerSettings.CONTENT_PADDING,
            top,
            ScreenSettings.WIDTH - DiagramViewerSettings.CONTENT_PADDING * 2,
            bottom - top,
        )

    def _return_button_rect(self) -> pygame.Rect:
        """Return bottom-left RETURN button rectangle."""
        left_x = DiagramViewerSettings.CONTENT_PADDING
        if DiagramViewerSettings.RETURN_CENTER_WITH_LIST:
            left_x += (
                DiagramViewerSettings.LIST_PANEL_WIDTH
                - DiagramViewerSettings.RETURN_BUTTON_WIDTH
            ) // 2
        left_x += DiagramViewerSettings.RETURN_X_OFFSET
        return pygame.Rect(
            left_x,
            ScreenSettings.HEIGHT
            - DiagramViewerSettings.OUTER_MARGIN_BOTTOM
            - DiagramViewerSettings.RETURN_BUTTON_HEIGHT,
            DiagramViewerSettings.RETURN_BUTTON_WIDTH,
            DiagramViewerSettings.RETURN_BUTTON_HEIGHT,
        )

    def _list_rect(self, content_rect: pygame.Rect) -> pygame.Rect:
        """Return left-column list panel rectangle.

        Args:
            content_rect: Main scene content rectangle.

        Returns:
            Left list panel rectangle.
        """
        return pygame.Rect(
            content_rect.left,
            content_rect.top,
            DiagramViewerSettings.LIST_PANEL_WIDTH,
            content_rect.height,
        )

    def _right_rect(self, content_rect: pygame.Rect, list_rect: pygame.Rect) -> pygame.Rect:
        """Return right-side details panel rectangle."""
        return pygame.Rect(
            list_rect.right + DiagramViewerSettings.CONTENT_GAP,
            content_rect.top,
            content_rect.right - list_rect.right - DiagramViewerSettings.CONTENT_GAP,
            content_rect.height,
        )

    def _list_index_at(self, pos: tuple[int, int]) -> int | None:
        """Map a cursor position to a list row index.

        Args:
            pos: Cursor position in screen coordinates.

        Returns:
            Zero-based row index, or None when not over an item.
        """
        content_rect = self._content_rect()
        list_rect = self._list_rect(content_rect)
        if not list_rect.collidepoint(pos):
            return None

        y = list_rect.top + DiagramViewerSettings.CONTENT_PADDING
        for index in range(len(self._entries)):
            item_rect = pygame.Rect(
                list_rect.left + DiagramViewerSettings.CONTENT_PADDING,
                y,
                list_rect.width - DiagramViewerSettings.CONTENT_PADDING * 2,
                DiagramViewerSettings.LIST_ITEM_HEIGHT,
            )
            if item_rect.collidepoint(pos):
                return index
            y += (
                DiagramViewerSettings.LIST_ITEM_HEIGHT
                + DiagramViewerSettings.LIST_ITEM_GAP
            )
        return None

    def _wrap_text(self, text: str | tuple | list, max_width: int, font: pygame.font.Font) -> list[str]:
        """Wrap text to lines that fit within a pixel width.

        Args:
            text: Input text with optional newlines.
            max_width: Max rendered line width in pixels.
            font: Font used to measure text width.

        Returns:
            List of wrapped lines.
        """
        if isinstance(text, (tuple, list)):
            text = " ".join(str(part) for part in text)
        else:
            text = str(text)

        wrapped_lines: list[str] = []
        paragraphs = text.split("\n")
        for paragraph in paragraphs:
            words = paragraph.split(" ")
            if not words or paragraph == "":
                wrapped_lines.append("")
                continue
            current = words[0]
            for word in words[1:]:
                candidate = f"{current} {word}"
                if font.size(candidate)[0] <= max_width:
                    current = candidate
                else:
                    wrapped_lines.append(current)
                    current = word
            wrapped_lines.append(current)
        return wrapped_lines

    def draw(self) -> None:
        """Draw list panel and selected diagram content."""
        self.screen.fill(DiagramViewerSettings.BG_COLOR)

        text_font = Fonts.text_box
        title_font = Fonts.component_label
        if text_font is None or title_font is None:
            return

        content_rect = self._content_rect()
        list_rect = self._list_rect(content_rect)
        right_rect = self._right_rect(content_rect, list_rect)

        if DiagramViewerSettings.CONTENT_TOP_GAP > 0:
            top_gap_rect = pygame.Rect(
                0,
                TopMenuBarSettings.HEIGHT,
                ScreenSettings.WIDTH,
                DiagramViewerSettings.CONTENT_TOP_GAP,
            )
            pygame.draw.rect(self.screen, DiagramViewerSettings.BG_COLOR, top_gap_rect)

        image_height = int(right_rect.height * DiagramViewerSettings.IMAGE_SECTION_RATIO)
        image_section_rect = pygame.Rect(
            right_rect.left,
            right_rect.top,
            right_rect.width,
            image_height,
        )
        description_rect = pygame.Rect(
            right_rect.left,
            image_section_rect.bottom + DiagramViewerSettings.CONTENT_GAP,
            right_rect.width,
            right_rect.bottom - image_section_rect.bottom - DiagramViewerSettings.CONTENT_GAP,
        )

        pygame.draw.rect(self.screen, DiagramViewerSettings.PANEL_BG_COLOR, list_rect)
        pygame.draw.rect(
            self.screen,
            DiagramViewerSettings.PANEL_BORDER_COLOR,
            list_rect,
            DiagramViewerSettings.PANEL_BORDER_THICKNESS,
        )

        pygame.draw.rect(self.screen, DiagramViewerSettings.PANEL_BG_COLOR, image_section_rect)
        pygame.draw.rect(
            self.screen,
            DiagramViewerSettings.PANEL_BORDER_COLOR,
            image_section_rect,
            DiagramViewerSettings.PANEL_BORDER_THICKNESS,
        )

        pygame.draw.rect(self.screen, DiagramViewerSettings.PANEL_BG_COLOR, description_rect)
        pygame.draw.rect(
            self.screen,
            DiagramViewerSettings.PANEL_BORDER_COLOR,
            description_rect,
            DiagramViewerSettings.PANEL_BORDER_THICKNESS,
        )

        y = list_rect.top + DiagramViewerSettings.CONTENT_PADDING
        for index, entry in enumerate(self._entries):
            item_rect = pygame.Rect(
                list_rect.left + DiagramViewerSettings.CONTENT_PADDING,
                y,
                list_rect.width - DiagramViewerSettings.CONTENT_PADDING * 2,
                DiagramViewerSettings.LIST_ITEM_HEIGHT,
            )
            if index == self._selected_index:
                bg_color = DiagramViewerSettings.LIST_ITEM_SELECTED_BG
            elif index == self._hover_index:
                bg_color = DiagramViewerSettings.LIST_ITEM_HOVER_BG
            else:
                bg_color = DiagramViewerSettings.LIST_ITEM_BG
            pygame.draw.rect(self.screen, bg_color, item_rect)
            pygame.draw.rect(
                self.screen,
                DiagramViewerSettings.PANEL_BORDER_COLOR,
                item_rect,
                1,
            )
            label_surface = text_font.render(
                entry["list_label"],
                True,
                DiagramViewerSettings.LIST_ITEM_TEXT_COLOR,
            )
            self.screen.blit(
                label_surface,
                (
                    item_rect.centerx - label_surface.get_width() // 2,
                    item_rect.centery - label_surface.get_height() // 2,
                ),
            )
            y += DiagramViewerSettings.LIST_ITEM_HEIGHT + DiagramViewerSettings.LIST_ITEM_GAP

        selected = self.selected_entry
        title_surface = title_font.render(
            selected["title"],
            True,
            DiagramViewerSettings.IMAGE_TITLE_COLOR,
        )
        title_pos = (
            image_section_rect.left + DiagramViewerSettings.IMAGE_PADDING,
            image_section_rect.top + DiagramViewerSettings.IMAGE_PADDING,
        )
        self.screen.blit(title_surface, title_pos)

        image_area_rect = pygame.Rect(
            image_section_rect.left + DiagramViewerSettings.IMAGE_PADDING,
            title_pos[1] + title_surface.get_height() + DiagramViewerSettings.IMAGE_PADDING,
            image_section_rect.width - DiagramViewerSettings.IMAGE_PADDING * 2,
            image_section_rect.height
            - title_surface.get_height()
            - DiagramViewerSettings.IMAGE_PADDING * 3,
        )
        pygame.draw.rect(self.screen, DiagramViewerSettings.IMAGE_BG_COLOR, image_area_rect)
        pygame.draw.rect(
            self.screen,
            DiagramViewerSettings.PANEL_BORDER_COLOR,
            image_area_rect,
            1,
        )

        image_surface = self._images[self._selected_index]
        if image_surface is not None:
            fitted = pygame.transform.smoothscale(
                image_surface,
                self._fit_size(image_surface.get_size(), image_area_rect.size),
            )
            fitted_rect = fitted.get_rect(center=image_area_rect.center)
            self.screen.blit(fitted, fitted_rect)
        else:
            missing_surface = text_font.render("IMAGE NOT FOUND", True, (220, 140, 140))
            self.screen.blit(
                missing_surface,
                (
                    image_area_rect.centerx - missing_surface.get_width() // 2,
                    image_area_rect.centery - missing_surface.get_height() // 2,
                ),
            )

        lines = self._wrap_text(
            selected["description"],
            description_rect.width - DiagramViewerSettings.IMAGE_PADDING * 2,
            text_font,
        )
        y = description_rect.top + DiagramViewerSettings.IMAGE_PADDING
        for line in lines:
            line_surface = text_font.render(
                line,
                True,
                DiagramViewerSettings.DESCRIPTION_TEXT_COLOR,
            )
            self.screen.blit(
                line_surface,
                (description_rect.left + DiagramViewerSettings.IMAGE_PADDING, y),
            )
            y += line_surface.get_height() + DiagramViewerSettings.DESCRIPTION_LINE_GAP
            if y > description_rect.bottom - DiagramViewerSettings.IMAGE_PADDING:
                break

        return_rect = self._return_button_rect()
        return_bg = (
            BankPopupButtonSettings.BODY_HOVER_COLOR
            if self._return_hovered
            else BankPopupButtonSettings.BODY_COLOR
        )
        pygame.draw.rect(
            self.screen,
            return_bg,
            return_rect,
            border_radius=BankPopupButtonSettings.BORDER_RADIUS,
        )
        pygame.draw.rect(
            self.screen,
            BankPopupButtonSettings.BORDER_COLOR,
            return_rect,
            BankPopupButtonSettings.BORDER_THICKNESS,
            border_radius=BankPopupButtonSettings.BORDER_RADIUS,
        )
        return_label = text_font.render(
            DiagramViewerSettings.RETURN_LABEL,
            True,
            BankPopupButtonSettings.LABEL_COLOR,
        )
        self.screen.blit(
            return_label,
            (
                return_rect.centerx - return_label.get_width() // 2,
                return_rect.centery - return_label.get_height() // 2,
            ),
        )

    def _fit_size(
        self,
        image_size: tuple[int, int],
        container_size: tuple[int, int],
    ) -> tuple[int, int]:
        """Scale an image size to fit inside a container while preserving aspect.

        Args:
            image_size: Source image (width, height).
            container_size: Destination bounds (width, height).

        Returns:
            Best-fit size (width, height) preserving source aspect ratio.
        """
        image_width, image_height = image_size
        max_width, max_height = container_size
        if image_width == 0 or image_height == 0:
            return max_width, max_height

        ratio = min(max_width / image_width, max_height / image_height)
        return max(1, int(image_width * ratio)), max(1, int(image_height * ratio))
