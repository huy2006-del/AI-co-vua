"""Small adapter for game controllers expecting choose_move/suggest."""
from enum import Enum
import chess
from .api import AlgorithmFactory, SearchResult
from .evaluation import Evaluator
from .options import SearchOptions


class AIPlayer:
    def __init__(
        self,
        algorithm: str | Enum = "alphabeta",
        depth: int = 3,
        evaluator: Evaluator | None = None,
        options: SearchOptions | None = None,
    ) -> None:
        self.algorithm: str | Enum = algorithm
        self.depth: int = depth
        self.evaluator: Evaluator | None = evaluator
        self.options: SearchOptions | None = options

    def suggest(self, board: chess.Board) -> SearchResult:
        return AlgorithmFactory.create(self.algorithm, self.evaluator, self.options).search(
            board, self.depth, evaluator=self.evaluator, options=self.options)

    def choose_move(self, board: chess.Board) -> SearchResult:
        return self.suggest(board)

