import unittest
import sqlite3
import os
import copy
import time
import tempfile
from unittest.mock import MagicMock
import sys

# Stub out tkinter so tests run headlessly (no display required)
sys.modules.setdefault("tkinter", MagicMock())
sys.modules.setdefault("tkinter.ttk", MagicMock())
sys.modules.setdefault("tkinter.messagebox", MagicMock())

import traffic_game as tg


# ─────────────────────────────────────────────────────────────────────────────
#  1. GRAPH GENERATION TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestGraphGeneration(unittest.TestCase):

    def setUp(self):
        self.graph, self.caps = tg.generate_graph()

    def test_all_edges_present(self):
        """All 13 required directed edges must exist."""
        for u, v in tg.EDGES:
            self.assertIn((u, v), self.caps,
                          f"Edge ({u}, {v}) missing from caps")
            self.assertIn(v, self.graph.get(u, {}),
                          f"Destination {v} missing from graph[{u}]")

    def test_capacity_range(self):
        """Every capacity must be an integer in [5, 15]."""
        for (u, v), cap in self.caps.items():
            self.assertIsInstance(cap, int)
            self.assertGreaterEqual(cap, 5,  f"Cap {cap} for ({u},{v}) < 5")
            self.assertLessEqual(cap,   15, f"Cap {cap} for ({u},{v}) > 15")

    def test_correct_number_of_edges(self):
        """Exactly 13 edges must be generated."""
        self.assertEqual(len(self.caps), 13)

    def test_randomness_across_calls(self):
        """generate_graph() must not always return identical capacities."""
        results = set()
        for _ in range(20):
            _, caps = tg.generate_graph()
            results.add(tuple(sorted(caps.values())))
        self.assertGreater(len(results), 1)

    def test_graph_and_caps_consistency(self):
        """graph[u][v] must equal caps[(u,v)] for every edge."""
        for (u, v), cap in self.caps.items():
            self.assertEqual(self.graph[u][v], cap)

    def test_required_nodes_present(self):
        """All nine nodes must appear somewhere in the edge list."""
        required = {"A", "B", "C", "D", "E", "F", "G", "H", "T"}
        seen = set()
        for u, v in self.caps:
            seen.add(u); seen.add(v)
        self.assertEqual(required, seen)


# ─────────────────────────────────────────────────────────────────────────────
#  2. FORD-FULKERSON TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestFordFulkerson(unittest.TestCase):

    def test_simple_chain(self):
        g = {"A": {"B": 7}, "B": {"T": 7}}
        self.assertEqual(tg.ford_fulkerson(g), 7)

    def test_parallel_paths(self):
        g = {"A": {"B": 5, "C": 3}, "B": {"T": 5}, "C": {"T": 3}}
        self.assertEqual(tg.ford_fulkerson(g), 8)

    def test_bottleneck(self):
        g = {"A": {"B": 10}, "B": {"T": 4}}
        self.assertEqual(tg.ford_fulkerson(g), 4)

    def test_no_path_returns_zero(self):
        g = {"A": {"B": 5}, "C": {"T": 5}}
        self.assertEqual(tg.ford_fulkerson(g), 0)

    def test_source_equals_sink_returns_zero(self):
        """FIX: source == sink must return 0 immediately, not hang."""
        g = {"A": {"B": 5}, "B": {"T": 5}}
        self.assertEqual(tg.ford_fulkerson(g, source="A", sink="A"), 0)

    def test_does_not_mutate_original(self):
        g = {"A": {"B": 7}, "B": {"T": 7}}
        original = copy.deepcopy(g)
        tg.ford_fulkerson(g)
        self.assertEqual(g, original)

    def test_known_game_graph(self):
        """All-10 graph: only G→T and H→T feed sink, so max flow = 20."""
        g = {
            "A": {"B": 10, "C": 10, "D": 10},
            "B": {"E": 10, "F": 10},
            "C": {"E": 10, "F": 10},
            "D": {"F": 10},
            "E": {"G": 10, "H": 10},
            "F": {"H": 10},
            "G": {"T": 10},
            "H": {"T": 10},
        }
        self.assertEqual(tg.ford_fulkerson(g), 20)

    def test_returns_non_negative_integer(self):
        g, _ = tg.generate_graph()
        result = tg.ford_fulkerson(g)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)


