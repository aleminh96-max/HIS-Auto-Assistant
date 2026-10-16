# Kiểm chứng và phần việc còn lại

Bản 0.1 là bản thử mô phỏng. Kết quả tự động cụ thể trong `test-results.xml` và artifact GitHub Actions. Những kiểm thử tọa độ/DPI là kiểm thử toán học của cấu hình, không phải thử GUI thật trên mọi màn hình.

| Phạm vi | Bằng chứng / trạng thái |
|---|---|
| ICD, lịch sử mũi 1–3, số đo, ba tờ qua ngày, không thuốc tờ 3 | pytest domain |
| Tách toa, chống trùng, sai lệch số lượng | pytest domain, GUI |
| CRUD mẫu, phiên bản, nhập/xuất, sao lưu | pytest storage |
| Duyệt, dừng khi đổi bệnh nhân/khoa/đợt/quyền, không lặp sau lỗi | pytest workflow |
| Ký đúng nội dung, thiếu quyền, kết quả chưa rõ, chỉ ký một lần | pytest documents (mô phỏng) |
| Máy in không tồn tại, chưa ký, chưa duyệt, lệnh in trùng | pytest documents (mô phỏng) |
| GUI nhập → chuẩn bị → duyệt → ba tờ; sửa sau duyệt | pytest-qt offscreen trên Windows |
| Nhận diện ảnh duy nhất / mơ hồ, tọa độ tương đối | pytest với ảnh tổng hợp |
| eHospital UIA thực tế / ánh xạ trường / OCR | NOT VERIFIED |
| Thao tác desktop ngoài tiến trình qua UIA | NOT VERIFIED |
| Windows 1366×768, 1920×1080, 2560×1440 và DPI 100/125/150% | NOT VERIFIED trên thiết bị thật |
| Bảng thuốc HIS cuộn ngang, checkbox đã chọn, F5/F7 ngoài tiến trình | NOT VERIFIED |
| PDF browser, Crystal Reports BCLS_273_EMR / BCLS_101_EMR | NOT IMPLEMENTED |
| Ký thật, ký hủy, cảnh báo/xác thực HIS, trạng thái chữ ký trên HIS | NOT VERIFIED |
| Hàng đợi Windows, máy in vật lý, khổ giấy, nhiều trang | NOT VERIFIED |
| Tự tạo/lưu/in phiếu lĩnh dược; in đúng toa mua ngoài | NOT IMPLEMENTED |
| Wizard hiệu chỉnh đầy đủ, khôi phục cấu hình từ UI, bộ cài | NOT IMPLEMENTED |
| Mã hóa dữ liệu local, đánh giá bảo mật và nghiệm thu bệnh viện | NOT VERIFIED |

## Cửa kiểm soát tích hợp thật

1. Đơn vị quản lý cấp quyền khảo sát và môi trường test.
2. Lấy cây UIA và ảnh đã loại thông tin thật; xây adapter theo phiên bản HIS.
3. Xác minh danh tính trên từng cửa sổ chính, F5, F7, ký, PDF, báo cáo và lĩnh dược. Không dựa riêng tiêu đề cửa sổ.
4. Thử trên dữ liệu giả: lưu/đọc lại, timeout, hủy, crash và tiếp tục. Lưu bất định không tự retry.
5. Kiểm thử tất cả thiết bị/DPI/máy in và các lỗi trong master prompt; ghi PASS/FAIL/NOT VERIFIED riêng.
6. Người có thẩm quyền nghiệm thu, xác nhận bảo mật và phạm vi dùng trước khi mở adapter ghi thật.
