"""Reference minimax implementation using White-positive evaluator scores."""
import chess
from threading import Event
from .api import SearchResult
from .evaluation import Evaluator
from .evaluation import DEFAULT_EVALUATOR, MATE_SCORE
from .options import SearchOptions
from .stats import SearchContext, SearchStopped
from .api import SearchAlgorithm


class MinimaxSearch(SearchAlgorithm):
    def __init__(self, evaluator: Evaluator | None = None, options: SearchOptions | None = None) -> None:
        self.evaluator = evaluator or DEFAULT_EVALUATOR
        self.options = options or SearchOptions(ordering=False)

    def search(
        self,
        board: chess.Board,
        depth: int,
        evaluator: Evaluator | None = None,
        options: SearchOptions | None = None,
        cancel_event: Event | None = None,
    ) -> SearchResult:
        if depth < 1:
            raise ValueError("depth phải từ 1 trở lên")
        evaluator = evaluator or self.evaluator
        options = options or self.options
        ctx = SearchContext(options, cancel_event)
        best_move, best_score = None, 0
        ctx.visit(0)
        depths = range(1, depth + 1) if options.iterative_deepening or options.time_limit else (depth,)
        try:
            for current_depth in depths:
                iteration_move, iteration_score = None, 0
                moves = list(board.legal_moves)
                if moves:
                    ctx.stats.expanded_nodes += 1
                for move in moves:
                    board.push(move)
                    try:
                        score = self._value(board, current_depth - 1, evaluator, ctx, 1)
                    finally:
                        board.pop()
                    if iteration_move is None or (score > iteration_score if board.turn == chess.WHITE else score < iteration_score):
                        iteration_move, iteration_score = move, score
                best_move, best_score = iteration_move, iteration_score
                ctx.stats.depth_reached = current_depth
        except SearchStopped:
            pass
        if best_move is None:
            best_score = evaluator.evaluate(board)
        ctx.finish()
        return SearchResult(best_move, best_score, ctx.stats.depth_reached, ctx.stats)

    def _value(
        self,
        board: chess.Board,
        depth: int,
        evaluator: Evaluator,
        ctx: SearchContext,
        ply: int,
    ) -> int:
        ctx.visit(ply)
        if board.is_checkmate():
            return -MATE_SCORE + ply if board.turn == chess.BLACK else MATE_SCORE - ply
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0
        if depth == 0:
            return evaluator.evaluate(board, ply)
        moves = list(board.legal_moves)
        if not moves:
            return evaluator.evaluate(board, ply)
        ctx.stats.expanded_nodes += 1
        maximizing = board.turn == chess.WHITE
        value = -MATE_SCORE if maximizing else MATE_SCORE
        for move in moves:
            board.push(move)
            try:
                child = self._value(board, depth - 1, evaluator, ctx, ply + 1)
            finally:
                board.pop()
            value = max(value, child) if maximizing else min(value, child)
        return value


