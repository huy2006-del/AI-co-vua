"""Connect benchmark code to a local Stockfish UCI process."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
import os
from pathlib import Path
import shutil

import chess
import chess.engine


class StockfishUnavailableError(RuntimeError):
    """Stockfish could not be located or started."""


class StockfishAdapter:
    """Manage one Stockfish process for synchronous benchmark calls."""

    def __init__(
        self,
        executable: str | Path | None = None,
        *,
        options: Mapping[str, str | int | bool | None] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.executable = executable
        self.options = dict(options or {})
        self.timeout = timeout
        self._engine: chess.engine.SimpleEngine | None = None

    def _resolve_executable(self) -> str:
        configured = self.executable
        if configured is None:
            configured = os.environ.get("STOCKFISH_PATH") or None

        if configured is not None:
            path = Path(configured).expanduser()
            if not path.is_file():
                raise StockfishUnavailableError(
                    f"Stockfish executable not found at {path}."
                )
            return str(path.resolve())

        command = shutil.which("stockfish")
        if command is None:
            raise StockfishUnavailableError(
                "Set STOCKFISH_PATH or pass --stockfish with the executable path."
            )
        return command

    def connect(self) -> StockfishAdapter:
        """Start Stockfish and apply the configured UCI options."""
        if self._engine is not None:
            return self

        try:
            command = self._resolve_executable()
            engine = chess.engine.SimpleEngine.popen_uci(command, timeout=self.timeout)
        except (OSError, chess.engine.EngineError) as error:
            raise StockfishUnavailableError(f"Could not start Stockfish. {error}") from error

        try:
            if self.options:
                engine.configure(self.options)
        except BaseException:
            engine.close()
            raise

        self._engine = engine
        return self

    def _connected_engine(self) -> chess.engine.SimpleEngine:
        if self._engine is None:
            raise StockfishUnavailableError("Call connect() to start Stockfish.")
        return self._engine

    @property
    def name(self) -> str:
        return self._connected_engine().id.get("name", "Stockfish")

    def analyse(
        self,
        board: chess.Board,
        limit: chess.engine.Limit,
        *,
        root_moves: Iterable[chess.Move] | None = None,
    ) -> chess.engine.InfoDict:
        return self._connected_engine().analyse(board, limit, root_moves=root_moves)

    def evaluate_move(
        self, board: chess.Board, move: chess.Move, limit: chess.engine.Limit
    ) -> chess.engine.PovScore:
        """Evaluate one legal move from the current position."""
        if move not in board.legal_moves:
            raise ValueError(f"Illegal move for this position: {move.uci()}")

        score = self.analyse(board, limit, root_moves=[move]).get("score")
        if score is None:
            raise chess.engine.EngineError("Stockfish did not return a score for the move.")
        return score

    def play(self, board: chess.Board, limit: chess.engine.Limit) -> chess.engine.PlayResult:
        return self._connected_engine().play(board, limit)

    def close(self) -> None:
        """Quit the process and release its transport."""
        engine, self._engine = self._engine, None
        if engine is None:
            return

        try:
            engine.quit()
        except (chess.engine.EngineTerminatedError, OSError):
            pass
        finally:
            engine.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Test the Stockfish connection.")
    parser.add_argument("--stockfish", type=Path, help="Path to the Stockfish executable.")
    parser.add_argument("--depth", type=int, default=6)
    args = parser.parse_args()
    if args.depth < 1:
        parser.error("--depth must be at least 1")

    board = chess.Board()
    limit = chess.engine.Limit(depth=args.depth)
    adapter = StockfishAdapter(args.stockfish)
    try:
        adapter.connect()
        name = adapter.name
        position_score = adapter.analyse(board, limit).get("score")
        move = adapter.play(board, limit).move
        if move is None or position_score is None:
            raise chess.engine.EngineError("Stockfish did not return a move and a score.")
        move_score = adapter.evaluate_move(board, move, limit)
    except StockfishUnavailableError as error:
        parser.exit(1, f"Stockfish unavailable. {error}\n")
    except (chess.engine.EngineError, OSError) as error:
        parser.exit(1, f"Stockfish error. {error}\n")
    finally:
        adapter.close()

    print(f"Stockfish OK: {name}")
    print(f"Best move: {move.uci()}")
    print(f"Position score: {position_score.pov(board.turn)}")
    print(f"Move score: {move_score.pov(board.turn)}")


if __name__ == "__main__":
    main()
