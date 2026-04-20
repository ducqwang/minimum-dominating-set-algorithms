"""
So sánh 4 thuật toán giải bài toán Tập Thống Trị Tối Thiểu
(Minimum Dominating Set – MDS)

Chạy: python main.py

Kết quả được lưu tự động vào:
  data/test_graphs.json          – các đồ thị test
  results/raw/results.csv        – số liệu thô (n, thuật toán, thời gian, kích thước)
  results/comparison/summary.txt – bảng so sánh dạng text
  results/plots/time_comparison.png  – biểu đồ thời gian
  results/plots/size_comparison.png  – biểu đồ kích thước nghiệm
"""

import sys
import os
import time
import random
import csv
import json

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.greedy import greedy_mds
from src.brute_force import brute_force_mds
from src.branch_bound import branch_bound_mds
from src.aco import aco_mds

BASE = os.path.dirname(__file__)


# Tiện ích đồ thị

def make_graph(n, edges):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def random_graph(n, edge_prob=0.3, seed=42):
    random.seed(seed)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)
             if random.random() < edge_prob]
    return make_graph(n, edges)


def graph_to_edgelist(adj):
    edges = []
    for u in range(len(adj)):
        for v in adj[u]:
            if v > u:
                edges.append([u, v])
    return edges


def is_valid_domset(domset, adj):
    n = len(adj)
    covered = set(domset)
    for v in domset:
        covered |= adj[v]
    return len(covered) == n



# Chạy thuật toán có đo thời gian

def run_algo(func, adj, skip=False):
    """Trả về (result, elapsed_seconds). result=None nếu skip."""
    if skip:
        return None, None
    start = time.perf_counter()
    result = func(adj)
    return result, time.perf_counter() - start



# Bước 1 – Chạy toàn bộ benchmark, thu thập dữ liệu

ALGO_DEFS = [
    ("Vét cạn",   lambda g: brute_force_mds(g)),
    ("Nhánh cận", lambda g: branch_bound_mds(g)),
    ("Tham lam",  lambda g: greedy_mds(g)),
    ("ACO",       lambda g: aco_mds(g, n_ants=20, n_iterations=60, seed=0)),
]

TEST_CASES = [
    # (n,  run_brute, run_bb)
    (8,   True,  True),
    (12,  True,  True),
    (16,  True,  True),
    (20,  False, True),
    (30,  False, True),
    (50,  False, False),
    (100, False, False),
]

SKIP_MAP = {
    "Vét cạn":   lambda n: n > 16,
    "Nhánh cận": lambda n: n > 30,
    "Tham lam":  lambda _: False,
    "ACO":       lambda _: False,
}


def run_benchmark():
    """
    Chạy tất cả thuật toán trên tất cả test case.
    Trả về (records, test_graphs).
      records: list of dict {n, algo, time, size, valid}
      test_graphs: dict {n: adj}
    """
    records = []
    test_graphs = {}

    for n, _, _ in TEST_CASES:
        adj = random_graph(n, edge_prob=0.3, seed=42)
        test_graphs[n] = adj
        print(f"  n={n:>3} ...", end=" ")

        for algo_name, func in ALGO_DEFS:
            skip = SKIP_MAP[algo_name](n)
            result, elapsed = run_algo(func, adj, skip=skip)

            if result is not None:
                valid = is_valid_domset(result, adj)
                records.append({
                    "n":     n,
                    "algo":  algo_name,
                    "time":  elapsed,
                    "size":  len(result),
                    "valid": valid,
                })
                print(f"{algo_name}={len(result)}", end=" ")
            else:
                print(f"{algo_name}=—", end=" ")

        print()

    return records, test_graphs



# Bước 2 – Lưu dữ liệu vào file

def save_graphs(test_graphs):
    """Lưu danh sách cạnh của mỗi đồ thị test vào data/test_graphs.json."""
    path = os.path.join(BASE, "data", "test_graphs.json")
    # Format thủ công để mỗi edge [u, v] nằm compact trên 1 dòng
    items = sorted(test_graphs.items())
    lines = ["{"]
    for i, (n, adj) in enumerate(items):
        edges = graph_to_edgelist(adj)
        edges_str = ", ".join(f"[{u}, {v}]" for u, v in edges)
        comma = "," if i < len(items) - 1 else ""
        lines.append(f'  "{n}": {{')
        lines.append(f'    "n": {n},')
        lines.append(f'    "edges": [{edges_str}]')
        lines.append(f'  }}{comma}')
    lines.append("}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  Đã lưu: data/test_graphs.json")


