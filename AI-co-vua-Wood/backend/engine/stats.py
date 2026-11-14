"""Counters and timings collected during one search."""
from dataclasses import dataclass, field
from threading import Event
from time import perf_counter
import chess
from .options import SearchOptions
from .tt import TTEntry


@dataclass(slots=True)
class SearchStats:
    nodes: int = 0
    cutoffs: int = 0
    tt_hits: int = 0
    expanded_nodes: int = 0
    elapsed: float = 0.0
    depth_reached: int = 0
    nodes_per_depth: list[int] = field(default_factory=list)
    cutoffs_per_depth: list[int] = field(default_factory=list)

    @property
    def avg_branching(self) -> float:
        return (self.nodes - 1) / self.expanded_nodes if self.expanded_nodes else 0.0


class SearchContext:
    """Mutable per-search state, including a cooperative cancellation/deadline check."""
    def __init__(self, options: SearchOptions, cancel_event: Event | None = None) -> None:
        self.options, self.cancel_event = options, cancel_event
        self.stats = SearchStats()
        self.started = perf_counter()
        self.deadline: float | None = self.started + options.time_limit if options.time_limit else None
        self.root_best: chess.Move | None = None
        self.completed_best: chess.Move | None = None
        self.completed_score: int = 0
        self.pv_move: chess.Move | None = None
        self.tt: dict[int, TTEntry] = {}

    def visit(self, ply: int) -> None:
        self.stats.nodes += 1
        while len(self.stats.nodes_per_depth) <= ply:
            self.stats.nodes_per_depth.append(0)
            self.stats.cutoffs_per_depth.append(0)
        self.stats.nodes_per_depth[ply] += 1
        if self.stats.nodes % self.options.check_interval == 0:
            if self.cancel_event is not None and self.cancel_event.is_set():
                raise SearchStopped
            if self.deadline is not None and perf_counter() >= self.deadline:
                raise SearchStopped

    def finish(self) -> None:
        self.stats.elapsed = perf_counter() - self.started


class SearchStopped(Exception):
    """Internal signal for time limit or cancellation."""

