import pygame

from elements import Component, LED, Switch
from settings import InputSettings, ScreenSettings, UISettings


class ComponentBank:
    """The toolbox at the bottom of the screen — templates students drag onto the workspace.

    Holds one template per spawnable Component subclass. Clicking a template
    spawns a fresh instance of the same class at the cursor and starts the
    drag immediately, so it follows the mouse into the workspace.
    """

    # Order is the left-to-right order shown in the toolbox.
    TEMPLATE_CLASSES = (Switch, Component, LED)

    def __init__(self):
        """Build the bank rect and the row of template components."""
        self.rect = UISettings.BANK_RECT
        self.templates = self._build_templates()

    def _build_templates(self):
        """Lay out one template per spawnable class, left-to-right inside the bank.

        Each template is vertically centered inside the bank regardless of
        its own height, so a future smaller / larger component still looks
        intentional. Spacing comes from UISettings so the layout has no
        magic numbers.

        Returns:
            list[Component]: The instantiated templates in display order.
        """
        x = UISettings.BANK_PADDING_X
        templates = []
        for cls in self.TEMPLATE_CLASSES:
            # Instantiate at a placeholder y, then vertically center based
            # on the component's actual height (which the class decides).
            tpl = cls(x, 0)
            tpl.rect.y = self.rect.y + (self.rect.height - tpl.rect.height) // 2
            templates.append(tpl)
            x += tpl.rect.width + UISettings.BANK_TEMPLATE_GAP
        return templates

    def draw(self, surface):
        """Render the bank background, separator line, and every template.

        Args:
            surface (pygame.Surface): The surface to draw onto.
        """
        pygame.draw.rect(surface, UISettings.BANK_COLOR, self.rect)
        pygame.draw.line(
            surface,
            UISettings.BANK_LINE_COLOR,
            (0, self.rect.y),
            (ScreenSettings.WIDTH, self.rect.y),
            2,
        )
        for tpl in self.templates:
            tpl.draw(surface)

    def handle_event(self, event, components_list):
        """Spawn a new component when the user left-clicks a template.

        The new component is the same runtime class as the clicked template
        (so a click on the Switch template spawns a Switch, etc.). It's
        dropped into the workspace centered on the cursor with dragging
        already on, so the next MOUSEMOTION carries it where the user is
        going.

        Args:
            event (pygame.event.Event): The event to inspect.
            components_list (list[Component]): The workspace's component list
                to append the spawned component into.

        Returns:
            bool: True if a template was clicked and the event was handled.
        """
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != InputSettings.LEFT_CLICK:
            return False
        for tpl in self.templates:
            if tpl.rect.collidepoint(event.pos):
                new_comp = type(tpl)(
                    event.pos[0] - tpl.rect.width // 2,
                    event.pos[1] - tpl.rect.height // 2,
                )
                new_comp.dragging = True
                # Match Component.handle_event's grip math so the spawned
                # component tracks the cursor cleanly on the next MOUSEMOTION.
                new_comp.offset_x = new_comp.rect.x - event.pos[0]
                new_comp.offset_y = new_comp.rect.y - event.pos[1]
                # The spawn drag was started by the bank, not by the
                # component's own MOUSEBUTTONDOWN, so suppress the click
                # hook on the upcoming release. Otherwise a Switch spawned
                # via a stationary click would toggle on the way out of
                # the bank.
                new_comp._moved_while_dragging = True
                components_list.append(new_comp)
                return True
        return False
