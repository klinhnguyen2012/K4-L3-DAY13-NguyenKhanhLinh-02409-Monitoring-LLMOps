# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Cập nhật ngày 2026-10-04. Bản sửa CP2 đã được kiểm tra trên commit `b8d2b7ec95eab50a267c91a5146984ee89b28372`; sau khi commit báo cáo, lấy SHA cuối bằng `git rev-parse HEAD` để nộp cùng URL repository.

## 1. Thông tin học viên

- **Họ và tên:** Nguyen Khanh Linh
- **MSSV:** 02409
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/klinhnguyen2012/K4-L3-DAY13-NguyenKhanhLinh-02409-Monitoring-LLMOps.git
- **Commit sửa CP2 đã kiểm tra:** `b8d2b7ec95eab50a267c91a5146984ee89b28372`.
- **Commit SHA cuối để nộp:** lấy bằng `git rev-parse HEAD` sau khi commit báo cáo/evidence và ghi trên LMS/Codelabs. Không thể ghi chính SHA của commit chứa báo cáo vào nội dung báo cáo đó.
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-02409` (đã đổi trong Project Settings và xác nhận tên mới trên Langfuse ngày 2026-10-04). Project ID giữ nguyên nên traces và prompt versions vẫn thuộc cùng project.

## 2. Evidence index

Các file evidence `01`–`14` hiện đã có. Ảnh Langfuse 06–10 và 14 được chụp trước khi đổi tên project nên vẫn hiện `day13-k3-l3b-02409`; project ID và dữ liệu trace/prompt không đổi. Ghi chú rà soát: ảnh 08 chưa thấy `correlation_id`; ảnh 12 là số liệu aggregate challenge, còn thời gian challenge được ghi ở mục 7; ảnh 14 thấy correlation ID nhưng lộ thuộc tính `scope.attributes.public_key` phía dưới — cần crop/ẩn phần đó trước khi nộp.

| Evidence | Đường dẫn / trạng thái |
|---|---|
| Pytest cuối | [01-pytest.txt](evidence/01-pytest.txt) — chạy 2026-10-04; 35 passed |
| Log validator | [02-log-validator.txt](evidence/02-log-validator.txt) — chạy 2026-10-04; 100/100 |
| Dashboard validator | [03-dashboard-validator.txt](evidence/03-dashboard-validator.txt) — chạy 2026-10-04; 6/6 |
| Structured log | [04-structured-log.png](evidence/04-structured-log.png) — có ảnh; rà lại sau khi chốt code |
| PII redaction | [05-pii-redaction.png](evidence/05-pii-redaction.png) — có ảnh test dữ liệu giả đã scrub |
| Trace list | [06-trace-list.png](evidence/06-trace-list.png) — project cá nhân và traces tự tạo |
| Trace waterfall | [07-trace-waterfall.png](evidence/07-trace-waterfall.png) — root agent, retrieval và generation |
| Trace metadata | [08-trace-metadata.png](evidence/08-trace-metadata.png) — model, prompt/version, usage và cost; correlation ID đối chiếu được ở Evidence 14 và mục 5/7 |
| Prompt versions | [09-prompt-versions.png](evidence/09-prompt-versions.png) — v1/v2 với labels `baseline`, `candidate`, `production` |
| Prompt rollback | [10-prompt-rollback.png](evidence/10-prompt-rollback.png) — trạng thái sau rollback; trace IDs của v2 trước và v1 sau rollback ghi ở mục 5 |
| Dashboard runtime | [11-dashboard-overview.png](evidence/11-dashboard-overview.png) — sáu panel có dữ liệu trong rolling 60 phút |
| Incident metric | [12-incident-metric.png](evidence/12-incident-metric.png) — aggregate 5 request challenge; thời gian challenge ghi ở mục 7 |
| Incident log | [13-incident-log.png](evidence/13-incident-log.png) — `response_sent` của `req-98640d6a`, latency 3492 ms |
| Incident trace | [14-incident-trace.png](evidence/14-incident-trace.png) — cùng correlation ID; retrieval span 2.50 s. Crop/ẩn `scope.attributes.public_key` trước khi nộp |

## 3. Kết quả kỹ thuật

Tests và validators đã chạy lại ngày 2026-10-04 trên bản sửa hiện tại: 35 tests pass, dashboard 6/6, log validator 100/100 với 34 records và 17 correlation IDs. Các số liệu runtime trong ảnh evidence 11 là snapshot cũ gồm 19 request/53 log records; dashboard dùng rolling window 60 phút.

| Nội dung | Baseline | Kết quả hiện tại | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100; 21 records; thiếu required fields/enrichment; 0 correlation ID; 0 PII leak | 100/100; 34 records; 17 correlation IDs; 0 field/enrichment thiếu; 0 PII leak | Chạy 2026-10-04; output tại `evidence/02-log-validator.txt`. |
| `validate_dashboard.py` | Chưa ghi baseline | 6/6 panel | Chạy 2026-10-04; output tại `evidence/03-dashboard-validator.txt`. |
| `pytest` | Chưa ghi baseline | 35 passed | Chạy 2026-10-04; output tại `evidence/01-pytest.txt`. |
| Số traces hợp lệ | Chưa ghi | 5 challenge traces + 10 baseline traces đã truy vấn qua API v2 | Có span tree và correlation metadata. |
| Số PII leak | Chưa ghi | 0 trong 34 log records mới nhất đã kiểm tra | Log validator không phát hiện PII theo các pattern được kiểm tra. |
| Latency P95 / TTFT P95 | Chưa ghi | Evidence 11 snapshot: P95 3492 ms / TTFT P95 55 ms; P99 3492 ms, 19 response | Rolling 60 phút trên workload lab; P95 vượt ngưỡng 3000 ms, không đại diện production traffic. |
| Retrieval success rate | Chưa ghi | Ảnh 11 ghi 100% tại thời điểm chụp | Sau commit `b8d2b7e`, runtime tính trên mọi log record có `tool_success` dạng boolean, gồm `response_sent` và `request_failed`; ảnh 11 chưa được chụp lại. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa context Structlog cũ. Nó nhận `x-request-id` đúng mẫu `req-` + 8 ký tự hex hoặc tự sinh ID mới, bind vào context, lưu trong `request.state`, rồi trả qua response header cùng `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`, cùng timestamp, event, service và correlation ID.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` chạy sau khi định dạng exception và trước JSONL file processor. Processor scrub chuỗi trong toàn bộ event dictionary, gồm các dictionary/list lồng nhau.
- **Cách kiểm chứng kết quả:** Middleware tests kiểm tra xóa context, nhận/tạo ID, bind và response headers. PII test ghi email, điện thoại Việt Nam, CCCD và số thẻ giả vào metadata/payload lồng nhau rồi xác nhận file không chứa giá trị thô. Log validator hiện báo 100/100 và 0 PII leak.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Query observations API v2 của project đang cấu hình; xác nhận 15 observations thuộc 5 challenge traces và 30 observations thuộc 10 baseline traces. Danh sách UI nằm ở [Evidence 06](evidence/06-trace-list.png).
- **Cấu trúc root/retrieval/generation observations:** `LabAgent.run` là agent observation; bên trong có child `retrieval` kiểu `retriever` và `llm-generation` kiểu `generation`. Generation ghi model, liên kết prompt, usage input/output, cost và preview đã scrub.
- **Cách nối trace với log:** `correlation_id` trong metadata trace khớp field cùng tên trong JSONL. Ví dụ `req-98640d6a` nối trace `0648d07ce148f5812676ff7003a0bf2b`.
- **Prompt name:** `day13-chat`; ban đầu không có managed prompt `production`, nên app dùng local fallback. Đã tạo prompt managed và xác minh trace dùng Langfuse.
- **Version/label baseline:** v1 có `baseline` và `production`.
- **Version/label candidate:** v2 có `candidate`; candidate hướng dẫn chỉ dựa evidence trong context và không đoán khi thiếu căn cứ.
- **Trace ID của v2:** `7d4e28c2a8a5461bf8d477d55f160dfa`, correlation `req-c2a70002`, generation dùng `day13-chat` v2.
- **Cách promote và rollback `production`:** `scripts/set_prompt_production.py --version 2` promote v2; `--version 1` rollback. Do cache SDK có TTL 60 giây và stale-while-revalidate, trace cuối sau refresh là `e707ed7975a589f13e21cf3691b6a420`, correlation `req-c2a70005`, generation dùng Langfuse v1. Production hiện ở v1.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard runtime nằm ở `dashboard/index.html`, chạy qua `scripts/dashboard.py`, đọc log thật với rolling window 60 phút và refresh 30 giây. Mỗi panel hiển thị giá trị thực cùng vạch threshold trên một thang đo chung; panel Errors có thêm vạch retrieval success. Retrieval success dùng mọi record có `tool_success` dạng boolean, kể cả request lỗi. Validator 6/6; ảnh runtime trước bản sửa đã lưu tại `evidence/11-dashboard-overview.png`.
- **SLO và lý do chọn:** `fast_successful_requests`: 99.5% request thành công với latency không quá 3000 ms trong cửa sổ 28 ngày, theo `config/slo.yaml`.
- **Cách tính error budget:** 100% − 99.5% = 0.5%. Với 10,000 requests trong cửa sổ SLO, ngân sách tối đa là 50 request không đạt.
- **Ba alert và runbook tương ứng:** `HighLatencyP95` (>3000 ms/5m, warning), `ElevatedRequestErrorRate` (>2%/5m, critical), `LowRetrievalSuccess` (<90%/10m, warning); Slack `#k4-l3b-alerts`, owner và runbook đã cấu hình. Headings `## Alert 1/2/3` khớp anchors trong YAML; test kiểm tra cả cấu hình và headings đích.

