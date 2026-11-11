# game/controller.py

import chess
from game.board_state import BoardState
from game.config import GameConfig
from game.records import GameRecord
from game.errors import InvalidMoveError

class GameController:
    def __init__(self, config: GameConfig = None):
        self.config = config or GameConfig()
        self.config.validate()
        self.board_state = BoardState()
        self.record = GameRecord()

    def new_game(self, fen: str = None):
        """Bắt đầu ván đấu mới, tùy chọn thiết lập theo FEN."""
        self.board_state = BoardState(fen)
        self.record.clear()

    def snapshot(self) -> str:
        """Lấy trạng thái bàn cờ hiện tại dưới dạng chuỗi FEN."""
        return self.board_state.fen()

    def legal_targets(self, square_str: str):
        """Lấy danh sách các ô có thể đi từ ô chỉ định (ví dụ: 'e2')."""
        sq_index = chess.parse_square(square_str)
        target_indices = self.board_state.legal_targets(sq_index)
        return [chess.square_name(idx) for idx in target_indices]

    def play_human_move(self, move_str: str):
        """Thực hiện nước đi của người chơi (hỗ trợ SAN như 'Nf3' hoặc UCI như 'e2e4')."""
        try:
            try:
                move = self.board_state.board.parse_san(move_str)
            except ValueError:
                move = chess.Move.from_uci(move_str)
            
            if move not in self.board_state.board.legal_moves:
                raise InvalidMoveError(f"Nước đi không hợp lệ: {move_str}")
            
            san_repr = self.board_state.board.san(move)
            self.board_state.push(move)
            self.record.add_move(san_repr)
            return move
        except Exception as e:
            raise InvalidMoveError(f"Không thể thực hiện nước đi '{move_str}': {e}")

    def history(self):
        """Lấy lịch sử các nước đi của ván đấu."""
        return self.record.get_history()

    def start_ai_move(self):
        """Khởi động tiến trình tìm kiếm nước đi của AI."""
        pass

    def poll_ai(self):
        """Kiểm tra trạng thái tính toán của AI."""
        pass


class FakeController(GameController):
    """Controller giả lập phục vụ cho việc kiểm thử nhanh."""
    pass