"""Wood-table chess app. Launch with python -m frontend.gui.app."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import chess
import pygame

from backend.benchmark.experiments import (POSITIONS, compare, engine_move, export_run,
                                            save_run, stockfish_path)
from backend.engine.api import ALGOS, EVALUATIONS
from backend.game.controller import GameController
from backend.game.fake_controller import FakeController
from .board_view import ASSETS, BoardView
from .config_screen import EXPERIMENT_OPTIONS, GAME_MODES, MATCH_OPTIONS, option_text
from .history_view import HistoryView
from .promotion_dialog import PromotionDialog
from .theme import FIELD, GOLD, INK, MUTED, PANEL, SIZE, button, panel, text

RESULTS = Path(__file__).resolve().parents[2] / "results"
TOOLS = (
    ("menu", "menu", "Menu", 32, 116),
    ("new", "reset", "Ván mới", 32, 212),
    ("flip", "flip", "Lật bàn", 32, 308),
    ("undo", "undo", "Hoàn tác", 1004, 116),
    ("history", "history", "Lịch sử", 1004, 212),
    ("hint", "hint", "Gợi ý", 1004, 308),
)
MODAL = pygame.Rect(246, 79, 608, 566)
CLOSE = pygame.Rect(789, 97, 43, 37)
HELP = (
    "Bấm quân của bên đến lượt, rồi bấm ô đích.",
    "Chấm xanh đánh dấu ô có thể đi. Ô vàng là nước vừa đi.",
    "Khi vua bị chiếu, ô vua đổi màu đỏ.",
    "Nhập thành bằng cách chọn vua rồi bấm ô đích của vua.",
    "Bắt tốt qua đường và phong cấp tuân theo luật cờ vua.",
    "Ở chế độ đấu AI, Hoàn tác quay về lượt trước của bạn.",
    "Gợi ý đánh dấu đường đi và không thay đổi bàn cờ.",
    "Tab mở lịch sử. Esc đóng bảng. F lật bàn.",
)


class ChessApp:
    def __init__(self, surface, executor, settings=None, fake=False):
        self.surface = surface
        self.executor = executor
        self.fake = fake
        fonts = ASSETS / "fonts"
        sans = fonts / "DejaVuSans.ttf"
        self.font = pygame.font.Font(str(sans), 17)
        self.small = pygame.font.Font(str(sans), 13)
        self.title = pygame.font.Font(str(fonts / "DejaVuSerif-Bold.ttf"), 29)
        self.board = BoardView(self.small)
        self.settings = dict(mode="ai", human=chess.WHITE, algorithm="alphabeta_ordered",
                             opponent="alphabeta", depth=3, evaluation="position", seconds=2.)
        self.settings.update(settings or {})
        self.experiment = dict(mode="Minimax / Alpha-Beta", position="Cả 3 thế mẫu",
                               algorithm="alphabeta_ordered", depth=3, evaluation="position",
                               seconds=2., nodes=20000)
        self.fen = chess.STARTING_FEN
        self.editing_fen = False
        self.screen = None
        self.dialog = None
        self.pending = None
        self.run = None
        self.export = None
        self.rows = []
        self.result_dir = None
        self.exp_offset = 0
        self.controls = []
        self.reset()

    def reset(self):
        if self.pending:
            self.pending[1].cancel()
        self.pending = None
        self.controller = (FakeController(self.settings["human"])
                           if self.fake and self.settings["mode"] == "ai"
                           else GameController(None, human=self.settings["human"],
                                               mode=self.settings["mode"]))
        self.board.flipped = self.controller.mode == "ai" and not self.controller.human
        self.board.selected = self.board.hint = None
        self.history = HistoryView((273, 215, 554, 302))
        self.dialog = None
        self.message = ""
        self.ai_error = False
        self.claimed = False
        self.paused = self.controller.mode == "engines"
        self.next_move_at = 0

    def _search(self, action):
        opts = self.settings
        board = self.controller.board.copy()
        algo = opts["algorithm"]
        if action == "hint":
            algo = "alphabeta_ordered" if algo == "stockfish" else algo
        elif self.controller.mode == "engines" and board.turn == chess.BLACK:
            algo = opts["opponent"]
        if action == "move" and self.fake and self.controller.mode == "ai":
            future = self.executor.submit(self.controller.choose_move, board)
        else:
            future = self.executor.submit(engine_move, board, algo, opts["depth"],
                                          opts["evaluation"], opts["seconds"], 120000)
        self.pending = action, future

    def _play(self, move):
        try:
            self.controller.play_human(move)
        except ValueError as exc:
            self.message = str(exc)
            return
        self.board.selected = self.board.hint = None
        self.message = ""

    def _play_square(self, point):
        if self.claimed or not self.controller.human_turn:
            return
        selected = self.board.selected
        board = self.controller.board if selected is None else None
        square = self.board.square_at(point, board)
        if square is None:
            return
        if self.pending and self.pending[0] == "hint":
            self.pending[1].cancel()
            self.pending = None
        if square == selected:
            self.board.selected = None
            self.message = ""
            return
        piece = self.controller.board.piece_at(square)
        if piece and piece.color == self.controller.board.turn:
            self.board.selected = square
            self.message = ""
            return
        if selected is None:
            self.message = "Hãy chọn quân của bên đến lượt."
            return
        moves = [move for move in self.controller.legal_moves(selected) if move.to_square == square]
        if not moves:
            self.message = "Nước đi không hợp lệ."
        elif moves[0].promotion:
            self.dialog = PromotionDialog(moves, self.surface.get_rect().center)
        else:
            self._play(moves[0])

    def _undo(self):
        if self.pending:
            self.pending[1].cancel()
            self.pending = None
        if self.controller.undo():
            self.board.selected = self.board.hint = None
            self.ai_error = self.claimed = False
            self.paused = self.controller.mode == "engines"
            self.message = "Đã hoàn tác nước đi."
        else:
            self.message = "Chưa có nước đi của bạn để hoàn tác."

    def _tool(self, action):
        self.error = ""
        if action in ("menu", "history", "new"):
            self.screen = "settings" if action == "new" else action
            self.draft = dict(self.settings)
        elif action == "flip":
            self.board.flipped = not self.board.flipped
        elif action == "undo":
            self._undo()
        elif action == "hint":
            if self.controller.mode != "ai":
                self.message = "Gợi ý chỉ dùng trong chế độ đấu AI."
            elif not self.claimed and self.controller.human_turn and not self.pending:
                self.message = ""
                self._search("hint")
        elif action == "pause":
            self.paused = not self.paused
            self.message = ""
            if self.paused and self.pending:
                self.pending[1].cancel()
                self.pending = None

    def click(self, point):
        if self.dialog:
            move = self.dialog.pick(point)
            if move:
                self.dialog = None
                self._play(move)
            return
        for rect, action in self.controls:
            if rect.collidepoint(point):
                action()
                return
        if not self.screen:
            self._play_square(point)

    def _start(self):
        opts = self.draft
        use_stockfish = opts["mode"] != "local" and (opts["algorithm"] == "stockfish" or
                         opts["mode"] == "engines" and opts["opponent"] == "stockfish")
        if use_stockfish and not stockfish_path():
            self.error = "Cài Stockfish và đặt STOCKFISH_PATH trước khi chọn engine này."
            return
        self.settings = dict(opts)
        self.screen = None
        self.reset()

    def _claim(self):
        self.claimed = self.controller.board.can_claim_draw()
        self.board.selected = self.board.hint = None
        self.screen = None

    def update(self):
        if self.pending and self.pending[1].done():
            action, future = self.pending
            self.pending = None
            try:
                result = future.result()
                move = result if isinstance(result, chess.Move) else result.move
                if action == "hint":
                    self.board.hint = move
                    self.message = f"Gợi ý: {self.controller.board.san(move)}"
                else:
                    self.controller.play_computer(move)
                    if not isinstance(result, chess.Move):
                        self.controller.stats[-1] = result
                    self.next_move_at = pygame.time.get_ticks() + 380
            except Exception as exc:
                if action == "move":
                    self.ai_error = True
                self.message = f"Lỗi engine: {exc}"
        if (not self.pending and not self.screen and not self.paused and not self.ai_error
                and not self.claimed and not self.controller.human_turn
                and self.controller.outcome is None and pygame.time.get_ticks() >= self.next_move_at):
            self._search("move")
        self.history.update(self.controller.history)
        if self.run and self.run.done():
            try:
                self.result_dir, self.rows = self.run.result()
                self.exp_offset = 0
                self.exp_message = f"Đã lưu {len(self.rows)} kết quả vào {self.result_dir.name}."
            except Exception as exc:
                self.exp_message = f"Lỗi thực nghiệm: {exc}"
            self.run = None
        if self.export and self.export.done():
            try:
                self.export.result()
                self.exp_message = "Đã xuất results.csv và comparison.png."
            except Exception as exc:
                self.exp_message = f"Lỗi xuất kết quả: {exc}"
            self.export = None

    def status(self):
        outcome = self.controller.outcome
        if self.claimed:
            return "Kết thúc · Hòa theo yêu cầu"
        if outcome:
            if outcome.winner is not None:
                winner = "Trắng thắng" if outcome.winner else "Đen thắng"
                return f"Chiếu hết · {winner} · {outcome.result()}"
            reason = {"STALEMATE": "hết nước hợp lệ", "INSUFFICIENT_MATERIAL": "thiếu quân chiếu hết",
                      "SEVENTYFIVE_MOVES": "luật 75 nước", "FIVEFOLD_REPETITION": "lặp thế 5 lần"}
            return f"Kết thúc · Hòa do {reason.get(outcome.termination.name, 'luật cờ')}"
        if self.message:
            return self.message
        side = "Trắng" if self.controller.board.turn else "Đen"
        if self.pending:
            return "Đang tính gợi ý…" if self.pending[0] == "hint" else f"{side} · Engine đang tính…"
        if self.paused:
            return f"Tạm dừng · Đến lượt {side}"
        check = " · Vua đang bị chiếu" if self.controller.board.is_check() else ""
        return f"Đến lượt {side}{check}"

    def _add(self, rect, label, action, selected=False, font=None):
        rect = pygame.Rect(rect)
        button(self.surface, font or self.font, rect, label, selected=selected)
        self.controls.append((rect, action))

    def _modal(self, title, subtitle=""):
        self.controls = []
        panel(self.surface, MODAL)
        text(self.surface, self.title, title, (273, 101))
        text(self.surface, self.small, subtitle, (274, 143), MUTED)
        self._add(CLOSE, "×", self._close)

    def _close(self):
        if self.editing_fen:
            pygame.key.stop_text_input()
        if self.screen == "results":
            self.screen = "experiments"
        else:
            self.screen = None
        self.editing_fen = False

    def _open(self, name):
        self.screen = name
        self.error = ""

    def _cycle(self, values, key, choices, amount):
        if self.editing_fen:
            pygame.key.stop_text_input()
            self.editing_fen = False
        values[key] = choices[(choices.index(values[key]) + amount) % len(choices)]
        self.error = ""

    def _option_rows(self, values, schema, top=174):
        for row, (key, (label, choices)) in enumerate(schema.items()):
            y = top + 44 * row
            text(self.surface, self.font, label, (274, y+8), MUTED)
            self._add((506, y, 38, 36), "‹", lambda k=key, v=choices: self._cycle(values, k, v, -1))
            rect = pygame.Rect(549, y, 231, 36)
            button(self.surface, self.font, rect, option_text(key, values[key]))
            self._add((785, y, 39, 36), "›", lambda k=key, v=choices: self._cycle(values, k, v, 1))

    def _draw_menu(self):
        self._modal("Menu ván cờ", "Chơi, xem hướng dẫn hoặc mở khu vực thực nghiệm")
        for index, (label, screen) in enumerate((
            ("Thiết lập ván mới", "settings"), ("Lịch sử và thống kê", "history"),
            ("Hướng dẫn chơi", "help"), ("Cấu hình thực nghiệm", "experiments"),
        )):
            self._add((274, 182+index*62, 550, 48), label, lambda s=screen: self._open(s))
        if not self.controller.outcome and not self.claimed and self.controller.human_turn and self.controller.board.can_claim_draw():
            self._add((274, 430, 550, 48), "Yêu cầu hòa", self._claim)
        self._add((674, 572, 150, 41), "Về bàn cờ", self._close, True)

    def _draw_settings(self):
        self._modal("Thiết lập ván cờ", "Chọn chế độ, màu quân và mức tìm kiếm")
        schema = dict(MATCH_OPTIONS)
        if self.draft["mode"] != "ai":
            schema.pop("human")
        if self.draft["mode"] != "engines":
            schema.pop("opponent")
        if self.draft["mode"] == "local":
            schema = {"mode": schema["mode"]}
        self._option_rows(self.draft, schema)
        text(self.surface, self.small, self.error, (274, 528), GOLD)
        self._add((650, 570, 174, 44), "Bắt đầu ván", self._start, True)

    def _draw_history(self):
        self._modal("Lịch sử và thống kê", "Ký hiệu SAN · Cuộn chuột hoặc dùng Page Up / Page Down")
        text(self.surface, self.font, "Số              Trắng                          Đen", (286, 185))
        self.history.draw(self.surface, self.font)
        searches = [result for result in self.controller.stats if result]
        text(self.surface, self.font, f"{len(self.controller.history)} lượt đi · "
             f"{sum(r.stats.nodes for r in searches):,} nút engine · "
             f"{sum(r.stats.elapsed for r in searches):.2f} giây", (274, 535))
        if searches:
            last = searches[-1]
            text(self.surface, self.small, f"Lần tính gần nhất · d{last.stats.completed_depth} · "
                 f"{last.stats.nodes:,} nút · {last.stats.elapsed:.3f} giây · "
                 f"điểm Trắng {last.score:+d} cp", (274, 569), MUTED)

    def _run_experiment(self):
        if self.editing_fen:
            self.editing_fen = False
            pygame.key.stop_text_input()
        if self.run or self.export:
            return
        options = dict(self.experiment)
        source = options["position"]
        if source == "Cả 3 thế mẫu":
            positions = dict(POSITIONS)
        elif source == "Ván hiện tại":
            positions = {source: self.controller.board.fen()}
        elif source == "FEN tùy chỉnh":
            positions = {source: self.fen.strip()}
        else:
            positions = {source: POSITIONS[source]}
        mode = options["mode"]
        algorithms = ALGOS[:2] if mode == "Minimax / Alpha-Beta" else (options["algorithm"],)
        evaluations = EVALUATIONS if mode == "Cấu hình AI" else (options["evaluation"],)
        depth = options["depth"]
        depths = tuple(sorted({max(1, depth-1), depth})) if mode == "Cấu hình AI" else (depth,)
        folder = RESULTS / datetime.now().strftime("run_%Y%m%d_%H%M%S_%f")

        def run():
            rows = compare(mode, positions, algorithms, evaluations, depths,
                           options["seconds"], options["nodes"])
            save_run(folder, dict(options, positions=positions), rows)
            return folder, rows

        self.run = self.executor.submit(run)
        self.exp_message = "Đang chạy thực nghiệm…"

    def _draw_experiments(self):
        self._modal("Thực nghiệm engine", "Chọn thế cờ, giới hạn và tiêu chí so sánh")
        schema = dict(EXPERIMENT_OPTIONS)
        if self.experiment["mode"] == "Minimax / Alpha-Beta":
            schema.pop("algorithm")
        if self.experiment["mode"] == "Cấu hình AI":
            schema.pop("evaluation")
        self._option_rows(self.experiment, schema)
        if self.experiment["position"] == "FEN tùy chỉnh":
            rect = pygame.Rect(274, 484, 550, 34)
            pygame.draw.rect(self.surface, FIELD, rect, border_radius=7)
            pygame.draw.rect(self.surface, GOLD if self.editing_fen else MUTED, rect, 1, border_radius=7)
            text(self.surface, self.small, "FEN  " + self.fen[-72:], (284, 492))
            self.controls.append((rect, self._focus_fen))
        message = getattr(self, "exp_message", "")
        text(self.surface, self.small, message[:80], (274, 530), GOLD)
        self._add((274, 570, 140, 42), "Chạy", self._run_experiment, True)
        if self.rows:
            self._add((430, 570, 188, 42), "Xem kết quả", lambda: self._open("results"))
            self._add((632, 570, 192, 42), "Xuất CSV + ảnh", self._export)

    def _focus_fen(self):
        self.editing_fen = True
        pygame.key.start_text_input()

    def _export(self):
        if self.rows and not self.export and not self.run:
            self.export = self.executor.submit(export_run, self.result_dir, self.rows)
            self.exp_message = "Đang xuất kết quả…"

    def _draw_results(self):
        self._modal("Kết quả thực nghiệm", "Cuộn để xem · d = độ sâu hoàn tất · cp = centipawn")
        for index, row in enumerate(self.rows[self.exp_offset:self.exp_offset+7]):
            y = 176 + index * 54
            pygame.draw.rect(self.surface, FIELD, (274, y, 550, 49), border_radius=5)
            text(self.surface, self.small,
                 f"{row['position']} · {option_text('algorithm', row['algorithm'])} · "
                 f"{option_text('evaluation', row['evaluation'])} · d{row['completed_depth']}/{row['depth']}",
                 (284, y+4))
            ref = f" · SF {row['stockfish_move']} · mất {row['stockfish_loss_cp']} cp" if row['stockfish_move'] else ""
            text(self.surface, self.small, f"{row['move']} · {row['nodes']:,} nút · "
                 f"{row['seconds']*1000:.1f} ms · {row['score_white_cp']:+d} cp{ref}",
                 (284, y+25), MUTED)

    def draw(self):
        self.controls = []
        self.board.draw(self.surface, self.controller)
        text(self.surface, self.title, "CỜ VUA", (32, 24))
        text(self.surface, self.small, "BÀN GỖ   /   CHESS STUDIO", (35, 65), GOLD)
        text(self.surface, self.font, GAME_MODES[self.controller.mode], (864, 32))
        for action, icon, label, x, y in TOOLS:
            self._draw_tool(action, icon, label, x, y)
        if self.controller.mode == "engines":
            self._add((973, 415, 105, 38), "Tiếp tục" if self.paused else "Tạm dừng",
                      lambda: self._tool("pause"), font=self.small)
        pygame.draw.rect(self.surface, PANEL, (206, 673, 688, 35), border_radius=11)
        text(self.surface, self.small, f"VÁN CỜ  /  D{self.settings['depth']}", (224, 684), GOLD)
        text(self.surface, self.font, self.status()[:64], (388, 679))
        if self.screen == "help":
            self._modal("Hướng dẫn chơi", "Điều khiển bàn cờ và các thao tác thường dùng")
            for i, line in enumerate(HELP):
                text(self.surface, self.font, line, (274, 186+42*i))
        elif self.screen:
            getattr(self, "_draw_" + self.screen)()
        if self.dialog:
            self.dialog.draw(self.surface, self.font)

    def _draw_tool(self, action, icon, label, x, y):
        from .panel import draw_icon
        rect = pygame.Rect(x, y, 64, 60)
        pygame.draw.rect(self.surface, PANEL, rect, border_radius=11)
        pygame.draw.rect(self.surface, "#886144", rect, 1, border_radius=11)
        draw_icon(self.surface, icon, rect.center)
        glyph = self.small.render(label, True, INK)
        self.surface.blit(glyph, glyph.get_rect(midtop=(rect.centerx, rect.bottom+5)))
        self.controls.append((rect.inflate(0, 12), lambda a=action: self._tool(a)))

    def _scroll(self, amount):
        if self.screen == "history":
            self.history.scroll(amount)
        elif self.screen == "results":
            self.exp_offset = max(0, min(max(0, len(self.rows)-7), self.exp_offset+amount))

    def handle(self, event, point=None):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and point is not None:
            self.click(point)
        elif event.type == pygame.MOUSEWHEEL:
            self._scroll(-event.y * 2)
        elif event.type == pygame.TEXTINPUT and self.editing_fen:
            self.fen = (self.fen + event.text)[:130]
        elif event.type == pygame.KEYDOWN:
            if self.editing_fen:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.editing_fen = False
                    pygame.key.stop_text_input()
                elif event.key == pygame.K_BACKSPACE:
                    self.fen = self.fen[:-1]
                elif event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
                    self.fen = ""
                elif event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                    try:
                        if not pygame.scrap.get_init():
                            pygame.scrap.init()
                        data = pygame.scrap.get(pygame.SCRAP_TEXT)
                        if data:
                            self.fen = data.decode("ascii").strip("\x00\r\n ")[:130]
                    except (UnicodeError, pygame.error):
                        self.exp_message = "Không đọc được clipboard. Bạn có thể nhập FEN trực tiếp."
            elif event.key == pygame.K_ESCAPE:
                if self.dialog:
                    self.dialog = None
                elif self.screen:
                    self._close()
                else:
                    self._tool("menu")
            elif not self.dialog:
                if event.key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                    self._scroll(-7 if event.key == pygame.K_PAGEUP else 7)
                elif event.key == pygame.K_TAB:
                    self.screen = None if self.screen == "history" else "history"
                elif event.key == pygame.K_f and not self.screen:
                    self._tool("flip")


def main():
    parser = argparse.ArgumentParser(description="Cờ vua bàn gỗ")
    parser.add_argument("--depth", type=int, choices=range(1, 5), default=3)
    parser.add_argument("--color", choices=("white", "black"), default="white")
    parser.add_argument("--opponent", choices=("demo", "fake", "team"), default="team")
    args = parser.parse_args()
    pygame.init()
    pygame.key.stop_text_input()
    try:
        window = pygame.display.set_mode((1100, 720), pygame.RESIZABLE)
        pygame.display.set_caption("Cờ vua · Bàn gỗ")
        surface = pygame.Surface(SIZE).convert()
        clock = pygame.time.Clock()
        with ThreadPoolExecutor(max_workers=2) as executor:
            app = ChessApp(surface, executor, {"depth": args.depth, "human": args.color == "white",
                           "evaluation": "material" if args.opponent == "demo" else "position"},
                           fake=args.opponent == "fake")
            while True:
                ww, wh = window.get_size()
                factor = min(ww/SIZE[0], wh/SIZE[1])
                rect = pygame.Rect(0, 0, max(1, int(SIZE[0]*factor)), max(1, int(SIZE[1]*factor)))
                rect.center = window.get_rect().center
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    point = (tuple(round((a-b)/factor) for a, b in zip(event.pos, rect.topleft))
                             if hasattr(event, "pos") and rect.collidepoint(event.pos) else None)
                    app.handle(event, point)
                app.update()
                app.draw()
                window.fill("#130d09")
                window.blit(pygame.transform.smoothscale(surface, rect.size), rect)
                pygame.display.flip()
                clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
