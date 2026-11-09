"""Scrollable SAN move list, grouped by full move number."""
import chess
import pygame


class HistoryView:
    row_height = 28

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.offset = 0
        self.rows = []
        self.count = 0

    @property
    def capacity(self):
        return (self.rect.height - 12) // self.row_height

    def scroll(self, steps):
        limit = max(0, len(self.rows) - self.capacity)
        self.offset = max(0, min(limit, self.offset + steps))

    def update(self, history):
        if len(history) == self.count:
            return
        rows = {}
        for number, color, san in history:
            row = rows.setdefault(number, ["", ""])
            row[0 if color == chess.WHITE else 1] = san
        self.rows = list(rows.items())
        self.count = len(history)
        self.offset = max(0, len(self.rows) - self.capacity)

    def draw(self, surface, font):
        pygame.draw.rect(surface, "#211610", self.rect, border_radius=8)
        if not self.rows:
            surface.blit(font.render("Chưa có nước đi", True, "#c1a990"),
                         (self.rect.x + 10, self.rect.y + 8))
        for index, (number, (white, black)) in enumerate(
                self.rows[self.offset:self.offset + self.capacity]):
            y = self.rect.y + 6 + index * self.row_height
            if index % 2 == 0:
                pygame.draw.rect(surface, "#38271e", (self.rect.x + 6, y,
                                                      self.rect.width - 12, self.row_height))
            for x, label in ((12, f"{number}."), (self.rect.width // 5, white), (self.rect.width // 2, black)):
                surface.blit(font.render(label, True, "#f4e0bd"), (self.rect.x + x, y + 4))
