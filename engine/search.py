# engine/search.py

import chess
from engine.evaluation import MaterialPstEvaluator

class AlphaBetaSearch:
    """Bộ tìm kiếm nước đi cho AI sử dụng Minimax kết hợp cắt tỉa Alpha-Beta."""
    
    def __init__(self, depth: int = 3, evaluator=None):
        self.depth = depth
        self.evaluator = evaluator or MaterialPstEvaluator()

    def find_best_move(self, board: chess.Board) -> chess.Move:
        """Tìm nước đi tốt nhất cho trạng thái bàn cờ hiện tại."""
        best_move = None
        is_maximizing = (board.turn == chess.WHITE)
        
        if is_maximizing:
            best_value = -float('inf')
            alpha = -float('inf')
            beta = float('inf')
            
            for move in board.legal_moves:
                board.push(move)
                value = self.minimax(board, self.depth - 1, alpha, beta, False)
                board.pop()
                
                if value > best_value:
                    best_value = value
                    best_move = move
                alpha = max(alpha, best_value)
        else:
            best_value = float('inf')
            alpha = -float('inf')
            beta = float('inf')
            
            for move in board.legal_moves:
                board.push(move)
                value = self.minimax(board, self.depth - 1, alpha, beta, True)
                board.pop()
                
                if value < best_value:
                    best_value = value
                    best_move = move
                beta = min(beta, best_value)

        # Trả về nước đi tốt nhất, nếu không có thì lấy nước hợp lệ đầu tiên
        if best_move is None and list(board.legal_moves):
            return list(board.legal_moves)[0]
            
        return best_move

    def minimax(self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
        """Thuật toán đệ quy Minimax với cắt tỉa Alpha-Beta."""
        if depth == 0 or board.is_game_over():
            return self.evaluator.evaluate(board)

        if maximizing_player:
            max_eval = -float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Cắt tỉa Beta
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Cắt tỉa Alpha
            return min_eval

        # --- Bổ sung để tương thích với CLI ---
def search(board: chess.Board, depth: int = 3, evaluator=None) -> chess.Move:
    """Hàm tiện ích tương thích để CLI gọi thuật toán tìm kiếm."""
    searcher = AlphaBetaSearch(depth=depth, evaluator=evaluator)
    return searcher.find_best_move(board)

ALGOS = {
    "alphabeta": AlphaBetaSearch,
    "alphabeta_ordered": AlphaBetaSearch,
}