## 7. Điều tra challenge

- **Challenge ID và nguồn:** `day13-k4-l3b-monitoring-llmops-v1` từ commit Lab Coach `0a7eadbeb938ccb265aa2bf3786bd126ce316943`. Git blob của `config/challenge.json` local khớp chính xác file trong commit đó; file local được Git ignore và không có trong index.

### Lượt chính có evidence 12–14 (2026-10-02)

- **Khoảng thời gian điều tra:** baseline 10 response lúc 08:24:09–08:24:13 UTC; challenge 5 response lúc 09:04:41–09:04:53 UTC ngày 2026-10-02 (16:04 giờ Việt Nam). Sau workload challenge đã tắt incident. Evidence 12 tổng hợp đúng năm correlation IDs challenge; khoảng thời gian được đối chiếu qua `ts` của log.
- **Triệu chứng từ metrics so với baseline:** baseline P50 413 ms, P95/P99 934 ms, TTFT P95 55 ms (10 response, retrieval thành công 10/10). Challenge P50 2936 ms, P95/P99 3492 ms, TTFT P95 vẫn 55 ms (5 response, 0 lỗi, retrieval thành công 5/5, tổng cost $0.00861). P95 tăng 2558 ms, khoảng 3.74 lần; một challenge request vượt ngưỡng 3000 ms. Các latency này lấy từ `response_sent.latency_ms`, không dùng thời gian phía client của load test.
- **Log và correlation ID:** [Evidence 13](evidence/13-incident-log.png) ghi `req-98640d6a`; event `response_sent`, latency 3492 ms, retrieval thành công, feature `monitoring`.
- **Trace và span:** [Evidence 14](evidence/14-incident-trace.png), trace `0648d07ce148f5812676ff7003a0bf2b`; metadata hiển thị cùng `correlation_id=req-98640d6a`. Retrieval span mất 2.500 s, generation khoảng 0.161 s. Các trace challenge còn lại cũng có retrieval khoảng 2.50 s và generation khoảng 0.155–0.157 s.
- **Root cause:** độ trễ retrieval/RAG chiếm khoảng 2.5 giây trong request, trong khi generation chỉ khoảng 0.16 giây; điều này giải thích P95 vượt ngưỡng 3000 ms. Kết luận khớp metrics, JSONL và span durations.
- **Fix action:** tắt injected challenge incident sau workload; API xác nhận tất cả incidents ở trạng thái false.
- **Preventive measure:** alert P95 >3000 ms trong 5 phút; dashboard 60 phút; tiếp tục nối metrics → correlation ID → retrieval span trước khi cân nhắc rollback/config change.

