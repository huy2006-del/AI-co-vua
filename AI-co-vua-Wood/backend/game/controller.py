"""Game state and move adapter shared by the GUI and legacy command tools."""

import chess

from backend.engine.api import search
from .board_state import BoardState
from .config import GameConfig
from .errors import InvalidMoveError
from .records import GameRecord


class _History(list):
    """List for the GUI that remains callable for the older controller API."""
    def __call__(self):
        return [san for _, _, san in self]


class GameController:
    def __init__(self, config=None, human=chess.WHITE, mode="ai", board=None):
        self.config = config if isinstance(config, GameConfig) else GameConfig()
        self.config.validate()
        self.human = human
        self.mode = mode
        self.board_state = BoardState()
        self.board = board if board is not None else self.board_state.board
        if board is not None:
            self.board_state.board = board
        self.record = GameRecord()
        self.history = _History()
        self.stats = []

    @property
    def human_turn(self):
        return self.mode == "local" or (self.mode == "ai" and self.board.turn == self.human)

    @property
    def outcome(self):
        return self.board.outcome(claim_draw=True)

    def new_game(self, fen=None):
        self.board_state = BoardState(fen)
        self.board = self.board_state.board
        self.record.clear()
        self.history.clear()
        self.stats.clear()

    def snapshot(self):
        return self.board.fen()

    def legal_moves(self, square=None):
        return [m for m in self.board.legal_moves if square is None or m.from_square == square]

    def legal_targets(self, square_str):
        square = chess.parse_square(square_str)
        return [chess.square_name(m.to_square) for m in self.legal_moves(square)]

    def _play(self, move):
        if isinstance(move, str):
            try:
                move = self.board.parse_san(move)
            except ValueError:
                move = chess.Move.from_uci(move)
        if move not in self.board.legal_moves:
            raise InvalidMoveError(f"Nước đi không hợp lệ: {move}")
        san = self.board.san(move)
        entry = (self.board.fullmove_number, self.board.turn, san)
        self.board.push(move)
        self.record.add_move(san)
        self.history.append(entry)
        return move

    def play_human(self, move):
        if not self.human_turn:
            raise InvalidMoveError("Hiện không phải lượt của người chơi.")
        return self._play(move)

    def play_human_move(self, move_str):
        return self.play_human(move_str)

    def play_computer(self, move):
        return self._play(move)

    def choose_move(self, board=None):
        position = board or self.board
        return search(position, self.config.ai_algorithm, self.config.ai_depth,
                      evaluation="position", time_limit=self.config.time_limit)

    def undo(self):
        if not self.board.move_stack:
            return None
        move = self.board.pop()
        self.history.pop()
        self.record.clear()
        for _, _, san in self.history:
            self.record.add_move(san)
        return move

    def history_moves(self):
        return self.history()

    def start_ai_move(self):
        return self.choose_move()

    def poll_ai(self):
        return None
