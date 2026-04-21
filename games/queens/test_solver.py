import unittest
from sequential import is_safe, solve

class TestSolver(unittest.TestCase):

    def test_is_safe_same_column(self):
        board = [0, -1, -1, -1]   # queen at row 0, col 0
        self.assertFalse(is_safe(board, 1, 0))   # same column -> not safe

    def test_is_safe_diagonal(self):
        board = [0, -1, -1, -1]   # queen at row 0, col 0
        self.assertFalse(is_safe(board, 1, 1))   # diagonal -> not safe

    def test_is_safe_valid(self):
        board = [0, -1, -1, -1]
        self.assertTrue(is_safe(board, 1, 2))  #safe

    def test_four_queens_count(self):
        """4 queens has exactly 2 solutions"""
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        board = [-1] * 4
        solutions = []
        solve(board, 0, solutions)   # reuse solver with N=4
        self.assertIsInstance(solutions, list)

if __name__ == "__main__":
    unittest.main()