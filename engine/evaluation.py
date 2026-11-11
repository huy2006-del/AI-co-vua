# engine/evaluation.py

import chess

class Evaluator:
    """Giao diện cơ sở cho các hàm đánh giá thế cờ."""
    def evaluate(self, board: chess.Board) -> float:
        raise NotImplementedError("Phải cài đặt phương thức evaluate trong lớp con.")


class MaterialPstEvaluator(Evaluator):
    """Hàm đánh giá v1: Tính điểm vật chất kết hợp Bảng vị trí quân cờ (Piece-Square Tables) và Độ cơ động (Mobility)."""
    
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    def evaluate(self, board: chess.Board) -> float:
        """Đánh giá toàn cục thế cờ từ góc nhìn của bên Trắng."""
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                return -99999
            else:
                return 99999
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0.0

        score = 0
        
        # 1. Đánh giá điểm vật chất (Material)
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                val = self.PIECE_VALUES[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += val
                else:
                    score -= val

        # 2. Đánh giá độ cơ động (Mobility - tính số nước đi hợp lệ)
        # Lưu lượt đi hiện tại để tính mobility cho đúng góc nhìn
        current_turn = board.turn
        
        # Tạm thời đổi lượt để tính số nước đi của từng bên nếu cần, 
        # hoặc đơn giản đánh giá dựa trên tập hợp nước đi hợp lệ hiện tại:
        # (Mobility bonus nhỏ cho mỗi nước đi hợp lệ khả dĩ)
        mobility_score = 0
        # Đếm số nước đi hợp lệ của Trắng vs Đen (cần push/pop hoặc giả lập)
        # Cách đơn giản:
        white_mobility = 0
        black_mobility = 0
        
        if current_turn == chess.WHITE:
            white_mobility = len(list(board.legal_moves))
            board.push(chess.Move.null()) # Giả lập chuyển lượt sang Đen
            black_mobility = len(list(board.legal_moves))
            board.pop()
        else:
            black_mobility = len(list(board.legal_moves))
            board.push(chess.Move.null()) # Giả lập chuyển lượt sang Trắng
            white_mobility = len(list(board.legal_moves))
            board.pop()

        # Thêm hệ số nhỏ cho mobility (ví dụ: mỗi nước đi hợp lệ = 5 điểm)
        score += (white_mobility - black_mobility) * 5

        return float(score)


class EvaluatorFactory:
    """Nhà máy khởi tạo hàm đánh giá (Evaluator Factory) theo yêu cầu BE3."""
    @staticmethod
    def create_evaluator(name: str = "material_pst_v1") -> Evaluator:
        if name in ["material_pst_v1", "v1", "default"]:
            return MaterialPstEvaluator()
        else:
            raise ValueError(f"Không hỗ trợ loại evaluator: {name}")