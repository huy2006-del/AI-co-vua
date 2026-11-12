"""Options for games and benchmark runs."""
import chess

from backend.benchmark.experiments import POSITIONS
from backend.engine.api import ALGOS, EVALUATIONS

GAME_MODES = {"ai": "Người đấu AI", "local": "Hai người", "engines": "Engine đấu engine"}
NAMES = {"minimax": "Minimax", "alphabeta": "Alpha-Beta",
         "alphabeta_ordered": "Alpha-Beta + sắp xếp", "stockfish": "Stockfish",
         "material": "Vật chất", "position": "Vật chất + vị trí",
         True: "Trắng", False: "Đen"}
MATCH_OPTIONS = {
    "mode": ("Chế độ", tuple(GAME_MODES)),
    "human": ("Màu quân", (chess.WHITE, chess.BLACK)),
    "algorithm": ("Engine chính / Trắng", ALGOS + ("stockfish",)),
    "opponent": ("Engine Đen", ALGOS + ("stockfish",)),
    "depth": ("Độ sâu", (1, 2, 3, 4)),
    "evaluation": ("Hàm đánh giá", EVALUATIONS),
    "seconds": ("Giây mỗi nước", (.5, 1., 2., 4.)),
}
EXPERIMENT_OPTIONS = {
    "mode": ("Thực nghiệm", ("Minimax / Alpha-Beta", "Cấu hình AI", "Stockfish")),
    "position": ("Thế cờ", ("Cả 3 thế mẫu", *POSITIONS, "Ván hiện tại", "FEN tùy chỉnh")),
    "algorithm": ("Thuật toán AI", ALGOS),
    "depth": ("Độ sâu tối đa", (1, 2, 3, 4)),
    "evaluation": ("Hàm đánh giá", EVALUATIONS),
    "seconds": ("Giây mỗi lượt chạy", (.5, 1., 2., 4., 8.)),
    "nodes": ("Giới hạn nút", (1000, 5000, 20000, 100000)),
}


def option_text(key, value):
    if key == "mode" and value in GAME_MODES:
        return GAME_MODES[value]
    if key in ("depth", "seconds", "nodes"):
        return str(value)
    return NAMES.get(value, str(value))
