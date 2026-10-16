# Hướng dẫn dùng thử

1. Giải nén đầy đủ gói Windows; chạy `HIS-Auto-Assistant.exe`.
2. Thẻ **Nhập dữ liệu** → **Nạp dữ liệu GIẢ để chạy thử**. Kiểm tra các ô; tự tích xác nhận lịch sử và nội dung tờ 3. Không sử dụng cho bệnh nhân thật.
3. Có thể chọn giang mai sớm: ICD sẽ bị xóa để người dùng tự chọn, lần tiêm để trống. Nhóm tiềm ẩn: chọn mũi 1, 2 hoặc 3 từ lịch sử đã xác nhận. Không tự xác định phác đồ hoặc lịch hẹn.
4. Nếu cần thử toa: **Soạn toa / lĩnh dược** → nạp danh mục mẫu. Bảng cuộn ngang có các cột tên, số lượng, cách dùng, thời gian, miễn phí, hàm lượng/quy cách, tổng liều và kho. Nhập tổng liều giả đã duyệt cho hai dòng còn `CHƯA DUYỆT`; kiểm tra đúng danh mục TEST; tích duyệt thuốc. Có thể xóa dòng không cần. Không suy tổng liều từ số lượng lọ.
5. Dịch vụ để trống nếu không chỉ định. Danh mục khảo sát chỉ là dữ liệu TEST tùy chọn.
6. **Chuẩn bị hồ sơ** → đọc bản xem trước gồm bệnh án, đợt điều trị, ba tờ, lần đo gốc, toa riêng và dịch vụ → **Duyệt hồ sơ đang xem** → **Bắt đầu**.
7. Mỗi nhịp xử lý một bước; có thể tạm dừng, tiếp tục hoặc dừng khẩn cấp/Esc. Thay đổi dữ liệu sau duyệt sẽ khóa quy trình. Muốn đổi nội dung, chuẩn bị và duyệt lại.
8. Hoàn thành mô phỏng → **Duyệt và ký số tài liệu đang xem**. Đây là hành động duyệt rõ ràng cho đúng phiên bản đang hiển thị. Không ký hai lần; kết quả chưa rõ cần kiểm tra, không tự thử lại.
9. Chọn máy in/khổ/số bản trong cấu hình → **Duyệt và in**. Đây là hàng đợi giả, không in giấy thật. Danh sách máy in Windows chỉ để kiểm tra cấu hình.
10. Trang chủ → **Mở HIS Simulator**. Chọn lỗi giả (đổi bệnh nhân, đổi đợt, sai khoa, HIS treo, thiếu quyền ký, kết quả ký chưa rõ, lỗi lưu tờ 2) để kiểm tra dừng. Không đổi về bình thường rồi mặc định chạy lại thao tác chưa rõ.

## Quản lý mẫu

Điền tên và nội dung ở thẻ nhập dữ liệu, lưu trong Quản lý mẫu. Lưu cùng tên tạo phiên bản mới. Có thể nhân bản, đặt mặc định, xem lịch sử, xuất/nhập JSON, xóa có xác nhận. Mẫu không chứng minh nội dung đúng cho người bệnh. Sao lưu SQLite trước khi nâng cấp. Bản 0.1 chưa có giao diện khôi phục toàn bộ SQLite; có thể nhập lại thư viện mẫu qua JSON.

## Đối chiếu lĩnh dược

Nhập ba đối tượng JSON với cùng mã TEST và số lượng. Ví dụ y lệnh `{"TEST-BENZ": 2}`, tổng hợp `{"TEST-BENZ": 1}`, phiếu lĩnh `{"TEST-BENZ": 1}` phải bị chặn. Chỉ tiếp tục sau khi người dùng giải quyết sai lệch. Chức năng này kiểm tra số lượng, chưa tạo/lưu phiếu lĩnh tự động.

## Lỗi và khôi phục

Workflow lưu `PENDING` trước thao tác. Nếu lỗi, quy trình mới chỉ bỏ qua bước khi backend còn chứng minh đúng nội dung đã lưu. Nếu backend mất trạng thái hoặc kết quả mâu thuẫn, cần kiểm tra thủ công. Không xóa nhật ký để ép chạy lại. Simulator hiện lưu bản ghi trong RAM; đóng ứng dụng sẽ mất bản ghi, trong khi SQLite giữ dấu vết. Với cùng bệnh án/giờ cũ, có thể bị chặn khi mở lại; dùng thời điểm TEST mới để mở phiên thử mới. Bản tiếp theo cần backend simulator bền vững và màn hình đối soát khôi phục.

## Triển khai bệnh viện

Chức năng ghi thật đang khóa bằng mã, không có nút bật. Cần quyền của đơn vị quản lý, ánh xạ UIA đã khảo sát, dữ liệu giả trên môi trường được phép, xác nhận bệnh nhân/đợt trên mọi cửa sổ và toàn bộ ma trận nghiệm thu. Không coi kiểm thử simulator là bằng chứng tương thích eHospital.
