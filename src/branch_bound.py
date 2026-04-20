"""
Thuật toán Nhánh Cận (Branch and Bound) cho bài toán Tập Thống Trị Tối Thiểu.

Ý tưởng:
  Duyệt cây tìm kiếm theo chiều sâu. Tại mỗi nút:
    - Tìm đỉnh u chưa được thống trị đầu tiên.
    - Phân nhánh: thêm u hoặc một trong các hàng xóm của u vào D.
      (bắt buộc phải chọn ít nhất một trong số đó để phủ u)
  Cắt nhánh (pruning) khi:
    - |D_hiện_tại| + LowerBound ≥ kết quả tốt nhất đã biết.
  Lower bound: số đỉnh chưa phủ / coverage tối đa mỗi đỉnh.

Độ phức tạp: O(2^n) worst-case, thực tế nhanh hơn nhiều nhờ cắt nhánh
Kết quả: chính xác (optimal)
"""

import math


def branch_bound_mds(adj):
    """
    Tìm tập thống trị tối thiểu bằng nhánh-cận.

    Tham số:
        adj: danh sách kề – adj[v] là set các đỉnh kề của v

    Trả về:
        set các đỉnh trong tập thống trị tối thiểu
    """
    n = len(adj)
    if n == 0:
        return set()

    # Phủ tối đa của một đỉnh = bậc + 1 (bản thân + hàng xóm)
    max_cover = max(len(adj[v]) + 1 for v in range(n))

    best = [None]  # best[0] = tập thống trị tốt nhất tìm được

    def lower_bound(dominated):
        """Cận dưới: số đỉnh còn chưa phủ / phủ tối đa mỗi lần."""
        uncovered = n - len(dominated)
        return math.ceil(uncovered / max_cover)

    def solve(dominated, domset):
        # Tìm được tập thống trị hợp lệ
        if len(dominated) == n:
            if best[0] is None or len(domset) < len(best[0]):
                best[0] = list(domset)
            return

        # Cắt nhánh: nếu không thể cải thiện kết quả hiện tại
        if best[0] is not None:
            if len(domset) + lower_bound(dominated) >= len(best[0]):
                return

        # Lấy đỉnh chưa được thống trị đầu tiên
        undom = next(v for v in range(n) if v not in dominated)

        # Phân nhánh: phải chọn undom hoặc một hàng xóm của nó
        # Ưu tiên đỉnh có bậc cao (phủ được nhiều hơn)
        candidates = sorted({undom} | adj[undom], key=lambda v: -len(adj[v]))

        for v in candidates:
            solve(
                dominated | adj[v] | {v},
                domset | {v}
            )

    solve(set(), set())
    return set(best[0]) if best[0] is not None else set(range(n))
