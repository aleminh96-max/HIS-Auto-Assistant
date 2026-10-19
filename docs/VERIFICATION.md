# Kiểm chứng và phần việc còn lại

Bản 0.1 là bản thử mô phỏng. Kết quả tự động cụ thể trong `test-results.xml` và artifact GitHub Actions. Những kiểm thử tọa độ/DPI là kiểm thử toán học của cấu hình, không phải thử GUI thật trên mọi màn hình.

| Phạm vi | Bằng chứng / trạng thái |
|---|---|
| Dashboard 12 mục theo trạng thái đã lưu, đối chiếu, hoặc bỏ qua có lý do; ngữ cảnh đổi khóa trạng thái | pytest-qt `test_dashboard_twelve_items_never_claims_unverified_completion` trên Windows, Python 3.13 |
| Workflow 12 bước gồm tạo phiếu, ký/in mô phỏng, xử lý bỏ qua, tiếp tục và khôi phục kết quả không rõ | pytest workflow, documents và GUI trên Windows, Python 3.13 |
| Ba nguồn số lượng lĩnh dược khớp toa trước khi chuẩn bị; không có thuốc thì bỏ qua kèm lý do | pytest domain và GUI |
| ICD, lịch sử mũi 1–3, số đo, ba tờ qua ngày, không thuốc tờ 3 | pytest domain |
| Tách toa, chống trùng, sai lệch số lượng | pytest domain, GUI |
| CRUD mẫu, phiên bản, nhập/xuất, sao lưu | pytest storage |
| Duyệt, dừng khi đổi bệnh nhân/khoa/đợt/quyền, không lặp sau lỗi | pytest workflow |
| Ký đúng nội dung, thiếu quyền, kết quả chưa rõ, chỉ ký một lần | pytest documents (mô phỏng) |
| Máy in không tồn tại, chưa ký, chưa duyệt, lệnh in trùng | pytest documents (mô phỏng) |
| GUI nhập → chuẩn bị → duyệt → ba tờ; sửa sau duyệt | pytest-qt offscreen trên Windows |
| Nhận diện ảnh duy nhất / mơ hồ, tọa độ tương đối | pytest với ảnh tổng hợp |
| Probe UIA metadata eHospital | PASS READ-ONLY — lần chạy 2026-10-19 thấy 1 tiến trình, 1 cửa sổ 1936×1048, classifier gợi ý `inpatient_record` từ nhãn tĩnh allowlist. Không đọc title hoặc giá trị trường; không xác minh khoa, bệnh nhân, đợt điều trị hay quyền. |
| Probe Win32 metadata eHospital | PASS READ-ONLY — baseline trước đó: 2 tiến trình, 4 cửa sổ (311×102, 1936×1048, 476×369, 1936×1048); chưa chạy lại Win32 probe trong lần kiểm tra 2026-10-19. |
| eHospital trên máy khảo sát | FPT Information System GMC; Product 4.0.0.0 / File 4.0.1.0, build .NET 4.0 ngày 27-04-2016. Người vận hành xác nhận phiên đang mở là sản xuất; không có thao tác nghiệp vụ. |
| API/SDK chính thức cho bản cài đặt này | NOT VERIFIED — chưa có API contract, endpoint test hoặc cơ chế xác thực từ bệnh viện/FPT. Tài liệu FPT nói về FHIR ở các giải pháp liên thông khác không xác nhận API khả dụng trong cài đặt này. |
| Ánh xạ ID/Name UIA của trường nghiệp vụ | NOT VERIFIED — probe không đọc giá trị hoặc nhãn ngoài allowlist; chưa đủ căn cứ để điền trường. |
| Điều hướng desktop ngoài tiến trình qua UIA | NOT VERIFIED — chưa điều hướng F5/F7 hoặc popup. |
| Windows 1366×768, 1920×1080, 2560×1440 và DPI 100/125/150% | NOT VERIFIED trên thiết bị thật |
| Bảng thuốc HIS cuộn ngang, checkbox đã chọn, F5/F7 ngoài tiến trình | NOT VERIFIED |
| PDF browser, Crystal Reports BCLS_273_EMR / BCLS_101_EMR | NOT IMPLEMENTED |
| Ký thật, ký hủy, cảnh báo/xác thực HIS, trạng thái chữ ký trên HIS | NOT VERIFIED |
| Hàng đợi Windows, máy in vật lý, khổ giấy, nhiều trang | NOT VERIFIED |
| Tự tạo/lưu/in phiếu lĩnh dược; in đúng toa mua ngoài | NOT IMPLEMENTED |
| Wizard hiệu chỉnh đầy đủ, khôi phục cấu hình từ UI, bộ cài | NOT IMPLEMENTED |
| Mã hóa dữ liệu local, đánh giá bảo mật và nghiệm thu bệnh viện | NOT VERIFIED |

## Cửa kiểm soát tích hợp thật

1. CNTT/FPT cung cấp môi trường test/bệnh nhân giả hoặc API test chính thức cho đúng bản cài đặt; phiên sản xuất hiện tại không dùng cho điều hướng/thao tác.
2. Trong môi trường đó, mở lần lượt các màn hình mục tiêu; chỉ thu ID/type/state/control label đã kiểm duyệt, tuyệt đối không lưu giá trị bệnh nhân.
3. Xác minh danh tính trên từng cửa sổ chính, F5, F7, ký, PDF, báo cáo và lĩnh dược. Không dựa riêng tiêu đề cửa sổ.
4. Thử trên dữ liệu giả: lưu/đọc lại, timeout, hủy, crash và tiếp tục. Lưu bất định không tự retry.
5. Kiểm thử tất cả thiết bị/DPI/máy in và các lỗi trong master prompt; ghi PASS/FAIL/NOT VERIFIED riêng.
6. Người có thẩm quyền nghiệm thu, xác nhận bảo mật và phạm vi dùng trước khi mở adapter ghi thật.
