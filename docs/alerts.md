# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1 — HighLatencyP95

- Severity/duration: `warning`, `p95(response_sent.latency_ms) > 3000` trong `5m`.
- Kênh/owner: Slack `#k4-l3b-alerts`; `student-02409`.
- SLI/SLO: latency P95; fast-successful-request SLO ≤3000 ms.
- Ảnh hưởng: người dùng đợi lâu hơn để nhận câu trả lời.
- Kiểm tra: xác nhận P95/P99 và time range trên dashboard; lọc log lấy `correlation_id`; mở trace tương ứng và so sánh retrieval với generation.
- Mitigation: rollback prompt/config gần nhất nếu trace chỉ ra regression; giảm tải demo nếu cần; lưu correlation ID và thời điểm trước thay đổi.

## Alert 2 — ElevatedRequestErrorRate

- Severity/duration: `critical`, request-failed/request-received > `2%` trong `5m`.
- Kênh/owner: Slack `#k4-l3b-alerts`; `student-02409`.
- SLI/SLO: tỷ lệ request lỗi, với ngưỡng guardrail 2%.
- Ảnh hưởng: một phần người dùng không nhận được câu trả lời.
- Kiểm tra: xem error rate và breakdown theo loại lỗi; lọc `request_failed` trong log theo thời gian/feature; mở trace theo correlation ID để tìm span lỗi.
- Mitigation: khôi phục dependency hoặc prompt/config gần nhất đã đổi; tắt practice incident nếu đang bật; xác nhận request thành công trước khi đóng alert.

## Alert 3 — LowRetrievalSuccess

- Severity/duration: `warning`, retrieval tool success < `90%` trong `10m`.
- Kênh/owner: Slack `#k4-l3b-alerts`; `student-02409`.
- SLI/guardrail: tỷ lệ retrieval thành công, ngưỡng tối thiểu 90%.
- Ảnh hưởng: câu trả lời có thể thiếu căn cứ hoặc không đầy đủ.
- Kiểm tra: xem retrieval success và error breakdown; lấy một correlation ID có `tool_success=false`; kiểm tra retrieval span và context được trả về.
- Mitigation: phục hồi cấu hình/index retrieval gần nhất; nếu chỉ xảy ra trong practice, tắt incident sau khi thu đủ evidence; chạy lại một truy vấn xác nhận.
