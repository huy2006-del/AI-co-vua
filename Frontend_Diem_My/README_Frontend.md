# Frontend cờ vua bàn gỗ của Diễm My

Giải nén thư mục `frontend/` vào thư mục gốc của dự án nhóm, ngang cấp với `backend/`.
Nếu dự án đã có thư mục `frontend/`, đối chiếu các tệp trùng trước khi ghép.

Bản này cần các mô-đun tương thích từ bản Cờ vua bàn gỗ:
- `backend.game.controller` và `backend.game.fake_controller`
- `backend.engine.api`
- `backend.benchmark.experiments`

Sau khi ghép và cài thư viện của dự án, mở CMD ở thư mục gốc rồi chạy
`py -3.12 -m frontend.gui.app`. Phông chữ tiếng Việt đi kèm trong `frontend/gui/assets/fonts/`.