# ─────────────────────────────────────────────────────────────────────────────
#  3. EDMONDS-KARP TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestEdmondsKarp(unittest.TestCase):

    def test_simple_chain(self):
        g = {"A": {"B": 7}, "B": {"T": 7}}
        self.assertEqual(tg.edmonds_karp(g), 7)

    def test_parallel_paths(self):
        g = {"A": {"B": 5, "C": 3}, "B": {"T": 5}, "C": {"T": 3}}
        self.assertEqual(tg.edmonds_karp(g), 8)

    def test_bottleneck(self):
        g = {"A": {"B": 10}, "B": {"T": 4}}
        self.assertEqual(tg.edmonds_karp(g), 4)

    def test_no_path_returns_zero(self):
        g = {"A": {"B": 5}, "C": {"T": 5}}
        self.assertEqual(tg.edmonds_karp(g), 0)

    def test_source_equals_sink_returns_zero(self):
        """FIX: source == sink must return 0 immediately, not loop."""
        g = {"A": {"B": 5}, "B": {"T": 5}}
        self.assertEqual(tg.edmonds_karp(g, source="A", sink="A"), 0)

    def test_does_not_mutate_original(self):
        g = {"A": {"B": 7}, "B": {"T": 7}}
        original = copy.deepcopy(g)
        tg.edmonds_karp(g)
        self.assertEqual(g, original)

    def test_known_game_graph(self):
        g = {
            "A": {"B": 10, "C": 10, "D": 10},
            "B": {"E": 10, "F": 10},
            "C": {"E": 10, "F": 10},
            "D": {"F": 10},
            "E": {"G": 10, "H": 10},
            "F": {"H": 10},
            "G": {"T": 10},
            "H": {"T": 10},
        }
        self.assertEqual(tg.edmonds_karp(g), 20)

    def test_returns_non_negative_integer(self):
        g, _ = tg.generate_graph()
        result = tg.edmonds_karp(g)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)


# ─────────────────────────────────────────────────────────────────────────────
#  4. ALGORITHM AGREEMENT TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestAlgorithmAgreement(unittest.TestCase):

    def test_agreement_on_random_graphs(self):
        for trial in range(50):
            g, _ = tg.generate_graph()
            ff = tg.ford_fulkerson(copy.deepcopy(g))
            ek = tg.edmonds_karp(copy.deepcopy(g))
            self.assertEqual(ff, ek, f"Trial {trial}: FF={ff} != EK={ek}")

    def test_agreement_on_fixed_graph(self):
        g = {"A": {"B": 6, "C": 9}, "B": {"T": 8}, "C": {"T": 5}}
        self.assertEqual(tg.ford_fulkerson(copy.deepcopy(g)),
                         tg.edmonds_karp(copy.deepcopy(g)))

    def test_agreement_on_min_capacity_graph(self):
        g = {u: {v: 5} for u, v in tg.EDGES}
        self.assertEqual(tg.ford_fulkerson(copy.deepcopy(g)),
                         tg.edmonds_karp(copy.deepcopy(g)))

    def test_agreement_on_max_capacity_graph(self):
        g = {u: {v: 15} for u, v in tg.EDGES}
        self.assertEqual(tg.ford_fulkerson(copy.deepcopy(g)),
                         tg.edmonds_karp(copy.deepcopy(g)))


