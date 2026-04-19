import unittest
import random
from main import generate_cost_matrix, greedy_assignment, hungarian_algorithm

class TestMinCostGame(unittest.TestCase):

    def test_generate_cost_matrix_size(self):
        """Test if cost matrix is n x n"""
        for n in [50, 75, 100]:
            matrix = generate_cost_matrix(n)
            self.assertEqual(len(matrix), n)
            for row in matrix:
                self.assertEqual(len(row), n)

    def test_generate_cost_matrix_values(self):
        """Test if cost values are within 20-200"""
        n = 50
        matrix = generate_cost_matrix(n)
        for row in matrix:
            for cost in row:
                self.assertGreaterEqual(cost, 20)
                self.assertLessEqual(cost, 200)

    def test_greedy_assignment_cost_positive(self):
        """Test if greedy algorithm returns positive total cost"""
        n = 5
        matrix = generate_cost_matrix(n)
        total_cost, duration = greedy_assignment(matrix)
        self.assertGreater(total_cost, 0)
        self.assertGreaterEqual(duration, 0)

    def test_hungarian_assignment_cost_positive(self):
        """Test if Hungarian algorithm returns positive total cost"""
        n = 5
        matrix = generate_cost_matrix(n)
        total_cost, duration = hungarian_algorithm(matrix)
        self.assertGreater(total_cost, 0)
        self.assertGreaterEqual(duration, 0)

    def test_hungarian_vs_greedy(self):
        """Hungarian total cost should be <= greedy total cost"""
        n = 10
        matrix = generate_cost_matrix(n)
        greedy_cost, _ = greedy_assignment(matrix)
        hungarian_cost, _ = hungarian_algorithm(matrix)
        self.assertLessEqual(hungarian_cost, greedy_cost)

    def test_small_known_matrix(self):
        """Test Hungarian on a small known matrix"""
        matrix = [
            [90, 75, 75, 80],
            [35, 85, 55, 65],
            [125, 95, 90, 105],
            [45, 110, 95, 115]
        ]
        # Known optimal assignment cost = 275
        hungarian_cost, _ = hungarian_algorithm(matrix)
        self.assertEqual(hungarian_cost, 275)

if __name__ == '__main__':
    unittest.main()