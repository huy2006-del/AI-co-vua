"""CLI: Nguoi choi vs AI."""

import argparse
import chess

from engine.api import search, ALGOS


def parse_move(board, text):
    """Chap nhan nuoc di SAN hoac UCI."""
    try:
        return board.parse_san(text)
    except ValueError:
        try:
            return board.parse_uci(text)
        except ValueError:
            return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", choices=ALGOS, default="alphabeta_ordered")
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--color", choices=["white", "black"], default="white")
    args = parser.parse_args()

    if args.depth < 1:
        parser.error("Depth phai lon hon 0.")

    if args.algo == "minimax" and args.depth > 3:
        parser.error("Minimax chi cho phep depth toi da 3.")

    if args.algo == "alphabeta_ordered" and args.depth > 5:
        parser.error("Alpha-Beta chi cho phep depth toi da 5.")

    human = chess.WHITE if args.color == "white" else chess.BLACK
    board = chess.Board()

    while not board.is_game_over():
        print("\n" + str(board))
        print("Luot:", "Trang" if board.turn else "Den")

        if board.turn == human:
            text = input("Nuoc di (SAN/UCI), hoac quit: ").strip()

            if text.lower() == "quit":
                print("Da thoat game.")
                return

            move = parse_move(board, text)

            if move is None or move not in board.legal_moves:
                print("Nuoc di khong hop le. Hay nhap lai.")
                continue

        else:
            print("May dang nghi...")
            result = search(board, args.algo, args.depth)

            move = result.move
            if move is None or move not in board.legal_moves:
                print("AI khong tra ve nuoc di hop le.")
                return

            stats = getattr(result, "stats", None)
            nodes = getattr(stats, "nodes", 0)
            cutoffs = getattr(stats, "cutoffs", 0)
            elapsed = getattr(stats, "elapsed", 0.0)
            depth = getattr(stats, "depth", args.depth)
            score = getattr(result, "score", 0)

            print("May di:", board.san(move))
            print("===== THONG KE AI =====")
            print("Nodes:", nodes)
            print("Cutoffs:", cutoffs)
            print("Time:", f"{elapsed:.3f}s")
            print("Score:", score)
            print("Depth:", depth)

        board.push(move)

    print("\n" + str(board))
    print("\nKet thuc:", board.result())
    outcome = board.outcome()
    if outcome is not None:
        print("Ly do:", outcome.termination.name)


if __name__ == "__main__":
    main()
