"""Stable search API consumed by the game controller and benchmarks."""
from dataclasses import dataclass
from enum import Enum
from threading import Event
import chess
from .evaluation import Evaluator, MaterialEvaluator, MaterialPstEvaluator, DEFAULT_EVALUATOR
from .options import SearchOptions
from .stats import SearchStats

ALGOS: tuple[str, ...] = ("minimax", "alphabeta", "alphabeta_ordered")
EVALUATIONS: tuple[str, ...] = ("material", "position")


def evaluator_for(name: str | None) -> Evaluator:
    if name in (None, "position", "material_pst_v1", "default"):
        return DEFAULT_EVALUATOR
    if name == "material":
        return MaterialEvaluator()
    raise ValueError(f"Hàm đánh giá không hỗ trợ: {name}")

@dataclass(slots=True)
class SearchResult:
    move: chess.Move | None
    score: int
    depth: int
    stats: SearchStats

    @property
    def best_move(self) -> chess.Move | None:
        return self.move


class SearchAlgorithm:
    def search(
        self,
        board: chess.Board,
        depth: int,
        evaluator: Evaluator | None = None,
        options: SearchOptions | None = None,
        cancel_event: Event | None = None,
    ) -> SearchResult:
        raise NotImplementedError


class AlgorithmFactory:
    @staticmethod
    def create(
        kind: str | Enum,
        evaluator: Evaluator | None = None,
        options: SearchOptions | None = None,
    ) -> SearchAlgorithm:
        from .alphabeta import AlphaBetaSearch
        from .minimax import MinimaxSearch
        key = getattr(kind, "value", kind)
        key = str(key).lower().replace("-", "_")
        if key in {"minimax", "minimaxsearch"}:
            return MinimaxSearch(evaluator, options)
        if key in {"alphabeta", "alpha_beta", "alphabeta_ordered", "alpha_beta_search"}:
            return AlphaBetaSearch(evaluator, options)
        raise ValueError(f"Thuật toán không hỗ trợ: {kind}")


def search(
    board: chess.Board,
    algo: str | Enum = "alphabeta",
    depth: int = 3,
    evaluator: Evaluator | None = None,
    options: SearchOptions | None = None,
    cancel_event: Event | None = None,
    evaluation: str | None = None,
    time_limit: float | None = None,
    node_limit: int | None = None,
) -> SearchResult:
    evaluator = evaluator or evaluator_for(evaluation)
    if options is None:
        options = SearchOptions(time_limit=time_limit, node_limit=node_limit)
    elif time_limit is not None or node_limit is not None:
        from dataclasses import replace
        options = replace(options,
                          time_limit=time_limit if time_limit is not None else options.time_limit,
                          node_limit=node_limit if node_limit is not None else options.node_limit)
    return AlgorithmFactory.create(algo, evaluator, options).search(
        board, depth, evaluator=evaluator, options=options, cancel_event=cancel_event)

