"""CLI: Nguoi choi vs AI."""

import argparse
import time
import chess

from backend.engine.api import search, ALGOS
from backend.game.controller import GameController
from backend.game.config import GameConfig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--algo", choices=list(ALGOS),
                        default="alphabeta_ordered")
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--color", choices=["white", "black"],
                        default="white")

    args = parser.parse_args()

    if args.depth < 1 or args.depth > 5:
        parser.error("Depth phai tu 1 den 5.")

    config = GameConfig(
        ai_depth=args.depth,
        ai_algorithm=args.algo,
        player_color=args.color
    )

    controller = GameController(config)
    board = controller.board_state.board

    human = chess.WHITE if args.color == "white" else chess.BLACK

    while not board.is_game_over():
        print("\n", board)
        print("Luot:", "Trang" if board.turn else "Den")

        if board.turn == human:
            text = input("Nuoc di SAN/UCI, hoac quit: ").strip()

            if text.lower() == "quit":
                print("Da thoat game.")
                return

            try:
                controller.play_human_move(text)
            except Exception as error:
                print("Nuoc di khong hop le:", error)
                continue

        else:
            print("May dang nghi...")
            start = time.perf_counter()

            result = search(board, args.algo, args.depth, time_limit=config.time_limit)
            move = result.move

            elapsed = time.perf_counter() - start

            if move is None or move not in board.legal_moves:
                print("AI khong tra ve nuoc di hop le.")
                return

            san_move = board.san(move)
            controller.board_state.push(move)
            controller.record.add_move(san_move)

            print("May di:", san_move)
            print("===== THONG KE AI =====")
            print("Time:", f"{elapsed:.3f}s")
            print("Depth:", args.depth)
            print("Nodes:", result.stats.nodes)
            print("Cutoffs:", result.stats.cutoffs)

    print("\n", board)
    print("Ket thuc:", board.result())

    outcome = board.outcome()
    if outcome:
        print("Ly do:", outcome.termination.name)


if __name__ == "__main__":
    main()
