"""Deterministic legal-move opponent used for interface smoke checks."""

import chess
from .controller import GameController


class FakeController(GameController):
    def __init__(self, human=chess.WHITE, board=None):
        super().__init__(human=human, mode="ai", board=board)

    def choose_move(self, board=None):
        position = board or self.board
        return next(iter(position.legal_moves), None)
