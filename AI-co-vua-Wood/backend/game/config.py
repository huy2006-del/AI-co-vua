# game/config.py

from dataclasses import dataclass
from game.errors import InvalidConfigurationError

@dataclass
class GameConfig:
    time_limit: float = 5.0      # Thời gian tối đa cho mỗi nước đi của AI (giây)
    ai_depth: int = 3            # Độ sâu tìm kiếm của AI
    ai_algorithm: str = "minimax"# Thuật toán sử dụng
    player_color: str = "white"  # Màu quân của người chơi ("white" hoặc "black")

    def validate(self):
        """Kiểm tra tính hợp lệ của các thông số cấu hình trò chơi."""
        if self.time_limit <= 0:
            raise InvalidConfigurationError("Thời gian giới hạn (time_limit) phải lớn hơn 0.")
        if self.ai_depth < 1:
            raise InvalidConfigurationError("Độ sâu AI (ai_depth) phải từ 1 trở lên.")
        if self.player_color not in ["white", "black"]:
            raise InvalidConfigurationError("Màu người chơi (player_color) chỉ có thể là 'white' hoặc 'black'.")
        return True
