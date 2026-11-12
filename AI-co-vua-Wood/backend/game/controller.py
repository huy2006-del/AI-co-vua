"""State and legal moves shared by the board, move history and opponent."""
from collections.abc import Callable

import chess


class GameController:
    def __init__(self, choose_move: Callable[[chess.Board], chess.Move], human=chess.WHITE,
                 board=None, mode="ai"):
        self.choose_move = choose_move
        self.human = human
        self.mode = mode
        self.stats = []
        self.board = chess.Board() if board is None else board.copy()
        self.history = []

    @property
    def outcome(self):
        return self.board.outcome()

    @property
    def human_turn(self):
        return self.outcome is None and (self.mode == "local" or (self.mode == "ai" and self.board.turn == self.human))

    def legal_moves(self, square):
        if not self.human_turn:
            return []
        return [move for move in self.board.legal_moves if move.from_square == square]

    def play_human(self, move):
        if not self.human_turn:
            raise ValueError("Chưa đến lượt bạn hoặc ván đã kết thúc.")
        self._play(move)

    def play_computer(self, move):
        if self.outcome is None and not self.human_turn:
            self._play(move)

    def undo(self):
        if not self.history:
            return False
        if self.mode == "ai":
            if len(self.history) == 1 and self.history[0][1] != self.human:
                return False
            while self.history:
                color = self.history[-1][1]
                self._undo_one()
                if color == self.human:
                    break
        else:
            self._undo_one()
        return True

    def _undo_one(self):
        self.board.pop()
        self.history.pop()
        self.stats.pop()

    def _play(self, move):
        if move not in self.board.legal_moves:
            raise ValueError("Nước đi không hợp lệ.")
        self.history.append((self.board.fullmove_number, self.board.turn, self.board.san(move)))
        self.board.push(move)
        self.stats.append(None)
