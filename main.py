"""
So sánh 4 thuật toán giải bài toán Tập Thống Trị Tối Thiểu
(Minimum Dominating Set – MDS)

Chạy: python main.py

Kết quả được lưu tự động vào:
  data/test_graphs.json          – các đồ thị test
  results/raw/results.csv        – số liệu thô (n, p, seed, thuật toán, thời gian, kích thước, gap)
  results/comparison/summary.txt – bảng so sánh dạng text
  results/plots/time_comparison.png  – biểu đồ thời gian
  results/plots/size_comparison.png  – biểu đồ kích thước nghiệm
"""

import sys
import os
import time
import random
import csv

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


def random_graph(n, edge_prob=0.3, seed=0):
    rng = random.Random(seed)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)
             if rng.random() < edge_prob]
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


def mean(values):
    return sum(values) / len(values) if values else None



# Bước 1 – Chạy toàn bộ benchmark, thu thập dữ liệu

ALGO_DEFS = [
    ("Vét cạn",   lambda g: brute_force_mds(g)),
    ("Nhánh cận", lambda g: branch_bound_mds(g)),
    ("Tham lam",  lambda g: greedy_mds(g)),
    ("ACO",       lambda g: aco_mds(g, n_ants=20, n_iterations=60, seed=0)),
]

