"""Flask backend.  Người phụ trách: Người 2 (backend), Người 3 (frontend dùng API này).

Backend là nguồn sự thật duy nhất về trạng thái cờ: mỗi request gửi kèm FEN,
server không lưu ván. Frontend luôn vẽ lại bàn cờ theo FEN server trả về.

Chạy:  python app.py   rồi mở http://127.0.0.1:5000
"""
import chess
from flask import Flask, jsonify, request

import config
from chessai.game import game_status
from chessai.search import ALGORITHMS, search

app = Flask(__name__, static_folder="static", static_url_path="")


def error(code, http=400, **extra):
    return jsonify({"valid": False, "error": code, **extra}), http


def parse_algo_depth(data):
    """Trả về (algorithm, depth, lỗi). lỗi là None nếu hợp lệ."""
    algorithm = data.get("algorithm")
    if algorithm not in ALGORITHMS:
        return None, None, error("bad_algorithm")
    depth = data.get("depth")
    if (not isinstance(depth, int) or isinstance(depth, bool)
            or not 1 <= depth <= config.MAX_DEPTH):
        return None, None, error("bad_depth", max_depth=config.MAX_DEPTH)
    return algorithm, depth, None


def parse_fen(data):
    try:
        return chess.Board(data["fen"]), None
    except (ValueError, TypeError, KeyError):
        return None, error("bad_fen")


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/move", methods=["POST"])
def api_move():
    """Hợp đồng đã chốt - xem README mục 'API'."""
    data = request.get_json(silent=True) or {}
    for field in ("fen", "move", "algorithm", "depth"):
        if field not in data:
            return error("missing_field", field=field)

    algorithm, depth, err = parse_algo_depth(data)
    if err:
        return err
    board, err = parse_fen(data)
    if err:
        return err

    try:
        player_move = chess.Move.from_uci(data["move"])
    except (ValueError, TypeError):
        return error("bad_move_format")

    if player_move not in board.legal_moves:
        return jsonify({"valid": False, "error": "illegal_move",
                        "fen": board.fen()}), 200

    board.push(player_move)

    ai_move, nodes, time_ms = None, 0, 0.0
    if not board.is_game_over():
        res = search(board, algorithm, depth)
        nodes, time_ms = res.nodes, res.time_ms
        if res.move is not None:
            ai_move = res.move.uci()
            board.push(res.move)

    status, winner = game_status(board)
    return jsonify({
        "valid": True,
        "fen": board.fen(),
        "player_move": player_move.uci(),
        "ai_move": ai_move,
        "nodes": nodes,
        "time_ms": round(time_ms, 2),
        "status": status,
        "winner": winner,
        "in_check": board.is_check(),
    })


@app.route("/api/new", methods=["POST"])
def api_new():
    """Ván mới. Nếu người chơi cầm Đen thì AI (Trắng) đi trước.

    Body: {"color": "white"|"black", "algorithm": ..., "depth": ...}
    (algorithm/depth chỉ cần khi color = "black").
    """
    data = request.get_json(silent=True) or {}
    color = data.get("color", "white")
    if color not in ("white", "black"):
        return error("bad_color")

    board = chess.Board()
    ai_move, nodes, time_ms = None, 0, 0.0
    if color == "black":
        algorithm, depth, err = parse_algo_depth(data)
        if err:
            return err
        res = search(board, algorithm, depth)
        nodes, time_ms = res.nodes, res.time_ms
        ai_move = res.move.uci()
        board.push(res.move)

    status, winner = game_status(board)
    return jsonify({
        "valid": True, "fen": board.fen(), "ai_move": ai_move,
        "nodes": nodes, "time_ms": round(time_ms, 2),
        "status": status, "winner": winner, "in_check": board.is_check(),
    })


@app.route("/api/legal_moves", methods=["POST"])
def api_legal_moves():
    """Danh sách nước hợp lệ (UCI) để frontend tô sáng ô đi được."""
    data = request.get_json(silent=True) or {}
    board, err = parse_fen(data)
    if err:
        return err
    return jsonify({"valid": True, "moves": [m.uci() for m in board.legal_moves]})


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """MỞ RỘNG (ngoài hợp đồng /api/move): chạy cả hai thuật toán trên cùng thế cờ.

    Dùng để demo trực tiếp điểm cốt lõi của đề: cùng giá trị, khác số node/thời gian.
    Body: {"fen": ..., "depth": ...}
    """
    data = request.get_json(silent=True) or {}
    board, err = parse_fen(data)
    if err:
        return err
    _, depth, err = parse_algo_depth({"algorithm": "minimax", "depth": data.get("depth")})
    if err:
        return err
    if board.is_game_over():
        return error("game_over")

    out = {"valid": True, "depth": depth}
    for algo in ALGORITHMS:
        r = search(board, algo, depth)
        out[algo] = {"move": r.move.uci() if r.move else None, "value": r.value,
                     "nodes": r.nodes, "time_ms": round(r.time_ms, 2)}
    out["same_value"] = out["minimax"]["value"] == out["alphabeta"]["value"]
    return jsonify(out)


if __name__ == "__main__":
    app.run(debug=True)
