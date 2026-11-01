# Sơ đồ giao diện eHospital 4.0.1.0 – khảo sát hình ảnh (không chứa dữ liệu bệnh nhân)

**Nguồn:** 12 ảnh do người sử dụng cung cấp để xác định vùng giao diện. Ảnh gốc chứa dữ liệu người bệnh và **không được lưu vào repository công khai, CI artifacts hoặc log**.

**Trạng thái:** SCREENSHOT_REVIEWED; metadata UIA/Win32 chỉ đọc đã chạy trên eHospital 4.0.1.0. Lần probe 2026-10-19 nhận diện 1 cửa sổ 1936×1048 với gợi ý `inpatient_record` từ nhãn tĩnh allowlist. Người vận hành xác nhận đây là HIS sản xuất. Nhãn giao diện không xác minh khoa, bệnh nhân, đợt điều trị hay quyền. Chưa xác minh AutomationId/Name của trường nghiệp vụ, chưa điều hướng, nhập hoặc lưu trên HIS.

## Kết quả khảo sát metadata-only trên máy

- Product Version 4.0.0.0 / File Version 4.0.1.0.
- Probe UIA mới nhất thấy một tiến trình và một cửa sổ 1936×1048; classifier đưa ra gợi ý `inpatient_record`. Kết quả này không chứng minh được khoa, bệnh nhân, đợt điều trị hoặc quyền truy cập.
- Baseline Win32 trước đó ghi nhận hai tiến trình và bốn cửa sổ (311×102, 1936×1048, 476×369, 1936×1048); chưa chạy lại Win32 probe cùng lần kiểm tra mới.
- Win32 đếm lớp control và rect tương đối; lớp `WindowsForms10.EDIT` có số lượng 1, 139, 3 và 37 theo bốn cửa sổ. Đây chưa phải ánh xạ trường; không có giá trị edit nào được đọc.
- Báo cáo JSON chỉ lưu tại `%LOCALAPPDATA%\HISAutoAssistant`, không nằm trong repo. Không chứa title, ảnh, nội dung bệnh nhân hoặc giá trị trường.
- File metadata ghi nhà cung cấp FPT Information System GMC, Product Version 4.0.0.0 và File Version 4.0.1.0. Tài liệu API/endpoint riêng cho bản cài đặt này chưa được cung cấp.

## Điều kiện chung trước mọi thao tác có tác động

- Chỉ làm việc với tiến trình `eHospital.exe` có đường dẫn được CNTT xác minh, tại chức năng `QLBA Nội Trú - Ngoại Trú → BA Nội trú - Ngoại Trú` và thuộc **Khoa Điều trị Nội trú ban ngày**. Không dựa riêng dòng khoa hiển thị trên status bar.
- Luồng được phép điều hướng sang F5, F7, phiếu lĩnh dược, trình xem ký số và in nhưng phải liên tục xác minh **đúng người bệnh/đợt điều trị/khoa** qua định danh được cấp quyền. Nếu thiếu chứng cứ thì dừng.
- Không tự bấm, nhập, lưu, ký hay in trên HIS sản xuất trong giai đoạn khảo sát. Sau khi được phê duyệt, những y lệnh và tài liệu có tính chuyên môn phải được bác sĩ duyệt chính nội dung trước thao tác.
- Ưu tiên UIA control ID/Name/Type (chỉ lấy nhãn tĩnh đã lọc); kết hợp Win32 class, layout anchors và xác minh trạng thái sau mỗi thao tác. Không chọn tọa độ cố định theo ảnh.

## Màn hình đã nhận diện bằng ảnh

| Screen key | Tên cửa sổ theo ảnh | Bằng chứng giao diện | Vai trò |
| --- | --- | --- | --- |
| `inpatient_record` | BA Nội trú - Ngoại Trú | tab **Hành chính, quản lý người bệnh**, **Chẩn đoán**, **Tổng kết Bệnh án**; thanh **Sửa/Lưu** | Bắt đầu quy trình, xác minh khoa và người bệnh; sửa chẩn đoán sau khi duyệt |
| `admission_exam_reference` | Phiếu Khám Bệnh Vào Viện | tab **Thông tin chung**, **Khám bệnh**; khối khám, CLS, dấu hiệu sinh tồn | **Chỉ là nguồn tham khảo**; KHÔNG phải màn hình khởi động workflow và KHÔNG tự ghi trong bản giang mai V1 |
| `service_registration` | Đăng Ký Dịch Vụ | **Nhóm dịch vụ**, **Mã dịch vụ**, danh sách dịch vụ và cột **Chọn In**; nút **Xác nhận ký** | F5, chuẩn bị/chỉ định dịch vụ và ký sau duyệt |
| `treatment_sheet` | Phiếu theo dõi điều trị | danh sách tờ trái; **S (Hỏi bệnh)**, **O.1 (Khám bệnh)**, **O.3 (Kết quả xét nghiệm, CLS)**, **A**, **P**; radio **Mua ngoài/Cấp thuốc**; bảng thuốc | F7, ba tờ điều trị và các lệnh in |
| `pharmacy_requisition` | Phiếu Lĩnh Dược | **Nơi lập phiếu**, **Nơi sẽ giao**, **Nguồn dược**, **Loại phiếu lĩnh**, **Tổng Hợp Y Lệnh**; bảng **SL yêu cầu** | Dược Phẩm → Phiếu Lĩnh Dược |

### BA Nội trú – tab Chẩn đoán

