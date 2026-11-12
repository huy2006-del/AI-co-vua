"""Write benchmark records and the settings needed to reproduce a run."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
from tempfile import mkdtemp
from typing import Iterable
from uuid import uuid4


@dataclass(frozen=True)
class ExperimentConfig:
    per_phase: int = 10
    max_depth: int = 4
    seed: int | None = None
    workers: int = 1
    algorithms: tuple[str, ...] = ("minimax", "alphabeta")
    search_options: dict[str, object] = field(default_factory=dict)
    stockfish_options: dict[str, object] | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("per_phase", self.per_phase),
            ("max_depth", self.max_depth),
            ("workers", self.workers),
        ):
            if value < 1:
                raise ValueError(f"{name} must be at least 1")


@dataclass(frozen=True)
class ExperimentRecord:
    """One algorithm's result for a position at a given depth."""

    position_id: str
    phase: str
    fen: str
    depth: int
    algorithm: str
    score: int | float
    nodes: int
    time_ms: float
    best_move: str | None = None
    cutoffs: int | None = None
class ResultStore:
    def __init__(self, output_dir: str | Path = "results/benchmark") -> None:
        self.output_dir = Path(output_dir)

    def save(
        self,
        config: ExperimentConfig,
        records: Iterable[ExperimentRecord],
    ) -> Path:
        """Save both files in a new run directory and return its path."""
        rows = list(records)
        if not rows:
            raise ValueError("The benchmark produced no records")

        created_at = datetime.now(timezone.utc)
        run_id = f"{created_at:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
        run_dir = self.output_dir / run_id
        metadata = {
            "run_id": run_id,
            "created_at_utc": created_at.isoformat(),
            "position_source": "fixed" if config.seed is None else "generated",
            "config": asdict(config),
            "position_count": len({row.position_id for row in rows}),
            "record_count": len(rows),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        staging_dir = Path(mkdtemp(prefix=".run-", dir=self.output_dir))
        try:
            fieldnames = [item.name for item in fields(ExperimentRecord)]
            with (staging_dir / "compare_algos.csv").open(
                "w", encoding="utf-8", newline=""
            ) as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(asdict(row) for row in rows)

            with (staging_dir / "meta.json").open("w", encoding="utf-8") as meta_file:
                json.dump(metadata, meta_file, ensure_ascii=False, indent=2, allow_nan=False)
                meta_file.write("\n")

            staging_dir.rename(run_dir)
        finally:
            shutil.rmtree(staging_dir, ignore_errors=True)

        return run_dir
