## Proof your algorithms work
## Independent validation
## Not just UI-based testing
## Tests BFS and DFS independently
##Ensures they return valid values
## Can be run without UI
## Helps catch bugs early 



import unittest
from main import bfs, dfs_limited

class TestAlgorithms(unittest.TestCase):

    def test_bfs(self):
        global snakes, ladders
        snakes = {}
        ladders = {}

        result = bfs(1, 36)
        self.assertTrue(result > 0)

    def test_dfs(self):
        global snakes, ladders
        snakes = {}
        ladders = {}

        result = dfs_limited(1, 36, 10)
        self.assertTrue(result > 0)

if __name__ == '__main__':
    unittest.main()