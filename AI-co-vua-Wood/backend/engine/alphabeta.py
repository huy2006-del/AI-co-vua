"""Alpha-beta negamax with optional ordering, iterative deepening, TT and quiescence."""
import chess
import chess.polyglot
from threading import Event
from .options import SearchOptions
from .stats import SearchContext, SearchStopped
from .tt import TTEntry, TTFlag, TranspositionTable
from .ordering import order_moves
from .quiescence import quiescence
from .evaluation import DEFAULT_EVALUATOR, MATE_SCORE
from .api import SearchAlgorithm
from .evaluation import Evaluator
from .api import SearchResult


class AlphaBetaSearch(SearchAlgorithm):
    def __init__(self, evaluator: Evaluator | None = None, options: SearchOptions | None = None) -> None:
        self.evaluator = evaluator or DEFAULT_EVALUATOR
        self.options = options or SearchOptions()

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
        legal = list(board.legal_moves)
        if not legal:
            return _result(None, self.evaluator.evaluate(board), 0, ctx)
        ctx.completed_best = legal[0]
        ctx.completed_score = self.evaluator.evaluate(board)
        tt = TranspositionTable(options.tt_size)
        depths = range(1, depth + 1) if options.iterative_deepening else (depth,)
        try:
            for current_depth in depths:
                ctx.root_best = None
                score = self._negamax(board, current_depth, -MATE_SCORE, MATE_SCORE,
                                      0, evaluator, ctx, tt)
                ctx.completed_score = score if board.turn == chess.WHITE else -score
                ctx.completed_best = ctx.root_best or ctx.completed_best
                ctx.stats.depth_reached = current_depth
                if ctx.completed_score >= MATE_SCORE - current_depth:
                    break
        except SearchStopped:
            pass
        ctx.finish()
        return _result(ctx.completed_best, ctx.completed_score, ctx.stats.depth_reached, ctx)

    def _negamax(
        self,
        board: chess.Board,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
        evaluator: Evaluator,
        ctx: SearchContext,
        tt: TranspositionTable,
    ) -> int:
        ctx.visit(ply)
        if board.is_checkmate():
            return -MATE_SCORE + ply
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0
        if depth <= 0:
            if ctx.options.quiescence:
                # Quiescence is written in negamax coordinates.
                class SideEvaluator:
                    def evaluate(self, board: chess.Board, ply: int = 0) -> int:
                        value = evaluator.evaluate(board, ply)
                        return value if board.turn == chess.WHITE else -value
                return quiescence(board, alpha, beta, SideEvaluator(), ctx, ply)
            value = evaluator.evaluate(board, ply)
            return value if board.turn == chess.WHITE else -value

        key = chess.polyglot.zobrist_hash(board)
        original_alpha, original_beta = alpha, beta
        entry = tt.get(key) if ctx.options.transposition_table else None
        tt_move = entry.best_move if entry else None
        if entry and entry.depth >= depth:
            ctx.stats.tt_hits += 1
            if entry.flag == TTFlag.EXACT:
                return entry.score
            if entry.flag == TTFlag.LOWER:
                alpha = max(alpha, entry.score)
            elif entry.flag == TTFlag.UPPER:
                beta = min(beta, entry.score)
            if alpha >= beta:
                return entry.score

        moves = list(board.legal_moves)
        if moves:
            ctx.stats.expanded_nodes += 1
        if ctx.options.ordering:
            moves = order_moves(board, moves, tt_move, ctx.pv_move)
        best_score, best_move = -MATE_SCORE, None
        for move in moves:
            board.push(move)
            try:
                score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1,
                                       evaluator, ctx, tt)
            finally:
                board.pop()
            if score > best_score:
                best_score, best_move = score, move
                if ply == 0:
                    ctx.root_best = move
            alpha = max(alpha, score)
            if alpha >= beta:
                ctx.stats.cutoffs += 1
                ctx.stats.cutoffs_per_depth[ply] += 1
                break
        if ctx.options.transposition_table:
            flag = TTFlag.UPPER if best_score <= original_alpha else (
                TTFlag.LOWER if best_score >= original_beta else TTFlag.EXACT)
            tt.put(key, TTEntry(depth, best_score, flag, best_move))
        return best_score


def _result(move: chess.Move | None, score: int, depth: int, context: SearchContext) -> SearchResult:
    return SearchResult(move=move, score=score, depth=depth, stats=context.stats)