- Có **nhiều khu vực chẩn đoán**: khối chẩn đoán hiện tại bên trái, khối chẩn đoán/ICD ra viện bên phải, và trường **Tình trạng ra viện**. Không coi chúng là một trường duy nhất.
- `A53.0` là mã cấu hình cho **giang mai tiềm ẩn không xác định sớm/muộn**; giang mai sớm để bác sĩ tự chọn. Không tự ghi tình trạng ra viện khi chưa duyệt và chưa đúng thời điểm.
- Các ô ICD có ô mã, nút chọn danh mục và nhãn diễn giải; cần đối chiếu **mã và diễn giải** trước khi lưu.

### F5 – Đăng ký dịch vụ

- Có danh sách nhiều dòng dịch vụ. Trong ảnh có cả dịch vụ khám và các dịch vụ điều trị/kiểm tra. **Không mặc định tất cả dòng đang hiển thị đều là chỉ định mẫu cần thêm mới**.
- Checkbox ở đầu dòng và checkbox cột **Chọn In** là **hai cột khác nhau**. Không dùng trạng thái tích ở đầu dòng làm bằng chứng `Chọn In = true`. Trước khi tích cần đọc trạng thái hiện tại.
- Phải xác minh dịch vụ thực sự nằm trong phiếu trước khi quyết định thêm; không tạo chỉ định trùng.
- Nút ký trên F5 được thể hiện với nhãn **Xác nhận ký** (không giống hoàn toàn nhãn ở màn hình bệnh án `Xác nhận ký số`). Cần ánh xạ riêng theo màn hình; chỉ kích hoạt sau khi tài liệu đúng nội dung được duyệt bởi người có thẩm quyền.

### F7 – Phiếu theo dõi điều trị

- Danh sách bên trái có nhiều tờ với thời điểm riêng; **không thể kết luận tờ nào là 1/2/3 chỉ dựa thứ tự hiển thị**.
- Mẫu workflow dự kiến tờ 1=T, tờ 2=T và tờ 3=T+30 phút. Các tờ cũ trên màn hình có giờ khác nhau, vì vậy **phải đọc trạng thái đã tồn tại và yêu cầu bác sĩ xác minh**, không sửa để khớp template và không tạo trùng.
- Dấu hiệu sinh tồn trong các ảnh không hoàn toàn đồng nhất; mỗi số đo cần lưu thời điểm đo thật, không tự sao chép như lần đo mới.
- Chọn riêng `Cấp thuốc` → `Kho miễn phí` và `Mua ngoài` → `Nhà thuốc`. Đừng suy ra ô được chọn từ màu giao diện nếu không đọc được trạng thái radio.
- Bảng thuốc có các cột thời điểm/buổi, **Số ngày**, **SL**, **Cách dùng**, **Ghi chú**, **Không tính tiền**; vị trí có thể đổi theo cuộn ngang và độ phân giải.
- Một ảnh toa cấp thuốc cho thấy số lượng dự kiến **2 lọ**; ảnh toa mua ngoài chỉ cho thấy **một phần** các vật tư mẫu, không đủ bằng chứng có toàn bộ 5 mặt hàng. Phải dùng danh sách được phê duyệt, đối chiếu trước khi thêm hoặc in.
- Các lệnh in `In phiếu công khai thuốc` và `In phiếu theo dõi điều trị` là nút riêng; chỉ coi hoàn tất sau khi xác minh đúng báo cáo và lệnh in.

### Phiếu lĩnh dược

- Màn hình có trạng thái phiếu mới và phiếu đã có dữ liệu, cùng các thông tin kho gửi/nhận, ngày, mục đích, loại phiếu và bảng danh mục.
- Ảnh phiếu đã có dữ liệu hiển thị số lượng yêu cầu **2 lọ**, nhưng chỉ đối chiếu qua dữ liệu y lệnh được duyệt trong trường hợp thực tế. Không tự điều chỉnh số lượng và không mặc nhiên kết luận phiếu đã lưu/in thành công.
- Nút `Tổng Hợp Y Lệnh` phụ thuộc trạng thái màn hình; cần phát hiện nút đang enabled/disabled, không click khi chưa hợp lệ.

## Những việc còn lại để chuyển từ khảo sát sang adapter thực tế

1. Khảo sát **control ID, control type, enabled/checked state** của từng trường trong môi trường HIS test hoặc bệnh nhân giả được bệnh viện cho phép; loại bỏ dữ liệu riêng tư ở mọi đầu ra.
2. Tạo `ScreenLocator` theo **PID + top-level window + tab + nhãn mốc tĩnh**, đối chiếu màn hình hiện tại, cảnh báo cửa sổ mơ hồ.
3. Ánh xạ `inpatient_record`, `service_registration`, `treatment_sheet`, `pharmacy_requisition` tới workflow; `admission_exam_reference` giữ read-only.
4. Tạo `LiveAdapter` có cấu trúc: detect → identify → verify identity → draft review → write ONE approved action → read-back verify; không bật trên production trước khi có môi trường test và nghiệm thu.
5. Kiểm chứng lần lượt **F5, F7, các popup thuốc, popup ký, PDF browser, Crystal Reports và Phiếu Lĩnh Dược**; báo trạng thái `VERIFIED` / `NOT VERIFIED` theo từng trường/bước.
6. Chạy các test sai bệnh nhân, mất focus, lỗi mạng, timeout lưu/ký/in, quyền không đủ, radio/checkbox đã chọn, khác DPI, qua ngày và hồi phục sau crash. Không tự retry thao tác có side effect chưa rõ trạng thái.

**Cảnh báo riêng tư:** 12 ảnh gốc chứa thông tin nhận dạng người bệnh. Không sao chép ảnh vào tài liệu hoặc commit; nếu dùng để hiệu chỉnh nội bộ phải được khử định danh, lưu theo quy định cơ sở y tế và xóa khi không còn cần thiết.
