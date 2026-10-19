# Bước đầu kết nối eHospital thật – khảo sát chỉ đọc

## Trạng thái
Đã chạy probe chỉ-đọc lại ngày 19-10-2026 trên eHospital 4.0.1.0. Lần này phát hiện 1 tiến trình và 1 cửa sổ UIA kích thước 1936×1048; classifier nhận diện gợi ý `inpatient_record` từ nhãn giao diện tĩnh trong allowlist. Tài khoản vận hành xác nhận phiên đang mở là HIS sản xuất. Gợi ý màn hình không xác minh khoa, bệnh nhân, đợt điều trị hay quyền truy cập. Chưa điều hướng, nhập, lưu, ký, in hoặc đọc dữ liệu hồ sơ. Chức năng ghi HIS, ký và lĩnh dược thật tiếp tục bị khóa.

Probe chỉ đọc loại control, nhãn tĩnh nằm trong allowlist và rect tương đối. Nó không đọc title cửa sổ, nội dung Edit/Text/DataItem, ảnh, DB, mật khẩu hay chứng thư. Báo cáo đã tạo cục bộ ngoài repo tại `%LOCALAPPDATA%\HISAutoAssistant\ehospital-uia-safe.json` và `winforms-metadata-only.json`.

Thông tin phiên bản tệp thực thi ghi nhà cung cấp FPT Information System GMC, Product Version 4.0.0.0, File Version 4.0.1.0, build .NET 4.0 ngày 27-04-2016. FPT công bố FPT.eHospital 2.0+ có thể tích hợp qua nền tảng RESTful API và trang công nghệ FPT mô tả eHospital 2.0 dùng .NET/SQL Server ([FPT.eHospital 2.0+](https://fpt-is.com/ehospital-2-0/), [FPT Healthcare](https://fpt-is.com/en/healthcare/)). Đây là hướng kết nối khả thi cần ưu tiên xác minh với FPT/CNTT; metadata `FileVersion 4.0.1.0` không xác nhận edition/module/API nào đang triển khai hoặc bật ở bệnh viện. Chưa có API contract, endpoint hay cơ chế xác thực dành riêng cho bản cài đặt này.

## Chuẩn bị máy Windows được phép khảo sát
1. Sử dụng một tài khoản và máy có quyền khảo sát kỹ thuật được bệnh viện phê duyệt.
2. Ưu tiên mở màn hình HIS **không hiển thị bệnh nhân thật**, chỉ sử dụng bệnh nhân thử nghiệm.
3. Cài project bằng `python -m pip install -e ".[dev]"`, rồi chạy:

```powershell
python -m his_auto.live_probe
```

4. Báo cáo nằm tại `%LOCALAPPDATA%\HISAutoAssistant\ehospital-uia-safe.json`; Win32 counts/geometry tại `winforms-metadata-only.json`. Không lưu vào thư mục GitHub. Công cụ chỉ ghi **nhãn giao diện tĩnh có trong danh sách cho phép**, loại điều khiển và hình học tương đối. Không truy vấn text của Edit/Text/grid; không thu thập title, screenshot, database, mật khẩu, chứng thư ký hay hồ sơ bệnh nhân.
5. Bộ phận CNTT kiểm tra báo cáo trước khi chia sẻ. Nếu công cụ không nhận diện được nhãn, chưa đủ cơ sở kết luận có thể tự động hóa an toàn.

## Roadmap để tích hợp thật
- CNTT/FPT cung cấp môi trường HIS **kiểm thử** do bệnh viện quản lý, dùng dữ liệu giả; phiên sản xuất hiện tại không dùng để điều hướng hoặc kiểm tra thao tác.
- Ưu tiên xác minh API RESTful chính thức của đúng edition eHospital đang chạy; đề nghị FPT/CNTT cung cấp OpenAPI/đặc tả, module được cấp phép, endpoint test, OAuth/certificate/scopes, operations đọc ngữ cảnh và ghi nghiệp vụ, audit/idempotency, cùng dữ liệu giả.
- Nếu FPT xác nhận không có API cho bản cài đặt, tiếp tục ánh xạ UIA chỉ trên môi trường test được phê duyệt. Không dùng SQL trực tiếp hoặc trích mật khẩu từ cấu hình.
- Chạy công cụ trên các màn hình `BA Nội trú - Ngoại Trú`, `F5`, `F7`, `Phiếu lĩnh dược`, `Crystal Reports`; lưu báo cáo theo từng màn hình khi không có dữ liệu nhạy cảm.
- Dựa vào kết quả, xây bộ `LiveAdapter` với bộ ánh xạ giao diện được xác minh. Không nhấp theo tọa độ đoán mò.
- Kiểm tra bệnh nhân/đợt/khoa qua phương pháp được cấp phép; nếu không xác minh được thì dừng.
- Thử tạo hồ sơ, lưu/đọc lại, ký, in trên môi trường thử nghiệm theo phê duyệt. Giữ các điểm kiểm tra chuyên môn và không tự ký tài liệu chưa duyệt.
- Kiểm thử nhiều máy/DPI/phiên bản HIS rồi xin nghiệm thu mới mở quyền ghi ở môi trường sản xuất.

## Cơ sở dữ liệu
Để tự động hóa theo giao diện **không cần sao chép database**. Nếu phải tra cứu dữ liệu, đề nghị bộ phận CNTT/nhà cung cấp HIS cấp API, bản sao **đã khử nhận dạng**, hoặc quyền **đọc hạn chế** tới môi trường thử nghiệm. Không tìm mật khẩu trong cấu hình hệ thống, không xuất toàn bộ database và không ghi SQL trực tiếp vào bảng HIS.
