# Bước đầu kết nối eHospital thật – khảo sát chỉ đọc

## Trạng thái
Mã nguồn trên nhánh này đã có công cụ kiểm tra cấu trúc điều khiển Windows UI Automation của eHospital đang chạy, **không phải adapter ghi vào HIS**. Chưa có kết quả khảo sát hoặc kiểm thử trên máy bệnh viện. Chức năng ghi HIS, ký và lĩnh dược thật tiếp tục bị khóa.

## Chuẩn bị máy Windows được phép khảo sát
1. Sử dụng một tài khoản và máy có quyền khảo sát kỹ thuật được bệnh viện phê duyệt.
2. Ưu tiên mở màn hình HIS **không hiển thị bệnh nhân thật**, chỉ sử dụng bệnh nhân thử nghiệm.
3. Cài project bằng `python -m pip install -e ".[dev]"`, rồi chạy:

```powershell
python -m his_auto.live_probe
```

4. Báo cáo nằm tại `%LOCALAPPDATA%\HISAutoAssistant\ehospital-uia-safe.json`. Không lưu vào thư mục GitHub. Công cụ chỉ ghi **nhãn giao diện tĩnh có trong danh sách cho phép**, loại điều khiển và hình học tương đối của chúng. Không thu thập title, text ô nhập, screenshot, database, mật khẩu, chứng thư ký, hay hồ sơ bệnh nhân.
5. Bộ phận CNTT kiểm tra báo cáo trước khi chia sẻ. Nếu công cụ không nhận diện được nhãn, chưa đủ cơ sở kết luận có thể tự động hóa an toàn.

## Roadmap để tích hợp thật
- Cung cấp quyền truy cập tới môi trường HIS **kiểm thử** do bệnh viện quản lý, dùng dữ liệu giả.
- Chạy công cụ trên các màn hình `BA Nội trú - Ngoại Trú`, `F5`, `F7`, `Phiếu lĩnh dược`, `Crystal Reports`; lưu báo cáo theo từng màn hình khi không có dữ liệu nhạy cảm.
- Dựa vào kết quả, xây bộ `LiveAdapter` với bộ ánh xạ giao diện được xác minh. Không nhấp theo tọa độ đoán mò.
- Kiểm tra bệnh nhân/đợt/khoa qua phương pháp được cấp phép; nếu không xác minh được thì dừng.
- Thử tạo hồ sơ, lưu/đọc lại, ký, in trên môi trường thử nghiệm theo phê duyệt. Giữ các điểm kiểm tra chuyên môn và không tự ký tài liệu chưa duyệt.
- Kiểm thử nhiều máy/DPI/phiên bản HIS rồi xin nghiệm thu mới mở quyền ghi ở môi trường sản xuất.

## Cơ sở dữ liệu
Để tự động hóa theo giao diện **không cần sao chép database**. Nếu phải tra cứu dữ liệu, đề nghị bộ phận CNTT/nhà cung cấp HIS cấp API, bản sao **đã khử nhận dạng**, hoặc quyền **đọc hạn chế** tới môi trường thử nghiệm. Không tìm mật khẩu trong cấu hình hệ thống, không xuất toàn bộ database và không ghi SQL trực tiếp vào bảng HIS.
