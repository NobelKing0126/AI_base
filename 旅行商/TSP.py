import json
import math
import random
import time
from pathlib import Path


SAMPLE_CITIES = [
    (12, 18),
    (20, 52),
    (33, 36),
    (45, 62),
    (57, 42),
    (70, 66),
    (78, 30),
    (64, 12),
    (48, 22),
    (29, 10),
    (8, 38),
    (55, 52),
]


def distance_matrix(cities):
    """Return Euclidean distances between all city coordinate pairs."""
    return [
        [math.hypot(x1 - x2, y1 - y2) for x2, y2 in cities]
        for x1, y1 in cities
    ]


def route_distance(route, distances):
    return sum(distances[route[i]][route[i + 1]] for i in range(len(route) - 1))


def held_karp(distances):
    """Find an optimal TSP route with subset dynamic programming."""
    city_count = len(distances)
    if city_count == 1:
        return [0, 0], 0.0

    dp = {}
    for city in range(1, city_count):
        mask = 1 << (city - 1)
        dp[(mask, city)] = (distances[0][city], 0)

    full_mask = (1 << (city_count - 1)) - 1
    for mask in range(1, full_mask + 1):
        for last in range(1, city_count):
            state = (mask, last)
            if state not in dp:
                continue
            cost, _ = dp[state]
            for next_city in range(1, city_count):
                bit = 1 << (next_city - 1)
                if mask & bit:
                    continue
                next_mask = mask | bit
                next_cost = cost + distances[last][next_city]
                previous = dp.get((next_mask, next_city))
                if previous is None or next_cost < previous[0]:
                    dp[(next_mask, next_city)] = (next_cost, last)

    total_distance, last_city = min(
        (dp[(full_mask, last)][0] + distances[last][0], last)
        for last in range(1, city_count)
    )

    reversed_route = []
    mask = full_mask
    while last_city != 0:
        reversed_route.append(last_city)
        _, previous_city = dp[(mask, last_city)]
        mask ^= 1 << (last_city - 1)
        last_city = previous_city

    route = [0] + list(reversed(reversed_route)) + [0]
    return route, total_distance


def nearest_neighbor(distances):
    city_count = len(distances)
    if city_count == 1:
        return [0, 0], 0.0

    route = [0]
    unvisited = set(range(1, city_count))
    while unvisited:
        current = route[-1]
        next_city = min(unvisited, key=lambda city: distances[current][city])
        route.append(next_city)
        unvisited.remove(next_city)
    route.append(0)
    return route, route_distance(route, distances)


def two_opt(route, distances):
    best_route = route[:]
    best_distance = route_distance(best_route, distances)
    city_count = len(best_route) - 1
    improved = True

    while improved:
        improved = False
        for start in range(1, city_count - 1):
            for end in range(start + 1, city_count):
                candidate = (
                    best_route[:start]
                    + best_route[start : end + 1][::-1]
                    + best_route[end + 1 :]
                )
                candidate_distance = route_distance(candidate, distances)
                if candidate_distance < best_distance - 1e-9:
                    best_route = candidate
                    best_distance = candidate_distance
                    improved = True
                    break
            if improved:
                break

    return best_route, best_distance


def _chromosome_distance(chromosome, distances):
    return route_distance([0] + chromosome + [0], distances)


def _ordered_crossover(parent_a, parent_b, rng):
    size = len(parent_a)
    if size < 2:
        return parent_a[:]
    left, right = sorted(rng.sample(range(size), 2))
    child = [None] * size
    child[left : right + 1] = parent_a[left : right + 1]
    remaining = [city for city in parent_b if city not in child]
    remaining_index = 0
    for index in range(size):
        if child[index] is None:
            child[index] = remaining[remaining_index]
            remaining_index += 1
    return child


