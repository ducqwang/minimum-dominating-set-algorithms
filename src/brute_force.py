"""
Thuật toán Vét Cạn (Brute Force) cho bài toán Tập Thống Trị Tối Thiểu.

Ý tưởng:
  Thử tất cả tập con của V theo thứ tự tăng dần về kích thước.
  Tập con đầu tiên là tập thống trị hợp lệ chính là kết quả tối ưu.

Độ phức tạp: O(2^n × n)
Kết quả: chính xác (optimal), chỉ khả thi với n ≤ 20
"""

from itertools import combinations


def brute_force_mds(adj):
    """
    Tìm tập thống trị tối thiểu bằng vét cạn.

    Tham số:
        adj: danh sách kề – adj[v] là set các đỉnh kề của v

    Trả về:
        set các đỉnh trong tập thống trị tối thiểu
    """
    n = len(adj)

    def is_dominating(subset):
        covered = set(subset)
        for v in subset:
            covered |= adj[v]
        return len(covered) == n

    # Thử từng kích thước 1, 2, ..., n
    for size in range(1, n + 1):
        for subset in combinations(range(n), size):
            if is_dominating(subset):
                return set(subset)

    return set(range(n))  # trường hợp không tìm thấy (không xảy ra)