def save_raw_csv(records):
    """Lưu số liệu thô vào results/raw/results.csv."""
    path = os.path.join(BASE, "results", "raw", "results.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["n", "algo", "time", "size", "valid"])
        writer.writeheader()
        writer.writerows(records)
    print(f"  Đã lưu: results/raw/results.csv")


def save_comparison_table(records):
    """Lưu bảng so sánh dạng text vào results/comparison/summary.txt."""
    path = os.path.join(BASE, "results", "comparison", "summary.txt")

    # Nhóm theo n
    ns = sorted({r["n"] for r in records})
    algos = [a for a, _ in ALGO_DEFS]

    col_w = 20
    header = f"{'n':>4}  " + "".join(f"{a:<{col_w}}" for a in algos)
    sep = "-" * len(header)

    lines = [
        "BÀI TOÁN TẬP THỐNG TRỊ TỐI THIỂU – KẾT QUẢ SO SÁNH",
        "(đồ thị ngẫu nhiên, edge_prob=0.3, seed=42)\n",
        "Ký hiệu: thời_gian / kích_thước  (— = không chạy)\n",
        header, sep,
    ]

    for n in ns:
        row_parts = [f"{n:>4}  "]
        for algo in algos:
            match = next((r for r in records if r["n"] == n and r["algo"] == algo), None)
            if match:
                cell = f"{match['time']:.4f}s / |{match['size']}|"
            else:
                cell = "—"
            row_parts.append(f"{cell:<{col_w}}")
        lines.append("".join(row_parts))

    lines += [
        sep,
        "\nKẾT LUẬN:",
        "  Vét cạn  : chính xác, chỉ dùng n <= 16",
        "  Nhánh cận: chính xác, dùng được n <= 30",
        "  Tham lam : nhanh nhất, kết quả xấp xỉ",
        "  ACO      : tốt hơn tham lam, chậm hơn nhưng dùng được n lớn",
    ]

    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Đã lưu: results/comparison/summary.txt")



# Bước 3 – Vẽ biểu đồ matplotlib

def plot_results(records):
    """Vẽ 2 biểu đồ và lưu vào results/plots/."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # không cần cửa sổ GUI
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [!] matplotlib chưa cài. Chạy: pip install matplotlib")
        return

    plt.rcParams.update({
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.fontsize": 10,
        "figure.dpi": 130,
    })

    COLORS = {
        "Vét cạn":   "#e74c3c",
        "Nhánh cận": "#e67e22",
        "Tham lam":  "#2ecc71",
        "ACO":       "#3498db",
    }
    MARKERS = {"Vét cạn": "o", "Nhánh cận": "s", "Tham lam": "^", "ACO": "D"}

    algos = [a for a, _ in ALGO_DEFS]

    # Nhóm dữ liệu theo (algo, n)
    data = {a: {} for a in algos}
    for r in records:
        data[r["algo"]][r["n"]] = r

    all_ns = sorted({r["n"] for r in records})

    # --- Biểu đồ 1: Thời gian thực thi ---
    fig, ax = plt.subplots(figsize=(8, 5))

    for algo in algos:
        xs, ys = [], []
        for n in all_ns:
            if n in data[algo]:
                xs.append(n)
                ys.append(data[algo][n]["time"])
        if xs:
            ax.plot(xs, ys, marker=MARKERS[algo], color=COLORS[algo],
                    label=algo, linewidth=2, markersize=7)

    ax.set_yscale("log")
    ax.set_xlabel("Số đỉnh n")
    ax.set_ylabel("Thời gian (giây, thang log)")
    ax.set_title("So sánh thời gian thực thi\n(Minimum Dominating Set)")
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.set_xticks(all_ns)

    # Ghi chú vùng khả thi
    ax.axvspan(0, 16.5,  alpha=0.05, color="red",   label="_bf_zone")
    ax.axvspan(0, 30.5,  alpha=0.05, color="orange", label="_bb_zone")

    # Chú thích nhỏ
    ax.text(8,  ax.get_ylim()[0] * 2, "Vét cạn\nkhả thi",
            fontsize=8, color="#e74c3c", ha="center", va="bottom")
    ax.text(23, ax.get_ylim()[0] * 2, "Nhánh cận\nkhả thi",
            fontsize=8, color="#e67e22", ha="center", va="bottom")

    plt.tight_layout()
    path1 = os.path.join(BASE, "results", "plots", "time_comparison.png")
    fig.savefig(path1, bbox_inches="tight")
    plt.close(fig)
    print(f"  Đã lưu: results/plots/time_comparison.png")

    # --- Biểu đồ 2: Kích thước tập thống trị tìm được ---
    fig, ax = plt.subplots(figsize=(8, 5))

    for algo in algos:
        xs, ys = [], []
        for n in all_ns:
            if n in data[algo]:
                xs.append(n)
                ys.append(data[algo][n]["size"])
        if xs:
            ax.plot(xs, ys, marker=MARKERS[algo], color=COLORS[algo],
                    label=algo, linewidth=2, markersize=7)

    ax.set_xlabel("Số đỉnh n")
    ax.set_ylabel("Kích thước tập thống trị |D|")
    ax.set_title("So sánh chất lượng nghiệm\n(Minimum Dominating Set)")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_xticks(all_ns)

    plt.tight_layout()
    path2 = os.path.join(BASE, "results", "plots", "size_comparison.png")
    fig.savefig(path2, bbox_inches="tight")
    plt.close(fig)
    print(f"  Đã lưu: results/plots/size_comparison.png")



# In kết quả ra console

def print_table(headers, rows):
    widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    sep = "  ".join("-" * w for w in widths)
    print("  " + fmt.format(*headers))
    print("  " + sep)
    for row in rows:
        print("  " + fmt.format(*row))


def print_benchmark_table(records):
    ns = sorted({r["n"] for r in records})
    algos = [a for a, _ in ALGO_DEFS]
    data = {(r["n"], r["algo"]): r for r in records}

    headers = ["n"] + algos
    rows = []
    for n in ns:
        row = [str(n)]
        for algo in algos:
            rec = data.get((n, algo))
            row.append(f"{rec['time']:.3f}s |{rec['size']}|" if rec else "—")
        rows.append(row)

    print_table(headers, rows)
    print()
    print("  Chú thích: thời_gian  |kích_thước_D|")


def print_small_demo():
    print("=" * 65)
    print("  VÍ DỤ NHỎ  (n=7)")
    print("=" * 65)
    print()
    print("  Đồ thị:")
    print("    0 -- 1 -- 3 -- 5")
    print("    |              |")
    print("    2 -- 4 -- 6 --/")
    print()

    adj = make_graph(7, [(0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 6)])
    algos_small = [
        ("Vét cạn",   lambda g: brute_force_mds(g)),
        ("Nhánh cận", lambda g: branch_bound_mds(g)),
        ("Tham lam",  lambda g: greedy_mds(g)),
        ("ACO",       lambda g: aco_mds(g, n_ants=10, n_iterations=30, seed=0)),
    ]

    rows = []
    for name, func in algos_small:
        result, elapsed = run_algo(func, adj)
        rows.append([
            name,
            str(len(result)),
            f"{elapsed:.4f}s",
            "OK" if is_valid_domset(result, adj) else "SAI",
            str(sorted(result)),
        ])
    print_table(["Thuật toán", "Kích thước", "Thời gian", "Hợp lệ", "Tập D"], rows)
    print()


def print_summary():
    print("=" * 65)
    print("  TỔNG HỢP & ĐÁNH GIÁ")
    print("=" * 65)
    print("""
  ┌──────────────┬────────────────┬──────────┬──────────────────────────────────────┐
  │ Thuật toán   │ Độ phức tạp    │ Tối ưu?  │ Nhận xét                             │
  ├──────────────┼────────────────┼──────────┼──────────────────────────────────────┤
  │ Vét cạn      │ O(2^n · n)     │ Có       │ Đúng hoàn toàn, chỉ dùng n ≤ 16     │
  ├──────────────┼────────────────┼──────────┼──────────────────────────────────────┤
  │ Nhánh cận    │ O(2^n) w.case  │ Có       │ Đúng, nhanh hơn nhờ cắt nhánh        │
  │              │ (nhanh hơn     │          │ Dùng được n ≤ 30                     │
  │              │  thực tế)      │          │                                      │
  ├──────────────┼────────────────┼──────────┼──────────────────────────────────────┤
  │ Tham lam     │ O(n²)          │ Không    │ Nhanh nhất, xấp xỉ ≤ (ln Δ+1)·OPT  │
  │              │                │          │ Luôn chạy được dù n lớn              │
  ├──────────────┼────────────────┼──────────┼──────────────────────────────────────┤
  │ ACO          │ O(iter·ant·n²) │ Không    │ Tốt hơn tham lam nhờ local search;  │
  │              │                │          │ chậm hơn, dùng được n lớn            │
  └──────────────┴────────────────┴──────────┴──────────────────────────────────────┘

  Khi nào dùng thuật toán nào?
    n ≤ 16        →  Vét cạn   (chắc chắn tối ưu, đơn giản nhất)
    16 < n ≤ 30   →  Nhánh cận (vẫn tối ưu, đủ nhanh)
    n > 30        →  Tham lam  (rất nhanh) hoặc ACO (nghiệm tốt hơn)
""")



# Main

if __name__ == "__main__":
    print_small_demo()

    print("=" * 65)
    print("  BENCHMARK  (đồ thị ngẫu nhiên, edge_prob=0.3, seed=42)")
    print("=" * 65)
    print()
    records, test_graphs = run_benchmark()
    print()
    print_benchmark_table(records)
    print_summary()

    print("=" * 65)
    print("  LƯU KẾT QUẢ")
    print("=" * 65)
    print()
    save_graphs(test_graphs)
    save_raw_csv(records)
    save_comparison_table(records)
    plot_results(records)
    print()
    print("  Xong! Mở thư mục results/ để xem biểu đồ và bảng so sánh.")
