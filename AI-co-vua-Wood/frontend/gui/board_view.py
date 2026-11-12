"""Perspective board with depth-sorted, shaded chess pieces."""
from pathlib import Path

import chess
import pygame

ASSETS = Path(__file__).with_name("assets")
BORDER = 24 / 848
PLAYABLE = 800 / 848
PERSPECTIVE = 1 - 560 / 832


class BoardView:
    def __init__(self, font, flipped=False):
        self.font = font
        self.flipped = flipped
        self.selected = None
        self.hint = None
        self.background = pygame.image.load(ASSETS / "table.jpg").convert()
        self.pieces = {
            p.symbol(): pygame.image.load(ASSETS / (
                ("w" if p.color else "b") + p.symbol().lower() + ".png")).convert_alpha()
            for p in (chess.Piece(kind, color) for kind in chess.PIECE_TYPES
                      for color in chess.COLORS)
        }
        self.scaled = {}
        self.shadows = {}

    @staticmethod
    def project(column, row):
        u, v = BORDER + column * PLAYABLE / 8, BORDER + row * PLAYABLE / 8
        divisor = 1 - PERSPECTIVE * v
        return (round(550 + (u - .5) * 560 / divisor),
                round(104 + 540 * (1 - PERSPECTIVE) * v / divisor))

    def _coordinates(self, square):
        file, rank = chess.square_file(square), chess.square_rank(square)
        return (7 - file, rank) if self.flipped else (file, 7 - rank)

    def square_at(self, point, board=None):
        x, y = point
        dy = (y - 104) / 540
        v = dy / (1 - PERSPECTIVE + PERSPECTIVE * dy)
        u = .5 + (x - 550) * (1 - PERSPECTIVE * v) / 560
        column = int((u - BORDER) * 8 / PLAYABLE)
        row = int((v - BORDER) * 8 / PLAYABLE)
        square = None
        if BORDER <= u < 1 - BORDER and BORDER <= v < 1 - BORDER:
            square = (chess.square(7 - column, row) if self.flipped
                      else chess.square(column, 7 - row))
        if board is None or (square is not None and board.piece_at(square)):
            return square
        occupied = sorted(board.piece_map().items(),
                          key=lambda item: self._coordinates(item[0])[1], reverse=True)
        for piece_square, piece in occupied:
            c, r = self._coordinates(piece_square)
            image, rect = self._sprite(piece, c, r)
            if rect.collidepoint(point) and image.get_at(
                    (point[0] - rect.x, point[1] - rect.y)).a >= 128:
                return piece_square
        return square

    def draw(self, surface, controller):
        surface.blit(self.background, (0, 0))
        board = controller.board
        previous = board.peek() if board.move_stack else None
        highlights = {s: (218, 162, 53, 130)
                      for s in (previous.from_square, previous.to_square)} if previous else {}
        if self.selected is not None:
            highlights[self.selected] = (56, 165, 123, 140)
        if board.is_check():
            highlights[board.king(board.turn)] = (209, 52, 47, 170)
        tint = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for square, color in highlights.items():
            c, r = self._coordinates(square)
            pygame.draw.polygon(tint, color, [self.project(c, r), self.project(c+1, r),
                                              self.project(c+1, r+1), self.project(c, r+1)])
        targets = {move.to_square for move in controller.legal_moves(self.selected)}
        for square in targets:
            c, r = self._coordinates(square)
            x, y = self.project(c+.5, r+.5)
            occupied = board.piece_at(square)
            radius = round(18 + r) if occupied else 7
            pygame.draw.ellipse(tint, (112, 239, 181, 225),
                                (x-radius, y-radius*.60, radius*2, radius*1.2),
                                3 if occupied else 0)
        surface.blit(tint, (0, 0))
        for r in range(8):
            rank = r + 1 if self.flipped else 8 - r
            self._label(surface, str(rank), self.project(-.12, r+.5))
            for c in range(8):
                square = (chess.square(7-c, r) if self.flipped else chess.square(c, 7-r))
                piece = board.piece_at(square)
                if piece:
                    self._piece(surface, piece, c, r)
        for c in range(8):
            self._label(surface, chess.FILE_NAMES[7-c if self.flipped else c].upper(),
                        self.project(c+.5, 8.13))
        if self.hint:
            start = self.project(*[n+.5 for n in self._coordinates(self.hint.from_square)])
            end = self.project(*[n+.5 for n in self._coordinates(self.hint.to_square)])
            direction = pygame.Vector2(end) - start
            tip = pygame.Vector2(end)
            normal = direction.normalize()
            tail = tip - normal * 23
            wing = normal.rotate(90) * 9
            pygame.draw.line(surface, "#f9da83", start, tail, 5)
            pygame.draw.polygon(surface, "#f9da83", [tip, tail+wing, tail-wing])

    def _label(self, surface, name, point):
        text = self.font.render(name, True, "#352011")
        surface.blit(text, text.get_rect(center=point))

    def _piece(self, surface, piece, column, row):
        image, rect = self._sprite(piece, column, row)
        width = image.get_width()
        x, y = self.project(column + .5, row + .65)
        if row not in self.shadows:
            shadow = pygame.Surface((width, width//2), pygame.SRCALPHA)
            for inset, alpha in ((0, 45), (4, 76), (8, 108)):
                pygame.draw.ellipse(shadow, (13, 7, 4, alpha),
                                    shadow.get_rect().inflate(-inset, -inset//2))
            self.shadows[row] = shadow
        shadow = self.shadows[row]
        surface.blit(shadow, shadow.get_rect(center=(x+3, y+2)))
        surface.blit(image, rect)

    def _sprite(self, piece, column, row):
        symbol = piece.symbol()
        width = 59 + row * 3
        x, y = self.project(column + .5, row + .65)
        key = symbol, row
        if key not in self.scaled:
            self.scaled[key] = pygame.transform.smoothscale(
                self.pieces[symbol], (width, round(width*1.18)))
        image = self.scaled[key]
        return image, image.get_rect(topleft=(x - width//2, y - round(image.get_height()*.86)))
