# Dự án AI cờ vua

Dự án gồm engine Minimax/Alpha-Beta tự xây dựng, giao diện chơi trên web, giao diện desktop Pygame và các công cụ benchmark/đối chiếu Stockfish.

## Chạy web trên Windows

Các lệnh dưới đây dành cho PowerShell. Chạy từ thư mục `AI-co-vua-Wood`:

```powershell
cd "D:\Trí tuệ nhân tạo\AI-co-vua1\AI-co-vua-Wood"
```

### Tạo môi trường Python lần đầu

Dự án dùng Python 3.14 được cài qua Python Launcher (`py`). Tạo môi trường ảo trong thư mục dự án:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Nếu PowerShell báo không cho chạy script, chỉ mở quyền trong terminal hiện tại rồi kích hoạt lại:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### Cài thư viện

Để chạy web, chỉ cần `python-chess`:

```powershell
python -m pip install "python-chess>=1.999,<2.0"
```

Để cài thêm thư viện giao diện desktop và benchmark:

```powershell
python -m pip install -r ..\requirements.txt
```

`requirements.txt` dùng `pygame-ce` thay cho `pygame` để tránh pip cố biên dịch Pygame từ mã nguồn trên Python mới.

### Khởi chạy web

```powershell
python web_app.py
```

Mở http://127.0.0.1:8000 trong trình duyệt. Dừng máy chủ bằng `Ctrl+C` trong terminal.

### Các lần chạy sau

Mở PowerShell mới và chạy:

```powershell
cd "D:\Trí tuệ nhân tạo\AI-co-vua1\AI-co-vua-Wood"
.\.venv\Scripts\Activate.ps1
python web_app.py
```

## Stockfish (tùy chọn)

Web app hiện sử dụng engine Python tích hợp; không cần Stockfish để chơi. Các công cụ benchmark có thể dùng Stockfish đã cài tại:

```text
D:\Trí tuệ nhân tạo\stockfish-windows-x86-64-universal\stockfish\stockfish-windows-x86-64-universal.exe
```

Đặt biến môi trường trong PowerShell hiện tại trước khi chạy benchmark:

```powershell
$env:STOCKFISH_PATH = "D:\Trí tuệ nhân tạo\stockfish-windows-x86-64-universal\stockfish\stockfish-windows-x86-64-universal.exe"
Test-Path $env:STOCKFISH_PATH
```

Kết quả `True` xác nhận đúng đường dẫn. Để cấu hình lâu dài cho tài khoản Windows:

```powershell
[Environment]::SetEnvironmentVariable("STOCKFISH_PATH", "D:\Trí tuệ nhân tạo\stockfish-windows-x86-64-universal\stockfish\stockfish-windows-x86-64-universal.exe", "User")
```

Sau khi đặt biến lâu dài, mở terminal mới để nhận cấu hình.

## Chạy kiểm tra

Cài dependencies đầy đủ theo mục trên, sau đó từ thư mục gốc repository:

```powershell
cd ..
python -m pytest -q
```

## Khắc phục lỗi thường gặp

- **Không tạo được `.venv` hoặc báo không ghi được `python.exe`:** đóng terminal/app đang sử dụng môi trường ảo. Nếu `.venv` cũ hỏng và xóa được, xóa đúng thư mục `AI-co-vua-Wood\.venv` rồi chạy lại lệnh tạo venv. Nếu Windows vẫn khóa file, khởi động lại máy rồi tạo lại trước khi mở IDE.
- **Pip báo lỗi khi cài Pygame:** nâng pip trong môi trường ảo bằng `python -m pip install --upgrade pip`, rồi cài lại. Chạy web không cần Pygame; chỉ cần cài `python-chess` theo hướng dẫn tối thiểu.
- **`No module named chess`:** xác nhận đã kích hoạt `.venv` (đầu dòng terminal có `(.venv)`), sau đó chạy `python -m pip install "python-chess>=1.999,<2.0"`.
- **Cổng 8000 đang được dùng:** đóng tiến trình web trước đó hoặc đổi `8000` trong dòng `ThreadingHTTPServer(("127.0.0.1",8000),Handler)` của `web_app.py`.

## Cấu trúc chính

```text
AI-co-vua1/
├── AI-co-vua-Wood/
│   ├── backend/engine/       # Tìm kiếm và đánh giá thế cờ
│   ├── backend/game/         # Luật chơi và trạng thái ván
│   ├── backend/benchmark/    # Đo đạc và đối chiếu Stockfish
│   ├── frontend/gui/         # Giao diện desktop
│   └── web_app.py            # Giao diện trình duyệt
├── tests/
└── requirements.txt
```
