"""Play color-swapped games with the baseline Alpha-Beta and Stockfish."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
from random import Random
from tempfile import TemporaryDirectory
from uuid import uuid4

import chess
import chess.engine

from .compare_algos import _MeasuredSearch
from .positions import get_fixed_positions
from .vs_stockfish import StockfishAdapter, StockfishUnavailableError


def play_game(
    board: chess.Board,
    *,
    ai_color: chess.Color,
    search: _MeasuredSearch,
    stockfish: StockfishAdapter,
    limit: chess.engine.Limit,
    max_plies: int | None,
) -> dict[str, int | str]:
    """Play one game and record the result from the AI's perspective."""
    moves: list[str] = []
    while True:
        outcome = board.outcome(claim_draw=True)
        if outcome is not None:
            if outcome.winner is None:
                ai_result = "draw"
            else:
                ai_result = "win" if outcome.winner == ai_color else "loss"
            result, termination = outcome.result(), outcome.termination.name.lower()
            break
        if max_plies is not None and len(moves) >= max_plies:
            result, ai_result, termination = "*", "unfinished", "ply_limit"
            break

        if board.turn == ai_color:
            _, move = search.search_root(board)
        else:
            move = stockfish.play(board, limit).move
        if move is None or move not in board.legal_moves:
            raise ValueError(f"Illegal or missing move at {board.fen()}")

        board.push(move)
        moves.append(move.uci())

    return {
        "result": result,
        "ai_result": ai_result,
        "termination": termination,
        "plies": len(moves),
        "moves_uci": " ".join(moves),
    }


def save_match(
    output_dir: Path,
    depth: int,
    records: list[dict[str, int | str]],
    metadata: dict[str, object],
) -> Path:
    """Publish the match CSV and settings together in a new run directory."""
    now = datetime.now(timezone.utc)
    run_id = f"{now:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    run_dir = output_dir / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".match-", dir=output_dir) as temporary_dir:
        staging = Path(temporary_dir)
        with (staging / f"match_d{depth}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        (staging / "meta.json").write_text(
            json.dumps(
                {"run_id": run_id, "created_at_utc": now.isoformat(), **metadata},
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            ) + "\n",
            encoding="utf-8",
        )
        staging.rename(run_dir)
    return run_dir.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stockfish", type=Path, help="Path to the Stockfish executable")
    parser.add_argument("--depth", type=int, default=3, help="Alpha-Beta search depth")
    parser.add_argument("--games", type=int, default=10, help="Even number of games")
    parser.add_argument("--elo", type=int, default=1350, help="Stockfish UCI_Elo setting")
    parser.add_argument("--stockfish-depth", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42, help="Seed for the opening order")
    parser.add_argument("--max-plies", type=int, help="Optional move limit for a short trial")
    parser.add_argument("--output-dir", type=Path, default=Path("results/stockfish"))
    args = parser.parse_args()

    if args.games < 2 or args.games % 2:
        parser.error("--games must be a positive even number")
    if min(args.depth, args.stockfish_depth, args.elo) < 1:
        parser.error("Search depths and Elo must be positive")
    if args.max_plies is not None and args.max_plies < 1:
        parser.error("--max-plies must be at least 1")

    openings = [position for position in get_fixed_positions() if position.phase == "opening"]
    Random(args.seed).shuffle(openings)
    stockfish_options = {
        "Threads": 1,
        "Hash": 16,
        "UCI_LimitStrength": True,
        "UCI_Elo": args.elo,
    }
    adapter = StockfishAdapter(args.stockfish, options=stockfish_options)
    search = _MeasuredSearch(args.depth, pruning=True)
    limit = chess.engine.Limit(depth=args.stockfish_depth)
    records: list[dict[str, int | str]] = []

    try:
        for index in range(args.games):
            pair = index // 2
            opening = openings[pair % len(openings)]
            ai_color = chess.WHITE if index % 2 == 0 else chess.BLACK
            ai_color_name = "white" if ai_color == chess.WHITE else "black"
            board = chess.Board(opening.fen)
            if not board.is_valid() or board.is_game_over():
                raise ValueError(f"Invalid starting position: {opening.position_id}")

            print(
                f"Game {index + 1}/{args.games}: {opening.position_id}, AI {ai_color_name}",
                flush=True,
            )
            # Use a fresh process for each game to reset Stockfish's search state.
            try:
                adapter.connect()
                stockfish_name = adapter.name
                game = play_game(
                    board,
                    ai_color=ai_color,
                    search=search,
                    stockfish=adapter,
                    limit=limit,
                    max_plies=args.max_plies,
                )
            finally:
                adapter.close()

            records.append(
                {
                    "game": index + 1,
                    "pair": pair + 1,
                    "opening_id": opening.position_id,
                    "start_fen": opening.fen,
                    "depth": args.depth,
                    "ai_color": ai_color_name,
                    **game,
                }
            )
            print(
                f"  {game['result']} ({game['ai_result']}, {game['termination']}, "
                f"{game['plies']} plies)",
                flush=True,
            )

        counts = Counter(record["ai_result"] for record in records)
        summary = {label: counts[label] for label in ("win", "draw", "loss", "unfinished")}
        run_dir = save_match(
            args.output_dir,
            args.depth,
            records,
            {
                "ai": {
                    "algorithm": "alphabeta",
                    "depth": args.depth,
                    "search_implementation": "backend.benchmark.compare_algos",
                    "evaluator": "engine.evaluation.MaterialPstEvaluator",
                    "alpha_beta_pruning": True,
                    "move_ordering": False,
                    "iterative_deepening": False,
                    "transposition_table": False,
                    "quiescence": False,
                },
                "stockfish": {
                    "name": stockfish_name,
                    "depth": args.stockfish_depth,
                    "options": stockfish_options,
                },
                "games": args.games,
                "seed": args.seed,
                "seed_scope": "opening_order",
                "opening_source": "fixed",
                "color_policy": "white_black_pairs",
                "claim_draw": True,
                "max_plies": args.max_plies,
                "python_version": platform.python_version(),
                "python_chess_version": chess.__version__,
                "summary": summary,
            },
        )
    except (StockfishUnavailableError, chess.engine.EngineError, OSError, ValueError) as error:
        parser.exit(1, f"Match error: {error}\n")

    print(f"Games: {len(records)}")
    print(
        f"AI wins: {summary['win']}, draws: {summary['draw']}, "
        f"losses: {summary['loss']}, unfinished: {summary['unfinished']}"
    )
    print(f"CSV: {run_dir / f'match_d{args.depth}.csv'}")
    print(f"Metadata: {run_dir / 'meta.json'}")


if __name__ == "__main__":
    main()
