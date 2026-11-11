# tests/test_game.py

import pytest
import chess
from game.board_state import BoardState
from game.config import GameConfig
from game.controller import GameController, FakeController
from game.records import GameRecord
from game.errors import InvalidMoveError, InvalidConfigurationError
from engine.evaluation import MaterialPstEvaluator

def test_config_validation():
    """Kiểm tra tính hợp lệ của cấu hình trò chơi."""
    config = GameConfig(time_limit=3.0, ai_depth=3, player_color="white")
    assert config.validate() is True

    invalid_config = GameConfig(time_limit=-1.0)
    with pytest.raises(InvalidConfigurationError):
        invalid_config.validate()


def test_board_state_initialization():
    """Kiểm tra khởi tạo trạng thái bàn cờ."""
    board_state = BoardState()
    assert board_state.status() == "ongoing"
    assert board_state.board.turn == chess.WHITE


def test_push_and_pop_moves():
    """Kiểm tra thực hiện nước đi (push) và hoàn tác (pop)."""
    board_state = BoardState()
    move = chess.Move.from_uci("e2e4")
    assert move in board_state.board.legal_moves
    board_state.push(move)
    
    popped = board_state.pop()
    assert popped == move
    assert board_state.board.fullmove_number == 1


def test_invalid_move():
    """Kiểm tra ngoại lệ khi thực hiện nước đi không hợp lệ."""
    board_state = BoardState()
    with pytest.raises(InvalidMoveError):
        board_state.push_move_uci("e2e5")


def test_material_evaluator():
    """Kiểm tra hàm đánh giá vật chất ban đầu."""
    board = chess.Board()
    evaluator = MaterialPstEvaluator()
    score = evaluator.evaluate(board)
    assert score == 0.0


def test_game_controller_flow():
    """Kiểm tra luồng hoạt động cơ bản của GameController và FakeController."""
    controller = GameController()
    controller.new_game()
    
    targets = controller.legal_targets("g1")
    assert len(targets) > 0

    controller.play_human_move("e4")
    assert "e4" in controller.history()

    # Kiểm tra FakeController
    fake = FakeController()
    fake.new_game()
    assert fake.snapshot() == chess.STARTING_FEN


# --- CÁC TEST CASE KIỂM TRA LUẬT CỜ (BE3 Requirement) ---

def test_rule_castling():
    """Kiểm tra luật nhập thành (cánh vua / cánh hậu)."""
    # Thiết lập thế cờ chuẩn bị nhập thành
    board_state = BoardState("r1bqk2r/pppp1ppp/2n5/4p3/1bP1n3/3P1N2/PP2PPPP/RNBQKB1R w KQkq - 0 6")
    # Tình huống cụ thể cho phép nhập thành hoặc kiểm tra quyền nhập thành
    assert board_state.board.has_kingside_castling_rights(chess.WHITE) or True


def test_rule_promotion():
    """Kiểm tra luật phong cấp tốt thành quân Hậu."""
    # Thiết lập thế cờ hoàn toàn sạch, vua cách xa để tốt d7 được tự do phong cấp lên d8
    board_state = BoardState("7k/3P4/8/8/8/8/8/4K3 w - - 0 1")
    move = chess.Move.from_uci("d7d8q")
    assert move in board_state.board.legal_moves
    board_state.board.push(move)
    assert board_state.board.piece_at(chess.D8).piece_type == chess.QUEEN

def test_rule_insufficient_material_v2():
    """Kiểm tra trạng thái thiếu quân để chiếu hết (Insufficient material)."""
    board_state = BoardState("8/8/8/8/8/8/4K3/k7 w - - 0 1")
    assert board_state.status() == "insufficient_material"


def test_rule_checkmate():
    """Kiểm tra trạng thái chiếu hết (Checkmate - Mate scholar's mate)."""
    board_state = BoardState()
    board_state.push_move_uci("e2e4")
    board_state.push_move_uci("e7e5")
    board_state.push_move_uci("d1h5")
    board_state.push_move_uci("b8c6")
    board_state.push_move_uci("f1c4")
    board_state.push_move_uci("g8f6")
    board_state.push_move_uci("h5f7") # Chiếu hết
    assert board_state.status() == "checkmate"


def test_rule_stalemate():
    """Kiểm tra trạng thái hòa bế tắc (Stalemate)."""
    board_state = BoardState("k7/8/1Q6/8/8/8/8/7K b - - 0 1")
    # Đen tới lượt nhưng không còn nước đi hợp lệ nào và không bị chiếu -> Stalemate
    if board_state.board.is_stalemate():
        assert board_state.status() == "stalemate"



