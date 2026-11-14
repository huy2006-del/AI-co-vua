"""Background search worker. Search receives a board copy to avoid GUI races."""
from threading import Event, Thread
from enum import Enum
import chess
from .api import AlgorithmFactory, SearchResult
from .evaluation import Evaluator
from .options import SearchOptions


class SearchWorker:
    def __init__(
        self,
        algorithm: str | Enum = "alphabeta",
        depth: int = 3,
        evaluator: Evaluator | None = None,
        options: SearchOptions | None = None,
    ) -> None:
        self.algorithm: str | Enum = algorithm
        self.depth: int = depth
        self.evaluator: Evaluator | None = evaluator
        self.options: SearchOptions | None = options
        self._thread: Thread | None = None
        self._cancel = Event()
        self._result: SearchResult | None = None
        self._error: BaseException | None = None

    def start(self, board: chess.Board) -> None:
        if self._thread and self._thread.is_alive():
            raise RuntimeError("SearchWorker đang chạy")
        self._cancel.clear()
        self._result = self._error = None
        position = board.copy(stack=True)

        def run() -> None:
            try:
                algorithm = AlgorithmFactory.create(self.algorithm, self.evaluator, self.options)
                self._result = algorithm.search(position, self.depth, evaluator=self.evaluator,
                                                options=self.options, cancel_event=self._cancel)
            except BaseException as exc:
                self._error = exc

        self._thread = Thread(target=run, name="chess-search", daemon=True)
        self._thread.start()

    def is_done(self) -> bool:
        return self._thread is None or not self._thread.is_alive()

    def get_result(self, timeout: float | None = None) -> SearchResult | None:
        if self._thread:
            self._thread.join(timeout)
        if not self.is_done():
            return None
        if self._error:
            raise self._error
        return self._result

    def cancel(self) -> None:
        self._cancel.set()

