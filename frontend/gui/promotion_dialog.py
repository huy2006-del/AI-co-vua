"""Modal choice among the four legal promotion pieces."""
import chess
import pygame

from .theme import EDGE, FIELD, INK, MUTED, PANEL


class PromotionDialog:
    choices = ((chess.QUEEN, "Hậu"), (chess.ROOK, "Xe"),
               (chess.BISHOP, "Tượng"), (chess.KNIGHT, "Mã"))

    def __init__(self, moves, center):
        self.moves = {move.promotion: move for move in moves}
        self.bounds = pygame.Rect(0, 0, 400, 142)
        self.bounds.center = center
        self.buttons = {
            piece: pygame.Rect(self.bounds.x + 12 + index * 96, self.bounds.y + 60, 88, 46)
            for index, (piece, _) in enumerate(self.choices)
        }

    def pick(self, point):
        for piece, button in self.buttons.items():
            if button.collidepoint(point):
                return self.moves.get(piece)
        return None

    def draw(self, surface, font):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((10, 18, 15, 155))
        surface.blit(overlay, (0, 0))
        pygame.draw.rect(surface, PANEL, self.bounds, border_radius=12)
        pygame.draw.rect(surface, EDGE, self.bounds, 2, border_radius=12)
        surface.blit(font.render("Chọn quân phong cấp", True, INK),
                     (self.bounds.x + 16, self.bounds.y + 16))
        for piece, name in self.choices:
            button = self.buttons[piece]
            pygame.draw.rect(surface, FIELD, button, border_radius=6)
            label = font.render(name, True, INK)
            surface.blit(label, label.get_rect(center=button.center))
        surface.blit(font.render("Esc để hủy", True, MUTED),
                     (self.bounds.x + 16, self.bounds.y + 111))
