"""Check the CPL calculation using a mock Stockfish adapter."""

from unittest import TestCase
from unittest.mock import Mock

import chess
import chess.engine

from backend.benchmark.cpl import measure_move, summarize
from backend.benchmark.vs_stockfish import StockfishAdapter


class StockfishCplTests(TestCase):
    def setUp(self):
        self.board = chess.Board()
        self.limit = chess.engine.Limit(depth=10)
        self.stockfish = Mock(spec=StockfishAdapter)

    def set_scores(self, best_move, best_score, chosen_score):
        self.stockfish.analyse.return_value = {
            "pv": [self.board.parse_uci(best_move)],
            "score": chess.engine.PovScore(best_score, chess.WHITE),
        }
        self.stockfish.evaluate_move.return_value = chess.engine.PovScore(
            chosen_score, chess.WHITE
        )

    def test_loss_from_white_perspective(self):
        self.set_scores("e2e4", chess.engine.Cp(42), chess.engine.Cp(12))
        move = self.board.parse_uci("d2d4")

        result = measure_move(self.stockfish, self.board, move, self.limit)

        self.assertEqual(result["cpl"], 30)
        self.assertEqual(result["same_move"], 0)
        self.stockfish.evaluate_move.assert_called_once_with(self.board, move, self.limit)

    def test_loss_from_black_perspective(self):
        self.board.push_uci("e2e4")
        self.set_scores("c7c5", chess.engine.Cp(-30), chess.engine.Cp(20))

        result = measure_move(
            self.stockfish, self.board, self.board.parse_uci("e7e5"), self.limit
        )

        self.assertEqual(result["stockfish_cp"], 30)
        self.assertEqual(result["ai_move_cp"], -20)
        self.assertEqual(result["cpl"], 50)

    def test_same_move_reuses_score(self):
        self.set_scores("e2e4", chess.engine.Cp(24), chess.engine.Cp(2))

        result = measure_move(
            self.stockfish, self.board, self.board.parse_uci("e2e4"), self.limit
        )

        self.assertEqual(result["same_move"], 1)
        self.assertEqual(result["cpl"], 0)
        self.stockfish.evaluate_move.assert_not_called()

    def test_higher_forced_score_gives_zero_loss(self):
        self.set_scores("e2e4", chess.engine.Cp(18), chess.engine.Cp(22))

        result = measure_move(
            self.stockfish, self.board, self.board.parse_uci("d2d4"), self.limit
        )

        self.assertEqual(result["cpl"], 0)
        self.assertEqual(result["same_move"], 0)

    def test_mate_score_is_kept_and_excluded_from_average(self):
        self.set_scores("e2e4", chess.engine.Mate(3), chess.engine.Cp(75))
        result = measure_move(
            self.stockfish, self.board, self.board.parse_uci("d2d4"), self.limit
        )

        stats = summarize(
            [
                {"phase": "opening", **result},
                {"phase": "opening", "cpl": 20, "same_move": 1},
            ]
        )["opening"]
        self.assertIsNone(result["cpl"])
        self.assertEqual(result["stockfish_score"], "#+3")
        self.assertEqual(stats["cpl_count"], 1)
        self.assertEqual(stats["mate_count"], 1)
        self.assertEqual(stats["mean_cpl"], 20)
        self.assertEqual(stats["same_move_rate"], 0.5)

    def test_illegal_move_is_rejected_before_stockfish(self):
        with self.assertRaisesRegex(ValueError, "Illegal benchmark move"):
            measure_move(
                self.stockfish, self.board, chess.Move.from_uci("e2e5"), self.limit
            )
        self.stockfish.analyse.assert_not_called()