def genetic_algorithm(
    distances, seed=42, population_size=80, generations=250, mutation_rate=0.15
):
    city_count = len(distances)
    if city_count <= 2:
        return nearest_neighbor(distances)

    rng = random.Random(seed)
    cities = list(range(1, city_count))
    population = []
    nearest_route, _ = nearest_neighbor(distances)
    population.append(nearest_route[1:-1])
    for _ in range(population_size - 1):
        chromosome = cities[:]
        rng.shuffle(chromosome)
        population.append(chromosome)

    def select_parent(ranked_population):
        candidates = rng.sample(ranked_population, 3)
        return min(candidates, key=lambda item: item[0])[1]

    for _ in range(generations):
        ranked = sorted(
            (_chromosome_distance(chromosome, distances), chromosome)
            for chromosome in population
        )
        new_population = [ranked[0][1][:], ranked[1][1][:]]
        while len(new_population) < population_size:
            parent_a = select_parent(ranked)
            parent_b = select_parent(ranked)
            child = _ordered_crossover(parent_a, parent_b, rng)
            if rng.random() < mutation_rate:
                first, second = rng.sample(range(len(child)), 2)
                child[first], child[second] = child[second], child[first]
            new_population.append(child)
        population = new_population

    best_chromosome = min(
        population, key=lambda chromosome: _chromosome_distance(chromosome, distances)
    )
    route = [0] + best_chromosome + [0]
    return route, route_distance(route, distances)


def _choose_next_city(current, unvisited, pheromone, distances, alpha, beta, rng):
    choices = list(unvisited)
    weights = [
        pheromone[current][city] ** alpha
        * (1.0 / max(distances[current][city], 1e-12)) ** beta
        for city in choices
    ]
    target = rng.random() * sum(weights)
    cumulative = 0.0
    for city, weight in zip(choices, weights):
        cumulative += weight
        if cumulative >= target:
            return city
    return choices[-1]


def ant_colony(
    distances,
    seed=42,
    ant_count=30,
    iterations=100,
    alpha=1.0,
    beta=3.0,
    evaporation=0.45,
    q=100.0,
):
    city_count = len(distances)
    if city_count <= 2:
        return nearest_neighbor(distances)

    rng = random.Random(seed)
    pheromone = [[1.0] * city_count for _ in range(city_count)]
    best_route = None
    best_distance = float("inf")

    for _ in range(iterations):
        routes = []
        for _ in range(ant_count):
            route = [0]
            unvisited = set(range(1, city_count))
            while unvisited:
                next_city = _choose_next_city(
                    route[-1], unvisited, pheromone, distances, alpha, beta, rng
                )
                route.append(next_city)
                unvisited.remove(next_city)
            route.append(0)
            length = route_distance(route, distances)
            routes.append((route, length))
            if length < best_distance:
                best_route = route[:]
                best_distance = length

        for first in range(city_count):
            for second in range(city_count):
                pheromone[first][second] *= 1.0 - evaporation

        for route, length in routes:
            deposit = q / length
            for index in range(len(route) - 1):
                first, second = route[index], route[index + 1]
                pheromone[first][second] += deposit
                pheromone[second][first] += deposit

    return best_route, best_distance


def run_experiment(cities):
    distances = distance_matrix(cities)
    algorithms = [
        ("Held-Karp动态规划", lambda: held_karp(distances)),
        ("最近邻算法", lambda: nearest_neighbor(distances)),
        ("2-opt局部优化", lambda: two_opt(nearest_neighbor(distances)[0], distances)),
        ("遗传算法", lambda: genetic_algorithm(distances, seed=42)),
        ("蚁群算法", lambda: ant_colony(distances, seed=42)),
    ]
    results = {}
    for name, solve in algorithms:
        start = time.perf_counter()
        route, length = solve()
        elapsed_ms = (time.perf_counter() - start) * 1000
        results[name] = {
            "route": route,
            "distance": length,
            "time_ms": elapsed_ms,
        }

    optimum = results["Held-Karp动态规划"]["distance"]
    for result in results.values():
        result["error_percent"] = (result["distance"] - optimum) / optimum * 100
    return results


def main():
    results = run_experiment(SAMPLE_CITIES)
    output_path = Path(__file__).with_name("tsp_results.json")
    output = {
        "cities": SAMPLE_CITIES,
        "results": results,
    }
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("TSP 算法实验结果")
    print("-" * 72)
    print(f"{'算法':<18}{'总距离':>12}{'相对误差/%':>14}{'运行时间/ms':>16}")
    for name, result in results.items():
        print(
            f"{name:<18}{result['distance']:>12.2f}"
            f"{result['error_percent']:>14.2f}{result['time_ms']:>16.3f}"
        )
        print(f"  路线: {' -> '.join(map(str, result['route']))}")
    print(f"\n结果已保存至: {output_path}")


if __name__ == "__main__":
    main()
