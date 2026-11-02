# Chess AI – Minimax vs Alpha-Beta (đối chiếu Stockfish)

## Cài đặt
```
pip install -r requirements.txt
# Cài Stockfish rồi: export STOCKFISH_PATH=/duong/dan/stockfish   (Windows: set STOCKFISH_PATH=...)
```

## Chạy
| Việc | Lệnh |
|---|---|
| GUI người vs máy | `python -m gui.app --depth 3` |
| Chơi bằng dòng lệnh | `python cli.py --depth 3` |
| Kiểm thử tính đúng | `python -m pytest -q` |
| Thực nghiệm A (Minimax vs Alpha-Beta) | `python -m benchmark.compare_algos --per-phase 10 --max-depth 4` |
| Thực nghiệm B1 (centipawn loss) | `python -m benchmark.vs_stockfish cpl --depth 3 --n 30` |
| Thực nghiệm B2 (đấu Stockfish) | `python -m benchmark.vs_stockfish match --depth 3 --games 10 --elo 1350` |
| Vẽ biểu đồ | `python -m benchmark.plots` |

## Kiến trúc
```
GUI/CLI/Benchmark  ──►  engine.api.search(board, algo, depth) ──► SearchResult
                                   │
        ┌──────────────────────────┼───────────────────────────┐
   minimax.py              alphabeta.py (+ordering.py)     evaluation.py
```
Quy ước: điểm luôn theo góc nhìn TRẮNG; Trắng maximize, Đen minimize.

## Phân công & TODO
- **A – Engine** (`engine/`): cải thiện `evaluation.py`; iterative deepening, transposition table, quiescence trong `alphabeta.py`.
- **B – Thực nghiệm** (`benchmark/`): chạy thực nghiệm, mở rộng `plots.py`, phân tích.
- **C – GUI/tài liệu** (`gui/`, `report/`): hộp thoại phong cấp, chọn màu, lịch sử nước đi, báo cáo, slide.
