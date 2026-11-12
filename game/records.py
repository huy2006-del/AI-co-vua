# game/records.py

class GameRecord:
    """Quản lý lịch sử các nước đi của ván đấu dưới dạng ký hiệu đại số (SAN)."""
    
    def __init__(self):
        self._history = []

    def add_move(self, move_san: str):
        """Thêm một nước đi vào lịch sử."""
        self._history.append(move_san)

    def get_history(self) -> list:
        """Trả về danh sách lịch sử các nước đi."""
        return list(self._history)

    def clear(self):
        """Xóa toàn bộ lịch sử ván đấu."""
        self._history.clear()