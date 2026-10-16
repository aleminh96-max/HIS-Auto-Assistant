# HIS Auto Assistant

Bản thử nghiệm Windows **0.1.0**, giao diện tiếng Việt và HIS Simulator độc lập. Phát triển theo yêu cầu quản lý hồ sơ nội trú ban ngày. **Mặc định và hiện tại chỉ chạy mô phỏng. Chưa được nghiệm thu trên eHospital thật.**

## Chạy bản EXE

Tải artifact `HIS-Auto-Assistant-trial-win64` trong [GitHub Actions](https://github.com/aleminh96-max/HIS-Auto-Assistant/actions), giải nén toàn bộ rồi mở `HIS-Auto-Assistant/HIS-Auto-Assistant.exe`. Giữ thư mục `_internal` bên cạnh EXE. Simulator riêng: `HIS-Simulator/HIS-Simulator.exe`. Simulator mở từ ứng dụng dùng chung trạng thái; EXE simulator chạy riêng có phiên mô phỏng riêng.

## Chạy từ mã nguồn

Windows 10/11 x64, Python 3.12+:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
his-assistant
# Hoặc: his-simulator
python -m pytest -v --junitxml=test-results.xml
.\scripts\build.ps1
```

## Chức năng bản thử

- Mẫu bệnh án: tạo, sửa, nhân bản, mặc định, lịch sử phiên bản, nhập/xuất JSON và sao lưu SQLite.
- Nhập lâm sàng, ICD thủ công cho nhóm sớm; A53.0 cho nhóm tiềm ẩn; xác nhận lịch sử mũi 1–3.
- Dấu hiệu sinh tồn có thời điểm gốc, kiểm tra định dạng và yêu cầu rà soát số đo bất thường.
- Ba tờ T, T, T+30 phút, xử lý qua ngày; tờ 3 không thuốc; dữ liệu cũ không bị gắn thời điểm đo mới.
- Soạn hai toa riêng từ danh mục TEST khảo sát; không tự tính tổng liều; duyệt hàm lượng, tổng liều, cách dùng, thời gian và an toàn trước khi chạy.
- Dịch vụ tùy chọn; đối chiếu y lệnh, tổng hợp và phiếu lĩnh, chặn số lượng không khớp.
- Workflow có duyệt nội dung, tạm dừng, tiếp tục, Esc dừng khẩn cấp; kiểm tra ngữ cảnh trước/sau từng bước; lưu dấu vết trước thao tác và không tự thử lại kết quả chưa rõ.
- Duyệt chữ ký gắn đúng tài liệu/nội dung; chỉ gửi ký một lần; mô phỏng lệnh in và chống gửi trùng.
- Phát hiện tiến trình eHospital ở chế độ chỉ đọc. Thư viện nhận diện UIA, ảnh và hồ sơ tọa độ tương đối có kiểm tra DPI/thiết bị.

## Giới hạn cần đọc

Workflow hiện gọi **backend simulator** (lưu dấu vân tay trạng thái vào SQLite), không điều khiển eHospital. Cửa sổ simulator hiển thị trạng thái backend và cho phép gây lỗi. Các thẻ báo cáo, lĩnh dược và bảng thuốc là khung mô phỏng; chưa tái tạo toàn bộ hộp thoại HIS. Chữ ký không phải chữ ký điện tử thật; lệnh in không gửi ra máy in; chưa có PDF trình duyệt/SAP Crystal Reports thật. Chưa có adapter ghi HIS, wizard hiệu chỉnh hoàn chỉnh, cài đặt Windows, hay nghiệm thu đa máy. Xem [ma trận kiểm chứng](docs/VERIFICATION.md) và [hướng dẫn tiếng Việt](docs/USER_GUIDE.vi.md).

## Dữ liệu

Chỉ dùng hồ sơ giả để thử. Dữ liệu mẫu, cấu hình và trạng thái chống trùng nằm tại `%LOCALAPPDATA%\HISAutoAssistant\assistant.sqlite3`; nhật ký giới hạn 1.000 sự kiện và không lưu nội dung bệnh án/định danh bệnh nhân. SQLite **chưa mã hóa**; chưa phù hợp lưu dữ liệu thật. Không đọc database HIS, không lưu mật khẩu/token/khóa ký, không gọi dịch vụ AI.

Repo do người dùng cung cấp đang **công khai**. Không đưa dữ liệu thật, tài khoản hoặc tệp cấu hình khảo sát nhạy cảm lên repo. Bản thử chưa đạt toàn bộ tiêu chí nghiệm thu của master prompt.
