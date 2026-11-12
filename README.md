# AI cờ vua: Minimax, Alpha-Beta và đối chiếu Stockfish

Dự án phục vụ môn Trí tuệ nhân tạo, gồm engine cờ vua tự cài đặt, giao diện chơi và các thực nghiệm so sánh. Các sơ đồ use case/class và tài liệu phân công là hợp đồng thiết kế. Hiện nhánh nguồn được cung cấp mới triển khai lõi tìm kiếm BE1; phần GUI và benchmark vẫn là khung rỗng, vì vậy README liệt kê rõ phần chạy được và phần chưa hoàn thiện.

## 1. Yêu cầu máy

- Windows 10/11 64-bit.
- Python 3.12.x (dự án dùng môi trường `.venv312`).
- Stockfish UCI 64-bit cho các thực nghiệm đối chiếu.
- Kết nối mạng ở lần đầu để pip tải thư viện.

## 2. Môi trường hiện được cấu hình

Trong workspace hiện có Python 3.12.10 tại `C:\Users\LENOVO\AppData\Local\Python\bin\python3.12-64.exe`; môi trường ảo đã được tạo ở `.venv312`. Stockfish có sẵn tại:

```text
D:\Trí tuệ nhân tạo\stockfish-windows-x86-64-universal\stockfish\stockfish-windows-x86-64-universal.exe
```

Đường dẫn mặc định này được tạo trong `config.py` theo vị trí hai thư mục cùng cấp. Nếu chuyển dự án hoặc dùng máy khác, đặt `STOCKFISH_PATH` theo hướng dẫn bên dưới.

## 3. Cài đặt lần đầu trên Windows

Mở PowerShell tại thư mục repository `AI-co-vua-main`:

```powershell
# Nếu Python 3.12 đã có trong PATH:
py -3.12 -m venv .venv312

# Hoặc chỉ định trực tiếp interpreter Python 3.12:
& "$env:LOCALAPPDATA\Python\bin\python3.12-64.exe" -m venv .venv312

Set-ExecutionPolicy -Scope Process Bypass
.\.venv312\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Đặt đường dẫn Stockfish cho cửa sổ PowerShell hiện tại:
$env:STOCKFISH_PATH = 'D:\Trí tuệ nhân tạo\stockfish-windows-x86-64-universal\stockfish\stockfish-windows-x86-64-universal.exe'
```

Mỗi lần mở terminal mới, kích hoạt lại môi trường và đặt biến Stockfish:

```powershell
Set-Location 'D:\Trí tuệ nhân tạo\AI-co-vua\AI-co-vua-main'
.\.venv312\Scripts\Activate.ps1
$env:STOCKFISH_PATH = 'D:\Trí tuệ nhân tạo\stockfish-windows-x86-64-universal\stockfish\stockfish-windows-x86-64-universal.exe'
```

Kiểm tra cài đặt:

```powershell
python --version
python -c "import chess; print('python-chess', chess.__version__)"
Test-Path $env:STOCKFISH_PATH
& $env:STOCKFISH_PATH
```

Stockfish chạy giao thức UCI và chờ lệnh nhập; dùng `quit` để thoát. Không cần thêm Stockfish vào `PATH` nếu đã đặt `STOCKFISH_PATH`.

## 4. Chạy phần hiện có

### Chơi cờ bằng CLI

```powershell
python cli.py --algo alphabeta --depth 3 --color white
```
Chạy

| Việc |	Lệnh |
|------|-------|
| GUI người vs máy |	python -m gui.app --depth 3 |
| Chơi bằng dòng lệnh |	python cli.py --depth 3 |
| Kiểm thử tính đúng | 	python -m pytest -q |
| Thực nghiệm A (Minimax vs Alpha-Beta) |	python -m benchmark.compare_algos --per-phase 10 --max-depth 4 |
| Thực nghiệm B1 (centipawn loss) |	python -m benchmark.vs_stockfish cpl --depth 3 --n 30|
| Thực nghiệm B2 (đấu Stockfish) |	python -m benchmark.vs_stockfish match --depth 3 --games 10 --elo 1350 |
| Vẽ biểu đồ |	python -m benchmark.plots |

Thuật toán nhận `minimax`, `alphabeta` hoặc `alphabeta_ordered`; màu người chơi nhận `white` hoặc `black`. Nước đi nhập được dạng SAN (ví dụ `Nf3`) hoặc UCI (ví dụ `g1f3`); nhập `quit` để thoát.

