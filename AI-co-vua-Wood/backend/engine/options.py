"""Search configuration shared by the chess engine."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SearchOptions:
    ordering: bool = True
    iterative_deepening: bool = False
    transposition_table: bool = False
    quiescence: bool = False
    time_limit: float | None = None
    max_quiescence_depth: int = 8
    tt_size: int = 200_000
    check_interval: int = 256

    def __post_init__(self) -> None:
        if self.time_limit is not None and self.time_limit <= 0:
            raise ValueError("time_limit phải lớn hơn 0")
        if self.max_quiescence_depth < 0 or self.tt_size < 1 or self.check_interval < 1:
            raise ValueError("Giới hạn tìm kiếm không hợp lệ")

    @classmethod
    def preset(cls, name: str, **kwargs: Any) -> "SearchOptions":
        presets = {
            "BASE": dict(ordering=False),
            "+ORDERING": dict(ordering=True),
            "+ID": dict(ordering=True, iterative_deepening=True),
            "+TT": dict(ordering=True, transposition_table=True),
            "+QS": dict(ordering=True, quiescence=True),
            "ALL": dict(ordering=True, iterative_deepening=True,
                        transposition_table=True, quiescence=True),
        }
        try:
            return cls(**(presets[name.upper()] | kwargs))
        except KeyError as exc:
            raise ValueError(f"Preset không hợp lệ: {name}") from exc


