"""Shared controls and lettering for the wood theme."""
import pygame

INK = "#f4e0bd"
MUTED = "#c1a990"
GOLD = "#eab46d"
EDGE = "#795238"
PANEL = "#281b15"
FIELD = "#3a291e"
SIZE = (1100, 720)


def text(surface, font, value, position, color=INK):
    surface.blit(font.render(str(value), True, color), position)


def button(surface, font, rect, label, *, selected=False):
    pygame.draw.rect(surface, "#78482a" if selected else FIELD, rect, border_radius=9)
    pygame.draw.rect(surface, GOLD if selected else EDGE, rect, 1, border_radius=9)
    image = font.render(label, True, INK)
    surface.blit(image, image.get_rect(center=rect.center))


def panel(surface, rect):
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((12, 7, 4, 178))
    surface.blit(shade, (0, 0))
    pygame.draw.rect(surface, PANEL, rect, border_radius=20)
    pygame.draw.rect(surface, EDGE, rect, 2, border_radius=20)
