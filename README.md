# Cờ vua với AI: Minimax và Alpha-Beta Pruning

Đề tài: "AI chơi Cờ Caro/Cờ vua đơn giản" (Minimax + Alpha-Beta Pruning). Nhóm chọn **cờ vua chuẩn**,
dùng `python-chess` cho luật, giao diện web (Flask + HTML/JS).

Yêu cầu của đề được bám sát:
1. Đối thủ máy tính tìm nước đi tối ưu bằng Minimax và Minimax + Alpha-Beta.
2. So sánh hiệu năng (thời gian, số node duyệt) giữa Minimax thuần và Alpha-Beta.
3. Đối chiếu chất lượng nước đi với Stockfish ở mức độ đơn giản.
4. Dữ liệu: tự sinh thế cờ, không dùng dataset.

## 1. Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Stockfish (chỉ cần cho thí nghiệm TN2, không cần cho demo web): tải từ trang chính thức của Stockfish,
rồi đặt đường dẫn:

```bash
export STOCKFISH_PATH=/duong/dan/stockfish        # Windows: set STOCKFISH_PATH=C:\...\stockfish.exe
```

Xem tùy chọn thật của bản Stockfish bạn tải: chạy file stockfish, gõ `uci`.

## 2. Chạy

```bash
python app.py                      # mở http://127.0.0.1:5000
python -m pytest -q                # chạy toàn bộ test
```

## 3. Thí nghiệm (kết quả ghi vào `results/`)

```bash
python -m chessai.game --per-phase 10                       # sinh data/positions.csv (seed cố định trong config.py)

# TN1: Minimax vs Alpha-Beta (thời gian + node)
python -m experiments.benchmark --depths 1 2 3 --repeats 3
python -m experiments.benchmark --depths 1 2 3 4 --minimax-max-depth 3   # nếu Minimax quá chậm ở độ sâu 4
python -m experiments.plot_results                          # biểu đồ + bảng tóm tắt

# TN2: chất lượng nước đi so với Stockfish
python -m experiments.quality --algorithm alphabeta --depth 3
python -m experiments.match --games 5 --depth 2 --elo <số trong khoảng engine hỗ trợ> --sf-time 0.05   # tùy chọn: đấu thực tế

# TN3 (tùy chọn): move ordering
python -m experiments.benchmark --depths 1 2 3 --ordering
```

**Lưu ý khi dùng số liệu trong báo cáo:** chỉ dùng số do nhóm tự chạy trên máy nhóm, ghi rõ cấu hình máy,
phiên bản Python/python-chess/Stockfish, seed, số thế cờ, `STOCKFISH_DEPTH`, `MULTIPV`. Các thước đo ở TN2
(trùng nước tốt nhất, top-k, centipawn loss, trần `CENTIPAWN_CAP`) là **do nhóm chọn**, phải nêu rõ trong báo cáo.

## 4. API (hợp đồng đã chốt)

### `POST /api/move`
Request: `{"fen": "...", "move": "e2e4", "algorithm": "minimax|alphabeta", "depth": 3}`
(`move` dạng UCI; phong cấp thêm chữ cuối, ví dụ `e7e8q`).

Thành công: `{"valid": true, "fen": "<sau khi AI đi>", "player_move", "ai_move", "nodes", "time_ms", "status": "playing|checkmate|stalemate|draw", "winner": "white|black|null", "in_check"}`

Nước không hợp lệ (HTTP 200): `{"valid": false, "error": "illegal_move", "fen": "<FEN gốc>"}`
Dữ liệu sai (HTTP 400): `error` là một trong `missing_field`, `bad_fen`, `bad_move_format`, `bad_algorithm`, `bad_depth`.

`nodes`, `time_ms` chỉ tính lượt tìm kiếm của AI. Nếu nước của người chơi đã kết thúc ván: `ai_move = null`, `nodes = 0`, `time_ms = 0`.

### Endpoint phụ (nhóm bổ sung, ngoài hợp đồng `/api/move`)
- `POST /api/new` `{"color": "white|black", "algorithm", "depth"}`: ván mới (người chơi cầm Đen thì AI đi trước).
- `POST /api/legal_moves` `{"fen"}`: danh sách nước hợp lệ (UCI) để tô sáng ô đi được.
- `POST /api/compare` `{"fen", "depth"}`: chạy cả hai thuật toán trên cùng thế cờ để demo.

## 5. Cấu trúc và phân công

```
app.py                  Flask API + phục vụ giao diện         Người 2
config.py               hằng số, đường dẫn Stockfish          Người 1
chessai/evaluation.py   hàm đánh giá v1 (+ stub v2)            Người 3
chessai/minimax.py      Minimax thuần + bộ đếm node            Người 3
chessai/alphabeta.py    Alpha-Beta + move ordering (tùy chọn)  Người 4
chessai/search.py       điểm vào gọi AI (đo thời gian)         Người 2 (3, 4 review)
chessai/game.py         trạng thái ván + sinh thế cờ (seed)    Người 2
static/                 giao diện web (HTML/CSS/JS)            Người 3
experiments/benchmark.py, plot_results.py   TN1                Người 4
chessai/stockfish_eval.py   giao tiếp Stockfish, đo chất lượng   Người 5 (BE-B)
experiments/quality.py, match.py            TN2 (dùng stockfish_eval)   Người 5 (BE-B)
tests/                  test tự động                           Người 2, 3, 4
report/                 báo cáo, slide                         Người 1
```

Người 1 còn lo: quản lý repo/tiến độ, tích hợp cuối mỗi tuần, báo cáo, slide, kịch bản demo.

### Việc còn lại cho từng người (checklist)
- **Người 1:** chốt `MAX_DEPTH` trong `config.py` dựa trên kết quả TN1; viết báo cáo + slide; chạy thử từ máy sạch theo README.
- **Người 2:** chạy `pytest`, bổ sung test cho trường hợp riêng của nhóm; kiểm tra bộ thế cờ cuối (số lượng/giai đoạn trong `PHASES` của `game.py` là do nhóm tự định nghĩa, nhớ nêu trong báo cáo).
- **Người 3:** (a) chốt hàm đánh giá v1, (b) hoàn thiện giao diện (hiện nước đi tạm của người chơi chưa vẽ nhập thành/bắt tốt qua đường cho tới khi server trả FEN thật), (c) tùy chọn: `evaluate_v2`.
- **Người 4:** chạy TN1 trên bộ thế cờ cuối, xuất biểu đồ, thử `--ordering` (TN3), kiểm tra Alpha-Beta luôn cho cùng giá trị với Minimax.
- **Người 5:** chạy TN2 với cấu hình Stockfish đã chọn, tùy chọn chạy `match.py`, ghi lại phiên bản và cấu hình Stockfish.

## 6. Quy ước quan trọng
- Điểm đánh giá tính theo góc nhìn **Trắng** (dương = Trắng lợi); Trắng là bên max, Đen là bên min.
- Đếm node: mỗi lần vào hàm tìm kiếm = 1 node, **giống nhau** ở Minimax và Alpha-Beta.
- Test tính đúng đắn so sánh **giá trị** của hai thuật toán, không so sánh nước đi (nhiều nước có thể bằng điểm).
- Backend là nguồn sự thật về trạng thái ván; frontend luôn vẽ lại theo FEN server trả về.
