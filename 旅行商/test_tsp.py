import math
import unittest

import TSP as tsp


def is_valid_route(route, city_count):
    return (
        route[0] == 0
        and route[-1] == 0
        and len(route) == city_count + 1
        and sorted(route[1:-1]) == list(range(1, city_count))
    )


class TSPTestCase(unittest.TestCase):
    def setUp(self):
        self.cities = [
            (10, 10),
            (15, 35),
            (30, 28),
            (42, 10),
            (48, 30),
            (35, 45),
            (18, 48),
            (5, 30),
        ]
        self.distances = tsp.distance_matrix(self.cities)

    def test_distance_matrix_uses_euclidean_distance(self):
        distances = tsp.distance_matrix([(0, 0), (3, 4), (0, 4)])

        self.assertEqual(distances[0][0], 0.0)
        self.assertAlmostEqual(distances[0][1], 5.0)
        self.assertAlmostEqual(distances[1][0], 5.0)
        self.assertAlmostEqual(distances[0][2], 4.0)

    def test_held_karp_finds_square_optimum(self):
        distances = tsp.distance_matrix([(0, 0), (1, 0), (1, 1), (0, 1)])

        route, length = tsp.held_karp(distances)

        self.assertTrue(is_valid_route(route, 4))
        self.assertAlmostEqual(length, 4.0)

    def test_nearest_neighbor_and_two_opt_return_valid_routes(self):
        route, length = tsp.nearest_neighbor(self.distances)
        improved_route, improved_length = tsp.two_opt(route, self.distances)

        self.assertTrue(is_valid_route(route, len(self.cities)))
        self.assertTrue(is_valid_route(improved_route, len(self.cities)))
        self.assertLessEqual(improved_length, length + 1e-9)

    def test_population_heuristics_return_valid_reproducible_routes(self):
        for solver in (tsp.genetic_algorithm, tsp.ant_colony):
            route, length = solver(self.distances, seed=42)
            route_again, length_again = solver(self.distances, seed=42)

            self.assertTrue(is_valid_route(route, len(self.cities)))
            self.assertAlmostEqual(length, tsp.route_distance(route, self.distances))
            self.assertEqual(route, route_again)
            self.assertAlmostEqual(length, length_again)

    def test_experiment_includes_requested_algorithms_and_error(self):
        results = tsp.run_experiment(self.cities)

        self.assertEqual(
            set(results),
            {"Held-Karp动态规划", "最近邻算法", "2-opt局部优化", "遗传算法", "蚁群算法"},
        )
        optimum = results["Held-Karp动态规划"]["distance"]
        self.assertTrue(math.isclose(results["Held-Karp动态规划"]["error_percent"], 0.0))
        for result in results.values():
            self.assertTrue(is_valid_route(result["route"], len(self.cities)))
            self.assertGreaterEqual(result["distance"], optimum - 1e-9)


if __name__ == "__main__":
    unittest.main()
