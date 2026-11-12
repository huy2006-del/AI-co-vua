"""Compare plain Minimax and Alpha-Beta on matched chess positions."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from functools import partial
from math import inf
import multiprocessing
from pathlib import Path
from time import perf_counter_ns

import chess

from engine.evaluation import MaterialPstEvaluator

from .positions import Position, generate_positions, get_fixed_positions
from .store import ExperimentConfig, ExperimentRecord, ResultStore


class _MeasuredSearch:
    """Run the same search with or without Alpha-Beta pruning."""

    def __init__(self, depth: int, *, pruning: bool) -> None:
        self.depth = depth
        self.evaluator = MaterialPstEvaluator()
        self.pruning = pruning
        self.nodes = 0
        self.cutoffs = 0

    def search_root(self, board: chess.Board) -> tuple[float, chess.Move | None]:
        self.nodes = 0
        self.cutoffs = 0
        return self._visit(board, self.depth, -inf, inf)

    def _visit(
        self,
        board: chess.Board,
        depth: int,
        alpha: float,
        beta: float,
    ) -> tuple[float, chess.Move | None]:
        self.nodes += 1
        if depth == 0 or board.is_game_over():
            return self.evaluator.evaluate(board), None

        maximizing = board.turn == chess.WHITE
        best_score = -inf if maximizing else inf
        best_move = None

        for move in board.legal_moves:
            board.push(move)
            try:
                score, _ = self._visit(board, depth - 1, alpha, beta)
            finally:
                board.pop()

            better = score > best_score if maximizing else score < best_score
            if best_move is None or better:
                best_score, best_move = score, move

            if self.pruning:
                if maximizing:
                    alpha = max(alpha, best_score)
                else:
                    beta = min(beta, best_score)
                if alpha >= beta:
                    self.cutoffs += 1
                    break

        return best_score, best_move


def _compare_position(
    position: Position, *, max_depth: int, algorithms: tuple[str, ...]
) -> list[ExperimentRecord]:
    records = []
    for depth in range(1, max_depth + 1):
        for algorithm in algorithms:
            pruning = algorithm == "alphabeta"
            board = chess.Board(position.fen)
            search = _MeasuredSearch(depth, pruning=pruning)
            started = perf_counter_ns()
            score, best_move = search.search_root(board)
            time_ms = (perf_counter_ns() - started) / 1_000_000

            records.append(
                ExperimentRecord(
                    position_id=position.position_id,
                    phase=position.phase,
                    fen=position.fen,
                    depth=depth,
                    algorithm=algorithm,
                    score=score,
                    nodes=search.nodes,
                    time_ms=time_ms,
                    best_move=best_move.uci() if best_move is not None else None,
                    cutoffs=search.cutoffs,
                )
            )
    return records


class AlgorithmComparison:
    def __init__(self, config: ExperimentConfig) -> None:
        algorithms = set(config.algorithms)
        if (
            not algorithms
            or algorithms - {"minimax", "alphabeta"}
            or len(algorithms) != len(config.algorithms)
        ):
            raise ValueError("algorithms must be unique entries from minimax, alphabeta")

        self.config = replace(
            config,
            search_options={
                "search_implementation": "backend.benchmark.compare_algos",
                "evaluator": "engine.evaluation.MaterialPstEvaluator",
                "score_perspective": "white",
                "alpha_beta_pruning": {"minimax": False, "alphabeta": True},
                "move_ordering": False,
                "iterative_deepening": False,
                "transposition_table": False,
                "quiescence": False,
                "time_limit": None,
                "node_count_includes_root": True,
            },
        )

    def run(self) -> list[ExperimentRecord]:
        config = self.config
        if config.seed is None:
            positions = get_fixed_positions(config.per_phase)
        else:
            positions = generate_positions(config.per_phase, seed=config.seed)

        compare = partial(
            _compare_position, max_depth=config.max_depth, algorithms=config.algorithms
        )
        if config.workers == 1:
            return [record for position in positions for record in compare(position)]

        # Keep both algorithms for a position in one worker process.
        with ProcessPoolExecutor(
            max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            return [record for batch in pool.map(compare, positions) for record in batch]


def main() -> None:
    defaults = ExperimentConfig()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-phase", type=int, default=defaults.per_phase)
    parser.add_argument("--max-depth", type=int, default=defaults.max_depth)
    parser.add_argument("--workers", type=int, default=defaults.workers)
    parser.add_argument("--seed", type=int, help="Use generated positions with this seed.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/benchmark"))
    args = parser.parse_args()

    try:
        comparison = AlgorithmComparison(
            ExperimentConfig(
                per_phase=args.per_phase,
                max_depth=args.max_depth,
                seed=args.seed,
                workers=args.workers,
            )
        )
        print(
            f"Benchmarking {3 * args.per_phase} positions at depths 1-{args.max_depth} "
            f"with {args.workers} worker(s).",
            flush=True,
        )
        records = comparison.run()
        run_dir = ResultStore(args.output_dir).save(comparison.config, records).resolve()
    except ValueError as error:
        parser.error(str(error))

    print(f"Positions: {len({record.position_id for record in records})}")
    print(f"Records: {len(records)}")
    print(f"CSV: {run_dir / 'compare_algos.csv'}")
    print(f"Metadata: {run_dir / 'meta.json'}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