# ─────────────────────────────────────────────────────────────────────────────
#  5. DATABASE TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestDatabase(unittest.TestCase):
    """
    Redirects sqlite3.connect to a temp file so real DB is untouched.

    Windows locks SQLite files for the lifetime of every open connection.
    To avoid PermissionError on tearDown we:
      1. Track every connection opened via our patched sqlite3.connect.
      2. Close them all in tearDown before deleting the temp file.
      3. Use a helper _conn() that registers its connection the same way,
         and always call it as a context manager so the connection is closed
         after the with-block.
    """

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        # Close the OS-level fd immediately; SQLite will reopen the file itself.
        os.close(self.db_fd)
        self.db_fd = None

        self._orig_connect = sqlite3.connect
        self._open_conns = []          # track every connection we open
        test_path = self.db_path
        open_conns = self._open_conns
        orig = self._orig_connect

        def patched_connect(path, *args, **kwargs):
            conn = orig(test_path if "traffic_game" in str(path) else path,
                        *args, **kwargs)
            open_conns.append(conn)
            return conn

        sqlite3.connect = patched_connect
        tg.init_db()

    def tearDown(self):
        # Restore the real connect first so nothing new can open the file.
        sqlite3.connect = self._orig_connect
        # Close every tracked connection — critical on Windows.
        for conn in self._open_conns:
            try:
                conn.close()
            except Exception:
                pass
        self._open_conns.clear()
        # Now the file is unlocked and can be removed.
        try:
            os.unlink(self.db_path)
        except OSError:
            pass   # best-effort; temp dir will clean up eventually

    def _conn(self):
        """Open a direct (unpatched) connection and register it for cleanup."""
        conn = self._orig_connect(self.db_path)
        self._open_conns.append(conn)
        return conn

    # ── init_db ──────────────────────────────────────────────────────────────
    def test_init_db_creates_players_table(self):
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'")
        self.assertIsNotNone(c.fetchone())

    def test_init_db_creates_game_rounds_table(self):
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='game_rounds'")
        self.assertIsNotNone(c.fetchone())

    def test_init_db_creates_correct_answers_table(self):
        """FIX: new correct_answers table must be created by init_db."""
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='correct_answers'")
        self.assertIsNotNone(c.fetchone())

    # ── get_or_create_player ─────────────────────────────────────────────────
    def test_create_new_player_returns_id(self):
        pid = tg.get_or_create_player("Alice")
        self.assertIsInstance(pid, int)
        self.assertGreater(pid, 0)

    def test_same_player_name_returns_same_id(self):
        self.assertEqual(tg.get_or_create_player("Bob"),
                         tg.get_or_create_player("Bob"))

    def test_different_players_get_different_ids(self):
        self.assertNotEqual(tg.get_or_create_player("Carol"),
                            tg.get_or_create_player("Dave"))

    def test_player_stored_in_db(self):
        tg.get_or_create_player("Eve")
        c = self._conn().cursor()
        c.execute("SELECT name FROM players WHERE name='Eve'")
        self.assertEqual(c.fetchone()[0], "Eve")

    # ── save_round — game_rounds table ────────────────────────────────────────
    def test_save_round_inserts_row(self):
        tg.save_round("Frank", 1, 25, 25, "win", 0.123, 0.456)
        c = self._conn().cursor()
        c.execute("SELECT COUNT(*) FROM game_rounds")
        self.assertEqual(c.fetchone()[0], 1)

    def test_save_round_correct_values(self):
        tg.save_round("Grace", 3, 18, 20, "lose", 1.1, 2.2)
        c = self._conn().cursor()
        c.execute("""
            SELECT gr.round_number, gr.correct_answer, gr.player_answer,
                   gr.result, gr.ford_fulkerson_ms, gr.edmonds_karp_ms
            FROM game_rounds gr
            JOIN players p ON p.id = gr.player_id
            WHERE p.name = 'Grace'
        """)
        row = c.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 3)
        self.assertEqual(row[1], 18)
        self.assertEqual(row[2], 20)
        self.assertEqual(row[3], "lose")
        self.assertAlmostEqual(row[4], 1.1, places=5)
        self.assertAlmostEqual(row[5], 2.2, places=5)

    def test_save_multiple_rounds(self):
        tg.save_round("Heidi", 1, 20, 20, "win",  0.1, 0.1)
        tg.save_round("Heidi", 2, 18, 15, "lose", 0.2, 0.2)
        c = self._conn().cursor()
        c.execute("""SELECT COUNT(*) FROM game_rounds gr
                     JOIN players p ON p.id=gr.player_id WHERE p.name='Heidi'""")
        self.assertEqual(c.fetchone()[0], 2)

    def test_timing_values_stored(self):
        tg.save_round("Ivan", 1, 22, 22, "win", 3.14159, 2.71828)
        c = self._conn().cursor()
        c.execute("SELECT ford_fulkerson_ms, edmonds_karp_ms FROM game_rounds")
        row = c.fetchone()
        self.assertAlmostEqual(row[0], 3.14159, places=4)
        self.assertAlmostEqual(row[1], 2.71828, places=4)

    # ── FIX: correct_answers table only written on wins ───────────────────────
    def test_win_saves_to_correct_answers(self):
        """FIX: a winning round must insert a row into correct_answers."""
        tg.save_round("Judy", 2, 17, 17, "win", 0.5, 0.4)
        c = self._conn().cursor()
        c.execute("""SELECT player_name, correct_answer, round_number
                     FROM correct_answers WHERE player_name='Judy'""")
        row = c.fetchone()
        self.assertIsNotNone(row, "Win was not saved to correct_answers")
        self.assertEqual(row[0], "Judy")
        self.assertEqual(row[1], 17)
        self.assertEqual(row[2], 2)

    def test_lose_does_not_save_to_correct_answers(self):
        """FIX: a losing round must NOT insert into correct_answers."""
        tg.save_round("Karl", 1, 20, 15, "lose", 0.3, 0.3)
        c = self._conn().cursor()
        c.execute("SELECT COUNT(*) FROM correct_answers WHERE player_name='Karl'")
        self.assertEqual(c.fetchone()[0], 0,
                         "Losing round incorrectly saved to correct_answers")

    def test_only_wins_accumulate_in_correct_answers(self):
        """Mix of wins and losses — only wins appear in correct_answers."""
        tg.save_round("Lena", 1, 18, 18, "win",  0.1, 0.1)
        tg.save_round("Lena", 2, 20, 99, "lose", 0.2, 0.2)
        tg.save_round("Lena", 3, 22, 22, "win",  0.3, 0.3)
        c = self._conn().cursor()
        c.execute("SELECT COUNT(*) FROM correct_answers WHERE player_name='Lena'")
        self.assertEqual(c.fetchone()[0], 2)


