# game/errors.py

class ChessGameError(Exception):
    """Lỗi cơ sở cho toàn bộ game cờ vua."""
    pass

class InvalidMoveError(ChessGameError):
    """Nước đi không hợp lệ theo luật cờ vua."""
    pass

class InvalidConfigurationError(ChessGameError):
    """Cấu hình khởi tạo không hợp lệ."""
    pass
