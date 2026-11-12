"""Deterministic opponent for frontend development."""
from .controller import GameController


class FakeController(GameController):
    def __init__(self, human=True, board=None):
        super().__init__(lambda position: next(iter(position.legal_moves)), human, board)
