"""Cấu hình chung của dự án. Chỉnh ở đây, đừng rải hằng số khắp nơi.

Người phụ trách: Người 1 (Trưởng nhóm) giữ file này; ai cần đổi thì báo cả nhóm.
"""
import os

# --- Server / demo -----------------------------------------------------------
# TẠM THỜI: số này chỉ để server không bị treo. Con số thật phải lấy từ kết quả
# TN1 (benchmark) trên máy của nhóm rồi cập nhật lại ở đây.
MAX_DEPTH = int(os.environ.get("MAX_DEPTH", 4))

# --- Stockfish (chỉ dùng ở experiments/, không cần cho demo web) -------------
# Đặt đường dẫn bằng biến môi trường STOCKFISH_PATH, ví dụ:
#   Windows : set STOCKFISH_PATH=C:\tools\stockfish\stockfish.exe
#   Linux   : export STOCKFISH_PATH=/usr/games/stockfish
STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH", "stockfish")

# Cấu hình Stockfish dùng trong thí nghiệm. PHẢI ghi các giá trị này vào báo cáo.
STOCKFISH_DEPTH = 12          # độ sâu Stockfish khi chấm điểm nước đi (nhóm tự chọn)
STOCKFISH_MULTIPV = 3         # top-k dùng cho thước đo "nằm trong top-k"

# --- Thí nghiệm --------------------------------------------------------------
SEED = 2024                   # seed cố định để sinh thế cờ tái lập được
POSITIONS_FILE = os.path.join("data", "positions.csv")
CENTIPAWN_CAP = 1000          # trần centipawn khi gặp điểm chiếu hết (nhóm tự chọn)
