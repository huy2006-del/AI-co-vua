
import pygame

from config import (
    DEFAULT_DEPTH,
    MAX_MINIMAX_DEPTH,
    MAX_ALPHABETA_DEPTH,
    STOCKFISH_ANALYSIS_DEPTH,
)


class ConfigScreen:
    WIDTH = 800
    HEIGHT = 600

    BG = (30, 35, 48)
    PANEL = (45, 52, 68)
    WHITE = (245, 245, 245)
    GRAY = (180, 185, 195)
    GREEN = (80, 190, 130)
    BLUE = (75, 130, 210)
    RED = (220, 85, 85)

    def __init__(self, screen):
        self.screen = screen

        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 34, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 18)

        self.player_color = "white"
        self.algorithm = "alphabeta_ordered"
        self.depth = DEFAULT_DEPTH

        self.message = ""

        self.color_options = ["white", "black"]
        self.algorithm_options = [
            "minimax",
            "alphabeta_ordered",
            "stockfish",
        ]

    def get_max_depth(self):
        if self.algorithm == "minimax":
            return MAX_MINIMAX_DEPTH

        if self.algorithm == "alphabeta_ordered":
            return MAX_ALPHABETA_DEPTH

        return STOCKFISH_ANALYSIS_DEPTH

    def validate(self):
        if self.player_color not in self.color_options:
            return False, "Mau quan khong hop le."

        if self.algorithm not in self.algorithm_options:
            return False, "Thuat toan khong hop le."

        if not isinstance(self.depth, int) or self.depth < 1:
            return False, "Depth phai lon hon 0."

        if self.depth > self.get_max_depth():
            return False, "Depth vuot qua gioi han."

        return True, ""

    def set_algorithm(self, algorithm):
        if algorithm not in self.algorithm_options:
            self.message = "Thuat toan khong hop le."
            return

        self.algorithm = algorithm
        self.depth = min(self.depth, self.get_max_depth())
        self.message = ""

    def change_depth(self, amount):
        self.depth += amount
        self.depth = max(1, min(self.depth, self.get_max_depth()))
        self.message = ""

    def get_config(self):
        valid, message = self.validate()

        if not valid:
            self.message = message
            return None

        return {
            "player_color": self.player_color,
            "algorithm": self.algorithm,
            "depth": self.depth,
        }

    def draw_text(self, text, x, y, color=None, font=None):
        font = font or self.font
        color = color or self.WHITE

        surface = font.render(str(text), True, color)
        self.screen.blit(surface, (x, y))

    def draw_button(self, rect, text, selected=False):
        color = self.BLUE if selected else self.PANEL

        pygame.draw.rect(
            self.screen,
            color,
            rect,
            border_radius=8,
        )

        pygame.draw.rect(
            self.screen,
            self.GRAY,
            rect,
            width=1,
            border_radius=8,
        )

        surface = self.font.render(text, True, self.WHITE)
        text_rect = surface.get_rect(center=rect.center)
        self.screen.blit(surface, text_rect)

    def draw(self):
        self.screen.fill(self.BG)

        self.draw_text(
            "GAME CONFIGURATION",
            220,
            45,
            self.WHITE,
            self.title_font,
        )

        self.draw_text("Player color:", 100, 145)

        self.draw_button(
            pygame.Rect(300, 135, 150, 45),
            "White",
            self.player_color == "white",
        )

        self.draw_button(
            pygame.Rect(470, 135, 150, 45),
            "Black",
            self.player_color == "black",
        )

        self.draw_text("Algorithm:", 100, 235)

        labels = [
            ("Minimax", "minimax"),
            ("Alpha-Beta", "alphabeta_ordered"),
            ("Stockfish", "stockfish"),
        ]

        for index, (label, value) in enumerate(labels):
            rect = pygame.Rect(100 + index * 220, 280, 200, 48)
            self.draw_button(
                rect,
                label,
                self.algorithm == value,
            )

        self.draw_text("Search depth:", 100, 375)

        self.draw_button(
            pygame.Rect(330, 365, 55, 45),
            "-",
        )

        self.draw_text(
            self.depth,
            415,
            370,
            self.GREEN,
            self.title_font,
        )

        self.draw_button(
            pygame.Rect(465, 365, 55, 45),
            "+",
        )

        self.draw_text(
            f"Maximum depth: {self.get_max_depth()}",
            100,
            435,
            self.GRAY,
            self.small_font,
        )

        if self.message:
            self.draw_text(self.message, 100, 485, self.RED)

        self.draw_button(
            pygame.Rect(300, 525, 200, 50),
            "Save configuration",
            True,
        )

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None

        if event.button != 1:
            return None

        x, y = event.pos

        if pygame.Rect(300, 135, 150, 45).collidepoint(x, y):
            self.player_color = "white"

        elif pygame.Rect(470, 135, 150, 45).collidepoint(x, y):
            self.player_color = "black"

        elif pygame.Rect(100, 280, 200, 48).collidepoint(x, y):
            self.set_algorithm("minimax")

        elif pygame.Rect(320, 280, 200, 48).collidepoint(x, y):
            self.set_algorithm("alphabeta_ordered")

        elif pygame.Rect(540, 280, 200, 48).collidepoint(x, y):
            self.set_algorithm("stockfish")

        elif pygame.Rect(330, 365, 55, 45).collidepoint(x, y):
            self.change_depth(-1)

        elif pygame.Rect(465, 365, 55, 45).collidepoint(x, y):
            self.change_depth(1)

        elif pygame.Rect(300, 525, 200, 50).collidepoint(x, y):
            return self.get_config()

        return None
