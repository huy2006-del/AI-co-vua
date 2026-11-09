"""Draw scalable toolbar icons without relying on system glyphs."""
from math import pi

import pygame

from .theme import INK


def draw_icon(surface, kind, center):
    x, y = center
    def lines(points):
        pygame.draw.lines(surface, INK, False, [(x+dx,y+dy) for dx,dy in points], 3)
    if kind == "menu":
        for dy in (-10, 0, 10):
            lines([(-15,dy),(15,dy)])
    elif kind in ("reset", "undo"):
        pygame.draw.arc(surface, INK, (x-14, y-13, 29, 27), -.45, pi*1.10, 3)
        lines([(-16,-10),(-16,-2),(-7,-2)])
        if kind == "reset":
            pygame.draw.circle(surface, INK, center, 3)
    elif kind == "flip":
        lines([(-14,-5),(13,-5),(7,-11)])
        lines([(14,5),(-13,5),(-7,11)])
    elif kind == "history":
        pygame.draw.rect(surface, INK, (x-11,y-14,22,28), 2, border_radius=3)
        for dy in (-6, 0, 6):
            lines([(-6,dy),(6,dy)])
    elif kind == "hint":
        pygame.draw.arc(surface, INK, (x-11,y-15,22,22), -.60, pi+ .60, 3)
        lines([(-8,2),(-4,8),(4,8),(8,2)])
        lines([(-4,12),(4,12)])
