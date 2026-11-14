"""Plot benchmark speed, node reduction, and Stockfish CPL by search depth."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter


ALGORITHM_LABELS = {"minimax": "Minimax", "alphabeta": "Alpha-Beta"}
PHASE_LABELS = {
    "opening": "Khai cuộc",
    "middlegame": "Trung cuộc",
    "endgame": "Tàn cuộc",
}
POSITION_COLUMNS = {"position_id": str, "phase": str, "fen": str, "depth": int}
PLOT_STYLES = (("#245580", "o"), ("#087F71", "s"), ("#A4571D", "^"))


def read_records(
    path: Path, column_types: dict[str, type], *, nullable: tuple[str, ...] = ()
) -> pd.DataFrame:
    records = pd.read_csv(path, usecols=list(column_types), dtype=column_types)
    required = [column for column in column_types if column not in nullable]
    if records.empty or records[required].isna().any().any():
        raise ValueError(f"{path.name} has empty or incomplete records")
    if (records["depth"] < 1).any():
        raise ValueError(f"{path.name} has an invalid AI depth")
    return records


def require_same_positions(records: pd.DataFrame) -> None:
    depth_count = records["depth"].nunique()
    depths_per_position = records.groupby(["position_id", "phase", "fen"])["depth"].nunique()
    if (depths_per_position != depth_count).any():
        raise ValueError("Use the same positions at every AI depth")


def compare_by_depth(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    records = read_records(
        path, {**POSITION_COLUMNS, "algorithm": str, "nodes": int, "time_ms": float}
    )
    if set(records["algorithm"]) != set(ALGORITHM_LABELS):
        raise ValueError("The comparison CSV must contain Minimax and Alpha-Beta")
    if (records["nodes"] < 1).any() or not records["time_ms"].between(
        0, float("inf"), inclusive="left"
    ).all():
        raise ValueError("The comparison CSV has invalid node counts or times")

    require_same_positions(records)
    pairs = records.pivot(
        index=["depth", "position_id", "phase", "fen"],
        columns="algorithm",
        values=["nodes", "time_ms"],
    )
    if pairs.isna().any().any():
        raise ValueError("Both algorithms must have a result for each position and depth")

    means = pairs.groupby(level="depth").mean()
    nodes = means["nodes"]
    reduction = 100 * (nodes["minimax"] - nodes["alphabeta"]) / nodes["minimax"]
    return (
        nodes[list(ALGORITHM_LABELS)].rename(columns=ALGORITHM_LABELS),
        means["time_ms"][list(ALGORITHM_LABELS)].rename(columns=ALGORITHM_LABELS),
        reduction.to_frame("Alpha-Beta"),
    )


def cpl_by_depth(paths: list[Path]) -> tuple[pd.DataFrame, str, int]:
    column_types = {
        **POSITION_COLUMNS,
        "algorithm": str,
        "stockfish_depth": int,
        "cpl": float,
    }
    records = pd.concat(
        [read_records(path, column_types, nullable=("cpl",)) for path in paths],
        ignore_index=True,
    )
    algorithms = records["algorithm"].unique()
    stockfish_depths = records["stockfish_depth"].unique()
    if len(algorithms) != 1 or algorithms[0] not in ALGORITHM_LABELS:
        raise ValueError("Use CPL CSVs for the same AI algorithm")
    if len(stockfish_depths) != 1 or stockfish_depths[0] < 1:
        raise ValueError("Use CPL CSVs with the same Stockfish analysis depth")
    if records.duplicated(["position_id", "depth"]).any():
        raise ValueError("A position appears more than once at the same CPL depth")
    if not set(records["phase"]).issubset(PHASE_LABELS):
        raise ValueError("The CPL CSVs contain an unknown game phase")
    if not records["cpl"].dropna().between(0, float("inf"), inclusive="left").all():
        raise ValueError("The CPL CSVs contain an invalid centipawn loss")

    require_same_positions(records)
    means = records.groupby(["depth", "phase"])["cpl"].mean().unstack()
    means = means.reindex(columns=list(PHASE_LABELS)).rename(columns=PHASE_LABELS)
    return means, ALGORITHM_LABELS[algorithms[0]], int(stockfish_depths[0])


def save_plot(
    path: Path,
    data: pd.DataFrame,
    *,
    title: str,
    ylabel: str,
    percent: bool = False,
) -> None:
    figure = Figure(figsize=(8.4, 4.8), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots()

    for label, (color, marker) in zip(data.columns, PLOT_STYLES):
        axes.plot(
            data.index, data[label], label=label, color=color, marker=marker,
            linewidth=2.2, markersize=6,
        )

    axes.set_title(title, loc="left", fontsize=15, fontweight="bold", pad=14)
    axes.set_xlabel("Độ sâu tìm kiếm của AI")
    axes.set_ylabel(ylabel)
    axes.set_xticks(data.index)
    axes.spines[["top", "right"]].set_visible(False)
    axes.set_axisbelow(True)
    axes.grid(axis="y", color="#DCE4ED")
    if data.min().min() >= 0:
        axes.set_ylim(bottom=0)
    if percent:
        axes.yaxis.set_major_formatter(PercentFormatter(xmax=100))
    if len(data.columns) > 1:
        axes.legend(frameon=False)
    if data.isna().all().all():
        axes.text(
            0.5, 0.5, "Không có điểm centipawn để tính CPL",
            ha="center", va="center", transform=axes.transAxes,
        )
    figure.savefig(path, dpi=160)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare", type=Path, required=True, help="Path to compare_algos.csv")
    parser.add_argument("--cpl", type=Path, nargs="+", required=True, help="Paths to cpl_d*.csv")
    parser.add_argument("--output-dir", type=Path, default=Path("results/plots"))
    args = parser.parse_args()

    try:
        nodes, times, reduction = compare_by_depth(args.compare)
        cpl, algorithm, stockfish_depth = cpl_by_depth(args.cpl)
        charts = (
            ("nodes_by_depth.png", nodes, "Số nút đã duyệt", "Số nút trung bình mỗi thế"),
            ("time_by_depth.png", times, "Thời gian tìm kiếm", "Thời gian trung bình mỗi thế (ms)"),
            ("node_reduction_by_depth.png", reduction, "Số nút giảm nhờ Alpha-Beta", "Giảm so với Minimax"),
            ("cpl_by_depth.png", cpl, f"CPL của {algorithm} với Stockfish sâu {stockfish_depth}", "CPL trung bình (cp)"),
        )

        args.output_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        run_dir = args.output_dir / f"{now:%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
        with TemporaryDirectory(prefix=".plots-", dir=args.output_dir) as temporary_dir:
            staging = Path(temporary_dir)
            for filename, data, title, ylabel in charts:
                save_plot(
                    staging / filename, data, title=title, ylabel=ylabel,
                    percent=filename == "node_reduction_by_depth.png",
                )
            staging.rename(run_dir)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Plot error: {error}\n")

    print(f"Plots: {run_dir.resolve()}")
    for filename, _, _, _ in charts:
        print(f"  {filename}")


if __name__ == "__main__":
    main()

