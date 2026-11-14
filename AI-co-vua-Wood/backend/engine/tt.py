"""Bounded transposition table keyed by python-chess Polyglot Zobrist hashes."""
from dataclasses import dataclass
from enum import Enum
import chess


class TTFlag(str, Enum):
    EXACT = "EXACT"
    LOWER = "LOWER"
    UPPER = "UPPER"

@dataclass(slots=True)
class TTEntry:
    depth: int
    score: int
    flag: TTFlag
    best_move: chess.Move | None

class TranspositionTable:
    def __init__(self, max_size: int = 200_000) -> None:
        self.max_size = max_size
        self.table: dict[int, TTEntry] = {}

    def get(self, key: int) -> TTEntry | None:
        return self.table.get(key)

    def put(self, key: int, entry: TTEntry) -> None:
        old = self.table.get(key)
        if old is not None and old.depth > entry.depth:
            return
        if len(self.table) >= self.max_size and key not in self.table:
            self.table.clear()
        self.table[key] = entry

    def clear(self) -> None:
        self.table.clear()

