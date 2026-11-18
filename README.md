# Dự án AI cờ vua

Dự án gồm engine cờ vua Minimax/Alpha-Beta, giao diện desktop dùng Pygame và các công cụ benchmark. Mã nguồn ứng dụng nằm trong `AI-co-vua-Wood`; `requirements.txt` và các script chạy nằm ở thư mục gốc.

> Các lệnh dưới đây giả định terminal đang mở tại thư mục chứa file README này. Không cần dùng đường dẫn tuyệt đối trên máy của một thành viên cụ thể.

## Yêu cầu

- Python 3.10 trở lên.
- Windows, macOS hoặc Linux. Giao diện cần môi trường desktop có thể mở cửa sổ Pygame.
- Stockfish chỉ cần cho các chế độ benchmark/đấu engine có đối thủ Stockfish; chơi với engine tích hợp không cần Stockfish.

## Cài đặt lần đầu

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Mỗi người trong nhóm tạo môi trường `.venv` riêng trên máy của mình. Không sao chép thư mục `.venv` từ máy khác; tạo lại bằng các lệnh trên để Python cài đúng thư viện cho hệ điều hành đó.

## Chạy ứng dụng

Cách nhanh nhất trên Windows là chạy `run.bat` ở thư mục gốc. Script tự tạo `.venv` nếu thiếu, cài dependencies nếu chưa có, rồi khởi động ứng dụng. Có thể truyền các tham số của ứng dụng sau tên file, ví dụ `run.bat --depth 2`. Thành viên không cần kích hoạt `.venv` bằng tay.

Trên macOS/Linux, chạy `bash run.sh` ở thư mục gốc; script cũng tự tạo môi trường và cài dependencies khi cần.

### Windows PowerShell

```powershell
Set-Location AI-co-vua-Wood
& ..\.venv\Scripts\python.exe -m frontend.gui.app
```

Các lệnh trực tiếp ở trên luôn dùng Python trong `.venv`, kể cả khi terminal chưa hiện tiền tố `(.venv)`. Không dùng `python -m frontend.gui.app` với Python hệ thống nếu chưa cài dependencies vào Python đó.

### macOS / Linux

```bash
cd AI-co-vua-Wood
../.venv/bin/python -m frontend.gui.app
```

Hoặc chạy `bash run.sh` từ thư mục gốc.

Trong bàn cờ, bấm quân cần đi rồi bấm ô đích. Mặc định người chơi cầm Trắng và engine tích hợp cầm Đen. Có thể chọn màu và độ sâu bằng tham số:

```powershell
& ..\.venv\Scripts\python.exe -m frontend.gui.app --color black --depth 3
```

Các tham số `--color` nhận `white` hoặc `black`; `--depth` nhận từ 1 đến 4. Để chạy với đối thủ giả lập dùng kiểm tra giao diện:

```powershell
& ..\.venv\Scripts\python.exe -m frontend.gui.app --opponent fake
```

Ván cờ dùng luật của `python-chess`: nước đi hợp lệ, nhập thành, bắt tốt qua đường, phong cấp, chiếu hết và hòa được xử lý theo luật. Khi ván kết thúc, trạng thái hiển thị kết quả; dùng **Ván mới** để chơi lại.

## Chạy benchmark

Từ thư mục gốc, vào thư mục ứng dụng rồi chạy:

```powershell
Set-Location AI-co-vua-Wood
& ..\.venv\Scripts\python.exe -m backend.benchmark.compare_algos --per-phase 10 --max-depth 3
```

Trên macOS/Linux, thay lệnh Python bằng `../.venv/bin/python`. Kết quả được tạo trong `AI-co-vua-Wood/results/benchmark`, theo từng lần chạy và có CSV cùng metadata cấu hình để đối chiếu sau này. Giao diện desktop cũng có màn hình thực nghiệm và chức năng xuất dữ liệu/đồ thị.

## Stockfish (tùy chọn)

Cài Stockfish riêng và đặt biến `STOCKFISH_PATH` trỏ tới file thực thi. Ví dụ PowerShell:

```powershell
$env:STOCKFISH_PATH = "C:\duong-dan\stockfish.exe"
```

macOS/Linux:

```bash
export STOCKFISH_PATH="/duong-dan/stockfish"
```

Biến môi trường chỉ áp dụng cho terminal hiện tại. Nếu bỏ qua cấu hình này, các chức năng dùng Stockfish sẽ không chạy; chơi với engine tích hợp vẫn hoạt động.

## Kết quả BE2 lưu trong repo

Các log, CSV, metadata và đồ thị BE2 được lưu trong `AI-co-vua-Wood/results/archive/be2-full-20261115-021529-511`. Đây là dữ liệu tham chiếu từ lần chạy trước, không phải mã nguồn hay dữ liệu đầu vào bắt buộc. Metadata ghi nhận 30 thế cờ, độ sâu 1–3 và 180 bản ghi so sánh. Log báo 17 kiểm tra đã qua; phần ablation bị bỏ qua vì thiếu hoặc rỗng trong checkout dùng cho lần chạy đó.

## Khắc phục lỗi thường gặp

- **`No module named chess` hoặc `No module named pygame`:** cài `requirements.txt` bằng đúng Python trong `.venv` như hướng dẫn cài đặt.
- **`No module named backend` hoặc `No module named frontend`:** trước khi chạy module, chuyển vào `AI-co-vua-Wood`.
- **PowerShell không cho kích hoạt `.venv`:** không cần kích hoạt môi trường; dùng trực tiếp `& ..\.venv\Scripts\python.exe` như các lệnh trên.
- **Lỗi lịch sử kiểu `not enough values to unpack`:** thường do các file lấy từ những phiên bản khác nhau. Cập nhật đồng bộ toàn bộ repo để giao diện và controller dùng cùng định dạng lịch sử.
- **`web_app.py` không tìm thấy:** checkout hiện tại không có ứng dụng web. Chạy giao diện desktop bằng `python -m frontend.gui.app` như hướng dẫn; lệnh web trong tài liệu cũ không áp dụng.
- **Stockfish không tìm thấy:** kiểm tra đường dẫn trong `STOCKFISH_PATH`. Engine cờ vua tích hợp không phụ thuộc Stockfish.
