
import pygame


class StatsPanel:
    WIDTH = 280
    HEIGHT = 500

    BG = (35, 40, 52)
    PANEL = (48, 55, 70)
    WHITE = (245, 245, 245)
    GREEN = (80, 200, 130)
    YELLOW = (245, 190, 70)
    GRAY = (170, 180, 195)

    def __init__(self, screen, x=0, y=0):
        self.screen = screen
        self.x = x
        self.y = y

        self.title_font = pygame.font.SysFont(
            "Arial", 25, bold=True
        )
        self.font = pygame.font.SysFont("Arial", 19)
        self.small_font = pygame.font.SysFont("Arial", 16)

        self.stats = {
            "nodes": 0,
            "cutoffs": 0,
            "elapsed": 0.0,
            "score": 0.0,
            "depth": 0,
        }

        self.is_thinking = False

    def update_stats(
        self,
        nodes=0,
        cutoffs=0,
        elapsed=0.0,
        score=0.0,
        depth=0,
        is_thinking=False,
    ):
        self.stats = {
            "nodes": nodes,
            "cutoffs": cutoffs,
            "elapsed": elapsed,
            "score": score,
            "depth": depth,
        }

        self.is_thinking = is_thinking

    def draw_text(self, text, x, y, color=None, font=None):
        font = font or self.font
        color = color or self.WHITE

        surface = font.render(str(text), True, color)
        self.screen.blit(surface, (x, y))

    def draw(self):
        panel_rect = pygame.Rect(
            self.x,
            self.y,
            self.WIDTH,
            self.HEIGHT,
        )

        pygame.draw.rect(
            self.screen,
            self.BG,
            panel_rect,
            border_radius=12,
        )

        self.draw_text(
            "AI STATISTICS",
            self.x + 20,
            self.y + 20,
            self.WHITE,
            self.title_font,
        )

        pygame.draw.line(
            self.screen,
            self.GRAY,
            (self.x + 20, self.y + 65),
            (self.x + self.WIDTH - 20, self.y + 65),
            2,
        )

        rows = [
            ("Nodes", self.stats["nodes"]),
            ("Cutoffs", self.stats["cutoffs"]),
            ("Time", f'{self.stats["elapsed"]:.2f} s'),
            ("Score", f'{self.stats["score"]:.2f}'),
            ("Depth", self.stats["depth"]),
        ]

        start_y = self.y + 95

        for index, (label, value) in enumerate(rows):
            row_y = start_y + index * 55

            self.draw_text(
                label,
                self.x + 20,
                row_y,
                self.GRAY,
            )

            self.draw_text(
                value,
                self.x + 145,
                row_y,
                self.WHITE,
            )

        pygame.draw.line(
            self.screen,
            self.GRAY,
            (self.x + 20, self.y + 385),
            (self.x + self.WIDTH - 20, self.y + 385),
            1,
        )

        status = "Máy đang nghĩ..." if self.is_thinking else "Máy đang chờ"

        status_color = self.YELLOW if self.is_thinking else self.GREEN

        self.draw_text(
            status,
            self.x + 20,
            self.y + 410,
            status_color,
        )

    def update_from_result(self, result, is_thinking=False):
        """Cap nhat bang thong ke tu ket qua tim kiem cua AI."""

        stats = (
            result.get("stats", {})
            if isinstance(result, dict)
            else getattr(result, "stats", None)
        )

        def read_value(obj, key, default=0):
            if isinstance(obj, dict):
                return obj.get(key, default)
            if obj is not None:
                return getattr(obj, key, default)
            return default

        nodes = read_value(stats, "nodes", 0)
        cutoffs = read_value(stats, "cutoffs", 0)
        elapsed = read_value(stats, "elapsed", 0.0)
        score = read_value(result, "score", 0.0)
        depth = read_value(stats, "depth", 0)

        self.update_stats(
            nodes=nodes,
            cutoffs=cutoffs,
            elapsed=elapsed,
            score=score,
            depth=depth,
            is_thinking=is_thinking,
        )

    def set_thinking(self, is_thinking):
        """Cap nhat trang thai AI dang suy nghi."""
        self.is_thinking = bool(is_thinking)
