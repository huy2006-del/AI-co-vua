# game/board_state.py

import chess
from game.errors import InvalidMoveError

class BoardState:
    def __init__(self, fen: str = None):
        """Khởi tạo bàn cờ, mặc định ở vị trí xuất phát hoặc từ chuỗi FEN."""
        if fen:
            self.board = chess.Board(fen)
        else:
            self.board = chess.Board()

    def reset(self):
        """Đặt lại ván đấu về trạng thái ban đầu."""
        self.board.reset()

    def push_move_uci(self, uci_str: str) -> chess.Move:
        """Đẩy một nước đi theo định dạng UCI (ví dụ: 'e2e4') vào bàn cờ."""
        move = chess.Move.from_uci(uci_str)
        if move in self.board.legal_moves:
            self.board.push(move)
            return move
        raise InvalidMoveError(f"Nước đi UCI không hợp lệ: {uci_str}")

    def push_move_san(self, san_str: str) -> chess.Move:
        """Đẩy một nước đi theo định dạng ký hiệu đại số SAN (ví dụ: 'Nf3', 'e4')."""
        try:
            move = self.board.parse_san(san_str)
            self.board.push(move)
            return move
        except Exception as e:
            raise InvalidMoveError(f"Nước đi SAN không hợp lệ '{san_str}': {e}")

    def push(self, move: chess.Move):
        """Thực hiện một đối tượng chess.Move trực tiếp."""
        if move in self.board.legal_moves:
            self.board.push(move)
        else:
            raise InvalidMoveError(f"Nước đi không hợp lệ: {move}")

    def pop(self) -> chess.Move:
        """Hoàn tác (undo) nước đi cuối cùng."""
        if self.board.move_stack:
            return self.board.pop()
        return None

    def legal_targets(self, square_index: int):
        """Lấy danh sách các ô có thể di chuyển từ một ô chỉ định (square_index từ 0-63)."""
        targets = []
        for move in self.board.legal_moves:
            if move.from_square == square_index:
                targets.append(move.to_square)
        return targets

    def needs_promotion(self, move: chess.Move) -> bool:
        """Kiểm tra xem nước đi có cần phong cấp quân Tốt hay không."""
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN:
            to_rank = chess.square_rank(move.to_square)
            if (self.board.turn == chess.WHITE and to_rank == 7) or \
               (self.board.turn == chess.BLACK and to_rank == 0):
                return True
        return False

    def status(self) -> str:
        """Trả về trạng thái hiện tại của ván đấu."""
        if self.board.is_checkmate():
            return "checkmate"
        elif self.board.is_stalemate():
            return "stalemate"
        elif self.board.is_insufficient_material():
            return "insufficient_material"
        elif self.board.is_game_over():
            return "game_over"
        return "ongoing"

    def fen(self) -> str:
        """Lấy chuỗi FEN hiện tại của bàn cờ."""
        return self.board.fen()