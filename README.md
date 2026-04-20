# Bài Toán Tập Thống Trị Tối Thiểu (Minimum Dominating Set)

> Project cuối kỳ môn **Thiết Kế và Đánh Giá Thuật Toán**

---

## Mô tả bài toán

Cho đồ thị vô hướng $G = (V, E)$, tìm tập $D \subseteq V$ có kích thước nhỏ nhất sao cho mọi đỉnh $v \notin D$ đều có ít nhất một hàng xóm thuộc $D$.

**Ứng dụng thực tế:** Đặt số đồn cảnh sát **ít nhất** để bao phủ toàn bộ các tuyến đường trong thành phố — mỗi đồn bảo vệ được con đường nơi nó đứng và các con đường liền kề.

---

## Các thuật toán được cài đặt

| Thuật toán | File | Độ phức tạp | Tối ưu? |
|---|---|---|---|
| Vét cạn (Brute Force) | `src/brute_force.py` | $O(2^n \cdot n)$ | ✅ Có |
| Nhánh cận (Branch & Bound) | `src/branch_bound.py` | $O(2^n)$ worst-case | ✅ Có |
| Tham lam (Greedy) | `src/greedy.py` | $O(n^2)$ | ❌ Xấp xỉ |
| Tối ưu đàn kiến (ACO) | `src/aco.py` | $O(\text{iter} \cdot \text{ant} \cdot n^2)$ | ❌ Xấp xỉ |

### Vét cạn
Thử toàn bộ $2^n$ tập con, kiểm tra từng tập từ nhỏ đến lớn. Tập hợp lệ đầu tiên chính là nghiệm tối ưu. Đảm bảo chính xác tuyệt đối nhưng chỉ khả thi với $n \leq 16$.

### Nhánh cận
Duyệt cây tìm kiếm theo chiều sâu. Tại mỗi nút tìm đỉnh $u$ chưa được thống trị, sau đó phân nhánh: thêm $u$ hoặc một trong các hàng xóm của $u$ vào $D$. Cắt nhánh khi $|D_{\text{hiện tại}}| + \text{LowerBound} \geq \text{best}$. Nhanh hơn vét cạn nhiều lần, dùng được đến $n \approx 30$.

### Tham lam
Mỗi bước chọn đỉnh chưa nằm trong $D$ mà phủ được nhiều đỉnh chưa được thống trị nhất (bản thân + hàng xóm chưa bị phủ). Rất nhanh, nhưng không đảm bảo tối ưu — tỉ lệ xấp xỉ $\leq (\ln \Delta + 1) \cdot \text{OPT}$.

### ACO (Ant Colony Optimization)
Mỗi "kiến" xây dựng lời giải bằng cách chọn đỉnh theo xác suất dựa trên pheromone $\tau$ và heuristic $\eta = \text{bậc} + 1$. Sau mỗi vòng lặp, pheromone bốc hơi và được bồi đắp từ các lời giải tốt. Áp dụng thêm **local search** (loại đỉnh dư thừa) sau mỗi kiến để cải thiện chất lượng.

$$P(v) = \frac{\tau(v)^\alpha \cdot \eta(v)^\beta}{\sum_{u} \tau(u)^\alpha \cdot \eta(u)^\beta}$$

---

## Cấu trúc thư mục

```
minimum-dominating-set-algorithms/
├── src/
│   ├── greedy.py          # Thuật toán tham lam
│   ├── brute_force.py     # Vét cạn
│   ├── branch_bound.py    # Nhánh cận
│   └── aco.py             # ACO
├── data/
│   └── test_graphs.json   # Đồ thị test (sinh tự động)
├── results/
│   ├── raw/
│   │   └── results.csv          # Số liệu thô
│   ├── comparison/
│   │   └── summary.txt          # Bảng so sánh
│   └── plots/
│       ├── time_comparison.png  # Biểu đồ thời gian
│       └── size_comparison.png  # Biểu đồ chất lượng nghiệm
├── main.py                # Script chạy benchmark & lưu kết quả
├── requirements.txt
└── .gitignore
```

---

## Cách chạy

### Yêu cầu
- Python ≥ 3.8
- matplotlib (để vẽ biểu đồ)

```bash
pip install matplotlib
```

### Chạy benchmark

```bash
python main.py
```

Sau khi chạy xong, kết quả được lưu tự động vào thư mục `results/` và `data/`.

---

## Kết quả thực nghiệm

Đồ thị ngẫu nhiên, `edge_prob = 0.3`, `seed = 42`:

| n | Vét cạn | Nhánh cận | Tham lam | ACO |
|---|---|---|---|---|
| 8 | 0.000s \|2\| | 0.000s \|2\| | 0.000s \|2\| | 0.021s \|2\| |
| 16 | 0.000s \|3\| | 0.000s \|3\| | 0.000s \|3\| | 0.058s \|3\| |
| 30 | — | 0.003s \|4\| | 0.000s \|4\| | 0.282s \|4\| |
| 50 | — | — | 0.000s \|5\| | 0.846s \|5\| |
| 100 | — | — | 0.001s \|6\| | 3.907s \|5\| |

`|k|` = kích thước tập thống trị tìm được, `—` = không chạy (quá chậm)

### Biểu đồ thời gian thực thi
![Time Comparison](results/plots/time_comparison.png)

### Biểu đồ chất lượng nghiệm
![Size Comparison](results/plots/size_comparison.png)

---

## Kết luận

| Tiêu chí | Vét cạn | Nhánh cận | Tham lam | ACO |
|---|:---:|:---:|:---:|:---:|
| Nghiệm tối ưu | ✅ | ✅ | ❌ | ❌ |
| Dùng được n lớn | ❌ | ⚠️ | ✅ | ✅ |
| Tốc độ | Chậm nhất | Chậm | Nhanh nhất | Trung bình |
| Chất lượng xấp xỉ | — | — | Khá | Tốt |

**Khi nào dùng thuật toán nào?**
- $n \leq 16$: **Vét cạn** — đơn giản, chắc chắn tối ưu
- $16 < n \leq 30$: **Nhánh cận** — vẫn tối ưu, tốc độ chấp nhận được
- $n > 30$: **Tham lam** (ưu tiên tốc độ) hoặc **ACO** (ưu tiên chất lượng nghiệm)
