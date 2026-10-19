# Hướng dẫn dùng thử

1. Giải nén đầy đủ gói Windows; chạy `HIS-Auto-Assistant.exe`.
2. Thẻ **Nhập dữ liệu** → **Nạp dữ liệu GIẢ để chạy thử**. Kiểm tra các ô; tự tích xác nhận lịch sử và nội dung tờ 3. Không sử dụng cho bệnh nhân thật.
3. Có thể chọn giang mai sớm: ICD sẽ bị xóa để người dùng tự chọn, lần tiêm để trống. Nhóm tiềm ẩn: chọn mũi 1, 2 hoặc 3 từ lịch sử đã xác nhận. Không tự xác định phác đồ hoặc lịch hẹn.
4. Nếu cần thử toa: **Soạn toa / lĩnh dược** → nạp danh mục mẫu. Bảng cuộn ngang có các cột tên, số lượng, cách dùng, thời gian, miễn phí, hàm lượng/quy cách, tổng liều và kho. Nhập tổng liều giả đã duyệt cho hai dòng còn `CHƯA DUYỆT`; kiểm tra đúng danh mục TEST; tích duyệt thuốc. Có thể xóa dòng không cần. Không suy tổng liều từ số lượng lọ.
5. Dịch vụ để trống nếu không chỉ định. Danh mục khảo sát chỉ là dữ liệu TEST tùy chọn.
6. Nếu có thuốc, nhập ba nguồn JSON (y lệnh, tổng hợp, phiếu lĩnh) có cùng mã và số lượng; tổng phải bằng các toa đã duyệt. Kiểm tra ba nguồn trước khi chuẩn bị. Không có thuốc thì để trống cả ba.
7. **Chuẩn bị hồ sơ** → đọc bản xem trước gồm bệnh án, đợt điều trị, ba tờ, lần đo gốc, toa riêng và dịch vụ → **Duyệt hồ sơ đang xem** → **Bắt đầu**.
8. Workflow lần lượt chạy 12 mục. Mục không áp dụng sẽ được bỏ qua và nêu lý do. Có thể tạm dừng, tiếp tục hoặc dừng khẩn cấp/Esc. Thay đổi dữ liệu sau duyệt sẽ khóa quy trình. Muốn đổi nội dung, chuẩn bị và duyệt lại.
9. Nếu lỗi, chỉ dùng **Khôi phục sau lỗi đã kiểm tra** khi trạng thái đã được đối chiếu. Kết quả `PENDING` chưa rõ sẽ không tự chạy lại; phải kiểm tra simulator.
10. Hoàn thành mô phỏng → **Duyệt và ký số tài liệu đang xem**. Đây là hành động duyệt rõ ràng cho đúng phiên bản đang hiển thị. Không ký hai lần; kết quả chưa rõ cần kiểm tra, không tự thử lại.
11. Chọn máy in/khổ/số bản trong cấu hình → **Duyệt và in**. Đây là hàng đợi giả, không in giấy thật. Danh sách máy in Windows chỉ để kiểm tra cấu hình.
12. Trang chủ → **Mở HIS Simulator**. Chọn lỗi giả (đổi bệnh nhân, đổi đợt, sai khoa, HIS treo, thiếu quyền ký, kết quả ký chưa rõ, lỗi lưu tờ 2 hoặc lỗi hàng đợi in) để kiểm tra dừng. Không đổi về bình thường rồi mặc định chạy lại thao tác chưa rõ.

## Quản lý mẫu

Điền tên và nội dung ở thẻ nhập dữ liệu, lưu trong Quản lý mẫu. Lưu cùng tên tạo phiên bản mới. Có thể nhân bản, đặt mặc định, xem lịch sử, xuất/nhập JSON, xóa có xác nhận. Mẫu không chứng minh nội dung đúng cho người bệnh. Sao lưu SQLite trước khi nâng cấp. Bản 0.1 chưa có giao diện khôi phục toàn bộ SQLite; có thể nhập lại thư viện mẫu qua JSON.

## Đối chiếu lĩnh dược

Nhập ba đối tượng JSON (y lệnh, tổng hợp và phiếu lĩnh) với cùng mã TEST và số lượng. Ví dụ `{"TEST-BENZ": 2}` ở cả ba nguồn khớp toa có 2 đơn vị; chênh lệch, thiếu mã hoặc thiếu một nguồn đều bị chặn. Chức năng này kiểm tra số lượng trong simulator, chưa kết nối hay tạo phiếu lĩnh trên HIS thật.

## Lỗi và khôi phục

Workflow lưu `PENDING` trước thao tác. Nếu lỗi, quy trình mới chỉ bỏ qua bước khi backend còn chứng minh đúng nội dung đã lưu. Nếu backend mất trạng thái hoặc kết quả mâu thuẫn, cần kiểm tra thủ công. Không xóa nhật ký để ép chạy lại. Simulator mở từ ứng dụng lưu dấu vân tay bản ghi, chữ ký giả và mã lệnh in giả trong SQLite để đối soát qua lần khởi động; không lưu nguyên nội dung hồ sơ. Dùng thời điểm TEST mới khi thử một bộ tờ mới. Simulator EXE riêng là phiên độc lập trong RAM. Chưa có màn hình đối soát khôi phục đầy đủ.

## Triển khai bệnh viện

Chức năng ghi thật đang khóa bằng mã, không có nút bật. Cần quyền của đơn vị quản lý, ánh xạ UIA đã khảo sát, dữ liệu giả trên môi trường được phép, xác nhận bệnh nhân/đợt trên mọi cửa sổ và toàn bộ ma trận nghiệm thu. Không coi kiểm thử simulator là bằng chứng tương thích eHospital.