### Lượt xác minh bổ sung (2026-10-04)

- **Metrics và thời gian:** baseline 10 response lúc 08:42:57–08:42:58 UTC có P50 159 ms, P95 916 ms, TTFT P95 55 ms; challenge 5 response lúc 08:58:50–08:59:00 UTC có P50 2664 ms, P95 2665 ms, TTFT P95 55 ms, 0 lỗi, retrieval thành công 5/5 và tổng cost $0.01158. P95 tăng 1749 ms (~2.91 lần) so với baseline nhưng **không vượt** ngưỡng 3000 ms. Các số này lấy từ `response_sent` trong log, không lấy thời gian phía client.
- **Log cùng request:** `req-8bdb3aa3`, session `k4-l3b-challenge-s05`, event `response_sent` lúc 08:59:00.899793 UTC, `latency_ms=2665`, `tool_success=true`.
- **Trace cùng request:** Langfuse trace `f28b5d65e188b5794dca3a1ad98ed1f2` có metadata `correlation_id=req-8bdb3aa3`; root `lab-agent-run` 2.67 s, child `retrieval` 2.51 s, `llm-generation` 0.16 s. Retrieval chiếm phần lớn độ trễ, phù hợp metric và log.
- **Kết luận và xử lý:** challenge `rag_slow` làm retrieval chậm so với baseline; response vẫn thành công. Đã tắt incident lúc 09:27:48 UTC, có event `incident_disabled` trong log. Giữ cảnh báo latency, dùng correlation ID để kiểm tra retrieval span trước khi thay đổi prompt hoặc model.
- Lượt này là kiểm chứng thêm; ảnh 12–14 vẫn thuộc **lượt chính ngày 2026-10-02**, không được dùng chúng để chứng minh các ID của lượt 2026-10-04.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Dùng correlation ID xuyên middleware, log và trace để tìm đúng request; scrub PII trước bước ghi file để log hữu ích mà không lưu giá trị nhạy cảm thô.
- **Một lỗi/blocker đã gặp:** ban đầu Langfuse trả 404 do chưa có managed prompt `day13-chat`/`production`; endpoint trace cũ trả 410 vì organization mới cần API v2.
- **Cách tìm nguyên nhân và xử lý:** Tạo prompt v1/v2, xác minh trace source/version; promote v2 rồi rollback về v1 và chờ cache refresh. Đọc spans bằng observations API v2.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics khoanh vùng triệu chứng/thời gian; logs chọn request bằng correlation ID; trace cho biết span cụ thể chậm hoặc lỗi; kết luận root cause cần khớp cả ba nguồn.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Version/label giúp xác định prompt của request và rollback khi có regression; token/cost cho thấy mức tiêu thụ; SLO và error budget định lượng mức chất lượng cho phép.
- **Điều quan trọng nhất đã học:** Một metric như P95 vượt SLO chỉ cho biết request đang chậm, chưa chỉ ra nguyên nhân. Dùng `correlation_id` để nối metric với đúng log và trace giúp xác định retrieval là span chiếm phần lớn độ trễ (~2.5 giây), thay vì quy lỗi cho generation hoặc prompt khi chưa có bằng chứng.
- **Hạn chế hoặc phần chưa hoàn thành:** Ảnh Langfuse 06–10 và 14 vẫn hiện tên cũ trước khi project được đổi sang mẫu K4; crop/ẩn `public_key` khỏi ảnh 14; cân nhắc cập nhật ảnh 08 để correlation ID hiện trực tiếp trong cùng ảnh metadata. Ảnh dashboard 11 được chụp trước bản sửa retrieval success. SHA cuối cần lấy sau commit báo cáo và điền trên LMS/Codelabs. Dashboard/metrics chỉ dựa trên workload lab, không phải production traffic.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence được tạo/kiểm tra trên commit SHA cuối; chạy lại sau khi commit báo cáo và ghi SHA đó trên LMS/Codelabs.
- [x] Chạy lại tests/validators; output mới của 01–03 đã lưu dạng `.txt`; rà soát 04–05 trước khi nộp.
- [x] Lưu ảnh trace list, waterfall, metadata, prompt versions và trạng thái rollback thành 06–10; trace IDs version trước/sau được ghi ở mục 5.
- [ ] Rà soát 08 để thêm correlation ID nếu có thể; ảnh 14 hiện nối correlation ID với trace.
- [x] Lưu dashboard runtime và incident metric/log/trace thành 11–14.
- [x] Incident evidence nối metric → log → trace: challenge aggregate (12), `req-98640d6a` trong log (13), cùng correlation ID trong trace (14).
- [ ] Ảnh Langfuse project cá nhân không lộ key/secret hoặc nội dung nhạy cảm.
- [ ] Repository cài đặt và chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác. `config/challenge.json` đã được bỏ khỏi Git index và `.gitignore` đang bỏ qua file local này; không còn staged removal.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
