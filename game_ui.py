from typing import Callable

import pygame
from consts import font2

def draw_rect_alpha(surface: pygame.Surface, color: tuple[int, int, int, int], rect: pygame.Rect) -> None:
    # sourced from https://stackoverflow.com/questions/6339057/draw-a-transparent-rectangles-and-polygons-in-pygame
    # draws a translucent rectangle on the screen
    shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
    surface.blit(shape_surf, rect)

class UIBar:
    text: str
    colour: tuple[int, int, int]
    get_percent: Callable[..., int | float]

    def __init__(self, text: str, color: tuple[int, int, int], get_percent: Callable[..., int | float]):
        self.text = text
        self.colour = color
        self.get_percent = get_percent

    def render(self, screen: pygame.Surface, position: pygame.Vector2) -> None:

        percent = self.get_percent()
        element_bar = pygame.Rect(position.x, position.y, 200 * percent, 20)

        element_text = font2.render(self.text, True, (0, 0, 0))
        element_text_rect = element_text.get_rect(left=20, top=element_bar.bottom + 5)

        pygame.draw.rect(screen, self.colour, element_bar)
        screen.blit(element_text, element_text_rect)
        return None