N_VALUES = [8, 12, 16, 20, 30, 50, 100]
EDGE_PROBS = [0.05, 0.10, 0.30, 0.50]
SEEDS = [0, 1, 2]
GRAPH_EXPORT_SEED = 0
EXACT_ALGOS = {"Vét cạn", "Nhánh cận"}

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
      records: list of dict {n, edge_prob, seed, algo, time, size, valid, opt_size, gap}
      test_graphs: list các đồ thị đại diện được lưu ra file
    """
    records = []
    test_graphs = []

    for edge_prob in EDGE_PROBS:
        print(f"  edge_prob={edge_prob:.2f}")

        for n in N_VALUES:
            print(f"    n={n:>3} ...", end=" ")

            for seed in SEEDS:
                adj = random_graph(n, edge_prob=edge_prob, seed=seed)
                if seed == GRAPH_EXPORT_SEED:
                    test_graphs.append({
                        "n": n,
                        "edge_prob": edge_prob,
                        "seed": seed,
                        "adj": adj,
                    })

                graph_records = []
                for algo_name, func in ALGO_DEFS:
                    skip = SKIP_MAP[algo_name](n)
                    result, elapsed = run_algo(func, adj, skip=skip)

                    if result is not None:
                        graph_records.append({
                            "n":         n,
                            "edge_prob": edge_prob,
                            "seed":      seed,
                            "algo":      algo_name,
                            "time":      elapsed,
                            "size":      len(result),
                            "valid":     is_valid_domset(result, adj),
                            "opt_size":  None,
                            "gap":       None,
                        })

                opt_candidates = [
                    r["size"] for r in graph_records
                    if r["algo"] in EXACT_ALGOS and r["valid"]
                ]
                opt_size = min(opt_candidates) if opt_candidates else None

                for rec in graph_records:
                    rec["opt_size"] = opt_size
                    rec["gap"] = rec["size"] - opt_size if opt_size is not None else None
                    records.append(rec)

            for algo_name, _ in ALGO_DEFS:
                samples = [
                    r for r in records
                    if r["edge_prob"] == edge_prob and r["n"] == n and r["algo"] == algo_name
                ]
                if not samples:
                    print(f"{algo_name}=—", end=" ")
                    continue

                avg_size = mean([r["size"] for r in samples])
                gaps = [r["gap"] for r in samples if r["gap"] is not None]
                gap_text = f", gap={mean(gaps):+.2f}" if gaps else ""
                print(f"{algo_name}=|{avg_size:.2f}|{gap_text}", end=" ")

            print()

    return records, test_graphs



# Bước 2 – Lưu dữ liệu vào file

def save_graphs(test_graphs):
    """Lưu danh sách cạnh của mỗi đồ thị test vào data/test_graphs.json."""
    path = os.path.join(BASE, "data", "test_graphs.json")
    # Format thủ công để mỗi edge [u, v] nằm compact trên 1 dòng
    items = sorted(test_graphs, key=lambda g: (g["edge_prob"], g["seed"], g["n"]))
    lines = ["{"]
    for i, graph in enumerate(items):
        n = graph["n"]
        edge_prob = graph["edge_prob"]
        seed = graph["seed"]
        adj = graph["adj"]
        key = f"p={edge_prob:.2f}_seed={seed}_n={n}"
        edges = graph_to_edgelist(adj)
        edges_str = ", ".join(f"[{u}, {v}]" for u, v in edges)
        comma = "," if i < len(items) - 1 else ""
        lines.append(f'  "{key}": {{')
        lines.append(f'    "n": {n},')
        lines.append(f'    "edge_prob": {edge_prob:.2f},')
        lines.append(f'    "seed": {seed},')
        lines.append(f'    "edges": [{edges_str}]')
        lines.append(f'  }}{comma}')
    lines.append("}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  Đã lưu: data/test_graphs.json")


def save_raw_csv(records):
    """Lưu số liệu thô vào results/raw/results.csv."""
    path = os.path.join(BASE, "results", "raw", "results.csv")
    fieldnames = ["n", "edge_prob", "seed", "algo", "time", "size", "valid", "opt_size", "gap"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = record.copy()
            if row["opt_size"] is None:
                row["opt_size"] = ""
            if row["gap"] is None:
                row["gap"] = ""
            writer.writerow(row)
    print(f"  Đã lưu: results/raw/results.csv")


def summarize_records(records, group_fields):
    """Tính trung bình thời gian, kích thước nghiệm và gap theo nhóm."""
    groups = {}
    for record in records:
        key = tuple(record[field] for field in group_fields)
        groups.setdefault(key, []).append(record)

    summaries = []
    for key, items in sorted(groups.items()):
        summary = dict(zip(group_fields, key))
        gaps = [item["gap"] for item in items if item["gap"] is not None]
        opt_sizes = [item["opt_size"] for item in items if item["opt_size"] is not None]
        summary.update({
            "runs":     len(items),
            "time":     mean([item["time"] for item in items]),
            "size":     mean([item["size"] for item in items]),
            "valid":    all(item["valid"] for item in items),
            "opt_size": mean(opt_sizes) if opt_sizes else None,
            "gap":      mean(gaps) if gaps else None,
        })
        summaries.append(summary)
    return summaries


def save_comparison_table(records):
    """Lưu bảng so sánh dạng text vào results/comparison/summary.txt."""
    path = os.path.join(BASE, "results", "comparison", "summary.txt")

    summaries = summarize_records(records, ("edge_prob", "n", "algo"))
    ns = sorted({r["n"] for r in records})
    algos = [a for a, _ in ALGO_DEFS]

    col_w = 38
    header = f"{'p':>5}  {'n':>4}  " + "".join(f"{a:<{col_w}}" for a in algos)
    sep = "-" * len(header)

    lines = [
        "BÀI TOÁN TẬP THỐNG TRỊ TỐI THIỂU – KẾT QUẢ SO SÁNH",
        f"(đồ thị ngẫu nhiên, p={EDGE_PROBS}, seed={SEEDS})\n",
        "Ký hiệu: thời_gian_tb / |D|_tb / gap_tb  (— = không chạy; gap = |D|-OPT)\n",
        header, sep,
    ]

    for edge_prob in EDGE_PROBS:
        for n in ns:
            row_parts = [f"{edge_prob:>5.2f}  {n:>4}  "]
            for algo in algos:
                match = next((
                    r for r in summaries
                    if r["edge_prob"] == edge_prob and r["n"] == n and r["algo"] == algo
                ), None)
                if match:
                    gap_text = f" / gap={match['gap']:+.2f}" if match["gap"] is not None else ""
                    valid_text = "" if match["valid"] else " / SAI"
                    cell = f"{match['time'] * 1000:.2f}ms / |{match['size']:.2f}|{gap_text}{valid_text}"
                else:
                    cell = "—"
                row_parts.append(f"{cell:<{col_w}}")
            lines.append("".join(row_parts))
        lines.append(sep)

    lines += [
        "\nKẾT LUẬN:",
        "  Vét cạn  : chính xác, chỉ dùng cho n nhỏ vì tăng theo 2^n",
        "  Nhánh cận: chính xác, thường nhanh hơn vét cạn nhờ cắt nhánh",
        "  Tham lam : rất nhanh, nghiệm xấp xỉ và không luôn tối ưu",
        "  ACO      : có thể cải thiện nghiệm tham lam ở một số trường hợp, nhưng chậm hơn",
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

    # Nhóm dữ liệu trung bình theo (algo, n), gộp tất cả p và seed
    summaries = summarize_records(records, ("n", "algo"))
    data = {a: {} for a in algos}
    for r in summaries:
        data[r["algo"]][r["n"]] = r

    all_ns = sorted({r["n"] for r in summaries})

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
    ax.set_title("So sánh thời gian thực thi trung bình\n(Minimum Dominating Set)")
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
    ax.set_title("So sánh chất lượng nghiệm trung bình\n(Minimum Dominating Set)")
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
    summaries = summarize_records(records, ("edge_prob", "n", "algo"))
    ns = sorted({r["n"] for r in records})
    algos = [a for a, _ in ALGO_DEFS]

    for edge_prob in EDGE_PROBS:
        data = {
            (r["n"], r["algo"]): r for r in summaries
            if r["edge_prob"] == edge_prob
        }

        print(f"  edge_prob = {edge_prob:.2f}")
        headers = ["n"] + algos
        rows = []
        for n in ns:
            row = [str(n)]
            for algo in algos:
                rec = data.get((n, algo))
                if rec:
                    gap_text = f" g{rec['gap']:+.2f}" if rec["gap"] is not None else ""
                    row.append(f"{rec['time'] * 1000:.2f}ms |{rec['size']:.2f}|{gap_text}")
                else:
                    row.append("—")
            rows.append(row)

        print_table(headers, rows)
        print()

    print()
    print("  Chú thích: thời_gian_tb  |kích_thước_D_tb|  gap_tb")


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
  │ Vét cạn      │ O(2^n · n)     │ Có       │ Đúng hoàn toàn, chỉ dùng n nhỏ      │
  ├──────────────┼────────────────┼──────────┼──────────────────────────────────────┤
  │ Nhánh cận    │ O(2^n) w.case  │ Có       │ Đúng, nhanh hơn nhờ cắt nhánh        │
  │              │                │          │ Hiệu quả phụ thuộc cấu trúc đồ thị   │
  ├──────────────┼────────────────┼──────────┼──────────────────────────────────────┤
  │ Tham lam     │ O(n(n+m))      │ Không    │ Nhanh, xấp xỉ H(Δ+1)·OPT            │
  │              │                │          │ Không đảm bảo tối ưu                 │
  ├──────────────┼────────────────┼──────────┼──────────────────────────────────────┤
  │ ACO          │ O(iter·ant·n²) │ Không    │ Có thể cho nghiệm tốt hơn tham lam; │
  │              │                │          │ đổi lại thời gian chạy lớn hơn       │
  └──────────────┴────────────────┴──────────┴──────────────────────────────────────┘

  Khi nào dùng thuật toán nào?
    n ≤ 16        →  Vét cạn   (chắc chắn tối ưu, đơn giản nhất)
    16 < n ≤ 30   →  Nhánh cận (vẫn tối ưu, đủ nhanh)
    n > 30        →  Tham lam  (ưu tiên tốc độ) hoặc ACO (ưu tiên tìm nghiệm tốt hơn)
""")



# Main

if __name__ == "__main__":
    print_small_demo()

    print("=" * 65)
    print(f"  BENCHMARK  (đồ thị ngẫu nhiên, p={EDGE_PROBS}, seed={SEEDS})")
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
