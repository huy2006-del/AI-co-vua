"""Run reproducible comparisons and export results."""
import csv
import json
import os
import shutil
from pathlib import Path
from time import perf_counter

import chess
import chess.engine

from backend.engine.api import search

POSITIONS = {
    "Khai cuộc": chess.STARTING_FEN,
    "Trung cuộc": "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 2 8",
    "Tàn cuộc": "8/2k5/3p4/3P4/4K3/7P/8/8 w - - 0 1",
}
FIELDS = ("position", "fen", "algorithm", "evaluation", "depth", "completed_depth",
          "node_limit", "time_limit", "limited", "move", "nodes", "seconds",
          "score_white_cp", "stockfish_move", "matches_stockfish", "stockfish_loss_cp")


def stockfish_path():
    configured = os.environ.get("STOCKFISH_PATH")
    return configured or shutil.which("stockfish")


def compare(mode, positions, algorithms, evaluations, depths, time_limit, node_limit,
            stockfish_depth=12):
    engine = None
    if mode == "Stockfish":
        path = stockfish_path()
        if not path:
            raise ValueError("Cần cài Stockfish và thiết lập STOCKFISH_PATH.")
        engine = chess.engine.SimpleEngine.popen_uci(path, timeout=10)
    try:
        rows = []
        for name, fen in positions.items():
            board = chess.Board(fen)
            if not board.is_valid() or board.is_game_over():
                raise ValueError(f"Thế cờ {name} không hợp lệ hoặc đã kết thúc.")
            limit = chess.engine.Limit(depth=stockfish_depth, time=min(time_limit, 3.0))
            best = engine.analyse(board, limit) if engine else None
            for algo in algorithms:
                for evaluation in evaluations:
                    for depth in depths:
                        result = search(board, algo, depth, evaluation=evaluation,
                                        time_limit=time_limit, node_limit=node_limit)
                        move = result.move
                        row = dict(position=name, fen=fen, algorithm=algo, evaluation=evaluation,
                                   depth=depth, completed_depth=result.stats.completed_depth,
                                   node_limit=node_limit, time_limit=time_limit,
                                   limited=result.stats.limited, move=board.san(move),
                                   nodes=result.stats.nodes, seconds=round(result.stats.elapsed, 6),
                                   score_white_cp=result.score, stockfish_move="",
                                   matches_stockfish="", stockfish_loss_cp="")
                        if best:
                            reference = best["pv"][0]
                            candidate = best if move == reference else engine.analyse(
                                board, limit, root_moves=[move])
                            best_score = best["score"].pov(board.turn).score(mate_score=100_000)
                            candidate_score = candidate["score"].pov(board.turn).score(mate_score=100_000)
                            row.update(stockfish_move=board.san(reference),
                                       matches_stockfish=move == reference,
                                       stockfish_loss_cp=max(0, best_score - candidate_score))
                        rows.append(row)
        return rows
    finally:
        if engine:
            engine.quit()


def save_run(folder, settings, rows):
    folder.mkdir(parents=True, exist_ok=False)
    with (folder / "run.json").open("w", encoding="utf-8") as stream:
        json.dump({"settings": settings, "results": rows}, stream, ensure_ascii=False, indent=2)


def export_run(folder: Path, rows):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    with (folder / "results.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    labels = [f"{r['position']}\n{r['algorithm']} · {r['evaluation']} · d{r['depth']}" for r in rows]
    figure, axes = plt.subplots(1, 2, figsize=(13, max(4, .43 * len(labels) + 1.4)))
    indices = range(len(labels))
    for axis, title, key in zip(axes, ("Thời gian (ms)", "Số nút"), ("seconds", "nodes")):
        values = [r[key] * (1000 if key == "seconds" else 1) for r in rows]
        axis.barh(indices, values, color="#a66d42")
        axis.set_yticks(list(indices), labels, fontsize=8)
        axis.set_title(title)
        axis.invert_yaxis()
    figure.tight_layout()
    figure.savefig(folder / "comparison.png", dpi=140)
    plt.close(figure)


def engine_move(board, algo, depth, evaluation, seconds, nodes):
    if algo != "stockfish":
        return search(board, algo, depth, evaluation=evaluation, time_limit=seconds,
                      node_limit=nodes)
    path = stockfish_path()
    if not path:
        raise ValueError("Cần cài Stockfish và thiết lập STOCKFISH_PATH.")
    started = perf_counter()
    with chess.engine.SimpleEngine.popen_uci(path, timeout=10) as engine:
        played = engine.play(board, chess.engine.Limit(depth=depth, time=seconds, nodes=nodes),
                             info=chess.engine.INFO_ALL)
    from backend.engine.api import SearchResult, SearchStats
    info = played.info
    score = info.get("score")
    return SearchResult(played.move, score.white().score(mate_score=100_000) if score else 0,
                        SearchStats(info.get("nodes", 0), perf_counter() - started,
                                    info.get("depth", 0), False))
