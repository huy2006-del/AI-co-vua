"""Capture-only leaf extension that avoids evaluating unstable tactical positions."""
import chess
from typing import Protocol
from .stats import SearchContext


class _Evaluator(Protocol):
    def evaluate(self, board: chess.Board, ply: int = 0) -> int: ...


def quiescence(
    board: chess.Board,
    alpha: int,
    beta: int,
    evaluator: _Evaluator,
    context: SearchContext,
    ply: int = 0,
    qdepth: int = 0,
) -> int:
    context.visit(ply)
    if board.is_checkmate():
        return -100_000 + ply
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0
    if qdepth >= context.options.max_quiescence_depth:
        return evaluator.evaluate(board, ply)

    in_check = board.is_check()
    stand_pat = evaluator.evaluate(board, ply)
    if not in_check:
        if stand_pat >= beta:
            return stand_pat
        alpha = max(alpha, stand_pat)
        moves = list(board.generate_legal_captures())
        moves.extend(m for m in board.legal_moves if m.promotion and not board.is_capture(m))
    else:
        moves = list(board.legal_moves)
    for move in moves:
        board.push(move)
        try:
            score = -quiescence(board, -beta, -alpha, evaluator, context, ply + 1, qdepth + 1)
        finally:
            board.pop()
        if score >= beta:
            return score
        alpha = max(alpha, score)
    return alpha


