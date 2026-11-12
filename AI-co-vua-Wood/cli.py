"""CLI: chơi người vs máy bằng dòng lệnh.
   python cli.py --algo alphabeta_ordered --depth 3 --color white
Nhập nước đi dạng UCI (e2e4) hoặc SAN (Nf3). 'quit' để thoát."""
import argparse
import chess
from backend.engine.api import search, ALGOS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo", choices=ALGOS, default="alphabeta_ordered")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--color", choices=["white", "black"], default="white")
    a = ap.parse_args()

    human = chess.WHITE if a.color == "white" else chess.BLACK
    board = chess.Board()
    while not board.is_game_over():
        print("\n" + str(board))
        if board.turn == human:
            text = input("Nước của bạn: ").strip()
            if text == "quit":
                return
            try:
                try:
                    move = board.parse_san(text)
                except ValueError:
                    move = board.parse_uci(text)
            except ValueError:
                print("Nước đi không hợp lệ.")
                continue
        else:
            r = search(board, a.algo, a.depth)
            move = r.move
            print(f"Máy đi {board.san(move)} | điểm {r.score} | node {r.stats.nodes} "
                  f"| {r.stats.elapsed:.2f}s")
        board.push(move)
    print("\nKết thúc:", board.result(), board.outcome().termination.name)


if __name__ == "__main__":
    main()
