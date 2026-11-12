# Cờ vua bàn gỗ

Ứng dụng desktop Python/Pygame, với bàn gỗ phối cảnh và quân cờ tạo hình có đổ bóng.
Cửa sổ có thể đổi kích thước. Hình bàn và quân đi kèm mã nguồn, chạy ngoại tuyến.

## Mở ứng dụng

Dùng Python 3.10 trở lên. Giải nén và mở terminal trong thư mục có tệp `requirements.txt`.

```bash
python -m pip install -r requirements.txt
python -m frontend.gui.app
```

Trên Windows, có thể mở `Chay_co_vua.bat` sau khi cài Python. Lần đầu, tệp này
cài thư viện nếu còn thiếu. Có thể chạy thử đối thủ xác định với
`python -m frontend.gui.app --opponent fake`.

## Chơi cờ

- Mở **Ván mới** để chọn Người đấu AI, Hai người trên cùng máy hoặc Engine đấu engine.
  Trong chế độ đấu AI, chọn màu quân, thuật toán, độ sâu, hàm đánh giá và thời gian.
- Bấm quân, rồi bấm ô đích. Bàn cờ chỉ hiện đích hợp lệ. Nhập thành, bắt tốt qua
  đường và phong cấp được xử lý theo luật. Quân vừa đi và vua bị chiếu được đánh dấu.
- **Gợi ý** dùng trong chế độ đấu AI. **Hoàn tác** quay về lượt gần nhất của người
  chơi trong chế độ đấu AI hoặc lùi một lượt đi trong hai chế độ còn lại.
- **Lịch sử** hiển thị ký hiệu SAN, tổng thời gian, số nút và thống kê lần tính gần nhất.
  Dùng con lăn hoặc Page Up / Page Down để cuộn. **F** lật bàn, **Tab** mở lịch sử.
- Trong chế độ engine đấu engine, chọn engine Trắng và Đen trong Thiết lập.
  Bấm **Tiếp tục** để bắt đầu theo dõi. Khi có quyền yêu cầu hòa, mục tương ứng
  xuất hiện trong menu.
- Đối thủ tích hợp gồm Minimax, Alpha-Beta và Alpha-Beta có sắp xếp nước đi.
  Hàm đánh giá hỗ trợ điểm vật chất hoặc điểm vật chất kết hợp vị trí.

## Thực nghiệm

Mở **Menu → Cấu hình thực nghiệm**. Chọn phép so sánh và bộ thế mẫu, ván hiện tại
hoặc FEN tùy chỉnh. Đặt độ sâu, ngân sách thời gian và số nút, rồi chọn **Chạy**.

| Phép so sánh | Chỉ số |
| --- | --- |
| Minimax và Alpha-Beta | Thời gian, số nút, nước chọn, độ sâu hoàn tất, điểm đánh giá |
| Cấu hình AI | Cùng thuật toán với hai hàm đánh giá và độ sâu đã chọn cùng độ sâu liền trước nếu có |
| Đối chiếu Stockfish | Nước tham chiếu, nước trùng và chênh lệch điểm từ góc nhìn bên đang đi |

Mỗi lần chạy thành công lưu cấu hình và dữ liệu trong `results/run_*/run.json`.
**Xuất CSV + ảnh** tạo `results.csv` và `comparison.png` cùng thư mục.
Khi chạm giới hạn, kết quả ghi độ sâu đã hoàn tất để so sánh đúng điều kiện.

Để dùng Stockfish, cài chương trình Stockfish trên máy và thêm vào PATH, hoặc đặt
biến môi trường `STOCKFISH_PATH` trỏ đến tệp chạy. Ví dụ trong PowerShell:

```powershell
$env:STOCKFISH_PATH = 'C:\Chess\stockfish.exe'
python -m frontend.gui.app
```

Stockfish dùng giao tiếp UCI và chạy như tiến trình riêng. Chơi cờ và các thực nghiệm
giữa những engine tích hợp chỉ cần thư viện Python trong `requirements.txt`.
