"""Deterministic move ordering: TT/PV move, promotions, then captures by MVV-LVA."""
import chess
from collections.abc import Iterable
from .evaluation import PIECE_VALUES


def order_moves(
    board: chess.Board,
    moves: Iterable[chess.Move],
    tt_move: chess.Move | None = None,
    pv_move: chess.Move | None = None,
) -> list[chess.Move]:
    def key(move: chess.Move) -> tuple[int, int]:
        if move == tt_move:
            return (3, 0)
        if move == pv_move:
            return (2, 0)
        if move.promotion:
            return (1, 10_000 + PIECE_VALUES[move.promotion])
        if board.is_capture(move):
            victim = board.piece_type_at(move.to_square)
            if board.is_en_passant(move):
                victim = chess.PAWN
            attacker = board.piece_type_at(move.from_square)
            victim_value = PIECE_VALUES.get(victim or chess.PAWN, 0)
            attacker_value = PIECE_VALUES.get(attacker or chess.PAWN, 0)
            return (1, 10_000 + 10 * (victim_value - attacker_value))
        return (0, 0)
    return sorted(moves, key=key, reverse=True)