### Gọi engine từ Python

```python
import chess
from backend.engine.api import search
from backend.engine.options import SearchOptions

board = chess.Board()
options = SearchOptions(
    ordering=True,
    iterative_deepening=True,
    transposition_table=True,
    quiescence=True,
    time_limit=2.0,
)
result = search(board, "alphabeta", depth=5, options=options)
print(board.uci(result.move), result.score, result.depth, result.stats)
```

Điểm số luôn theo góc nhìn Trắng: số dương có lợi cho Trắng, số âm có lợi cho Đen. Giá trị vật chất tính theo centipawn. `depth` là độ sâu tối đa; nếu bật iterative deepening và hết giờ, kết quả dùng nước tốt nhất từ lần tìm kiếm hoàn tất gần nhất. `SearchWorker` chạy phép tìm kiếm trên bản sao bàn cờ ở luồng nền.


## 5. Lệnh dự kiến sau khi các phần khác được triển khai

Các module `frontend/gui` và `backend/benchmark` hiện là file giữ chỗ rỗng. Vì vậy các lệnh GUI/thực nghiệm dưới đây **chưa chạy được ở snapshot hiện tại**; chúng ghi lại mục tiêu tích hợp của dự án, không phải chức năng đã hoàn thành.

| Use case | Lệnh dự kiến | Module cần hoàn thiện |
|---|---|---|
| UC01, UC02: cấu hình và chơi với AI | `python -m frontend.gui.app` | `frontend/gui/app.py`, `backend/game/*` |
| UC03, UC11: lịch sử và thống kê | Trong ứng dụng GUI | `frontend/gui/history_view.py`, controller |
| UC04, UC05: hai engine và so sánh thuật toán | `python -m backend.benchmark.compare_algos` | `backend/benchmark/compare_algos.py` |
| UC06, UC13: đối chiếu/đấu Stockfish | `python -m backend.benchmark.vs_stockfish` | `backend/benchmark/vs_stockfish.py` |
| UC07: so sánh cấu hình | `python -m backend.benchmark.ablation` | `backend/benchmark/ablation.py` |
| UC08: CSV và biểu đồ | `python -m backend.benchmark.plots` | `backend/benchmark/plots.py`, `store.py` |
| UC09: người với người | Trong ứng dụng GUI | controller và bàn cờ GUI |
| UC10: gợi ý nước đi | Trong ứng dụng GUI | `GameController.request_hint`, `AIPlayer` |
| UC12: hướng dẫn chơi | Trong ứng dụng GUI | màn hình hướng dẫn |

`pytest` đã có trong `requirements.txt`; tuy nhiên thư mục `tests/` hiện chưa có test case. Các tiêu chí chính theo tài liệu phân công gồm PCN02 (Minimax và Alpha-Beta cùng điểm trên 30 thế ở độ sâu 1–3), PCN03 (tìm kiếm không khóa GUI), và TT không làm đổi điểm ở độ sâu cố định.


## 6. Cây thư mục

```text
AI-co-vua-main/
├── backend/
│   ├── engine/       # BE1: tìm kiếm và thống kê
│   ├── game/         # khung BE3
│   └── benchmark/    # khung BE2
├── frontend/gui/     # khung FE1
├── results/          # dữ liệu thực nghiệm
├── tests/            # test sẽ được bổ sung theo PCN
├── cli.py
├── config.py
├── requirements.txt
└── README.md
```

## 7. Phân công và quy trình Git

- **BE1 – Gia Huy:** Minimax, Alpha-Beta, move ordering, iterative deepening, TT, quiescence, thống kê, AIPlayer/SearchWorker.
- **BE2 – Quốc Thái:** benchmark, Stockfish adapter, lưu kết quả và biểu đồ.
- **BE3 – Trí Nhân:** luật cờ, GameController và evaluator.
- **FE1 – Diễm My:** bàn cờ và tương tác GUI.
- **FE2 – Đình Chí:** cấu hình, thống kê, CLI và đóng gói chạy.

Theo quy trình nhóm đã thống nhất, mỗi người làm trên nhánh riêng `feature/<ten>-<viec>`, tạo pull request nhỏ vào `dev`; không push thẳng vào `main`. Chạy test liên quan và review chéo trước khi hợp nhất.
