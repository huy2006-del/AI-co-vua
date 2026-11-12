"""Search API shared by live play and experiments."""
from dataclasses import dataclass
from time import perf_counter

import chess

ALGOS = ("minimax", "alphabeta", "alphabeta_ordered")
EVALUATIONS = ("material", "position")
VALUES = dict(zip(chess.PIECE_TYPES, (100, 320, 330, 500, 900, 0)))
MATE = 100_000
INF = 2 * MATE


@dataclass(frozen=True)
class SearchStats:
    nodes: int
    elapsed: float
    completed_depth: int
    limited: bool


@dataclass(frozen=True)
class SearchResult:
    move: chess.Move | None
    score: int
    stats: SearchStats


class SearchLimit(Exception):
    pass


def evaluate(board, evaluation):
    score = 0
    for square, piece in board.piece_map().items():
        value = VALUES[piece.piece_type]
        if evaluation == "position":
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            forward = rank if piece.color else 7 - rank
            center = 14 - abs(2 * file - 7) - abs(2 * rank - 7)
            if piece.piece_type == chess.PAWN:
                value += 6 * forward + center
            elif piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                value += 4 * center
        score += value if piece.color else -value
    return score


def search(board, algo="alphabeta_ordered", depth=3, *, evaluation="position",
           time_limit=None, node_limit=None):
    """Return the chosen move and a score from White's perspective."""
    if algo not in ALGOS or evaluation not in EVALUATIONS or depth < 1:
        raise ValueError("Cấu hình tìm kiếm không hợp lệ.")
    board = board.copy()
    started = perf_counter()
    deadline = started + time_limit if time_limit is not None else None
    nodes = 0
    pruning = algo != "minimax"

    def visit(remaining, alpha, beta, ply):
        nonlocal nodes
        if (node_limit is not None and nodes >= node_limit
                or deadline is not None and perf_counter() >= deadline):
            raise SearchLimit
        nodes += 1
        outcome = board.outcome()
        if outcome:
            return (0 if outcome.winner is None else -MATE + ply), None
        if remaining == 0:
            return evaluate(board, evaluation) * (1 if board.turn else -1), None
        moves = list(board.legal_moves)
        if algo == "alphabeta_ordered":
            def priority(move):
                capture = board.piece_type_at(move.to_square)
                if board.is_en_passant(move):
                    capture = chess.PAWN
                return (VALUES.get(move.promotion, 0)
                        + (10 * VALUES[capture] - VALUES[board.piece_type_at(move.from_square)]
                           if capture else 0))
            moves.sort(key=priority, reverse=True)
        best, best_move = -INF, None
        for move in moves:
            board.push(move)
            try:
                value, _ = visit(remaining - 1, -beta, -alpha, ply + 1)
            finally:
                board.pop()
            if -value > best:
                best, best_move = -value, move
            if pruning:
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
        return best, best_move

    limited = False
    done = 0
    sign = 1 if board.turn else -1
    best_move = next(iter(board.legal_moves), None) if not board.outcome() else None
    score = evaluate(board, evaluation) * sign
    levels = range(1, depth + 1) if deadline is not None or node_limit is not None else (depth,)
    for level in levels:
        try:
            score, best_move = visit(level, -INF, INF, 0)
        except SearchLimit:
            limited = True
            break
        done = level
        if best_move is None:
            break
    return SearchResult(best_move, score * sign,
                        SearchStats(nodes, perf_counter() - started, done, limited))
