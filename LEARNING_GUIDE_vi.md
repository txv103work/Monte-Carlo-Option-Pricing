# Hướng dẫn học cùng dự án

Mục tiêu không phải chỉ chạy được mã nguồn, mà là có thể tự giải thích từng
bước khi phỏng vấn.

## 1. Những ý tưởng cần hiểu

### Từ SDE đến công thức mô phỏng

Trong độ đo trung hòa rủi ro, giá cổ phiếu thỏa mãn

$$
dS_t=rS_tdt+\sigma S_tdW_t.
$$

Áp dụng công thức Itô cho \(\log S_t\) thu được

$$
d\log S_t=\left(r-\frac12\sigma^2\right)dt+\sigma dW_t.
$$

Tích phân từ 0 đến \(T\):

$$
S_T=S_0\exp\left[
\left(r-\frac12\sigma^2\right)T+\sigma W_T
\right].
$$

Vì \(W_T\sim N(0,T)\), ta có thể viết \(W_T=\sqrt{T}Z\), trong đó
\(Z\sim N(0,1)\). Đây chính là công thức được dùng để sinh trực tiếp \(S_T\).

### Vì sao dùng xác suất trung hòa rủi ro?

Trong định giá không-arbitrage, lợi suất kỳ vọng thực tế của cổ phiếu không
xuất hiện trong công thức. Dưới độ đo \(\mathbb Q\), tốc độ tăng trung bình của
cổ phiếu được thay bằng lãi suất phi rủi ro \(r\). Giá quyền chọn là kỳ vọng
chiết khấu của payoff:

$$
V_0=e^{-rT}\mathbb E^{\mathbb Q}[H(S_T)].
$$

### Monte Carlo đang xấp xỉ điều gì?

Ta sinh \(N\) mẫu độc lập \(S_T^{(1)},\ldots,S_T^{(N)}\), rồi thay kỳ vọng bằng
trung bình mẫu:

$$
\widehat V_N=e^{-rT}\frac1N\sum_{i=1}^NH(S_T^{(i)}).
$$

Theo luật số lớn, \(\widehat V_N\) hội tụ về \(V_0\). Theo định lý giới hạn
trung tâm, sai số chuẩn giảm xấp xỉ theo \(1/\sqrt N\).

## 2. Thứ tự đọc mã

1. Đọc `OptionParameters` trong `src/option_pricing/pricing.py`.
2. Tự tính `black_scholes_price` bằng giấy với bộ tham số mặc định.
3. Đọc `monte_carlo_price` và nối từng dòng với công thức toán tương ứng.
4. Chạy notebook, thay đổi lần lượt \(N\), \(\sigma\), \(K\) và \(T\).
5. Đọc `run_experiments.py` để hiểu cách tạo một thí nghiệm tái lập.
6. Đọc các kiểm thử trong `tests/test_pricing.py`.

## 3. Bài tập nên tự làm

- Giải thích vì sao không cần mô phỏng toàn bộ đường đi để định giá quyền chọn
  European.
- Kiểm chứng put-call parity bằng cả giá Black--Scholes và Monte Carlo.
- Vẽ histogram của payoff chiết khấu và nhận xét về phân phối của nó.
- Chạy 100 thí nghiệm độc lập và kiểm tra khoảng 95% khoảng tin cậy có chứa giá
  Black--Scholes hay không.
- So sánh sai số chuẩn khi dùng và không dùng antithetic variates.
- Thêm dividend yield \(q\) vào cả mô hình GBM và công thức Black--Scholes.

## 4. Câu hỏi phỏng vấn cần trả lời được

- Geometric Brownian motion là gì và vì sao giá mô phỏng luôn dương?
- Phân biệt độ đo xác suất thực tế \(\mathbb P\) và trung hòa rủi ro
  \(\mathbb Q\).
- Tại sao dùng Black--Scholes để đối chứng?
- Khoảng tin cậy Monte Carlo có ý nghĩa gì?
- Vì sao tăng số mô phỏng lên 100 lần chỉ giảm sai số khoảng 10 lần?
- Antithetic variates giảm phương sai như thế nào?
- Những giả định nào của Black--Scholes không phù hợp hoàn toàn với thị trường?

Chỉ nên đưa dự án vào CV sau khi bạn có thể tự chạy lại, giải thích các công
thức chính và mô tả ít nhất một hạn chế của mô hình.

