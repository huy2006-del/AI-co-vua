"""Score saved benchmark moves against Stockfish at a fixed depth."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from statistics import fmean
from tempfile import TemporaryDirectory
from uuid import uuid4

import chess
import chess.engine

from .vs_stockfish import StockfishAdapter, StockfishUnavailableError


PHASES = ("opening", "middlegame", "endgame")
STOCKFISH_OPTIONS = {
    "Threads": 1,
    "Hash": 16,
    "UCI_LimitStrength": False,
    "Skill Level": 20,
}


@dataclass(frozen=True)
class BenchmarkMove:
    position_id: str
    phase: str
    fen: str
    move_uci: str


def read_benchmark_moves(
    path: Path, *, depth: int, algorithm: str, per_phase: int | None = None
) -> list[BenchmarkMove]:
    groups: dict[str, list[BenchmarkMove]] = {phase: [] for phase in PHASES}
    seen: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = {"position_id", "phase", "fen", "depth", "algorithm", "best_move"}
        if missing := columns.difference(reader.fieldnames or ()):
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")

        for row in reader:
            if row["depth"] != str(depth) or row["algorithm"] != algorithm:
                continue
            position_id, phase = row["position_id"], row["phase"]
            if phase not in groups or not all((position_id, row["fen"], row["best_move"])):
                raise ValueError(f"Incomplete benchmark record on CSV line {reader.line_num}")
            if position_id in seen:
                raise ValueError(f"Duplicate position at depth {depth}: {position_id}")
            seen.add(position_id)
            groups[phase].append(BenchmarkMove(position_id, phase, row["fen"], row["best_move"]))

    for phase, moves in groups.items():
        if len(moves) < (per_phase or 1):
            raise ValueError(
                f"Only {len(moves)} {phase} records for {algorithm} at depth {depth}"
            )
    return [move for moves in groups.values() for move in moves[:per_phase]]


def measure_move(
    stockfish: StockfishAdapter,
    board: chess.Board,
    move: chess.Move,
    limit: chess.engine.Limit,
) -> dict[str, str | int | None]:
    """Compare both moves from the perspective of the side to move."""
    if not board.is_valid() or board.is_game_over():
        raise ValueError("A valid position with a game in progress is required")
    if move not in board.legal_moves:
        raise ValueError(f"Illegal benchmark move: {move.uci()}")

    analysis = stockfish.analyse(board, limit)
    variation, position_score = analysis.get("pv"), analysis.get("score")
    if not variation or position_score is None:
        raise chess.engine.EngineError("Stockfish did not return a move and score")

    best_move = variation[0]
    same_move = move == best_move
    best_score = position_score.pov(board.turn)
    move_score = (
        best_score if same_move else stockfish.evaluate_move(board, move, limit).pov(board.turn)
    )
    best_cp, move_cp = best_score.score(), move_score.score()
    # Mate scores remain in the CSV but are excluded from the centipawn average.
    loss = None if best_cp is None or move_cp is None else max(0, best_cp - move_cp)
    return {
        "ai_move": move.uci(),
        "stockfish_move": best_move.uci(),
        "same_move": int(same_move),
        "stockfish_score": str(best_score),
        "ai_move_score": str(move_score),
        "stockfish_cp": best_cp,
        "ai_move_cp": move_cp,
        "cpl": loss,
    }


def summarize(records: list[dict[str, str | int | None]]) -> dict[str, dict[str, int | float | None]]:
    summary = {}
    for phase in PHASES:
        rows = [record for record in records if record["phase"] == phase]
        losses = [row["cpl"] for row in rows if isinstance(row["cpl"], int)]
        matches = sum(row["same_move"] == 1 for row in rows)
        summary[phase] = {
            "position_count": len(rows),
            "cpl_count": len(losses),
            "mate_count": len(rows) - len(losses),
            "mean_cpl": fmean(losses) if losses else None,
            "same_move_count": matches,
            "same_move_rate": matches / len(rows) if rows else None,
        }
    return summary


def save_results(
    output_dir: Path,
    depth: int,
    records: list[dict[str, str | int | None]],
    metadata: dict[str, object],
) -> Path:
    now = datetime.now(timezone.utc)
    run_dir = output_dir / f"{now:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    output_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".cpl-", dir=output_dir) as temporary_dir:
        staging = Path(temporary_dir)
        with (staging / f"cpl_d{depth}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        (staging / "meta.json").write_text(
            json.dumps(
                {"created_at_utc": now.isoformat(), **metadata},
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            ) + "\n",
            encoding="utf-8",
        )
        staging.rename(run_dir)
    return run_dir.resolve()


def positive_int(value: str) -> int:
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="Week 1 compare_algos.csv")
    parser.add_argument("--depth", type=positive_int, default=3, help="Saved AI search depth")
    parser.add_argument("--algorithm", choices=("minimax", "alphabeta"), default="alphabeta")
    parser.add_argument("--stockfish", type=Path, help="Path to the Stockfish executable")
    parser.add_argument("--stockfish-depth", type=positive_int, default=10)
    parser.add_argument("--per-phase", type=positive_int, help="Limit positions per phase")
    parser.add_argument("--output-dir", type=Path, default=Path("results/stockfish"))
    args = parser.parse_args()

    adapter = StockfishAdapter(args.stockfish, options=STOCKFISH_OPTIONS)
    try:
        moves = read_benchmark_moves(
            args.csv, depth=args.depth, algorithm=args.algorithm, per_phase=args.per_phase
        )
        source_meta_path = args.csv.with_name("meta.json")
        source_meta = (
            json.loads(source_meta_path.read_text(encoding="utf-8"))
            if source_meta_path.is_file()
            else {}
        )
        if not isinstance(source_meta, dict):
            raise ValueError("The input meta.json must contain a JSON object")
        limit = chess.engine.Limit(depth=args.stockfish_depth)

        adapter.connect()
        print(
            f"Analysing {len(moves)} positions at AI depth {args.depth} "
            f"and Stockfish depth {args.stockfish_depth}.",
            flush=True,
        )
        records = []
        for sample in moves:
            try:
                board = chess.Board(sample.fen)
                move = board.parse_uci(sample.move_uci)
                measured = measure_move(adapter, board, move, limit)
            except (ValueError, chess.engine.EngineError) as error:
                raise ValueError(f"{sample.position_id}: {error}") from error
            records.append(
                {
                    "position_id": sample.position_id,
                    "phase": sample.phase,
                    "fen": sample.fen,
                    "algorithm": args.algorithm,
                    "depth": args.depth,
                    "stockfish_depth": args.stockfish_depth,
                    **measured,
                }
            )

        summary = summarize(records)
        run_dir = save_results(
            args.output_dir,
            args.depth,
            records,
            {
                "input_csv": args.csv.name,
                "input_csv_sha256": sha256(args.csv.read_bytes()).hexdigest(),
                "source_run_id": source_meta.get("run_id"),
                "source_position_source": source_meta.get("position_source"),
                "source_config": source_meta.get("config"),
                "algorithm": args.algorithm,
                "depth": args.depth,
                "per_phase": args.per_phase,
                "position_count": len(records),
                "score_perspective": "side_to_move",
                "mate_scores_excluded_from_cpl": True,
                "stockfish": {
                    "name": adapter.name,
                    "depth": args.stockfish_depth,
                    "options": STOCKFISH_OPTIONS,
                },
                "summary_by_phase": summary,
            },
        )
    except (StockfishUnavailableError, chess.engine.EngineError, OSError, ValueError) as error:
        parser.exit(1, f"CPL error: {error}\n")
    finally:
        adapter.close()

    for phase, stats in summary.items():
        mean = stats["mean_cpl"]
        mean_label = "n/a" if mean is None else f"{mean:.2f} cp"
        print(
            f"{phase}: mean CPL {mean_label} ({stats['cpl_count']}/{stats['position_count']}), "
            f"same move {stats['same_move_count']}/{stats['position_count']}"
        )
    print(f"CSV: {run_dir / f'cpl_d{args.depth}.csv'}")
    print(f"Metadata: {run_dir / 'meta.json'}")


if __name__ == "__main__":
    main()
