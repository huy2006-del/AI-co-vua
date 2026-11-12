"""Small alpha-beta opponent for GUI demos before the team engine is available."""
import chess

VALUES = dict(zip(chess.PIECE_TYPES, (100, 320, 330, 500, 900, 0)))
MATE = 100_000


def choose_move(board, depth):
    def score(remaining, alpha, beta):
        outcome = board.outcome()
        if outcome:
            return 0 if outcome.winner is None else -(MATE + remaining)
        if remaining == 0:
            own = sum(value * len(board.pieces(piece, board.turn))
                      for piece, value in VALUES.items())
            other = sum(value * len(board.pieces(piece, not board.turn))
                        for piece, value in VALUES.items())
            return own - other
        best = -2 * MATE
        for move in ordered_moves():
            board.push(move)
            value = -score(remaining - 1, -beta, -alpha)
            board.pop()
            best = max(best, value)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best

    def ordered_moves():
        return sorted(board.legal_moves, key=lambda move: (
            bool(move.promotion), board.is_capture(move)
        ), reverse=True)

    best_value = -2 * MATE
    best_move = None
    for move in ordered_moves():
        board.push(move)
        value = -score(depth - 1, -2 * MATE, -best_value)
        board.pop()
        if value > best_value:
            best_value, best_move = value, move
    return best_move
