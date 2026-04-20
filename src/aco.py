"""
Thuật toán Tối Ưu Đàn Kiến (ACO – Ant Colony Optimization)
cho bài toán Tập Thống Trị Tối Thiểu.

Ý tưởng:
  - Mỗi "kiến" xây dựng một lời giải bằng cách lần lượt chọn đỉnh
    theo xác suất dựa trên pheromone (τ) và heuristic (η = bậc + 1).
  - Sau khi xây xong, áp dụng local search để loại bỏ đỉnh dư thừa.
  - Pheromone được cập nhật: bốc hơi (evaporation) + bồi đắp từ các
    lời giải tốt trong mỗi vòng lặp.

Công thức chọn đỉnh v:
    P(v) = τ(v)^α × η(v)^β  /  Σ τ(u)^α × η(u)^β

Độ phức tạp: O(iterations × ants × n²)
Kết quả: xấp xỉ tối ưu, chất lượng tốt hơn tham lam
"""

import random


def aco_mds(adj, n_ants=20, n_iterations=50, alpha=1.0, beta=2.0, rho=0.1, seed=None):
    """
    Tìm tập thống trị gần tối thiểu bằng ACO.

    Tham số:
        adj         : danh sách kề
        n_ants      : số kiến mỗi vòng lặp
        n_iterations: số vòng lặp
        alpha       : trọng số pheromone
        beta        : trọng số heuristic (bậc đỉnh)
        rho         : tốc độ bốc hơi pheromone (0 < rho < 1)
        seed        : random seed để tái tạo kết quả

    Trả về:
        set các đỉnh trong tập thống trị tìm được
    """
    if seed is not None:
        random.seed(seed)

    n = len(adj)
    if n == 0:
        return set()

    pheromone = [1.0] * n  # khởi tạo pheromone đều nhau

    def heuristic(v):
        return len(adj[v]) + 1  # bậc + 1: đỉnh bậc cao phủ nhiều hơn

    def construct_solution():
        """Một kiến xây dựng một lời giải."""
        dominated = set()
        domset = set()

        while len(dominated) < n:
            # Tính xác suất chọn từng đỉnh chưa ở trong domset
            probs = []
            for v in range(n):
                if v not in domset:
                    gain = len((adj[v] | {v}) - dominated)
                    if gain > 0:
                        p = (pheromone[v] ** alpha) * (heuristic(v) ** beta)
                        probs.append((v, p))

            if not probs:
                # An toàn: thêm đỉnh chưa phủ bất kỳ (hiếm xảy ra)
                v = next(u for u in range(n) if u not in dominated)
                domset.add(v)
                dominated |= adj[v] | {v}
                continue

            # Roulette wheel selection
            total = sum(p for _, p in probs)
            r = random.uniform(0, total)
            cumsum = 0.0
            chosen = probs[-1][0]
            for v, p in probs:
                cumsum += p
                if cumsum >= r:
                    chosen = v
                    break

            domset.add(chosen)
            dominated |= adj[chosen] | {chosen}

        return domset

    def local_search(domset):
        """
        Loại bỏ các đỉnh dư thừa: nếu xóa v mà tập vẫn là tập thống trị
        thì xóa v để thu nhỏ lời giải.
        """
        current = set(domset)
        improved = True
        while improved:
            improved = False
            for v in list(current):
                candidate = current - {v}
                covered = set(candidate)
                for u in candidate:
                    covered |= adj[u]
                if len(covered) == n:
                    current = candidate
                    improved = True
                    break
        return current

    best_solution = None

    for _ in range(n_iterations):
        # Mỗi kiến xây dựng lời giải + cải thiện bằng local search
        solutions = [local_search(construct_solution()) for _ in range(n_ants)]

        # Cập nhật pheromone: bốc hơi
        for i in range(n):
            pheromone[i] = max(0.01, pheromone[i] * (1 - rho))

        # Bồi đắp pheromone từ tất cả kiến (deposit ∝ 1/|solution|)
        for sol in solutions:
            deposit = 1.0 / len(sol)
            for v in sol:
                pheromone[v] += deposit

        # Cập nhật lời giải tốt nhất
        iter_best = min(solutions, key=len)
        if best_solution is None or len(iter_best) < len(best_solution):
            best_solution = iter_best

    return best_solution