# ─────────────────────────────────────────────────────────────────────────────
#  6. EDGE / BOUNDARY TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestEdgeCases(unittest.TestCase):

    def test_single_edge_graph(self):
        g = {"A": {"T": 9}}
        self.assertEqual(tg.ford_fulkerson(g), 9)
        self.assertEqual(tg.edmonds_karp(g),   9)

    def test_zero_capacity_edge(self):
        g = {"A": {"T": 0}}
        self.assertEqual(tg.ford_fulkerson(g), 0)
        self.assertEqual(tg.edmonds_karp(g),   0)

    def test_source_equals_sink(self):
        """Both algorithms must return 0 when source == sink (not hang)."""
        g = {"A": {"B": 5}, "B": {"T": 5}}
        self.assertEqual(tg.ford_fulkerson(g, source="A", sink="A"), 0)
        self.assertEqual(tg.edmonds_karp(g,   source="A", sink="A"), 0)

    def test_large_capacity(self):
        g = {"A": {"T": 10_000}}
        self.assertEqual(tg.ford_fulkerson(g), 10_000)
        self.assertEqual(tg.edmonds_karp(g),   10_000)

    def test_capacity_boundaries(self):
        _, caps = tg.generate_graph()
        for v in caps.values():
            self.assertGreaterEqual(v, 5)
            self.assertLessEqual(v,   15)

    def test_ff_ek_match_on_boundary_capacities(self):
        for cap in (5, 15):
            g = {u: {v: cap} for u, v in tg.EDGES}
            self.assertEqual(tg.ford_fulkerson(copy.deepcopy(g)),
                             tg.edmonds_karp(copy.deepcopy(g)))


# ─────────────────────────────────────────────────────────────────────────────
#  7. PERFORMANCE TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestAlgorithmPerformance(unittest.TestCase):

    def test_ff_completes_within_timeout(self):
        g, _ = tg.generate_graph()
        start = time.perf_counter()
        tg.ford_fulkerson(g)
        self.assertLess(time.perf_counter() - start, 1.0)

    def test_ek_completes_within_timeout(self):
        g, _ = tg.generate_graph()
        start = time.perf_counter()
        tg.edmonds_karp(g)
        self.assertLess(time.perf_counter() - start, 1.0)

    def test_timing_is_non_negative_float(self):
        g, _ = tg.generate_graph()
        t0 = time.perf_counter()
        tg.ford_fulkerson(g)
        ms = (time.perf_counter() - t0) * 1000
        self.assertIsInstance(ms, float)
        self.assertGreaterEqual(ms, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    unittest.main(verbosity=2)