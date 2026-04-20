"""
Thuật toán Tham Lam (Greedy) cho bài toán Tập Thống Trị Tối Thiểu.

Ý tưởng:
  Mỗi bước chọn đỉnh chưa nằm trong tập D mà "phủ" được nhiều đỉnh
  chưa được thống trị nhất (bản thân + hàng xóm chưa bị phủ).

Độ phức tạp: O(n^2)
Kết quả: xấp xỉ, không đảm bảo tối ưu (tỉ lệ xấp xỉ ≤ ln(Δ) + 1)
"""


def greedy_mds(adj):
    """
    Tìm tập thống trị bằng thuật toán tham lam.

    Tham số:
        adj: danh sách kề – adj[v] là set các đỉnh kề của v

    Trả về:
        set các đỉnh trong tập thống trị tìm được
    """
    n = len(adj)
    dominated = set()   # tập các đỉnh đã được thống trị (covered)
    domset = set()      # tập thống trị đang xây dựng

    while len(dominated) < n:
        # Với mỗi đỉnh chưa vào domset, tính số đỉnh mới sẽ được phủ
        best = max(
            (v for v in range(n) if v not in domset),
            key=lambda v: len((adj[v] | {v}) - dominated)
        )
        domset.add(best)
        dominated |= adj[best] | {best}

    return domset
