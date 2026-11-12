"""Fixed and seeded chess positions for algorithm benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
import random

import chess


@dataclass(frozen=True)
class Position:
    position_id: str
    phase: str
    fen: str


# These positions were reached by replaying legal moves from the starting board.
FIXED_FENS: dict[str, tuple[str, ...]] = {
    'opening': (
        'r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4',
        'rnbqkb1r/pp2pppp/3p1n2/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 1 5',
        'rnbqkb1r/ppp2ppp/4pn2/3p4/3PP3/2N5/PPP2PPP/R1BQKBNR w KQkq - 2 4',
        'rnbqkbnr/pp2pppp/2p5/8/3PN3/8/PPP2PPP/R1BQKBNR b KQkq - 0 4',
        'rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4',
        'rnbqk2r/ppp1ppbp/3p1np1/8/2PPP3/2N5/PP3PPP/R1BQKBNR w KQkq - 0 5',
        'rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4',
        'rnbqkb1r/ppp2ppp/5n2/3Pp3/8/2N3P1/PP1PPP1P/R1BQKBNR b KQkq - 0 4',
        'r1bqkbnr/pp2pppp/2n5/2pp4/8/5NP1/PPPPPPBP/RNBQK2R w KQkq - 2 4',
        'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2BPP3/2P2N2/PP3PPP/RNBQK2R b KQkq - 0 5',
    ),
    'middlegame': (
        '6nr/1ppnbkpp/3q1P2/3p4/r4Q2/2NP4/PPP2PPP/R1BK3R b - - 0 14',
        'rnb1k1nr/1Q1qB2p/p3Npp1/4p3/P4b2/5P1P/1PP3P1/RN2KB1R b KQkq - 0 14',
        'rn2k2r/pp1b1p1p/N1p2qp1/1Q5n/3b2P1/BP6/P1PRNP1P/4KB1R w Kkq - 2 18',
        'r1b1kb1r/1p1q1Npp/2n1p2n/pP4B1/3p4/P4P2/2P3PP/R2QKBNR w KQkq - 2 15',
        'r2q2r1/1bbn1k1p/1pn1ppp1/2Np4/p1PP4/PNQ1P3/1P3PPP/RKB2B1R b - - 6 17',
        'rn2k2r/p1qb1p1p/1p3p1b/2pP4/P3n1p1/8/1P2NPPP/R3KBNR w KQ - 0 18',
        'rnb1k2r/p1pp4/1p2p1pn/2P2pq1/3P1PpP/4B3/PP1bP2R/1R1K1BN1 w kq - 0 16',
        'rn2kb1r/pp1n1p2/4b1pp/3P1q2/P2Q4/2N4N/RP1PP2P/2B1KB1R b Kkq - 1 13',
        '1n2k2r/4qp1p/rp1b2pB/p1P1p1Q1/2b1p2P/P2P1NP1/5P2/RN2KB1R b Kk - 2 17',
        'r1b2B2/1ppp3p/B1n2qk1/p2Pp1p1/P3P3/1PP5/5PP1/1N2Kn1R w K - 1 17',
    ),
    'endgame': (
        '8/8/7k/1R3Ppp/8/1p4PR/r5P1/4K3 b - - 2 39',
        '3kr3/2n5/5npp/P7/6PP/7K/3r4/b7 w - - 0 41',
        'r7/5k1p/p7/P2r2R1/6P1/5K1P/2P2P2/8 w - - 0 46',
        '3r4/3k1n2/1P6/5p1p/2p5/1p6/b5NP/3K4 w - - 0 48',
        '3k4/1r5p/6p1/1B3R2/8/1P2P1P1/7P/K1R5 b - - 0 41',
        '8/5p1p/5pnk/3P1K2/2r5/3N3p/8/5B1N b - - 5 37',
        '1r1k4/8/p6n/1P3pp1/2B5/4Kb2/P7/B7 w - - 0 54',
        '8/7B/n3k3/p6p/P7/P2K4/6RP/3r3R w - - 0 48',
        '2R4N/1r2k2p/8/5p2/Pp6/N5P1/8/R5K1 w - - 0 40',
        '8/8/p1p5/pP2p2p/1P6/3K2k1/6P1/8 b - - 0 38',
    ),
}
def get_fixed_positions(per_phase: int = 10) -> list[Position]:
    """Return the requested number of fixed positions from each phase."""
    if not 1 <= per_phase <= 10:
        raise ValueError("per_phase must be between 1 and 10 for the fixed set")

    return [
        Position(f"{phase}-{index:02d}", phase, fen)
        for phase, fens in FIXED_FENS.items()
        for index, fen in enumerate(fens[:per_phase], start=1)
    ]


def _position_key(fen: str) -> tuple[str, ...]:
    # Move counters do not distinguish the same board, turn and move rights.
    return tuple(fen.split()[:4])


def _matches_phase(board: chess.Board, phase: str) -> bool:
    piece_count = len(board.piece_map())
    if phase == "opening":
        return board.ply() <= 16 and piece_count >= 26
    if phase == "middlegame":
        return board.ply() >= 18 and piece_count >= 16
    return piece_count <= 12


def generate_positions(per_phase: int = 10, seed: int = 42) -> list[Position]:
    """Generate positions by continuing fixed positions with legal moves."""
    if per_phase < 1:
        raise ValueError("per_phase must be at least 1")

    rng = random.Random(seed)
    seen = {_position_key(fen) for fens in FIXED_FENS.values() for fen in fens}
    positions: list[Position] = []

    for phase, fens in FIXED_FENS.items():
        count = 0
        for _ in range(100 * per_phase):
            board = chess.Board(rng.choice(fens))
            for _ in range(rng.randint(1, 3)):
                moves = sorted(board.legal_moves, key=chess.Move.uci)
                if not moves:
                    break
                board.push(rng.choice(moves))

            if board.is_game_over() or not _matches_phase(board, phase):
                continue

            fen = board.fen()
            key = _position_key(fen)
            if key in seen:
                continue

            seen.add(key)
            count += 1
            positions.append(Position(f"seed-{seed}-{phase}-{count:02d}", phase, fen))
            if count == per_phase:
                break
        else:
            raise ValueError(f"Only generated {count} distinct positions for {phase}")

    return positions


if __name__ == "__main__":
    from collections import Counter

    fixed = get_fixed_positions()
    generated = generate_positions(seed=42)
    for label, positions in (("Fixed", fixed), ("Generated", generated)):
        counts = Counter(position.phase for position in positions)
        if counts != {phase: 10 for phase in FIXED_FENS}:
            raise ValueError(f"Unexpected phase counts: {dict(counts)}")
        for position in positions:
            board = chess.Board(position.fen)
            if not board.is_valid() or board.is_game_over():
                raise ValueError(f"Invalid or finished position: {position.position_id}")
        print(f"{label}: {dict(counts)}")

    if generated != generate_positions(seed=42):
        raise RuntimeError("The same seed generated different positions")
    print("Seed 42 reproducible: OK")